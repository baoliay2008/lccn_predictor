import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def say_hi():
    await asyncio.sleep(0.1)
    print('hi')


async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(say_hi, 'interval', seconds=10)
    scheduler.start()

