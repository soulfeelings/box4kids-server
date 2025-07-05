from pydantic import BaseModel
from typing import List


class SkillBase(BaseModel):
    name: str


class SkillResponse(SkillBase):
    id: int
    
    class Config:
        from_attributes = True


class SkillsListResponse(BaseModel):
    skills: List[SkillResponse] 