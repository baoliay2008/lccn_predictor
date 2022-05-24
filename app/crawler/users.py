import asyncio
from datetime import datetime

from app.crawler.utils import multi_http_request
from app.db.models import ContestFinal, User, ContestPredict
from app.db.mongodb import get_async_mongodb_connection

DEFAULT_RATING_FOR_NEWCOMER = '{"attendedContestsCount": 0, "rating": 1500}'


async def multi_insert(graphql_response_list, user_dict_list):
    update_tasks = list()
    for response, user_dict in zip(graphql_response_list, user_dict_list):
        if response is None:
            continue
        data = response.json().get("data", {}).get("userContestRanking")
        print(user_dict, data)
        if data is None:
            # should insert DEFAULT_RATING_FOR_NEWCOMER here
            continue
        user_dict.pop("_id")
        user_dict.update({"update_time": datetime.utcnow()})
        user_dict.update(data)
        user = User.parse_obj(user_dict)
        update_tasks.append(User.insert_one(user))
    await asyncio.gather(*update_tasks)


async def multi_request_user_cn(cn_multi_request_list):
    cn_response_list = await multi_http_request(
        {
            user_dict["user_slug"]: {
                "url": "https://leetcode-cn.com/graphql/noj-go/",
                "method": "POST",
                "json": {
                    "query": """
                                             query userContestRankingInfo($userSlug: String!) {
                                                     userContestRanking(userSlug: $userSlug) {
                                                         attendedContestsCount
                                                         rating
                                                         globalRanking
                                                         topPercentage
                                                         localRanking
                                                         globalTotalParticipants
                                                         localTotalParticipants
                                                     }
                                                 }
                                             """,
                    "variables": {"userSlug": user_dict["user_slug"]},
                },
            }
            for user_dict in cn_multi_request_list
        },
        concurrent_num=10,
    )
    await multi_insert(cn_response_list, cn_multi_request_list)
    cn_multi_request_list.clear()


async def multi_request_user_us(us_multi_request_list):
    us_response_list = await multi_http_request(
        {
            user_dict["username"]: {
                "url": "https://leetcode.com/graphql/",
                "method": "POST",
                "json": {
                    "query": """
                                             query getContestRankingData($username: String!) {
                                                userContestRanking(username: $username) {
                                                    attendedContestsCount
                                                    rating
                                                    globalRanking
                                                    topPercentage
                                                    totalParticipants
                                                }
                                             }
                                             """,
                    "variables": {"username": user_dict["username"]},
                },
            }
            for user_dict in us_multi_request_list
        },
        concurrent_num=10,
    )
    await multi_insert(us_response_list, us_multi_request_list)
    us_multi_request_list.clear()


async def insert_users_of_a_contest(contest_name, predict=True):
    # currently there is no distinct method in beanie
    # https://github.com/roman-right/beanie/pull/268/commits
    # here have to write raw mongo queries, aggregate, or iterate on duplicated username
    if predict:
        col = get_async_mongodb_connection(ContestPredict.__name__)
    else:
        col = get_async_mongodb_connection(ContestFinal.__name__)
    cn_multi_request_list = list()
    us_multi_request_list = list()
    concurrent_num = 200
    async for doc in col.aggregate(
        [
            {"$match": {"contest_name": contest_name}},
            {"$sort": {"rank": 1}},
            {
                "$group": {
                    "_id": "$username",
                    "username": {"$first": "$username"},
                    "user_slug": {"$first": "$user_slug"},
                    "data_region": {"$first": "$data_region"},
                }
            },
        ]
    ):
        if await User.find_one(User.username == doc["username"]):
            continue
        if len(cn_multi_request_list) + len(us_multi_request_list) >= concurrent_num:
            print(f"run multi_request_list \n"
                  f"cn_multi_request_list{cn_multi_request_list}\n"
                  f"us_multi_request_list{us_multi_request_list}")
            await asyncio.gather(
                multi_request_user_cn(cn_multi_request_list),
                multi_request_user_us(us_multi_request_list),
            )
        if doc["data_region"] == "CN":
            cn_multi_request_list.append(doc)
        elif doc["data_region"] == "US":
            us_multi_request_list.append(doc)
        else:
            print("fatal error: data_region is not CN or US. doc={doc}")


async def insert_historical_contests_users():
    # for i in range(293, 100, -1):
    #     await insert_users_of_a_contest(contest_name=f"weekly-contest-{i}", predict=False)
    # for i in range(78, 0, -1):
    #     await insert_users_of_a_contest(contest_name=f"biweekly-contest-{i}", predict=False)
    for i in range(278, 100, -1):
        await insert_users_of_a_contest(contest_name=f"weekly-contest-{i}", predict=False)



