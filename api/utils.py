from fastapi import HTTPException
from loguru import logger

from app.db.models import Contest


async def check_contest_name(contest_name: str) -> None:
    """
    Check whether a contest_name is valid.
    - Valid: silently passed
    - Invalid: just raise HTTPException (fastapi will return error msg gracefully)
    :param contest_name:
    :return:
    """
    contest = await Contest.find_one(Contest.titleSlug == contest_name)
    if not contest:
        msg = f"contest not found for {contest_name=}"
        logger.error(msg)
        raise HTTPException(status_code=400, detail=msg)
