from pydantic import BaseModel

from app.db.models import DATA_REGION


class UserKey(BaseModel):
    # Unique key of User collection, DON'T miss `data_region` when dealing with User models
    username: str
    data_region: DATA_REGION
