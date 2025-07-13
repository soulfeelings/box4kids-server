from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Optional, List
from datetime import date
from models.child import Gender
from .interest_schemas import InterestResponse
from .skill_schemas import SkillResponse


def validate_birth_date(birth_date: date) -> date:
    """Общая валидация даты рождения"""
    today = date.today()
    
    # Дата рождения не может быть в будущем
    if birth_date > today:
        raise ValueError("Дата рождения не может быть в будущем")
    
    # Вычисляем возраст
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    # Возраст не может быть отрицательным (для детей младше года)
    age = max(0, age)
    
    # Ребенок должен быть от 0 до 18 лет
    if age > 18:
        raise ValueError("Возраст ребенка должен быть от 0 до 18 лет")
        
    return birth_date


class ChildCreate(BaseModel):
    name: str = Field(..., description="Имя ребенка")
    date_of_birth: date = Field(..., description="Дата рождения ребенка")
    gender: Gender = Field(..., description="Пол ребенка")
    has_limitations: bool = Field(default=False, description="Есть ли ограничения по здоровью")
    comment: Optional[str] = Field(None, description="Комментарий о ребенке")
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        return validate_birth_date(v)


class ChildResponse(BaseModel):
    id: int
    name: str
    date_of_birth: date
    gender: Gender
    has_limitations: bool
    comment: Optional[str]
    parent_id: int
    interests: List[InterestResponse] = []
    skills: List[SkillResponse] = []
    
    @computed_field
    @property
    def age(self) -> int:
        """Вычисляет возраст ребенка на основе даты рождения.
        
        Примечание: Вычисление происходит только по датам без учета времени и часовых поясов.
        Это покрывает 99% случаев корректно для детских игрушек.
        """
        today = date.today()
        age = today.year - self.date_of_birth.year
        
        # Если день рождения еще не прошел в этом году, вычитаем 1
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
            
        # Возраст не может быть отрицательным (для детей младше года)
        return max(0, age)
    
    class Config:
        from_attributes = True


class ChildUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    has_limitations: Optional[bool] = None
    comment: Optional[str] = None
    interest_ids: Optional[List[int]] = None
    skill_ids: Optional[List[int]] = None
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return None
        return validate_birth_date(v) 