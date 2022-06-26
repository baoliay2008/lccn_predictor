from typing import Optional, List
from datetime import datetime
from beanie import Document, Indexed
from pydantic import BaseModel, Field, validator

from app.utils import epoch_time_to_utc_datetime


class Question(BaseModel):
    question_id: int
    credit: int
    title: str
    title_slug: str
    real_time_count: Optional[list] = None


class Contest(Document):
    titleSlug: Indexed(str, unique=True)
    title: Indexed(str)
    startTime: Indexed(datetime)
    duration: int
    endTime: Indexed(datetime)
    past: bool
    questions: Optional[List[Question]] = None
    update_time: datetime = Field(default_factory=datetime.utcnow)
    predict_time: Optional[datetime] = None

    @validator('startTime', 'endTime', pre=True)
    def epoch_to_utc(cls, v):
        if isinstance(v, int):
            return epoch_time_to_utc_datetime(v)
        elif isinstance(v, datetime):
            return v
        else:
            raise TypeError(f"startTime={v} is not int or datetime")


class ContestRecord(Document):
    contest_name: Indexed(str)
    contest_id: int
    username: Indexed(str)
    user_slug: Indexed(str)
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    rank: Indexed(int)
    score: int
    finish_time: datetime
    data_region: Indexed(str)

    @validator('finish_time', pre=True)
    def epoch_to_utc(cls, v):
        if isinstance(v, int):
            return epoch_time_to_utc_datetime(v)
        elif isinstance(v, datetime):
            return v
        else:
            raise TypeError(f"finish_time={v} is not int or datetime")


class ContestRecordPredict(ContestRecord):
    # Predicted records' will be inserted only once, won't update any fields.
    # Records in this collection can be used to calculated MSE directly even after a long time because it won't change.
    insert_time: datetime = Field(default_factory=datetime.utcnow)
    attendedContestsCount: Optional[int] = None
    old_rating: Optional[float] = None
    new_rating: Optional[float] = None
    delta_rating: Optional[float] = None
    predict_time: Optional[datetime] = None


class ContestRecordArchive(ContestRecord):
    # Archived records will be updated.
    # Leetcode will rejudge some submissions(cheat detection, add test cases, etc.)
    update_time: datetime = Field(default_factory=datetime.utcnow)
    real_time_rank: Optional[list] = None


class User(Document):
    username: Indexed(str)
    user_slug: Indexed(str)
    data_region: Indexed(str)
    attendedContestsCount: int
    rating: Indexed(float)
    update_time: datetime = Field(default_factory=datetime.utcnow)
    # TODO: add historical ranking field, save into an array. (ranking.length = attendedContestsCount)


class Submission(Document):
    # these four can be used as compound Index
    contest_name: Indexed(str)
    username: Indexed(str)
    data_region: Indexed(str)
    question_id: Indexed(int)
    date: Indexed(datetime)
    fail_count: int
    credit: int
    submission_id: int
    status: int
    contest_id: int
    update_time: datetime = Field(default_factory=datetime.utcnow)

    @validator('date', pre=True)
    def epoch_to_utc(cls, v):
        if isinstance(v, int):
            return epoch_time_to_utc_datetime(v)
        elif isinstance(v, datetime):
            return v
        else:
            raise TypeError(f"date={v} is not int or datetime")


class KeyUniqueContestRecord(BaseModel):
    contest_name: str
    username: str
    data_region: str


class ProjectionUniqueUser(BaseModel):
    username: str
    data_region: str


