from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PredictionEvent(BaseModel):
    name: str
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["Ongoing", "Passed", "Failed"] = "Ongoing"


class UserContestHistoryRecord(BaseModel):
    contest_title: str
    finishTimeInSeconds: int
    # Actually, `rating` here is `new_rating` in ContestRecord
    rating: float
    ranking: int
    solved_questions_id: Optional[List[int]] = None
