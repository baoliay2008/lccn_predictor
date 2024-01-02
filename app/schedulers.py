import asyncio
from datetime import datetime, timedelta
from typing import Optional

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.constants import (
    BIWEEKLY_CONTEST_BASE,
    BIWEEKLY_CONTEST_START,
    WEEKLY_CONTEST_BASE,
    WEEKLY_CONTEST_START,
    CronTimePointWkdHrMin,
)
from app.core.predictor import predict_contest
from app.crawler.contest import save_all_contests
from app.crawler.contest_records import (
    check_cn_data_is_ready,
    save_archive_contest_records,
    save_predict_contest_records,
)
from app.utils import exception_logger_reraise, get_passed_weeks

global_scheduler: Optional[AsyncIOScheduler] = None


@exception_logger_reraise
async def save_last_two_contest_records() -> None:
    """
    Update last weekly contest, and last biweekly contest.
    Upsert contest records in ContestRecordArchive, its users will also be updated in the save_archive_contest function.
    :return:
    """
    utc = datetime.utcnow()

    biweekly_passed_weeks = get_passed_weeks(utc, BIWEEKLY_CONTEST_BASE.dt)
    last_biweekly_contest_name = (
        f"biweekly-contest-{biweekly_passed_weeks // 2 + BIWEEKLY_CONTEST_BASE.num}"
    )
    logger.info(f"{last_biweekly_contest_name=} update archive contests")
    await save_archive_contest_records(
        contest_name=last_biweekly_contest_name, data_region="CN"
    )

    weekly_passed_weeks = get_passed_weeks(utc, WEEKLY_CONTEST_BASE.dt)
    last_weekly_contest_name = (
        f"weekly-contest-{weekly_passed_weeks + WEEKLY_CONTEST_BASE.num}"
    )
    logger.info(f"{last_weekly_contest_name=} update archive contests")
    await save_archive_contest_records(
        contest_name=last_weekly_contest_name, data_region="CN"
    )


@exception_logger_reraise
async def composed_predict_jobs(
    contest_name: str,
    max_try_times: int = 25,
) -> None:
    """
    All three steps which should be run when the contest is just over
    :param contest_name:
    :param max_try_times:
    :return:
    """
    tried_times = 1
    while (
        not (cn_data_is_ready := check_cn_data_is_ready(contest_name))
        and tried_times < max_try_times
    ):
        await asyncio.sleep(60)
        tried_times += 1
    if not cn_data_is_ready:
        logger.error(
            f"give up after failed {tried_times=} times. CONTINUE WITH INCOMPLETE DATA"
        )
    await save_predict_contest_records(contest_name=contest_name, data_region="CN")
    await predict_contest(contest_name=contest_name)
    await save_archive_contest_records(
        contest_name=contest_name, data_region="CN", save_users=False
    )


async def pre_save_predict_users(contest_name: str) -> None:
    """
    Cache CN and US users during contest
    :param contest_name:
    :return:
    """
    await save_predict_contest_records(contest_name, "CN")
    await save_predict_contest_records(contest_name, "US")


async def add_prediction_schedulers(contest_name: str) -> None:
    """
    First add two save_predict_contest_records jobs to caching participants' info (mainly whose latest rating)
    by doing so can improve the speed of real calculation job greatly
    because we are wasting most of the time at fetching participants' info. (`save_users_of_contest` function)
    Then add one composed_predict_jobs (real calculation jobs)
    :param contest_name:
    :return:
    """
    utc = datetime.utcnow()
    global global_scheduler
    for pre_save_time in [utc + timedelta(minutes=25), utc + timedelta(minutes=70)]:
        # preparation for prediction running, get users in advance.
        global_scheduler.add_job(
            pre_save_predict_users,
            kwargs={"contest_name": contest_name},
            trigger="date",
            run_date=pre_save_time,
        )
    # postpone 5 minutes to wait for LeetCode updating final result.
    predict_run_time = utc + timedelta(minutes=95)
    # real prediction running function.
    global_scheduler.add_job(
        composed_predict_jobs,
        kwargs={"contest_name": contest_name},
        trigger="date",
        run_date=predict_run_time,
    )


async def scheduler_entry() -> None:
    """
    Dispatch jobs at every minute.
    :return:
    """
    global global_scheduler
    utc = datetime.utcnow()
    time_point = CronTimePointWkdHrMin(utc.weekday(), utc.hour, utc.minute)
    if time_point == WEEKLY_CONTEST_START:
        passed_weeks = get_passed_weeks(utc, WEEKLY_CONTEST_BASE.dt)
        contest_name = f"weekly-contest-{passed_weeks + WEEKLY_CONTEST_BASE.num}"
        logger.info(f"parsed {contest_name=}")
        await add_prediction_schedulers(contest_name)
    elif time_point == BIWEEKLY_CONTEST_START:
        passed_weeks = get_passed_weeks(utc, BIWEEKLY_CONTEST_BASE.dt)
        if passed_weeks % 2 != 0:
            logger.info(
                f"will not run biweekly prediction, passed_weeks={passed_weeks} is odd for now={utc}"
            )
            return
        contest_name = (
            f"biweekly-contest-{passed_weeks // 2 + BIWEEKLY_CONTEST_BASE.num}"
        )
        logger.info(f"parsed {contest_name=}")
        await add_prediction_schedulers(contest_name)
    elif (
        2 <= time_point.weekday <= 5  # Wednesday, Tuesday, Friday and Saturday 00:00
        and time_point.hour == 0
        and time_point.minute == 0
    ):
        # do other low-priority jobs such as updating user's rating and participated contest count.
        global_scheduler.add_job(
            save_all_contests,
            trigger="date",
            run_date=utc + timedelta(minutes=1),
        )
        global_scheduler.add_job(
            save_last_two_contest_records,
            trigger="date",
            run_date=utc + timedelta(minutes=10),
        )
    else:
        logger.trace(f"job_dispatcher nothing to do for {utc=} {time_point=}")
    if len(job_list := global_scheduler.get_jobs()) > 1:
        # logging when there are more schedulers besides scheduler_entry itself.
        logger.info(f"global_scheduler jobs={'; '.join(str(job) for job in job_list)}")


async def start_scheduler() -> None:
    """
    Add `scheduler_entry` interval job when main process started.
    :return:
    """
    global global_scheduler
    if global_scheduler is not None:
        logger.error("global_scheduler could only be started once.")
    global_scheduler = AsyncIOScheduler(timezone=pytz.utc)
    global_scheduler.add_job(scheduler_entry, "interval", minutes=1)
    global_scheduler.start()
    logger.success("started schedulers")
