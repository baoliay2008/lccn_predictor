from typing import Optional
from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field


class ContestRecord(Document):
    contest_name: Indexed(str)
    contest_id: int
    username: Indexed(str)
    user_slug: Indexed(str)
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    rank: Indexed(int)
    score: int
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
    # TODO: add historical ranking field, save into an array. (array.length = attendedContestsCount)




