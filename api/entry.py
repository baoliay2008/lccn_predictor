import time

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from loguru import logger

from app.config import get_yaml_config
from app.db.mongodb import start_async_mongodb
from app.utils import start_loguru

from .routers import contest_records, contests, questions

app = FastAPI()
yaml_config = get_yaml_config().get("fastapi")


app.include_router(contests.router, prefix="/api/v1")
app.include_router(contest_records.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    start_loguru(process="api")
    await start_async_mongodb()


app.add_middleware(
    CORSMiddleware,
    allow_origins=yaml_config.get("CORS_allow_origins"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        f"Received request: {request.client.host} {request.method} {request.url.path}"
    )
    t1 = time.time()
    response = await call_next(request)
    t2 = time.time()
    logger.info(f"Cost {(t2 - t1) * 1e3:.2f} ms {response.status_code=}")
    return response


# Redirect Old API to new one
legacy_router = APIRouter(
    tags=["legacy_apis"],
)


@legacy_router.post("/predict_records")
async def legacy_predicted_rating(request: Request):
    """
    This api is a legacy api for third-party projects like https://github.com/XYShaoKang/refined-leetcode
    Just do nothing but redirecting to new API
    :return:
    """
    base_url = str(request.base_url)[:-1]
    new_path = app.url_path_for("predicted_rating")
    new_url = base_url + new_path
    return RedirectResponse(new_url)


app.include_router(legacy_router)
