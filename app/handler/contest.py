import asyncio
from typing import Dict, List

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.contest import (
    request_contest_user_num,
    request_next_two_contests,
    request_recent_contests,
)
from app.crawler.utils import multi_http_request
from app.db.models import Contest
from app.utils import (
    exception_logger_reraise,
    exception_logger_silence,
    gather_with_limited_concurrency,
)


async def multi_upsert_contests(
    contests: List[Dict],
    past: bool,
) -> None:
    """
    Save meta data of Contests into MongoDB
    :param contests:
    :param past:
    :return:
    """
    tasks = list()
    for contest_dict in contests:
        try:
            contest_dict["past"] = past
            contest_dict["endTime"] = (
                contest_dict["startTime"] + contest_dict["duration"]
            )
            logger.debug(f"{contest_dict=}")
            contest = Contest.model_validate(contest_dict)
            logger.debug(f"{contest=}")
        except Exception as e:
            logger.exception(
                f"parse contest_dict error {e}. skip upsert {contest_dict=}"
            )
            continue
        tasks.append(
            Contest.find_one(Contest.titleSlug == contest.titleSlug,).upsert(
                Set(
                    {
                        Contest.update_time: contest.update_time,
                        Contest.title: contest.title,
                        Contest.startTime: contest.startTime,
                        Contest.duration: contest.duration,
                        Contest.past: past,
                        Contest.endTime: contest.endTime,
                    }
                ),
                on_insert=contest,
            )
        )
    await gather_with_limited_concurrency(tasks)
    logger.success("finished")


@exception_logger_reraise
async def save_recent_and_next_two_contests() -> None:
    """
    Save past contests and top two coming contests
    :return:
    """
    # Send Http requests to same server, don't do it concurrently
    top_two_contests = await request_next_two_contests()
    ten_past_contests = await request_recent_contests()
    # Save them in database, do it concurrently
    await asyncio.gather(
        multi_upsert_contests(top_two_contests, past=False),
        multi_upsert_contests(ten_past_contests, past=True),
    )


@exception_logger_silence
async def save_user_num(
    contest_name: str,
) -> None:
    """
    Save user_num of US and CN data_region to database
    :param contest_name:
    :return:
    """
    user_num_us, user_num_cn = await asyncio.gather(
        request_contest_user_num(contest_name, "US"),
        request_contest_user_num(contest_name, "CN"),
    )
    logger.info(f"{user_num_us=} {user_num_cn=}")
    await Contest.find_one(Contest.titleSlug == contest_name,).update(
        Set(
            {
                Contest.user_num_us: user_num_us,
                Contest.user_num_cn: user_num_cn,
            }
        )
    )


async def is_cn_contest_data_ready(
    contest_name: str,
) -> bool:
    """
    Check data from CN region when contest finished, if it is ready then return True
    :param contest_name:
    :return:
    """
    try:
        cn_data = (
            await multi_http_request(
                {
                    "req": {
                        "url": f"https://leetcode.cn/contest/api/ranking/{contest_name}/",
                        "method": "GET",
                    }
                }
            )
        )[0].json()
        fallback_local = cn_data.get("fallback_local")
        if fallback_local is not None:
            logger.info(f"check {fallback_local=} unsatisfied")
            return False
        us_data = (
            await multi_http_request(
                {
                    "req": {
                        "url": f"https://leetcode.com/contest/api/ranking/{contest_name}/",
                        "method": "GET",
                    }
                }
            )
        )[0].json()
        # check user_num in two different regions, if they are equal then return True
        is_satisfied = (cn_user_num := cn_data.get("user_num")) >= (
            us_user_num := us_data.get("user_num")
        )
        logger.info(f"check {cn_user_num=} {us_user_num=} {is_satisfied=}")
        if is_satisfied:
            await save_user_num(contest_name)
        return is_satisfied
    except Exception as e:
        logger.error(f"check fallback_local error={e}")
        return False
