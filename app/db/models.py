from typing import Optional, List
from datetime import datetime
from beanie import Document, Indexed
from pydantic import BaseModel, Field


class Question(BaseModel):
    question_id: int
    credit: int
    title: str
    title_slug: str


class Contest(Document):
    contest_name: Indexed(str, unique=True)  # titleSlug
    title: Indexed(str)
    start_time: Indexed(datetime)
    duration: int
    questions: Optional[List[Question]] = None
    # computed field
    end_time: Indexed(datetime)
    # for tracking
    past: bool
    update_time: datetime = Field(default_factory=datetime.utcnow)


class ContestRecord(Document):
    contest_name: Indexed(str)
    contest_id: int
    username: Indexed(str)
    user_slug: Indexed(str)
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    rank: Indexed(int)
    score: int
    # TODO: change finish_time from int to indexed utc datetime using `epoch_time_to_utc_datetime`, the same as Submission.date
    finish_time: int
    data_region: Indexed(str)


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
    # save latest value
    username: Indexed(str)
    user_slug: Indexed(str)
    data_region: Indexed(str)
    update_time: datetime = Field(default_factory=datetime.utcnow)
    # following fields come from graphql
    attendedContestsCount: int
    rating: float
    # removed the following six fields, they are useless, no need to save them now.(fields removed in graphql also)
    # globalRanking: int
    # topPercentage: float
    # totalParticipants:  Optional[int] = None  # US users only
    # localRanking: Optional[int] = None  # CN users only
    # globalTotalParticipants: Optional[int] = None  # CN users only
    # localTotalParticipants: Optional[int] = None  # CN users only
    # TODO: add historical ranking field, save into an array. (ranking.length = attendedContestsCount)


class Submission(Document):
    # these four can be used as compound Index
    contest_name: Indexed(str)
    username: Indexed(str)
    data_region: Indexed(str)
    question_id: Indexed(int)
    # following three for sorting
    date: Indexed(datetime)
    fail_count: int
    credit: int
    # following three are useless now
    submission_id: int
    status: int
    contest_id: int
    # for tracking
    update_time: datetime = Field(default_factory=datetime.utcnow)


class ProjectionUniqueUser(BaseModel):
    username: str
    data_region: str


