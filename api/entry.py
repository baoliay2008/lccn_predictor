from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_yaml_config
from app.db.mongodb import start_async_mongodb
from app.utils import start_loguru

from .routers import contest_records, contests, questions

app = FastAPI()
yaml_config = get_yaml_config().get("fastapi")

app.add_middleware(
    CORSMiddleware,
    allow_origins=yaml_config.get("CORS_allow_origins"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contests.router, prefix="/api/v1")
app.include_router(contest_records.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    start_loguru(process="api")
    await start_async_mongodb()
