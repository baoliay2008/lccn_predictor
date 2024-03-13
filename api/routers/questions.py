import asyncio
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, NonNegativeInt, conlist

from api.utils import check_contest_name
from app.db.models import Question

router = APIRouter(
    prefix="/questions",
    tags=["questions"],
)


class QueryOfQuestions(BaseModel):
    contest_name: Optional[str] = None
    question_id_list: Optional[
        conlist(NonNegativeInt, min_length=1, max_length=4)
    ] = None


@router.post("/")
async def questions(
    request: Request,
    query: QueryOfQuestions,
) -> List[Question]:
    """
    Query questions for a given contest.
    Questions number must between 1 and 4 inclusively.
    :param request:
    :param query:
    :return:
    """
    logger.info(f"{request.client=}")
    if not (bool(query.contest_name) ^ bool(query.question_id_list)):
        msg = "contest_name OR question_id_list must be given!"
        logger.error(msg)
        raise HTTPException(status_code=400, detail=msg)
    # if `contest_name` is given, use it to query
    if query.contest_name:
        await check_contest_name(query.contest_name)
        return await Question.find(
            Question.contest_name == query.contest_name
        ).to_list()
    # or use `question_id_list` to query
    else:
        tasks = (
            Question.find_one(Question.question_id == question_id)
            for question_id in query.question_id_list
        )
        return await asyncio.gather(*tasks)
    # notice that if both parameters are given, only use `contest_name`
