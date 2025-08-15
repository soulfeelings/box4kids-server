from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.security import get_current_admin
from services.inventory_service import InventoryService
from typing import List
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin Inventory"])

# Схемы для управления складом
class InventoryItemResponse(BaseModel):
    id: int
    category_id: int
    category_name: str
    available_quantity: int
    reserved_quantity: int
    total_quantity: int  # available + reserved
    created_at: datetime
    updated_at: datetime

class UpdateInventoryRequest(BaseModel):
    available_quantity: int

@router.get("/inventory", response_model=List[InventoryItemResponse])
async def get_inventory(
    current_admin: dict = Depends(get_current_admin),
    inventory_service: InventoryService = Depends(lambda db=Depends(get_db): InventoryService(db))
):
    """Получить все остатки на складе"""
    inventory_items = inventory_service.get_all()
    
    result = []
    for item in inventory_items:
        total_quantity = item.available_quantity + item.reserved_quantity
        result.append(InventoryItemResponse(
            id=item.id,
            category_id=item.category_id,
            category_name=item.category.name if item.category else "Неизвестная категория",
            available_quantity=item.available_quantity,
            reserved_quantity=item.reserved_quantity,
            total_quantity=total_quantity,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return result

@router.put("/inventory/{category_id}")
async def update_inventory(
    category_id: int,
    request: UpdateInventoryRequest,
    current_admin: dict = Depends(get_current_admin),
    inventory_service: InventoryService = Depends(lambda db=Depends(get_db): InventoryService(db))
):
    """Обновить остатки на складе для категории"""
    logger.info(f"Попытка обновления остатков для категории {category_id}: {request.available_quantity}")
    
    inventory = inventory_service.get_by_category_id(category_id)
    if not inventory:
        logger.error(f"Категория {category_id} на складе не найдена")
        raise HTTPException(status_code=404, detail="Категория на складе не найдена")
    
    old_quantity = inventory.available_quantity
    inventory.available_quantity = request.available_quantity
    inventory.updated_at = datetime.utcnow()
    
    logger.info(f"Обновляем остатки: {old_quantity} -> {request.available_quantity}")
    
    # Сохраняем изменения в БД
    success = inventory_service.update_inventory(inventory)
    if not success:
        logger.error(f"Не удалось обновить остатки для категории {category_id}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении остатков")
    
    logger.info(f"Успешно обновлены остатки для категории {category_id}")
    
    # Возвращаем обновленные данные
    return {
        "message": "Остатки обновлены", 
        "category_id": category_id, 
        "new_quantity": request.available_quantity,
        "updated_at": inventory.updated_at.isoformat()
    }

 