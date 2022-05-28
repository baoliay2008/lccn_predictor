import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.constant import WEEKLY_CONTEST_END, BIWEEKLY_CONTEST_END, \
    WEEKLY_CONTEST_BASE, BIWEEKLY_CONTEST_BASE, CronTimePointWkdHrMin
from app.core.predictor import predict_contest


async def predict_biweekly_contest():
    utc = datetime.utcnow()
    passed_weeks = round(
        (utc - BIWEEKLY_CONTEST_BASE.datetime).total_seconds() / (7 * 24 * 60 * 60)
    )
    if passed_weeks % 2 != 0:
        print(f"predict_biweekly_contest return, passed_weeks={passed_weeks} is odd for now={utc}")
        return
    contest_name = f"biweekly-contest-{passed_weeks // 2 + BIWEEKLY_CONTEST_BASE.num}"
    print(f"predict_biweekly_contest running, contest_name={contest_name}")
    await asyncio.sleep(15)
    await predict_contest(contest_name=contest_name, update_user_using_prediction=True)


async def predict_weekly_contest():
    utc = datetime.utcnow()
    passed_weeks = round(
        (utc - WEEKLY_CONTEST_BASE.datetime).total_seconds() / (7 * 24 * 60 * 60)
    )
    contest_name = f"weekly-contest-{passed_weeks + WEEKLY_CONTEST_BASE.num}"
    print(f"predict_weekly_contest running, contest_name={contest_name}")
    await asyncio.sleep(15)
    await predict_contest(contest_name=contest_name)


async def scheduler_entry():
    utc = datetime.utcnow()
    time_point = CronTimePointWkdHrMin(utc.weekday(), utc.hour, utc.minute)
    if time_point == WEEKLY_CONTEST_END:
        await predict_weekly_contest()
    elif time_point == BIWEEKLY_CONTEST_END:
        await predict_biweekly_contest()
    elif (
            time_point.weekday <= 4  # Monday to Friday
            and time_point.hour == 0
            and time_point.minute == 0
    ):
        # do other low-priority jobs such as updating user's rating and participated contest count.
        pass
    else:
        print(f"job_dispatcher nothing to do for utc={utc} time_point={time_point}")


async def start_scheduler():
    scheduler = AsyncIOScheduler()
    # 10 seconds is OK, make sure scheduler_entry will be executed in every minute.
    # no need to worry about duplicated run, prediction function cannot finish with 10 seconds, rest will be skipped.
    # By default, only one instance of each job is allowed to be run at the same time.
    scheduler.add_job(scheduler_entry, 'interval', seconds=10)
    scheduler.start()

