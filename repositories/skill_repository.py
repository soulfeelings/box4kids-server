from typing import List, Optional
from sqlalchemy.orm import Session
from models.skill import Skill


class SkillRepository:
    """Репозиторий для работы с навыками"""
    
    def __init__(self, db: Session):
        self._db = db
    
    def get_all(self) -> List[Skill]:
        """Получить все навыки"""
        return self._db.query(Skill).all()
    
    def get_by_ids(self, ids: List[int]) -> List[Skill]:
        """Получить навыки по списку ID"""
        return self._db.query(Skill).filter(Skill.id.in_(ids)).all()
    
    def get_by_id(self, skill_id: int) -> Optional[Skill]:
        """Получить навык по ID"""
        return self._db.query(Skill).filter(Skill.id == skill_id).first()
    
    def get_by_name(self, name: str) -> Optional[Skill]:
        """Получить навык по имени"""
        return self._db.query(Skill).filter(Skill.name == name).first()
    
    def create(self, name: str) -> Skill:
        """Создать новый навык"""
        skill = Skill(name=name)
        self._db.add(skill)
        self._db.flush()  # Только flush для получения ID
        self._db.refresh(skill)
        return skill
    
    def create_many(self, skills_data: List[dict]) -> List[Skill]:
        """Создать несколько навыков"""
        skills = []
        for data in skills_data:
            skill = Skill(**data)
            skills.append(skill)
        
        self._db.add_all(skills)
        self._db.flush()  # Только flush для получения ID
        
        # Refresh all objects
        for skill in skills:
            self._db.refresh(skill)
        
        return skills
    
    def delete(self, skill_id: int) -> bool:
        """Удалить навык по ID"""
        skill = self.get_by_id(skill_id)
        if skill:
            self._db.delete(skill)
            return True
        return False
    
    def delete_all(self) -> None:
        """Удалить все навыки"""
        self._db.query(Skill).delete() 