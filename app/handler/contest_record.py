import asyncio
from datetime import datetime

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.contest_record_and_submission import request_contest_records
from app.db.models import DATA_REGION, ContestRecordArchive, ContestRecordPredict, User
from app.handler.submission import save_submission
from app.handler.users import save_users_of_contest
from app.utils import exception_logger_reraise


@exception_logger_reraise
async def save_predict_contest_records(
    contest_name: str,
    data_region: DATA_REGION,
) -> None:
    """
    Save fetched contest records into `ContestRecordPredict` collection for predicting new contest
    :param contest_name:
    :param data_region:
    :return:
    """

    async def _fill_old_rating_and_count(_user_rank: ContestRecordPredict):
        user = await User.find_one(
            User.username == _user_rank.username,
            User.data_region == _user_rank.data_region,
        )
        _user_rank.old_rating = user.rating
        _user_rank.attendedContestsCount = user.attendedContestsCount
        await _user_rank.save()

    user_rank_list, _, _ = await request_contest_records(contest_name, data_region)
    user_rank_objs = list()
    # Full update, delete all old records
    await ContestRecordPredict.find(
        ContestRecordPredict.contest_name == contest_name,
    ).delete()
    unique_keys = set()
    for user_rank_dict in user_rank_list:
        key = (user_rank_dict["data_region"], user_rank_dict["username"])
        if key in unique_keys:
            # during the contest, request_contest_ranking may return duplicated records (user ranking is changing)
            logger.warning(f"duplicated user record. {user_rank_dict=}")
            continue
        unique_keys.add(key)
        user_rank_dict.update({"contest_name": contest_name})
        user_rank = ContestRecordPredict.model_validate(user_rank_dict)
        user_rank_objs.append(user_rank)
    insert_tasks = (
        ContestRecordPredict.insert_one(user_rank) for user_rank in user_rank_objs
    )
    await asyncio.gather(*insert_tasks)
    await save_users_of_contest(contest_name=contest_name, predict=True)
    # fill rating and attended count, must be called after save_users_of_contest and before predict_contest,
    fill_tasks = (
        _fill_old_rating_and_count(user_rank)
        for user_rank in user_rank_objs
        if user_rank.score != 0
    )
    await asyncio.gather(*fill_tasks)


@exception_logger_reraise
async def save_archive_contest_records(
    contest_name: str,
    data_region: DATA_REGION = "US",
    save_users: bool = True,
) -> None:
    """
    Save fetched contest records into `ContestRecordArchive` collection for archiving old contests
    :param contest_name:
    :param data_region:
    :param save_users:
    :return:
    """
    time_point = datetime.utcnow()
    (
        user_rank_list,
        nested_submission_list,
        questions_list,
    ) = await request_contest_records(contest_name, data_region)
    user_rank_objs = list()
    for user_rank_dict in user_rank_list:
        user_rank_dict.update({"contest_name": contest_name})
        user_rank = ContestRecordArchive.model_validate(user_rank_dict)
        user_rank_objs.append(user_rank)
    tasks = (
        ContestRecordArchive.find_one(
            ContestRecordArchive.contest_name == user_rank.contest_name,
            ContestRecordArchive.username == user_rank.username,
            ContestRecordArchive.data_region == user_rank.data_region,
        ).upsert(
            Set(
                {
                    ContestRecordArchive.rank: user_rank.rank,
                    ContestRecordArchive.score: user_rank.score,
                    ContestRecordArchive.finish_time: user_rank.finish_time,
                    ContestRecordArchive.update_time: user_rank.update_time,
                }
            ),
            on_insert=user_rank,
        )
        for user_rank in user_rank_objs
    )
    await asyncio.gather(*tasks)
    # remove old records
    await ContestRecordArchive.find(
        ContestRecordArchive.contest_name == contest_name,
        ContestRecordArchive.update_time < time_point,
    ).delete()
    if save_users is True:
        await save_users_of_contest(contest_name=contest_name, predict=False)
    else:
        logger.info(f"{save_users=}, will not save users")
    await save_submission(
        contest_name, user_rank_list, nested_submission_list, questions_list
    )
