import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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
    t1 = time.time()
    response = await call_next(request)
    t2 = time.time()
    logger.info(
        f"Received request: {request.client.host} {request.method} {request.url.path} "
        f"Cost {(t2 - t1) * 1e3:.2f} ms {response.status_code=}"
    )
    return response
