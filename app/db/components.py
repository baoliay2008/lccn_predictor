from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class PredictionEvent(BaseModel):
    name: str
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["Ongoing", "Passed", "Failed"] = "Ongoing"
