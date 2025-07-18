from sqlalchemy.orm import Session
from repositories.subscription_plan_repository import SubscriptionPlanRepository
from repositories.plan_toy_configuration_repository import PlanToyConfigurationRepository
from schemas.subscription_plan_schemas import (
    SubscriptionPlanResponse, 
    SubscriptionPlansListResponse,
    ToyCategoryConfigResponse
)


class SubscriptionPlanService:
    """Сервис для работы с планами подписки"""
    
    def __init__(self, db: Session):
        self._plan_repository = SubscriptionPlanRepository(db)
        self._config_repository = PlanToyConfigurationRepository(db)
    
    def get_all_plans(self) -> SubscriptionPlansListResponse:
        """Получить все планы подписки с конфигурациями"""
        plans = self._plan_repository.get_all()
        plan_responses = []
        
        for plan in plans:
            # Получаем конфигурации для каждого плана
            configurations = self._config_repository.get_by_plan_id(getattr(plan, 'id'))
            
            # Преобразуем конфигурации в ответ
            toy_configs = []
            for config in configurations:
                # Создаем dict для ToyCategoryConfigResponse
                toy_config_data = {
                    "id": getattr(config.category, 'id'),
                    "name": getattr(config.category, 'name'),
                    "description": getattr(config.category, 'description'),
                    "icon": getattr(config.category, 'icon'),
                    "quantity": getattr(config, 'quantity')
                }
                toy_config = ToyCategoryConfigResponse(**toy_config_data)
                toy_configs.append(toy_config)
            
            # Создаем ответ для плана
            plan_data = {
                "id": getattr(plan, 'id'),
                "name": getattr(plan, 'name'),
                "price_monthly": getattr(plan, 'price_monthly'),
                "toy_count": getattr(plan, 'toy_count'),
                "description": getattr(plan, 'description'),
                "toy_configurations": toy_configs
            }
            plan_response = SubscriptionPlanResponse(**plan_data)
            plan_responses.append(plan_response)
        
        return SubscriptionPlansListResponse(plans=plan_responses) 