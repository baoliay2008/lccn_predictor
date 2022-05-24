import asyncio

from app.core.predictor import predict_contest
from app.crawler.rank import start_crawler
from app.crawler.users import insert_historical_contests_users
from app.db.mongodb import start_async_mongodb


async def start():
    await start_async_mongodb()
    # await start_scheduler()
    # await start_crawler()
    # await insert_historical_contests_users()
    await predict_contest(contest_name="weekly-contest-294")

if __name__ == "__main__":
    asyncio.run(start())
    # loop = asyncio.get_event_loop()
    # loop.create_task(start())
    # try:
    #     loop.run_forever()
    # except (KeyboardInterrupt, SystemExit):
    #     pass
