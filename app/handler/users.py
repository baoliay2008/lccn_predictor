from datetime import datetime, timedelta

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.constants import (
    DEFAULT_NEW_USER_ATTENDED_CONTESTS_COUNT,
    DEFAULT_NEW_USER_RATING,
)
from app.crawler.users import request_user_rating_and_attended_contests_count
from app.db.models import DATA_REGION, ContestRecordArchive, ContestRecordPredict, User
from app.db.mongodb import get_async_mongodb_collection
from app.utils import exception_logger_reraise, gather_with_limited_concurrency


async def upsert_users_rating_and_attended_contests_count(
    data_region: DATA_REGION,
    username: str,
) -> None:
    """
    Upsert users rating and attendedContestsCount by sending HTTP request to get latest data.
    :param data_region:
    :param username:
    :return:
    """
    try:
        (
            rating,
            attended_contests_count,
        ) = await request_user_rating_and_attended_contests_count(data_region, username)
        if rating is None:
            logger.info(
                f"graphql data is None, new user found, {data_region=} {username=}"
            )
            rating = DEFAULT_NEW_USER_RATING
            attended_contests_count = DEFAULT_NEW_USER_ATTENDED_CONTESTS_COUNT
        user = User(
            username=username,
            user_slug=username,
            data_region=data_region,
            attendedContestsCount=attended_contests_count,
            rating=rating,
        )
        await User.find_one(
            User.username == user.username,
            User.data_region == user.data_region,
        ).upsert(
            Set(
                {
                    User.update_time: user.update_time,
                    User.attendedContestsCount: user.attendedContestsCount,
                    User.rating: user.rating,
                }
            ),
            on_insert=user,
        )
    except Exception as e:
        logger.exception(f"user update error. {data_region=} {username=} Exception={e}")


@exception_logger_reraise
async def save_users_of_contest(
    contest_name: str,
    predict: bool,
) -> None:
    """
    Update all users' rating and attendedContestsCount.
    For the ContestRecordPredict collection, don't update users who have a zero score or were updated recently.
    :param contest_name:
    :param predict:
    :return:
    """
    if predict:
        col = get_async_mongodb_collection(ContestRecordPredict.__name__)
        pipeline = [
            {"$match": {"contest_name": contest_name, "score": {"$ne": 0}}},
            {
                "$lookup": {
                    "from": "User",
                    "let": {"data_region": "$data_region", "username": "$username"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$data_region", "$$data_region"]},
                                        {"$eq": ["$username", "$$username"]},
                                        {
                                            "$gte": [
                                                "$update_time",
                                                datetime.utcnow() - timedelta(hours=36),
                                            ]
                                        },
                                    ]
                                }
                            }
                        },
                    ],
                    "as": "recent_updated_user",
                }
            },
            {"$match": {"recent_updated_user": {"$eq": []}}},
            {"$project": {"_id": 0, "data_region": 1, "username": 1}},
        ]
    else:
        col = get_async_mongodb_collection(ContestRecordArchive.__name__)
        pipeline = [
            {"$match": {"contest_name": contest_name}},
            {"$project": {"_id": 0, "data_region": 1, "username": 1}},
        ]
    cursor = col.aggregate(pipeline)
    docs = await cursor.to_list(length=None)
    cn_tasks = []
    us_tasks = []
    for doc in docs:
        if doc["data_region"] == "CN":
            cn_tasks.append(
                upsert_users_rating_and_attended_contests_count(
                    doc["data_region"], doc["username"]
                )
            )
        else:
            us_tasks.append(
                upsert_users_rating_and_attended_contests_count(
                    doc["data_region"], doc["username"]
                )
            )
    await gather_with_limited_concurrency(
        [
            # CN site has a strong rate limit
            gather_with_limited_concurrency(cn_tasks, 1),
            gather_with_limited_concurrency(us_tasks, 8),
        ],
    )
