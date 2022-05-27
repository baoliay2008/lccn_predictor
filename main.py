import asyncio

from app.core.predictor import predict_contest
from app.core.schedulers import start_scheduler
from app.crawler.contests import first_time_contest_crawler
from app.db.mongodb import start_async_mongodb


async def start():
    await start_async_mongodb()
    await start_scheduler()
    await first_time_contest_crawler()
    # await predict_contest(contest_name="weekly-contest-294")
    print("finished start in main.py")


if __name__ == "__main__":
    # asyncio.run(start())
    loop = asyncio.new_event_loop()
    loop.create_task(start())
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
