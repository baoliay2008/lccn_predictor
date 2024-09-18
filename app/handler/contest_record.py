from datetime import datetime

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.contest_record_and_submission import request_contest_records
from app.db.models import DATA_REGION, ContestRecordArchive, ContestRecordPredict, User
from app.handler.submission import save_submission
from app.handler.user import save_users_of_contest
from app.utils import exception_logger_reraise, gather_with_limited_concurrency


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

    async def _fill_old_rating_and_count(_contest_record: ContestRecordPredict):
        user = await User.find_one(
            User.username == _contest_record.username,
            User.data_region == _contest_record.data_region,
        )
        _contest_record.old_rating = user.rating
        _contest_record.attendedContestsCount = user.attendedContestsCount
        await _contest_record.save()

    contest_record_list, _ = await request_contest_records(contest_name, data_region)
    contest_records = list()
    # Full update, delete all old records
    await ContestRecordPredict.find(
        ContestRecordPredict.contest_name == contest_name,
    ).delete()
    unique_keys = set()
    for contest_record_dict in contest_record_list:
        # Only the API for the US site has changed. Now, `username` from LCCN is `user_slug` from LCUS.
        if data_region == "US":
            # TODO: LCUS changed API, now we have to use `user_slug`, not `username`
            contest_record_dict["username"] = contest_record_dict["user_slug"]
        key = (contest_record_dict["data_region"], contest_record_dict["username"])
        if key in unique_keys:
            # during the contest, request_contest_ranking may return duplicated records (user ranking is changing)
            logger.warning(f"duplicated user record. {contest_record_dict=}")
            continue
        unique_keys.add(key)
        contest_record_dict.update({"contest_name": contest_name})
        contest_record = ContestRecordPredict.model_validate(contest_record_dict)
        contest_records.append(contest_record)
    insert_tasks = [
        ContestRecordPredict.insert_one(contest_record)
        for contest_record in contest_records
    ]
    await gather_with_limited_concurrency(insert_tasks, max_con_num=50)
    await save_users_of_contest(contest_name=contest_name, predict=True)
    # fill rating and attended count, must be called after save_users_of_contest and before predict_contest,
    fill_tasks = [
        _fill_old_rating_and_count(contest_record)
        for contest_record in contest_records
        if contest_record.score != 0
    ]
    await gather_with_limited_concurrency(fill_tasks, max_con_num=50)


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
    (contest_record_list, nested_submission_list) = await request_contest_records(
        contest_name, data_region
    )
    contest_records = list()
    for contest_record_dict in contest_record_list:
        # Only the API for the US site has changed. Now, `username` from LCCN is `user_slug` from LCUS.
        if data_region == "US":
            # TODO: LCUS changed API, now we have to use `user_slug`, not `username`
            contest_record_dict["username"] = contest_record_dict["user_slug"]
        contest_record_dict.update({"contest_name": contest_name})
        contest_record = ContestRecordArchive.model_validate(contest_record_dict)
        contest_records.append(contest_record)
    tasks = [
        ContestRecordArchive.find_one(
            ContestRecordArchive.contest_name == contest_record.contest_name,
            ContestRecordArchive.username == contest_record.username,
            ContestRecordArchive.data_region == contest_record.data_region,
        ).upsert(
            Set(
                {
                    ContestRecordArchive.rank: contest_record.rank,
                    ContestRecordArchive.score: contest_record.score,
                    ContestRecordArchive.finish_time: contest_record.finish_time,
                    ContestRecordArchive.update_time: contest_record.update_time,
                }
            ),
            on_insert=contest_record,
        )
        for contest_record in contest_records
    ]
    await gather_with_limited_concurrency(tasks, max_con_num=50)
    # remove old records
    await ContestRecordArchive.find(
        ContestRecordArchive.contest_name == contest_name,
        ContestRecordArchive.update_time < time_point,
    ).delete()
    if save_users is True:
        await save_users_of_contest(contest_name=contest_name, predict=False)
    else:
        logger.info(f"{save_users=}, will not save users")
    await save_submission(contest_name, contest_record_list, nested_submission_list)
