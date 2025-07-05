from pydantic import BaseModel
from typing import List


class InterestBase(BaseModel):
    name: str


class InterestResponse(InterestBase):
    id: int
    
    class Config:
        from_attributes = True


class InterestsListResponse(BaseModel):
    interests: List[InterestResponse] 