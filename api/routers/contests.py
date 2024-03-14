from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Request
from loguru import logger
from pydantic import BaseModel, NonNegativeInt, conint

from app.db.models import Contest

router = APIRouter(
    prefix="/contests",
    tags=["contests"],
)


class ResultOfContestsUserNum(BaseModel):
    titleSlug: str
    title: str
    startTime: datetime
    user_num_us: Optional[int] = None
    user_num_cn: Optional[int] = None


@router.get("/user-num-last-ten")
async def contests_user_num_last_ten(
    request: Request,
) -> List[ResultOfContestsUserNum]:
    """
    Obtain user counts from both the US and CN regions for the last ten contests.
    :param request:
    :return:
    """
    records = (
        await Contest.find(
            Contest.user_num_us >= 0,
            Contest.user_num_cn >= 0,
            projection_model=ResultOfContestsUserNum,
        )
        .sort(-Contest.startTime)
        .limit(10)
        .to_list()
    )
    return records


@router.get("/count")
async def contests_count(
    request: Request,
    archived: Optional[bool] = False,
) -> int:
    """
    Count total contests in database.
    By default, count predicted contests only.
    Count all archived contests when setting `archived = True` explicitly.
    :param request:
    :param archived:
    :return:
    """
    logger.info(f"{request.client=}")
    if archived:
        total_num = await Contest.count()
    else:
        total_num = await Contest.find(
            Contest.predict_time > datetime(1970, 1, 1),
        ).count()
    return total_num


@router.get("/")
async def contests(
    request: Request,
    archived: Optional[bool] = False,
    skip: Optional[NonNegativeInt] = 0,
    limit: Optional[conint(ge=1, le=25)] = 10,
) -> List[Contest]:
    """
    Query contests in database.
    By default, Query predicted contests only.
    Query archived contests when setting `archived = True` explicitly.
    :param request:
    :param archived:
    :param skip:
    :param limit:
    :return:
    """
    logger.info(f"{request.client=}")
    if archived:
        records = (
            await Contest.find_all()
            .sort(-Contest.startTime)
            .skip(skip)
            .limit(limit)
            .to_list()
        )
    else:
        records = (
            await Contest.find(
                Contest.predict_time > datetime(1970, 1, 1),
            )
            .sort(-Contest.startTime)
            .skip(skip)
            .limit(limit)
            .to_list()
        )
    return records
