import json
import asyncio
import traceback
from datetime import datetime

import httpx

from app.crawler.utils import multi_http_request
from app.db.models import ContestFinal, User
from app.db.mongodb import get_async_mongodb_connection

DEFAULT_RATING_FOR_NEWCOMER = '{"attendedContestsCount": 0, "rating": 1500}'


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


async def post_user_contest_ranking_info_cn(user_slug):
    async with httpx.AsyncClient() as client:  # TODO: take out client to reuse.
        response = await client.post(
            url="https://leetcode-cn.com/graphql/noj-go/",
            json={
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
                "variables": {"userSlug": user_slug},
            },
        )
        if response.status_code == 200:
            return response.json().get("data", {}).get("userContestRanking")
        else:
            print(
                f"post_user_contest_ranking_info_cn request failed. username {user_slug}, {response.status_code}"
            )
            return {}


async def post_user_contest_ranking_info_us(username):
    async with httpx.AsyncClient() as client:  # TODO: take out client to reuse.
        response = await client.post(
            url="https://leetcode.com/graphql/",
            json={
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
                "variables": {"username": username},
            },
        )
        if response.status_code == 200:
            return response.json().get("data", {}).get("userContestRanking")
        else:
            print(
                f"post_user_contest_ranking_info_us request failed. username {username}, {response.status_code}"
            )
            return


async def insert_users():
    # currently there is no distinct method in beanie
    # https://github.com/roman-right/beanie/pull/268/commits
    # here have to write raw mongo queries, aggregate, or iterate on duplicated username

    col = get_async_mongodb_connection(ContestFinal.__name__)

    i = 0
    async for doc in col.aggregate(
        [
            {
                "$group": {
                    "_id": "$username",
                    "username": {"$first": "$username"},
                    "user_slug": {"$first": "$user_slug"},
                    "data_region": {"$first": "$data_region"},
                }
            }
        ]
    ):
        i += 1
        if await User.find_one(User.username == doc["username"]):
            continue
        if doc["data_region"] == "CN":
            user_contest_ranking_info = await post_user_contest_ranking_info_cn(
                doc["user_slug"]
            )
        elif doc["data_region"] == "US":
            user_contest_ranking_info = await post_user_contest_ranking_info_us(
                doc["username"]
            )
        else:
            raise ValueError(f"data_region is not CN or US. doc={doc}")
        if user_contest_ranking_info is None:
            print(f"cannot find user_contest_ranking_info of {doc['username']}")
            continue
        try:
            user = User(
                username=doc["username"],
                user_slug=doc["user_slug"],
                data_region=doc["data_region"],
                update_time=datetime.utcnow(),
                attendedContestsCount=user_contest_ranking_info[
                    "attendedContestsCount"
                ],
                rating=user_contest_ranking_info["rating"],
                globalRanking=user_contest_ranking_info["globalRanking"],
                topPercentage=user_contest_ranking_info["topPercentage"],
            )
            if doc["data_region"] == "CN":
                user.localRanking = user_contest_ranking_info["localRanking"]
                user.globalTotalParticipants = user_contest_ranking_info[
                    "globalTotalParticipants"
                ]
                user.localTotalParticipants = user_contest_ranking_info[
                    "localTotalParticipants"
                ]
            else:
                user.totalParticipants = user_contest_ranking_info["totalParticipants"]
            await User.insert_one(user)
            print(f"successfully insert user {i}th {user}")
        except Exception as e:
            print(f"insert users error of {e}")
            traceback.print_exc()
