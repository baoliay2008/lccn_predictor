import asyncio
import math
from datetime import datetime
from typing import Final, List, Literal, Optional

from fastapi import Body, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel

from app.db.models import Contest, ContestRecordArchive, ContestRecordPredict, Question
from app.db.mongodb import start_async_mongodb
from app.utils import start_loguru


class KeyUniqueContestRecord(BaseModel):
    contest_name: str
    username: str
    data_region: str


app = FastAPI()
app.mount("/static", StaticFiles(directory="api/deprecated/static"), name="static")
templates = Jinja2Templates(directory="api/deprecated/templates")


@app.on_event("startup")
async def startup_event():
    start_loguru(process="api")
    await start_async_mongodb()


@app.get("/", response_class=HTMLResponse)
async def index_page_get(
    request: Request,
):
    logger.info(f"index_page_get {request.client=}")
    predict_contests = (
        #  Contest.predict_time != None,  # beanie does not support `is not None` here.
        await Contest.find(
            Contest.predict_time > datetime(2000, 1, 1),
        )
        .sort(-Contest.startTime)
        .to_list()
    )
    logger.trace(f"{predict_contests=}")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "predict_contests": predict_contests,
        },
    )


@app.get("/{contest_name}/{page}", response_class=HTMLResponse)
async def contest_page_get(
    request: Request,
    contest_name: str,
    page: int = 1,
):
    logger.info(f"{request.client=} {contest_name=}, {page=}")
    # TODO: check contest_name, notify invalid contest_name(eg. not started with weekly or biweekly)
    total_num = await ContestRecordPredict.find(
        ContestRecordPredict.contest_name == contest_name,
        ContestRecordPredict.score != 0,
    ).count()
    max_page = math.ceil(total_num / 25)
    pagination_list = [i for i in range(page - 4, page + 5) if 1 <= i <= max_page]
    records = (
        await ContestRecordPredict.find(
            ContestRecordPredict.contest_name == contest_name,
            ContestRecordPredict.score != 0,
        )
        .sort(ContestRecordPredict.rank)
        .skip(25 * (page - 1))
        .limit(25)
        .to_list()
    )
    return templates.TemplateResponse(
        "contest.html",
        {
            "request": request,
            "contest_name": contest_name,
            "user_list": records,
            "current_page": page,
            "max_page": max_page,
            "pagination_list": pagination_list,
        },
    )


@app.post("/{contest_name}/query_user", response_class=HTMLResponse)
async def contest_user_post(
    request: Request,
    contest_name: str,
    username: Optional[str] = Form(None),
):
    logger.info(f"{request.client=}, {contest_name=}, {username=}")
    record = await ContestRecordPredict.find_one(
        ContestRecordPredict.contest_name == contest_name,
        ContestRecordPredict.username == username,
        ContestRecordPredict.score != 0,
    )
    return templates.TemplateResponse(
        "contest.html",
        {
            "request": request,
            "contest_name": contest_name,
            "user_list": [record] if record else [],
            "current_page": None,
        },
    )


@app.post("/user_rank_list")
async def contest_user_rank_list(
    request: Request,
    unique_contest_record: KeyUniqueContestRecord,
):
    logger.info(f"{request.client=} {unique_contest_record=}")
    contest = await Contest.find_one(
        Contest.titleSlug == unique_contest_record.contest_name
    )
    if not contest:
        logger.error(f"contest not found for {unique_contest_record=}")
        return {}
    start_time = contest.startTime
    record = await ContestRecordArchive.find_one(
        ContestRecordArchive.contest_name == unique_contest_record.contest_name,
        ContestRecordArchive.username == unique_contest_record.username,
        ContestRecordArchive.data_region == unique_contest_record.data_region,
    )
    if not record:
        logger.error(f"user contest record not found for {unique_contest_record=}")
    data = [["Minute", "User", "Rank"],] + [
        [minute + 1, unique_contest_record.username, x]
        for minute, x in enumerate(
            record.real_time_rank if record and record.real_time_rank else []
        )
    ]
    logger.trace(f"{unique_contest_record=} {data=}")
    return {
        "real_time_rank": data,
        "start_time": start_time,
    }


@app.post("/questions_finished_list")
async def contest_questions_finished_list(
    request: Request,
    contest_name: str = Body(embed=True),
):
    logger.info(f"{request.client=} {contest_name=}")
    data = [["Minute", "Question", "Count"]]
    contest = await Contest.find_one(
        Contest.titleSlug == contest_name,
    )
    if not contest:
        logger.error(f"contest not found for {contest_name=}")
        return {}
    questions = await Question.find(Question.contest_name == contest_name).to_list()
    if not questions:
        logger.error(f"{questions=}, no data now")
        return {"real_time_count": data}
    questions.sort(key=lambda q: q.credit)
    logger.trace(f"{questions=}")
    for i, question in enumerate(questions):
        data.extend(
            [
                [minute + 1, f"Q{i+1}", count]
                for minute, count in enumerate(question.real_time_count)
            ]
        )
    logger.trace(f"{contest_name=} {data=}")
    return {"real_time_count": data}


DATA_REGION = Literal["CN", "US"]


class UniqueUser(BaseModel):
    username: str
    data_region: DATA_REGION


class QueryPredictedRecords(BaseModel):
    contest_name: str
    users: List[UniqueUser]


class ProjectionPredictedResult(BaseModel):
    old_rating: Optional[float] = None
    new_rating: Optional[float] = None
    delta_rating: Optional[float] = None


@app.post("/predict_records")
async def contest_predict_records(
    request: Request,
    query: QueryPredictedRecords,
):
    """
    Query multiple predicted records in a contest.
    :param request:
    :param query:
    :return:
    """
    logger.info(f"{request.client=} {query=}")
    MAX_USERS: Final[int] = 26
    contest = await Contest.find_one(Contest.titleSlug == query.contest_name)
    if not contest:
        logger.error(f"contest not found for {query.contest_name=}")
        raise HTTPException(
            status_code=400, detail=f"contest not found for {query.contest_name=}"
        )
    if (users_count := len(query.users)) > MAX_USERS:
        logger.error(f"{users_count=} per request, denied.")
        raise HTTPException(
            status_code=400,
            detail=f"request denied because {users_count=}, which is bigger than maximum value={MAX_USERS}",
        )
    tasks = (
        ContestRecordPredict.find_one(
            ContestRecordPredict.contest_name == query.contest_name,
            ContestRecordPredict.data_region == user.data_region,
            ContestRecordPredict.username == user.username,
            projection_model=ProjectionPredictedResult,
        )
        for user in query.users
    )
    return await asyncio.gather(*tasks)
