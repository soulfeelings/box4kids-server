from sqlalchemy.orm import Session
from models.child import Child, Gender
from models.interest import Interest
from models.skill import Skill
from typing import Optional, List
from datetime import date
from fastapi import HTTPException
from repositories.child_repository import ChildRepository
from schemas.child_schemas import ChildUpdate, ChildResponse
from services.interest_service import InterestService
from services.skill_service import SkillService


class ChildService:
    def __init__(self, db: Session):
        self._repository = ChildRepository(db)
        self._interest_service = InterestService(db)
        self._skill_service = SkillService(db)
    
    def create_child(self, parent_id: int, name: str, date_of_birth: date, gender: Gender, 
                     has_limitations: bool = False, comment: Optional[str] = None) -> Child:
        """Создает ребенка"""
        # Валидация даты рождения
        self._validate_date_of_birth(date_of_birth)
        
        child = Child(
            name=name,
            date_of_birth=date_of_birth,
            gender=gender,
            has_limitations=has_limitations,
            comment=comment,
            parent_id=parent_id
        )
        
        # Используем репозиторий вместо прямой работы с БД
        child = self._repository.create(child)
        
        # ПОСЛЕ создания ребенка пересчитываем скидки для всех детей пользователя
        from services.subscription_service import SubscriptionService
        subscription_service = SubscriptionService(self._repository._db)
        subscription_service.recalculate_discounts_for_user(parent_id)
        
        return child
    
    def get_children_by_parent(self, parent_id: int) -> List[ChildResponse]:
        """Получает детей пользователя с интересами и навыками"""
        children = self._repository.get_by_parent_id(parent_id)
        return [ChildResponse.model_validate(child) for child in children]
    
    def get_child_by_id(self, child_id: int) -> Optional[ChildResponse]:
        """Получает ребенка по ID с интересами и навыками"""
        child = self._repository.get_by_id(child_id)
        if not child:
            return None
        
        self._repository._db.refresh(child)
        return ChildResponse.model_validate(child)
    
    def update_child(self, child_id: int, update_data: ChildUpdate) -> Optional[ChildResponse]:
        """Обновляет информацию о ребенке"""
        # Получаем ребенка
        child = self._repository.get_by_id(child_id)
        
        if not child:
            return None
        
        # Валидируем ВСЕ данные ПЕРЕД началом изменений
        if update_data.interest_ids is not None:
            if not self._interest_service.validate_interest_ids(update_data.interest_ids):
                raise HTTPException(status_code=400, detail="Некоторые интересы не найдены")
        
        if update_data.skill_ids is not None:
            if not self._skill_service.validate_skill_ids(update_data.skill_ids):
                raise HTTPException(status_code=400, detail="Некоторые навыки не найдены")
        
        # Атомарное обновление в транзакции
        # Обновляем основные поля
        update_dict = update_data.model_dump(exclude_unset=True, exclude={"interest_ids", "skill_ids"})
        for field, value in update_dict.items():
            if field == "date_of_birth":
                self._validate_date_of_birth(value)
            setattr(child, field, value)
        
        # Обновляем интересы если нужно
        if update_data.interest_ids is not None:
            interests = self._repository._db.query(Interest).filter(Interest.id.in_(update_data.interest_ids)).all()
            child.interests = interests
        
        # Обновляем навыки если нужно
        if update_data.skill_ids is not None:
            skills = self._repository._db.query(Skill).filter(Skill.id.in_(update_data.skill_ids)).all()
            child.skills = skills
        
        # Применяем изменения в памяти
        self._repository._db.flush()
        
        # Обновляем объект с актуальными данными из БД
        self._repository._db.refresh(child)
        
        # Возвращаем обновленные данные без дополнительного запроса
        return ChildResponse.model_validate(child)
    
    def delete_child(self, child_id: int) -> bool:
        """Помечает ребенка как удаленного (soft delete)"""
        # Получаем ребенка перед удалением, чтобы знать parent_id
        child = self._repository.get_by_id(child_id)
        if not child:
            return False
        
        parent_id = child.parent_id
        
        # Удаляем ребенка
        result = self._repository.delete(child_id)
        
        # ПОСЛЕ удаления ребенка пересчитываем скидки для оставшихся детей
        if result:
            from services.subscription_service import SubscriptionService
            subscription_service = SubscriptionService(self._repository._db)
            subscription_service.recalculate_discounts_for_user(parent_id)
        
        return result
    
    def _validate_date_of_birth(self, date_of_birth: date) -> None:
        """Валидирует дату рождения"""
        today = date.today()
        
        # Дата рождения не может быть в будущем
        if date_of_birth > today:
            raise HTTPException(status_code=400, detail="Дата рождения не может быть в будущем")
        
        # Вычисляем возраст
        age = today.year - date_of_birth.year
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1
        
        # Возраст не может быть отрицательным (для детей младше года)
        age = max(0, age)
        
        # Ребенок должен быть от 0 до 18 лет
        if age > 18:
            raise HTTPException(status_code=400, detail="Возраст ребенка должен быть от 0 до 18 лет") 