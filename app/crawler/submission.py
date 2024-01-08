from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.contest import save_all_contests
from app.crawler.question import fill_questions_field, save_question_finish_count
from app.db.models import ContestRecordArchive, KeyOfUser, Submission
from app.db.mongodb import get_async_mongodb_collection
from app.utils import (
    exception_logger_reraise,
    gather_with_limited_concurrency,
    get_contest_start_time,
)


async def aggregate_rank_at_time_point(
    contest_name: str,
    time_point: datetime,
) -> Tuple[Dict[Tuple[str, str], int], int]:
    """
    For a single time_point, rank all the participants.
    Be careful that every wrong submission should add a 5-minutes penalty.
    :param contest_name:
    :param time_point:
    :return:
    """
    col = get_async_mongodb_collection(
        Submission.__name__
    )  # hard to use beanie here, so use raw MongoDB aggregation
    rank_map = dict()
    last_credit_sum = None
    last_penalty_date = None
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
    """
    For every delta_minutes, invoke `aggregate_rank_at_time_point` function to get ranking on single time_point
    Then append every user's ranking to a list and save it
    :param contest_name:
    :param delta_minutes:
    :return:
    """
    logger.info("started running real_time_rank update function")
    users = (
        await ContestRecordArchive.find(
            ContestRecordArchive.contest_name == contest_name,
            ContestRecordArchive.score != 0,  # No need to query users who have 0 score
        )
        .project(KeyOfUser)
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
    tasks = [
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
    ]
    logger.info("updating real_time_rank field in ContestRecordArchive collection")
    await gather_with_limited_concurrency(tasks, max_con_num=20)
    logger.success(f"finished updating real_time_rank for {contest_name=}")


@exception_logger_reraise
async def save_submission(
    contest_name: str,
    user_rank_list: List[Dict],
    nested_submission_list: List[Dict],
    questions_list: List[Dict],
) -> None:
    """
    Save all of submission-related data to MongoDB
    :param contest_name:
    :param user_rank_list:
    :param nested_submission_list:
    :param questions_list:
    :return:
    """
    time_point = datetime.utcnow()
    await save_all_contests()
    await fill_questions_field(contest_name, questions_list)
    question_credit_mapper = {
        question["question_id"]: question["credit"] for question in questions_list
    }
    submission_objs = list()
    for user_rank_dict, nested_submission_dict in zip(
        user_rank_list, nested_submission_list
    ):
        for k, value_dict in nested_submission_dict.items():
            nested_submission_dict[k].pop("id")
            nested_submission_dict[k] |= {
                "contest_name": contest_name,
                "username": user_rank_dict["username"],
                "credit": question_credit_mapper[value_dict["question_id"]],
            }
        submission_objs.extend(
            [
                Submission.model_validate(value_dict)
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
            Set(
                {
                    Submission.date: submission.date,
                    Submission.fail_count: submission.fail_count,
                    Submission.credit: submission.credit,
                    Submission.update_time: submission.update_time,
                }
            ),
            on_insert=submission,
        )
        for submission in submission_objs
    ]
    logger.info("updating Submission collection")
    await gather_with_limited_concurrency(tasks, max_con_num=50)
    # Old submissions may be rejudged, must be deleted here, or will cause error when plotting.
    await Submission.find(
        Submission.contest_name == contest_name,
        Submission.update_time < time_point,
    ).delete()
    logger.success("finished updating submissions, begin to save real_time_rank")
    await save_question_finish_count(contest_name)
    await save_real_time_rank(contest_name)
