import asyncio
from typing import Dict, List

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.contest import save_next_two_contests, save_recent_contests
from app.db.models import Contest
from app.utils import exception_logger_reraise


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
    await asyncio.gather(*tasks)
    logger.success("finished")


@exception_logger_reraise
async def save_recent_and_next_two_contests() -> None:
    """
    Save past contests and top two coming contests
    :return:
    """
    # Send Http requests to same server, don't do it concurrently
    top_two_contests = await save_next_two_contests()
    ten_past_contests = await save_recent_contests()
    # Save them in database, do it concurrently
    await asyncio.gather(
        multi_upsert_contests(top_two_contests, past=False),
        multi_upsert_contests(ten_past_contests, past=True),
    )
