import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def say_hi():
    await asyncio.sleep(0.1)
    print(f'{datetime.utcnow()}\thi')


async def predict_biweekly_contest():
    pass


async def predict_weekly_contest():
    pass


async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(say_hi, 'interval', seconds=10)
    scheduler.start()

