from datetime import datetime, timedelta
import asyncio
import math
from typing import List, Dict, Tuple

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.db.models import Submission, ContestRecordArchive, ProjectionUniqueUser, Contest
from app.db.mongodb import get_async_mongodb_collection
from app.utils import epoch_time_to_utc_datetime, get_contest_end_time


async def aggregate_question_real_time_count(
        contest_name: str,
        question_id: int,
        time_point: datetime,
) -> int:
    col = get_async_mongodb_collection(Submission.__name__)
    res = [
        x async for x in col.aggregate(
            [
                {
                    "$match": {
                        "contest_name": contest_name,
                        "question_id": question_id,
                    }
                },
                {
                    "$addFields": {
                        "penalty_date": {
                            "$dateAdd": {
                                "startDate": "$date",
                                "unit": "minute",
                                "amount": {"$multiply": [5, "$fail_count"]}
                            }
                        }
                    }
                },
                {
                    "$match": {
                        "penalty_date": {"$lte": time_point}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "finished_count": {"$sum": 1},
                    }
                }
            ]
        )
    ]
    return res[0].get("finished_count") if res else 0


async def save_question_finish_count(
        contest_name: str,
        delta_minutes: int = 1
) -> None:
    contest: Contest = await Contest.find_one(
        Contest.titleSlug == contest_name,
    )
    time_series = list()
    end_time = get_contest_end_time(contest_name)
    start_time = end_time - timedelta(minutes=90)
    while start_time <= end_time:
        time_series.append(start_time)
        start_time += timedelta(minutes=delta_minutes)
    logger.info(f"contest_name={contest_name} time_series={time_series}")
    for question in contest.questions:
        question.real_time_count = await asyncio.gather(
            *[
                aggregate_question_real_time_count(contest_name, question.question_id, time_point)
                for time_point in time_series
            ]
        )
    await contest.save()


async def aggregate_rank_at_time_point(
    contest_name: str,
    time_point: datetime,
) -> Tuple[Dict[Tuple[str, str], int], int]:
    col = get_async_mongodb_collection(Submission.__name__)
    rank_map = dict()
    last_credit_sum = math.inf
    last_penalty_date = epoch_time_to_utc_datetime(0)
    tie_rank = raw_rank = 0
    async for record in col.aggregate(
        [
            {"$match": {"contest_name": contest_name, "date": {"$lte": time_point}}},
            {
                "$group": {
                    "_id": {"username": "$username", "data_region": "$data_region"},
                    "credit_sum": {"$sum": "$credit"},
                    "fail_count_sum": {"$sum": "$fail_count"},
                    "date_max": {"$max": "$date"},
                }
            },
            {
                "$addFields": {
                    "penalty_date": {
                        "$dateAdd": {
                            "startDate": "$date_max",
                            "unit": "minute",
                            "amount": {"$multiply": [5, "$fail_count_sum"]},
                        }
                    },
                    "username": "$_id.username",
                    "data_region": "$_id.data_region",
                }
            },
            {"$unset": ["_id"]},
            {"$sort": {"credit_sum": -1, "penalty_date": 1}},
        ]
    ):
        raw_rank += 1
        if (
            record["credit_sum"] == last_credit_sum
            and record["penalty_date"] == last_penalty_date
        ):
            rank_map[(record["username"], record["data_region"])] = tie_rank
        else:
            tie_rank = raw_rank
            rank_map[(record["username"], record["data_region"])] = raw_rank
        last_credit_sum = record["credit_sum"]
        last_penalty_date = record["penalty_date"]
    return rank_map, raw_rank


async def save_real_time_rank(
    contest_name: str,
    delta_minutes: int = 1,
) -> None:
    logger.info(f"started running real_time_rank update function")
    users: List[ProjectionUniqueUser] = (
        await ContestRecordArchive.find(
            ContestRecordArchive.contest_name == contest_name,
        )
        .project(ProjectionUniqueUser)
        .to_list()
    )
    real_time_rank_map = {(user.username, user.data_region): list() for user in users}
    end_time = get_contest_end_time(contest_name)
    start_time = end_time - timedelta(minutes=90)
    i = 1
    while start_time <= end_time:
        rank_map, last_rank = await aggregate_rank_at_time_point(
            contest_name, start_time
        )
        # logger.info(f"rank_map = {rank_map}, last_rank = {last_rank}")
        last_rank += 1
        for (username, data_region), rank in rank_map.items():
            real_time_rank_map[(username, data_region)].append(rank)
        for k in real_time_rank_map.keys():
            if len(real_time_rank_map[k]) != i:
                real_time_rank_map[k].append(last_rank)
        start_time += timedelta(minutes=delta_minutes)
        i += 1
    tasks = (
        ContestRecordArchive.find_one(
            ContestRecordArchive.contest_name == contest_name,
            ContestRecordArchive.username == username,
            ContestRecordArchive.data_region == data_region,
        ).update(
            Set(
                {
                    ContestRecordArchive.real_time_rank: rank_list,
                }
            )
        )
        for (username, data_region), rank_list in real_time_rank_map.items()
    )
    await asyncio.gather(*tasks)
    logger.success(f"finished updating real_time_rank for contest_name={contest_name}")


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
    logger.success("finished updating submissions, begin to save real_time_rank")
    await save_real_time_rank(contest_name)
