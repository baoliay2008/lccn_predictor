import asyncio
import math
import sys
from asyncio import iscoroutinefunction
from datetime import datetime, timedelta
from functools import partial, wraps
from typing import Any, Callable, Coroutine, Sequence

from loguru import logger

from app.constants import BIWEEKLY_CONTEST_BASE, WEEKLY_CONTEST_BASE


async def gather_with_limited_concurrency(
    crts: Sequence[Coroutine], max_con_num: int = 10
):
    """
    limit the concurrent number of tasks in `asyncio.gather`
    by using `asyncio.Semaphore`
    :param crts:
    :param max_con_num:
    :return:
    """

    async def crt_with_semaphore(crt: Coroutine):
        async with semaphore:
            return await crt

    semaphore = asyncio.Semaphore(max_con_num)
    tasks = [crt_with_semaphore(crt) for crt in crts]
    await asyncio.gather(*tasks)


def get_passed_weeks(t: datetime, base_t: datetime) -> int:
    """
    Calculate how many weeks passed from base_t to t
    :param t:
    :param base_t:
    :return:
    """
    return math.floor((t - base_t).total_seconds() / (7 * 24 * 60 * 60))


def get_contest_start_time(contest_name: str) -> datetime:
    """
    It's a simple, bold, but EFFECTIVE conjecture here, take two baselines separately,
    then from the expected `contest_name` calculate its start time, just let it run on server periodically, no bother.
    It's just unnecessary to use dynamic configuration things instead.
    This conjecture worked precisely in the past, hopefully will still work well in the future.
    :param contest_name:
    :return:
    """
    contest_num = int(contest_name.split("-")[-1])
    if contest_name.lower().startswith("weekly"):
        start_time = WEEKLY_CONTEST_BASE.dt + timedelta(
            weeks=contest_num - WEEKLY_CONTEST_BASE.num
        )
    else:
        start_time = BIWEEKLY_CONTEST_BASE.dt + timedelta(
            weeks=(contest_num - BIWEEKLY_CONTEST_BASE.num) * 2
        )
    logger.info(f"{contest_name=} {start_time=}")
    return start_time


def start_loguru(process: str = "main") -> None:
    """
    error-prone warning: misuse process parameter (for example, use main in fastapi process
    or reassign a different value) will mess up logs.
    TODO: could set a global singleton variable to make sure this function will only be called once in a single process.
    :param process: "main" for main.py backend process, "api" for fastapi http-server process.
    :return:
    """
    from app.config import get_yaml_config

    try:
        loguru_config = get_yaml_config().get("loguru").get(process)
        logger.add(
            sink=loguru_config["sink"],
            rotation=loguru_config["rotation"],
            level=loguru_config["level"],
        )
    except Exception as e:
        logger.exception(
            f"Failed to start loguru, check loguru config in config.yaml file. error={e}"
        )
        sys.exit(1)


def exception_logger(func: Callable[..., Any], reraise: bool) -> Callable[..., Any]:
    """
    A decorator to write logs and try-catch for the key functions you want to keep eyes on.
    :param func:
    :param reraise:
    :return:
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            logger.info(f"{func.__name__} is about to run.")
            res = await func(*args, **kwargs)
            logger.success(f"{func.__name__} is finished.")
            return res
        except Exception as e:
            logger.exception(f"{func.__name__} error={e}.")
            if reraise:
                raise e

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.info(f"{func.__name__} is about to run.")
            res = func(*args, **kwargs)
            logger.success(f"{func.__name__} is finished.")
            return res
        except Exception as e:
            logger.exception(f"{func.__name__} args={args} kwargs={kwargs} error={e}.")
            if reraise:
                raise e

    return async_wrapper if iscoroutinefunction(func) else wrapper


exception_logger_reraise = partial(exception_logger, reraise=True)
exception_logger_silence = partial(exception_logger, reraise=False)
