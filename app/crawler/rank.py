from datetime import datetime
from math import ceil
import asyncio

import httpx
from beanie.odm.operators.update.general import Set

from app.crawler.utils import multi_http_request
from app.db.models import ContestPredict, ContestFinal


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
    for i in range(293, 100, -1):
        # await save_historical_contest(contest_name=f"weekly-contest-{i}")
        await check_contest_user_num(contest_name=f"weekly-contest-{i}")
    for i in range(78, 0, -1):
        # await save_historical_contest(contest_name=f"biweekly-contest-{i}")
        await check_contest_user_num(contest_name=f"biweekly-contest-{i}")

