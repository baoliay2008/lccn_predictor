import asyncio
from app.db.mongodb import start_async_mongodb
from app.core.crawler import start_crawler
from app.core.schedulers import start_scheduler


async def start():
    await start_async_mongodb()
    await start_scheduler()
    await start_crawler()


if __name__ == "__main__":
    # asyncio.run(start())
    loop = asyncio.get_event_loop()
    loop.create_task(start())
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
