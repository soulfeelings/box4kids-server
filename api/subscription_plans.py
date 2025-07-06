from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.subscription_plan_service import SubscriptionPlanService
from schemas.subscription_plan_schemas import SubscriptionPlansListResponse

router = APIRouter(prefix="/subscription-plans", tags=["Subscription Plans"])


def get_subscription_plan_service(db: Session = Depends(get_db)) -> SubscriptionPlanService:
    return SubscriptionPlanService(db)


@router.get("/", response_model=SubscriptionPlansListResponse)
async def get_all_subscription_plans(
    plan_service: SubscriptionPlanService = Depends(get_subscription_plan_service)
):
    """Получить все планы подписки с конфигурациями игрушек"""
    return plan_service.get_all_plans() 