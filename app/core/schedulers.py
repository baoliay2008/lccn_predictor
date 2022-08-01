import pytz
from typing import Optional
from datetime import datetime, timedelta

from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.constants import WEEKLY_CONTEST_START, BIWEEKLY_CONTEST_START, WEEKLY_CONTEST_BASE, BIWEEKLY_CONTEST_BASE, \
    CronTimePointWkdHrMin
from app.core.predictor import predict_contest
from app.crawler.contest import save_all_contests
from app.crawler.contest_records import save_archive_contest_records, save_predict_contest_records
from app.utils import get_passed_weeks, exception_logger_reraise


global_scheduler: Optional[AsyncIOScheduler] = None


@exception_logger_reraise
async def save_last_two_contest_records() -> None:
    """
    update last weekly contest, and biweekly contest if exists.
    upsert contest records in ContestRecordArchive, its users will be also updated in the save_archive_contest function.
    :return:
    """
    utc = datetime.utcnow()
    weekly_passed_weeks = get_passed_weeks(utc, WEEKLY_CONTEST_BASE.dt)
    last_weekly_contest_name = f"weekly-contest-{weekly_passed_weeks + WEEKLY_CONTEST_BASE.num}"
    logger.info(f"last_weekly_contest_name={last_weekly_contest_name} update archive contests")
    await save_archive_contest_records(contest_name=last_weekly_contest_name)
    biweekly_passed_weeks = get_passed_weeks(utc, BIWEEKLY_CONTEST_BASE.dt)
    if biweekly_passed_weeks % 2 != 0:
        logger.info(f"will not update last biweekly users, passed_weeks={biweekly_passed_weeks} is odd for now={utc}")
        return
    last_biweekly_contest_name = f"biweekly-contest-{biweekly_passed_weeks // 2 + BIWEEKLY_CONTEST_BASE.num}"
    logger.info(f"last_biweekly_contest_name={last_biweekly_contest_name} update archive contests")
    await save_archive_contest_records(contest_name=last_biweekly_contest_name)


@exception_logger_reraise
async def composed_predict_jobs(contest_name: str) -> None:
    await save_predict_contest_records(contest_name=contest_name)
    await predict_contest(contest_name=contest_name)
    await save_archive_contest_records(contest_name=contest_name, save_users=False)


async def add_prediction_schedulers(contest_name: str) -> None:
    utc = datetime.utcnow()
    global global_scheduler
    for pre_save_time in [utc + timedelta(minutes=25), utc + timedelta(minutes=70)]:
        global_scheduler.add_job(
            save_predict_contest_records,  # preparation for prediction running, get users in advance.
            kwargs={"contest_name": contest_name},
            trigger='date',
            run_date=pre_save_time,
        )
    predict_run_time = utc + timedelta(minutes=105)  # postpone 15 minutes to wait for leetcode updating final result.
    global_scheduler.add_job(
        composed_predict_jobs,  # real prediction running function.
        kwargs={"contest_name": contest_name},
        trigger='date',
        run_date=predict_run_time,
    )


async def scheduler_entry() -> None:
    global global_scheduler
    utc = datetime.utcnow()
    time_point = CronTimePointWkdHrMin(utc.weekday(), utc.hour, utc.minute)
    if time_point == WEEKLY_CONTEST_START:
        passed_weeks = get_passed_weeks(utc, WEEKLY_CONTEST_BASE.dt)
        contest_name = f"weekly-contest-{passed_weeks + WEEKLY_CONTEST_BASE.num}"
        logger.info(f"parsed contest_name={contest_name}")
        await add_prediction_schedulers(contest_name)
    elif time_point == BIWEEKLY_CONTEST_START:
        passed_weeks = get_passed_weeks(utc, BIWEEKLY_CONTEST_BASE.dt)
        if passed_weeks % 2 != 0:
            logger.info(f"will not run biweekly prediction, passed_weeks={passed_weeks} is odd for now={utc}")
            return
        contest_name = f"biweekly-contest-{passed_weeks // 2 + BIWEEKLY_CONTEST_BASE.num}"
        logger.info(f"parsed contest_name={contest_name}")
        await add_prediction_schedulers(contest_name)
    elif (
            2 <= time_point.weekday <= 5  # Wednesday, Tuesday, Friday and Saturday 00:00
            and time_point.hour == 0
            and time_point.minute == 0
    ):
        # do other low-priority jobs such as updating user's rating and participated contest count.
        global_scheduler.add_job(
            save_all_contests,
            trigger='date',
            run_date=utc + timedelta(minutes=1),
        )
        global_scheduler.add_job(
            save_last_two_contest_records,
            trigger='date',
            run_date=utc + timedelta(minutes=10),
        )
    else:
        logger.trace(f"job_dispatcher nothing to do for utc={utc} time_point={time_point}")
    if len(job_list := global_scheduler.get_jobs()) > 1:
        # logging when there are more schedulers besides scheduler_entry itself.
        logger.info(f"global_scheduler jobs={'; '.join(str(job) for job in job_list)}")


async def start_scheduler() -> None:
    global global_scheduler
    if global_scheduler is not None:
        logger.error("global_scheduler could only be started once.")
    global_scheduler = AsyncIOScheduler(timezone=pytz.utc)
    global_scheduler.add_job(scheduler_entry, 'interval', minutes=1)
    global_scheduler.start()
    logger.success("started schedulers")
