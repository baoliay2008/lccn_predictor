from typing import List, Dict, Tuple
from math import ceil
import asyncio

from loguru import logger
import httpx
from beanie.odm.operators.update.general import Set

from app.crawler.contest import fill_questions_field
from app.crawler.users import save_users_of_contest
from app.crawler.utils import multi_http_request
from app.db.models import ContestRecordPredict, ContestRecordArchive, User, Submission
from app.db.mongodb import get_async_mongodb_collection
from app.utils import epoch_time_to_utc_datetime


async def request_contest_ranking(
    contest_name: str,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    req = httpx.get(
        f"https://leetcode.com/contest/api/ranking/{contest_name}/",
        timeout=60,
    )
    data = req.json()
    user_num = data.get("user_num")
    questions_list = data.get("questions")
    page_max = ceil(user_num / 25)
    user_rank_list = list()
    nested_submission_list = list()
    url_list = [
        f"https://leetcode.com/contest/api/ranking/{contest_name}/?pagination={page}&region=global"
        for page in range(1, page_max + 1)
    ]
    responses = await multi_http_request(
        {url: {"url": url, "method": "GET"} for url in url_list},
        concurrent_num=10,
    )
    for res in responses:
        if res is None:
            continue
        res_dict = res.json()
        user_rank_list.extend(res_dict.get("total_rank"))
        nested_submission_list.extend(res_dict.get("submissions"))
    return user_rank_list, nested_submission_list, questions_list


async def save_submission(
        contest_name: str,
        user_rank_list: List[Dict],
        nested_submission_list: List[Dict],
        questions_list: List[Dict],
) -> None:
    question_credit_mapper = {
        question["question_id"]: question["credit"]
        for question in questions_list
    }
    submission_objs = list()
    for user_rank_dict, nested_submission_dict in zip(user_rank_list, nested_submission_list):
        for k, value_dict in nested_submission_dict.items():
            nested_submission_dict[k].pop("id")
            nested_submission_dict[k] |= {
                        "contest_name": contest_name,
                        "username": user_rank_dict["username"],
                        "date": epoch_time_to_utc_datetime(value_dict["date"]),
                        "credit": question_credit_mapper[value_dict["question_id"]],
                    }
        submission_objs.extend(
            [
                Submission.parse_obj(value_dict)
                for value_dict in nested_submission_dict.values()
            ]
        )
    tasks = [
        Submission.find_one(
            Submission.contest_name == submission.contest_name,
            Submission.username == submission.username,
            Submission.data_region == submission.data_region,
            Submission.question_id == submission.question_id,
        ).upsert(
            Set({
                Submission.date: submission.date,
                Submission.fail_count: submission.fail_count,
                Submission.update_time: submission.update_time,
            }),
            on_insert=submission,
        )
        for submission in submission_objs
    ]
    await asyncio.gather(*tasks)


async def save_predict_contest_records(
    contest_name: str,
) -> None:
    async def _insert_one_if_not_exists(_user_rank):
        # must insert once here
        doc = await ContestRecordPredict.find_one(
            ContestRecordPredict.contest_name == _user_rank.contest_name,
            ContestRecordPredict.username == _user_rank.username,
            ContestRecordPredict.data_region == _user_rank.data_region,
        )
        if doc:
            logger.info(f"doc found, won't insert. {doc}")
        else:
            await ContestRecordPredict.insert_one(_user_rank)
    user_rank_list, nested_submission_list, questions_list = await request_contest_ranking(contest_name)
    user_rank_objs = list()
    for user_rank_dict in user_rank_list:
        user_rank_dict.update({"contest_name": contest_name})
        user_rank = ContestRecordPredict.parse_obj(user_rank_dict)
        user_rank_objs.append(user_rank)
    tasks = (
        _insert_one_if_not_exists(user_rank) for user_rank in user_rank_objs
    )
    await asyncio.gather(*tasks)
    await save_users_of_contest(contest_name=contest_name)
    await fill_questions_field(contest_name, questions_list)


async def save_archive_contest_records(
        contest_name: str,
) -> None:
    user_rank_list, nested_submission_list, questions_list = await request_contest_ranking(contest_name)
    user_rank_objs = list()
    for user_rank_dict in user_rank_list:
        user_rank_dict.update({"contest_name": contest_name})
        user_rank = ContestRecordArchive.parse_obj(user_rank_dict)
        user_rank_objs.append(user_rank)
    tasks = (
        ContestRecordArchive.find_one(
            ContestRecordArchive.contest_name == user_rank.contest_name,
            ContestRecordArchive.username == user_rank.username,
            ContestRecordArchive.data_region == user_rank.data_region,
        ).upsert(
            Set({
                ContestRecordArchive.rank: user_rank.rank,
                ContestRecordArchive.score: user_rank.score,
                ContestRecordArchive.finish_time: user_rank.finish_time,
                ContestRecordArchive.update_time: user_rank.update_time,
            }),
            on_insert=user_rank,
        )
        for user_rank in user_rank_objs
    )
    await asyncio.gather(*tasks)
    await save_users_of_contest(contest_name=contest_name, in_predict_col=False, new_user_only=False)
    await fill_questions_field(contest_name, questions_list)
    await save_submission(contest_name, user_rank_list, nested_submission_list, questions_list)
    from app.core.rank import save_real_time_rank
    await save_real_time_rank(contest_name)


async def check_contest_user_num(
    contest_name: str,
) -> None:
    req = httpx.get(
        f"https://leetcode.com/contest/api/ranking/{contest_name}/",
        timeout=60,
    )
    data = req.json()
    user_num = data.get("user_num")
    archive_num = await ContestRecordArchive.find(ContestRecordArchive.contest_name == contest_name).count()
    predict_num = await ContestRecordPredict.find(ContestRecordPredict.contest_name == contest_name).count()
    logger.info(f"{contest_name}: total={user_num} archive={archive_num} predict={predict_num}")
    logger.info(f"archive get all records? {user_num == archive_num}")
    logger.info(f"predict get all records? {user_num == predict_num}")
    # join table query how many of the users of this contest have been inserted in User collection
    # for convenience, here use pymongo aggregate directly, not beanie ODM(poor aggregate $lookup support now).
    col = get_async_mongodb_collection(ContestRecordPredict.__name__)
    res = [
        x async for x in col.aggregate(
            [
                {"$match": {"contest_name": contest_name}},
                {"$lookup": {
                    "from": User.__name__,
                    "localField": "username",
                    "foreignField": "username",
                    "as": "found_user"
                }},
                {"$addFields": {"found_user_count": {"$size": "$found_user"}}},
                {"$group": {"_id": "_id", "count": {"$sum": "$found_user_count"}}}
            ]
        )
    ]
    saved_user_num = res[0].get("count") if res else 0
    logger.info(f"User db saved_user_num={saved_user_num}")
    logger.info(f"all users now in User db? {user_num == saved_user_num}")


async def first_time_contest_crawler() -> None:
    for i in range(294, 100, -1):
        contest_name = f"weekly-contest-{i}"
        await save_archive_contest_records(contest_name=contest_name)
        await check_contest_user_num(contest_name=contest_name)
    for i in range(78, 0, -1):
        contest_name = f"biweekly-contest-{i}"
        await save_archive_contest_records(contest_name=contest_name)
        await check_contest_user_num(contest_name=contest_name)
