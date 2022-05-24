from typing import Optional
from pydantic import BaseModel, validator
from beanie import Document, Indexed
from datetime import datetime


class Contest(Document):
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

    # @validator('contest_name')
    # def contest_must_be_weekly_or_biweekly(cls, v):
    #     pass


class ContestPredict(Contest):
    # fields in Contest will be inserted only once, won't update further.
    insert_time: datetime
    # following predicted fields will be inserted only once, too.
    attendedContestsCount: Optional[int] = None
    old_rating: Optional[float] = None
    new_rating: Optional[float] = None
    delta_rating: Optional[float] = None
    predict_time: Optional[datetime] = None


class ContestFinal(Contest):
    # leetcode will rejudge some submissions(cheat detection, add test cases, etc.), so will update here.
    update_time: datetime


class User(Document):
    # save latest value
    username: Indexed(str)
    user_slug: Indexed(str)
    data_region: Indexed(str)
    update_time: datetime
    # following come from graphql
    attendedContestsCount: int
    rating: float
    globalRanking: int
    topPercentage: float
    totalParticipants:  Optional[int] = None  # US
    localRanking: Optional[int] = None  # CN
    globalTotalParticipants: Optional[int] = None  # CN
    localTotalParticipants: Optional[int] = None  # CN
    # TODO: add historical rating, save into a array.




