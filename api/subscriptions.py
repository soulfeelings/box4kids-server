from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
from services.subscription_service import SubscriptionService
from schemas.auth_schemas import UserFromToken
from schemas.subscription_schemas import (
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
    SubscriptionResponse,
    SubscriptionWithDetailsResponse,
    PauseSubscriptionResponse,
    ResumeSubscriptionResponse,
)
from typing import List
from core.i18n import translate

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription_order(
    request: SubscriptionCreateRequest,
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    """Создает заказ подписки для текущего пользователя"""
    # TODO: Здесь нужно проверить что child_id принадлежит current_user
    # Пока оставляю как есть, но нужно добавить проверку
    try:
        return subscription_service.create_subscription_order(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Ошибка при создании заказа подписки: {e}")
        raise HTTPException(status_code=500, detail=translate('internal_server_error', lang))


@router.get("/user", response_model=List[SubscriptionWithDetailsResponse])
async def get_user_subscriptions(
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    """Получает подписки текущего пользователя"""
    try:
        print(f"DEBUG: Получаем подписки для пользователя {current_user.id}")
        subscriptions = subscription_service.get_user_subscriptions(current_user.id)
        print(f"DEBUG: Получено {len(subscriptions)} подписок")
        return subscriptions
    except Exception as e:
        print(f"ERROR: Ошибка в get_user_subscriptions: {e}")
        print(f"ERROR: Тип ошибки: {type(e)}")
        import traceback
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=translate('error_getting_subscriptions', lang) + f": {str(e)}")


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    """Получает подписку по ID"""
    subscription = subscription_service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail=translate('subscription_not_found', lang))
    
    # TODO: Проверить что подписка принадлежит текущему пользователю
    # if subscription.user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Нет доступа к этой подписке")
    
    return subscription

@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdateRequest,
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    """Обновляет подписку"""
    # TODO: Проверить что подписка принадлежит текущему пользователю
    try:
        subscription = subscription_service.update_subscription(subscription_id, update_data)
        if not subscription:
            raise HTTPException(status_code=404, detail=translate('subscription_not_found', lang))
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Ошибка при обновлении подписки: {e}")
        raise HTTPException(status_code=500, detail=translate('internal_server_error', lang))


@router.post("/{subscription_id}/pause", response_model=PauseSubscriptionResponse)
async def pause_subscription(
    subscription_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    """Приостанавливает подписку по ID"""
    try:
        success = subscription_service.pause_subscription(subscription_id, current_user.id)
        if success:
            return PauseSubscriptionResponse(message=translate('subscription_paused', lang))
        else:
            raise HTTPException(status_code=400, detail=translate('failed_to_pause_subscription', lang))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subscription_id}/resume", response_model=ResumeSubscriptionResponse)
async def resume_subscription(
    subscription_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    """Возобновляет приостановленную подписку по ID"""
    try:
        success = subscription_service.resume_subscription(subscription_id, current_user.id)
        if success:
            return ResumeSubscriptionResponse(message=translate('subscription_resumed', lang))
        else:
            raise HTTPException(status_code=400, detail=translate('failed_to_resume_subscription', lang))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
 

@router.post("/recalculate-discounts")
async def recalculate_discounts(
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    """Принудительно пересчитывает скидки для всех подписок пользователя"""
    try:
        subscription_service.recalculate_discounts_for_user(current_user.id)
        return {"message": translate('discounts_recalculated', lang)}
    except Exception as e:
        print(f"Ошибка при пересчете скидок: {e}")
        raise HTTPException(status_code=500, detail=translate('error_recalculating_discounts', lang))
 