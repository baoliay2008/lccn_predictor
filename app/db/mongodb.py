import urllib.parse

from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient, AgnosticCollection, AgnosticDatabase  # bad idea to use these three here,
# just for temporary autocompleting, given that motor doesn't have type annotations yet,
# see https://jira.mongodb.org/browse/MOTOR-331
# and https://www.mongodb.com/community/forums/t/support-for-type-hint/107593
from beanie import init_beanie

from app.config import get_yaml_config
from app.db.models import ContestRecordPredict, ContestRecordArchive, User

async_mongodb_client = None


def get_mongodb_config():
    config = get_yaml_config()
    return config.get("mongodb")


def get_async_mongodb_client() -> AgnosticClient:
    global async_mongodb_client
    if async_mongodb_client is None:
        ip = get_mongodb_config().get("ip")
        port = get_mongodb_config().get("port")
        username = urllib.parse.quote_plus(get_mongodb_config().get("username"))
        password = urllib.parse.quote_plus(get_mongodb_config().get("password"))
        db = get_mongodb_config().get("db")
        async_mongodb_client = AsyncIOMotorClient(
            f"mongodb://{username}:{password}@{ip}:{port}/{db}",
            # connectTimeoutMS=None,
        )
    return async_mongodb_client


def get_async_mongodb_database(db_name=None) -> AgnosticDatabase:
    if db_name is None:
        db_name = get_mongodb_config().get("db")
    client = get_async_mongodb_client()
    return client[db_name]


def get_async_mongodb_connection(col_name) -> AgnosticCollection:
    db = get_async_mongodb_database()
    return db[col_name]


async def start_async_mongodb() -> None:
    async_mongodb_database = get_async_mongodb_database()
    await init_beanie(
        database=async_mongodb_database,
        document_models=[
            ContestRecordPredict,
            ContestRecordArchive,
            User,
        ]
    )


