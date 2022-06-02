import math
import asyncio
from datetime import datetime

from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.constant import WEEKLY_CONTEST_END, BIWEEKLY_CONTEST_END, \
    WEEKLY_CONTEST_BASE, BIWEEKLY_CONTEST_BASE, CronTimePointWkdHrMin
from app.core.predictor import predict_contest
from app.crawler.contests import save_archive_contest


def get_passed_weeks(t: datetime, base_t: datetime) -> int:
    return math.floor(
        (t - base_t).total_seconds() / (7 * 24 * 60 * 60)
    )


async def update_last_two_contests() -> None:
    """
    update last weekly contest, and biweekly contest if exists.
    upsert contest records in ContestRecordArchive, its users will be also updated in the save_archive_contest function.
    :return:
    """
    utc = datetime.utcnow()
    weekly_passed_weeks = get_passed_weeks(utc, WEEKLY_CONTEST_BASE.datetime)
    last_weekly_contest_name = f"weekly-contest-{weekly_passed_weeks + WEEKLY_CONTEST_BASE.num}"
    logger.info(f"last_weekly_contest_name={last_weekly_contest_name} update users")
    await save_archive_contest(contest_name=last_weekly_contest_name)
    biweekly_passed_weeks = get_passed_weeks(utc, BIWEEKLY_CONTEST_BASE.datetime)
    if biweekly_passed_weeks % 2 != 0:
        logger.info(f"will not update last biweekly users, passed_weeks={biweekly_passed_weeks} is odd for now={utc}")
        return
    last_biweekly_contest_name = f"biweekly-contest-{biweekly_passed_weeks // 2 + BIWEEKLY_CONTEST_BASE.num}"
    logger.info(f"last_biweekly_contest_name={last_biweekly_contest_name} update users")
    await save_archive_contest(contest_name=last_biweekly_contest_name)
    logger.info("finished update_last_two_contests_users")


async def predict_biweekly_contest() -> None:
    utc = datetime.utcnow()
    passed_weeks = get_passed_weeks(utc, BIWEEKLY_CONTEST_BASE.datetime)
    if passed_weeks % 2 != 0:
        logger.info(f"will not run biweekly prediction, passed_weeks={passed_weeks} is odd for now={utc}")
        return
    contest_name = f"biweekly-contest-{passed_weeks // 2 + BIWEEKLY_CONTEST_BASE.num}"
    logger.info(f"biweekly contest prediction running, contest_name={contest_name}")
    await asyncio.sleep(15)
    await predict_contest(contest_name=contest_name, update_user_using_prediction=True)
    logger.info("finished predict_biweekly_contest")


async def predict_weekly_contest() -> None:
    utc = datetime.utcnow()
    passed_weeks = get_passed_weeks(utc, WEEKLY_CONTEST_BASE.datetime)
    contest_name = f"weekly-contest-{passed_weeks + WEEKLY_CONTEST_BASE.num}"
    logger.info(f"weekly contest prediction running, contest_name={contest_name}")
    await asyncio.sleep(15)
    await predict_contest(contest_name=contest_name)
    logger.info("finished predict_weekly_contest")


async def scheduler_entry() -> None:
    utc = datetime.utcnow()
    time_point = CronTimePointWkdHrMin(utc.weekday(), utc.hour, utc.minute)
    if time_point == WEEKLY_CONTEST_END:
        await predict_weekly_contest()
    elif time_point == BIWEEKLY_CONTEST_END:
        await predict_biweekly_contest()
    elif (
            3 <= time_point.weekday <= 6  # Tuesday, Friday and Saturday 00:00
            and time_point.hour == 0
            and time_point.minute == 0
    ):
        # do other low-priority jobs such as updating user's rating and participated contest count.
        await update_last_two_contests()
    else:
        logger.debug(f"job_dispatcher nothing to do for utc={utc} time_point={time_point}")


async def start_scheduler() -> None:
    scheduler = AsyncIOScheduler()
    # 10 seconds is OK, make sure scheduler_entry will be executed in every minute.
    # no need to worry about duplicated run, prediction function cannot finish with 10 seconds, rest will be skipped.
    # By default, only one instance of each job is allowed to be run at the same time.
    scheduler.add_job(scheduler_entry, 'interval', seconds=10)
    scheduler.start()
    logger.success("started schedulers")
