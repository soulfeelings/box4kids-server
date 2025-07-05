from pydantic import BaseModel
from typing import List, Optional


class ToyCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class ToyCategoryResponse(ToyCategoryBase):
    id: int
    
    class Config:
        from_attributes = True


class ToyCategoriesListResponse(BaseModel):
    categories: List[ToyCategoryResponse] 