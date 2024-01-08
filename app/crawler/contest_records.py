import asyncio
from datetime import datetime
from math import ceil
from typing import Dict, Final, List, Tuple

import httpx
from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.submission import save_submission
from app.crawler.users import save_users_of_contest
from app.crawler.utils import multi_http_request
from app.db.models import DATA_REGION, ContestRecordArchive, ContestRecordPredict, User
from app.utils import exception_logger_reraise


def check_cn_data_is_ready(
    contest_name: str,
) -> bool:
    """
    Check data from CN region when contest finished, if it is ready then return True
    :param contest_name:
    :return:
    """
    try:
        cn_data = httpx.get(
            f"https://leetcode.cn/contest/api/ranking/{contest_name}/",
            timeout=60,
        ).json()
        fallback_local = cn_data.get("fallback_local")
        if fallback_local is None:
            us_data = httpx.get(
                f"https://leetcode.com/contest/api/ranking/{contest_name}/",
                timeout=60,
            ).json()
            # check user_num in two different regions, if they are equal then return True
            is_satisfied = (cn_user_num := cn_data.get("user_num")) >= (
                us_user_num := us_data.get("user_num")
            )
            logger.info(f"check {cn_user_num=} {us_user_num=} {is_satisfied=}")
            return is_satisfied
        else:
            logger.info(f"check {fallback_local=} unsatisfied")
            return False
    except Exception as e:
        logger.error(f"check fallback_local error={e}")
        return False


async def request_contest_records(
    contest_name: str,
    data_region: DATA_REGION,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Fetch all ranking records of a contest by sending http request per page concurrently
    :param contest_name:
    :param data_region:
    :return:
    """
    base_url: Final[str] = (
        "https://leetcode.com" if data_region == "US" else "https://leetcode.cn"
    )
    logger.info(f"start {base_url=}")
    req = httpx.get(
        f"{base_url}/contest/api/ranking/{contest_name}/",
        timeout=60,
    )
    data = req.json()
    user_num = data.get("user_num")
    questions_list = data.get("questions")
    page_max = ceil(user_num / 25)
    user_rank_list = list()
    nested_submission_list = list()
    url_list = [
        f"{base_url}/contest/api/ranking/{contest_name}/?pagination={page}&region=global"
        for page in range(1, page_max + 1)
    ]
    responses = await multi_http_request(
        {url: {"url": url, "method": "GET"} for url in url_list},
        concurrent_num=20 if data_region == "US" else 1,
    )
    for res in responses:
        if res is None:
            continue
        res_dict = res.json()
        user_rank_list.extend(res_dict.get("total_rank"))
        nested_submission_list.extend(res_dict.get("submissions"))
    logger.success("finished")
    return user_rank_list, nested_submission_list, questions_list


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
