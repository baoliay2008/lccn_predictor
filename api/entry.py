from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.mongodb import start_async_mongodb
from app.utils import start_loguru

from .routers import contest_records, contests, questions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lccn.lbao.site",
        # "http://localhost:3000",
    ],
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
