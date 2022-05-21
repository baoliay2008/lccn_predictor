from datetime import datetime
from math import ceil
from typing import List, Dict, Optional
import json
from collections import deque, defaultdict
import asyncio
import httpx
from beanie.odm.operators.update.general import Set

from app.db.models import ContestPredict, ContestFinal


DEFAULT_RATING_FOR_NEWCOMER = '{"attendedContestsCount": 0, "rating": 1500}'


async def multi_http_request(
    multi_requests: Dict,
    concurrent_num: int = 5,
) -> List[Optional[httpx.Response]]:
    response_mapper = defaultdict(int)  # values means: [int: retried time / Response: successful result]
    crawler_queue = deque(multi_requests.items())
    total_num = len(crawler_queue)
    # gradually adjust wait_time by detect number of failed requests in the last round.
    wait_time = 0
    while crawler_queue:
        requests_list = list()
        # gradually increase wait_time according to max retry times
        # wait_time = response_mapper[job_queue[-1][0]]
        while len(requests_list) < concurrent_num and crawler_queue:
            key, request = crawler_queue.popleft()
            if response_mapper[key] >= 10:
                continue
            requests_list.append((key, request))
        if not requests_list:
            break
        print(f"remaining={len(crawler_queue) / total_num * 100 :.2f}% wait_time={wait_time} "
              f"requests_list={[(key, response_mapper[key]) for key, request in requests_list]}")
        await asyncio.sleep(wait_time)
        async with httpx.AsyncClient() as client:
            tasks = [client.request(**request) for key, request in requests_list]
            response_list = await asyncio.gather(*tasks, return_exceptions=True)
            wait_time = 0
            for response, (key, request) in zip(response_list, requests_list):
                if isinstance(response, httpx.Response) and response.status_code == 200:
                    # TODO: Very high memory usage here when saving response directly, say, if run 20000 requests.
                    response_mapper[key] = response
                else:
                    print(f"multi_http_request_with_retry error: {response}")
                    response_mapper[key] += 1
                    wait_time += 1
                    crawler_queue.append((key, request))
    return [
        None if isinstance(response, int) else response
        for key, response in response_mapper.items()
    ]


async def get_user_rating_cn(user_list) -> None:
    response_list = await multi_http_request(
        {
            user["user_slug"]: {
                "url": "https://leetcode-cn.com/graphql/noj-go/",
                "method": "POST",
                "json": {
                    "query": """
                                query userContestRankingInfo($userSlug: String!) {
                                         userContestRanking(userSlug: $userSlug) {
                                             attendedContestsCount
                                             rating
                                             globalRanking
                                             localRanking
                                             globalTotalParticipants
                                             localTotalParticipants
                                             topPercentage
                                         }
                                     }
                            """,
                    "variables": {"userSlug": user["user_slug"]},
                },
            }
            for user in user_list
        }
    )
    for response, user in zip(response_list, user_list):
        if response is None:
            continue
        data = response.json().get("data")
        user.update(
            data["userContestRanking"] or json.loads(DEFAULT_RATING_FOR_NEWCOMER)
        )


async def get_user_rating_us(user_list) -> None:
    response_list = await multi_http_request(
        {
            user["user_slug"]: {
                "url": "https://leetcode.com/graphql/",
                "method": "POST",
                "json": {
                    "query": """
                                query getContestRankingData($username: String!) {
                                    userContestRanking(username: $username) {
                                        attendedContestsCount
                                        rating
                                        globalRanking
                                        totalParticipants
                                        topPercentage
                                    }
                                }
                            """,
                    "variables": {"username": user["username"]},
                },
            }
            for user in user_list
        }
    )
    for response, user in zip(response_list, user_list):
        if response is None:
            continue
        data = response.json().get("data")
        user.update(
            data["userContestRanking"] or json.loads(DEFAULT_RATING_FOR_NEWCOMER)
        )


async def update_user_rating(user_list):
    # Notice that if a user didn't attend any contests, return data will be `{'userContestRanking': None}`,
    # and this issue has been taken care of in `get_user_rating_cn` and `get_user_rating_us` by using default value
    cn_user_list = list()
    us_user_list = list()
    for user in user_list:
        if user.get("data_region") == "CN":
            cn_user_list.append(user)
        else:
            us_user_list.append(user)
    await asyncio.gather(
        get_user_rating_cn(cn_user_list), get_user_rating_us(us_user_list)
    )


async def get_single_contest_ranking(contest_name: str):
    # weekly-contest-293
    # biweekly-contest-78
    req = httpx.get(
        f"https://leetcode.com/contest/api/ranking/{contest_name}/",
        timeout=60
    )
    data = req.json()
    user_num = data.get("user_num")
    page_max = ceil(user_num / 25)
    user_rank_list = list()
    url_list = [
        f"https://leetcode.com/contest/api/ranking/{contest_name}/?pagination={page}&region=global"
        for page in range(1, page_max + 1)
    ]
    responses = await multi_http_request(
        {url: {"url": url, "method": "GET"} for url in url_list}
    )
    for res in responses:
        if res is None:
            continue
        user_rank_list.extend(res.json().get("total_rank"))
    return user_rank_list


async def save_temporary_contest(contest_name):
    async def _insert_one_if_not_exists(_user_rank):
        # must insert one time here, because
        doc = await ContestPredict.find_one(
            ContestPredict.contest_name == _user_rank.contest_name,
            ContestPredict.username == _user_rank.username,
        )
        if doc:
            print(f"doc found, won't insert. {doc}")
        await ContestPredict.insert_one(_user_rank)
    user_rank_list = await get_single_contest_ranking(contest_name)
    user_rank_objs = list()
    for user_rank_dict in user_rank_list:
        user_rank_dict.update({"contest_name": contest_name, "insert_time": datetime.utcnow()})
        user_rank = ContestPredict.parse_obj(user_rank_dict)
        user_rank_objs.append(user_rank)
    tasks = (
        _insert_one_if_not_exists(user_rank) for user_rank in user_rank_objs
    )
    await asyncio.gather(*tasks)


async def save_historical_contest(contest_name):
    user_rank_list = await get_single_contest_ranking(contest_name)
    user_rank_objs = list()
    for user_rank_dict in user_rank_list:
        user_rank_dict.update({"contest_name": contest_name, "update_time": datetime.utcnow()})
        user_rank = ContestFinal.parse_obj(user_rank_dict)
        user_rank_objs.append(user_rank)
    tasks = (
        ContestFinal.find_one(
            ContestFinal.contest_name == user_rank.contest_name,
            ContestFinal.username == user_rank.username,
        ).upsert(
            Set({
                ContestFinal.rank: user_rank.rank,
                ContestFinal.score: user_rank.score,
                ContestFinal.finish_time: user_rank.finish_time,
                ContestFinal.update_time: user_rank.update_time,
            }),
            on_insert=user_rank,
        )
        for user_rank in user_rank_objs
    )
    await asyncio.gather(*tasks)


async def check_contest_user_num(contest_name):
    req = httpx.get(
        f"https://leetcode.com/contest/api/ranking/{contest_name}/",
        timeout=60
    )
    data = req.json()
    user_num = data.get("user_num")
    final_num = await ContestFinal.find(ContestFinal.contest_name == contest_name).count()
    predict_num = await ContestPredict.find(ContestPredict.contest_name == contest_name).count()
    print(f"check_contest_user_num {contest_name}. total {user_num}, final {final_num}, predict {predict_num}")
    print(f"final get all records? {user_num == final_num}")
    print(f"predict get all records? {user_num == predict_num}")


async def start_crawler():
    # await save_temporary_contest(contest_name="weekly-contest-293")
    for i in range(293, 62, -1):
        # await save_historical_contest(contest_name=f"weekly-contest-{i}")
        await check_contest_user_num(contest_name=f"weekly-contest-{i}")
    for i in range(61, 0, -1):
        # await save_historical_contest(contest_name=f"weekly-contest-{i}")
        await check_contest_user_num(contest_name=f"weekly-contest-{i}")
    for i in range(78, 0, -1):
        # await save_historical_contest(contest_name=f"biweekly-contest-{i}")
        await check_contest_user_num(contest_name=f"biweekly-contest-{i}")

