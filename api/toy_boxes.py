from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services.toy_box_service import ToyBoxService
from schemas.toy_box_schemas import (
    ToyBoxResponse,
    ToyBoxCreateRequest,
    ToyBoxReviewRequest,
    ToyBoxListResponse,
    ToyBoxReviewsResponse,
    NextBoxResponse
)

router = APIRouter(prefix="/toy-boxes", tags=["Toy Boxes"])


def get_toy_box_service(db: Session = Depends(get_db)) -> ToyBoxService:
    return ToyBoxService(db)


@router.get("/current/{child_id}", response_model=ToyBoxResponse)
async def get_current_box(
    child_id: int,
    toy_box_service: ToyBoxService = Depends(get_toy_box_service)
):
    """Получить текущий набор ребёнка"""
    current_box = toy_box_service.get_current_box_by_child(child_id)
    
    if not current_box:
        raise HTTPException(status_code=404, detail="Текущий набор не найден")
    
    return current_box


@router.get("/next/{child_id}", response_model=NextBoxResponse)
async def get_next_box(
    child_id: int,
    toy_box_service: ToyBoxService = Depends(get_toy_box_service)
):
    """Получить следующий набор для ребёнка (генерируется на лету)"""
    try:
        next_box = toy_box_service.generate_next_box_for_child(child_id)
        if not next_box:
            raise HTTPException(status_code=404, detail="Не удалось сформировать следующий набор")
        return next_box
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create", response_model=ToyBoxResponse)
async def create_toy_box(
    request: ToyBoxCreateRequest,
    toy_box_service: ToyBoxService = Depends(get_toy_box_service)
):
    """Создать набор для подписки"""
    try:
        box = toy_box_service.create_box_for_subscription(request.subscription_id)
        return box
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{box_id}/review")
async def add_box_review(
    box_id: int,
    request: ToyBoxReviewRequest,
    toy_box_service: ToyBoxService = Depends(get_toy_box_service)
):
    """Добавить отзыв к набору"""
    result = toy_box_service.add_review(
        box_id=box_id,
        user_id=request.user_id,
        rating=request.rating,
        comment=request.comment
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Отзыв добавлен", "review": result["review"]}


@router.get("/{box_id}/reviews", response_model=ToyBoxReviewsResponse)
async def get_box_reviews(
    box_id: int,
    toy_box_service: ToyBoxService = Depends(get_toy_box_service)
):
    """Получить все отзывы для набора"""
    reviews = toy_box_service.get_box_reviews(box_id)
    from schemas.toy_box_schemas import ToyBoxReviewResponse
    review_responses = [ToyBoxReviewResponse.model_validate(review) for review in reviews]
    return ToyBoxReviewsResponse(reviews=review_responses)


@router.get("/history/{user_id}", response_model=ToyBoxListResponse)
async def get_box_history(
    user_id: int,
    limit: int = 10,
    toy_box_service: ToyBoxService = Depends(get_toy_box_service)
):
    """Получить историю наборов пользователя"""
    boxes = toy_box_service.get_box_history_by_user(user_id, limit)
    box_responses = [ToyBoxResponse.model_validate(box) for box in boxes]
    return ToyBoxListResponse(boxes=box_responses)


@router.get("/{box_id}", response_model=ToyBoxResponse)
async def get_box_by_id(
    box_id: int,
    toy_box_service: ToyBoxService = Depends(get_toy_box_service)
):
    """Получить набор по ID"""
    box = toy_box_service.box_repo.get_by_id(box_id)
    
    if not box:
        raise HTTPException(status_code=404, detail="Набор не найден")
    
    return box 