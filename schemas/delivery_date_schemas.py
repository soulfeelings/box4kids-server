from pydantic import BaseModel
from typing import List


class AllowedDatesResponse(BaseModel):
    dates: List[str]


class AllowedDateRequest(BaseModel):
    date: str  # YYYY-MM-DD

