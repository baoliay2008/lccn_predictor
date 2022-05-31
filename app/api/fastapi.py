import math
from typing import List, Tuple, Optional
import asyncio

from loguru import logger
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db.models import ContestRecordPredict
from app.db.mongodb import start_async_mongodb, get_async_mongodb_collection


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    await start_async_mongodb()


@app.get("/", response_class=HTMLResponse)
async def contest_page_get(
        request: Request,
):
    # Now beanie ODM doesn't have a distinct method, use raw mongodb query here.
    # https://github.com/roman-right/beanie/issues/133
    # https://github.com/roman-right/beanie/pull/268
    col = get_async_mongodb_collection(ContestRecordPredict.__name__)
    contest_name_list = await col.distinct("contest_name")
    tasks = [
        ContestRecordPredict.find_one(
            ContestRecordPredict.contest_name == contest_name,
        ) for contest_name in contest_name_list
    ]
    distinct_contests = await asyncio.gather(*tasks)
    logger.debug(distinct_contests)
    # TODO: support showing contests metadata in homepage, do the following things:
    # 1. Add a contests table in db, save history contests info
    # and next two coming contest, weekly and biweekly respectively.
    # 2. Then it's easier to support homepage view(such as table pagination, start and end time and other fields)
    # 3. Remember front-end table should also be paginated.
    # 4. Determine whether a contest_name is valid or not in contest_page_get function by querying this new table.
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "distinct_contests": sorted(distinct_contests, key=lambda obj: obj.insert_time, reverse=True),
        },
    )


@app.get("/{contest_name}", response_class=HTMLResponse)
@app.get("/{contest_name}/{page}", response_class=HTMLResponse)
async def contest_page_get(
        request: Request,
        contest_name: str,
        page: int = 1,
):
    # TODO: check contest_name, notify invalid contest_name(eg. not started with weekly or biweekly)
    total_num = await ContestRecordPredict.find(
        ContestRecordPredict.contest_name == contest_name,
        ContestRecordPredict.score != 0,
    ).count()
    max_page = math.ceil(total_num / 25)
    pagination_list = [i for i in range(page-4, page+5) if 1 <= i <= max_page]
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
    logger.info(f"username={username}")
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
