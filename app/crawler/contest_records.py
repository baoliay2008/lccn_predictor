from typing import List, Dict, Tuple
from math import ceil
import asyncio

from loguru import logger
import httpx
from beanie.odm.operators.update.general import Set

from app.core.rank import save_submission
from app.crawler.users import save_users_of_contest
from app.crawler.utils import multi_http_request
from app.db.models import ContestRecordPredict, ContestRecordArchive, User


async def request_contest_ranking(
    contest_name: str,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    logger.info("start")
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
    logger.info("finished")
    return user_rank_list, nested_submission_list, questions_list


async def save_predict_contest_records(
    contest_name: str,
) -> None:
    async def _fill_old_rating_and_count(_user_rank: ContestRecordPredict):
        user = await User.find_one(
            User.username == _user_rank.username,
            User.data_region == _user_rank.data_region,
        )
        _user_rank.old_rating = user.rating
        _user_rank.attendedContestsCount = user.attendedContestsCount
        await _user_rank.save()

    user_rank_list, _, _ = await request_contest_ranking(contest_name)
    user_rank_objs = list()
    # Full update, delete all old records
    await ContestRecordPredict.find(
        ContestRecordPredict.contest_name == contest_name,
    ).delete()
    for user_rank_dict in user_rank_list:
        user_rank_dict.update({"contest_name": contest_name})
        user_rank = ContestRecordPredict.parse_obj(user_rank_dict)
        user_rank_objs.append(user_rank)
    insert_tasks = (
        ContestRecordPredict.insert_one(user_rank) for user_rank in user_rank_objs
    )
    await asyncio.gather(*insert_tasks)
    await save_users_of_contest(contest_name=contest_name)
    # fill rating and attended count, must be called after save_users_of_contest and before predict_contest,
    fill_tasks = (
        _fill_old_rating_and_count(user_rank) for user_rank in user_rank_objs if user_rank.score != 0
    )
    await asyncio.gather(*fill_tasks)
    logger.success("finished")


async def save_archive_contest_records(
        contest_name: str,
        save_users: bool = True,
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
    if save_users is True:
        await save_users_of_contest(contest_name=contest_name, in_predict_col=False, new_user_only=False)
    else:
        logger.info(f"save_users={save_users}, will not save users")
    await save_submission(contest_name, user_rank_list, nested_submission_list, questions_list)
