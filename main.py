import asyncio

from app.crawler.users import insert_users
from app.db.mongodb import start_async_mongodb


async def start():
    await start_async_mongodb()
    # await start_scheduler()
    # await start_crawler()
    await insert_users()

if __name__ == "__main__":
    # asyncio.run(start())
    loop = asyncio.get_event_loop()
    loop.create_task(start())
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
