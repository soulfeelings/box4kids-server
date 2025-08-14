from pydantic import BaseModel
from typing import List


class AllowedTimesResponse(BaseModel):
    ranges: List[str]
    hours: List[str]


class AddRangeRequest(BaseModel):
    range: str


class AddHourRequest(BaseModel):
    hour: str


