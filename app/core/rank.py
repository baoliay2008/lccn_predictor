from datetime import datetime, timedelta
import asyncio
import math
from typing import List, Dict, Tuple

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.contest import fill_questions_field, save_all_contests
from app.db.models import Submission, ContestRecordArchive, ProjectionUniqueUser, Contest
from app.db.mongodb import get_async_mongodb_collection
from app.utils import epoch_time_to_utc_datetime, get_contest_start_time, exception_logger


async def save_question_finish_count(
        contest_name: str,
        delta_minutes: int = 1
) -> None:
    contest: Contest = await Contest.find_one(
        Contest.titleSlug == contest_name,
    )
    time_series = list()
    start_time = get_contest_start_time(contest_name)
    end_time = start_time + timedelta(minutes=90)
    while (start_time := start_time + timedelta(minutes=delta_minutes)) <= end_time:
        time_series.append(start_time)
    logger.info(f"contest_name={contest_name} time_series={time_series}")
    for question in contest.questions:
        tasks = (
            Submission.find(
                    Submission.contest_name == contest_name,
                    Submission.question_id == question.question_id,
                    Submission.date <= time_point,
            ).count()
            for time_point in time_series
        )
        question.real_time_count = await asyncio.gather(*tasks)
    await contest.save()
    logger.success("finished")


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


@exception_logger
async def save_real_time_rank(
    contest_name: str,
    delta_minutes: int = 1,
) -> None:
    logger.info(f"started running real_time_rank update function")
    users: List[ProjectionUniqueUser] = (
        await ContestRecordArchive.find(
            ContestRecordArchive.contest_name == contest_name,
            ContestRecordArchive.score != 0,  # No need to query users who have 0 score
        )
        .project(ProjectionUniqueUser)
        .to_list()
    )
    real_time_rank_map = {(user.username, user.data_region): list() for user in users}
    start_time = get_contest_start_time(contest_name)
    end_time = start_time + timedelta(minutes=90)
    i = 1
    while (start_time := start_time + timedelta(minutes=delta_minutes)) <= end_time:
        rank_map, last_rank = await aggregate_rank_at_time_point(
            contest_name, start_time
        )
        last_rank += 1
        for (username, data_region), rank in rank_map.items():
            real_time_rank_map[(username, data_region)].append(rank)
        for k in real_time_rank_map.keys():
            if len(real_time_rank_map[k]) != i:
                real_time_rank_map[k].append(last_rank)
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
    time_point = datetime.utcnow()
    await save_all_contests()
    await fill_questions_field(contest_name, questions_list)
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
    tasks = (
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
    )
    await asyncio.gather(*tasks)
    # Old submissions may be rejudged, must be deleted here, or will cause error when plotting.
    await Submission.find(
        Submission.contest_name == contest_name,
        Submission.update_time < time_point,
    ).delete()
    logger.success("finished updating submissions, begin to save real_time_rank")
    await save_question_finish_count(contest_name)
    await save_real_time_rank(contest_name)
