from sqlalchemy.orm import Session, joinedload
from models.plan_toy_configuration import PlanToyConfiguration
from typing import List, Optional


class PlanToyConfigurationRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[PlanToyConfiguration]:
        """Получить все конфигурации"""
        return self.db.query(PlanToyConfiguration).all()
    
    def get_by_plan_id(self, plan_id: int) -> List[PlanToyConfiguration]:
        """Получить конфигурации для плана с загрузкой категорий"""
        return (
            self.db.query(PlanToyConfiguration)
            .options(joinedload(PlanToyConfiguration.category))
            .filter(PlanToyConfiguration.plan_id == plan_id)
            .all()
        )
    
    def get_by_id(self, config_id: int) -> Optional[PlanToyConfiguration]:
        """Получить конфигурацию по ID"""
        return self.db.query(PlanToyConfiguration).filter(PlanToyConfiguration.id == config_id).first()
    
    def create(self, config_data: dict) -> PlanToyConfiguration:
        """Создать новую конфигурацию"""
        config = PlanToyConfiguration(**config_data)
        self.db.add(config)
        self.db.flush()
        self.db.refresh(config)
        return config
    
    def create_many(self, configs_data: List[dict]) -> List[PlanToyConfiguration]:
        """Создать множество конфигураций"""
        configs = []
        for config_data in configs_data:
            config = PlanToyConfiguration(**config_data)
            self.db.add(config)
            configs.append(config)
        
        self.db.flush()
        
        for config in configs:
            self.db.refresh(config)
        
        return configs
    
    def delete_by_plan_id(self, plan_id: int) -> None:
        """Удалить все конфигурации для плана"""
        self.db.query(PlanToyConfiguration).filter(PlanToyConfiguration.plan_id == plan_id).delete()
        self.db.flush() 