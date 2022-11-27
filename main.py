import asyncio

from loguru import logger

from app.core.schedulers import start_scheduler
from app.db.mongodb import start_async_mongodb
from app.utils import start_loguru


async def start() -> None:
    start_loguru()
    await start_async_mongodb()
    await start_scheduler()
    logger.success("started all entry functions")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(start())
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.critical(f"Closing loop. {e=}")
    finally:
        loop.close()
        logger.critical("Closed loop.")
