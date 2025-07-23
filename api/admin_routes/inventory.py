from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_admin
from services.inventory_service import InventoryService
from typing import List
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin Inventory"])

# Схемы для управления складом
class InventoryItemResponse(BaseModel):
    id: int
    category_id: int
    category_name: str
    available_quantity: int
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
        result.append(InventoryItemResponse(
            id=item.id,
            category_id=item.category_id,
            category_name=item.category.name if item.category else "Неизвестная категория",
            available_quantity=item.available_quantity,
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
    inventory = inventory_service.get_by_category_id(category_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Категория на складе не найдена")
    
    inventory.available_quantity = request.available_quantity
    inventory.updated_at = datetime.utcnow()
    
    # Сохраняем изменения в БД
    success = inventory_service.update_inventory(inventory)
    if not success:
        raise HTTPException(status_code=500, detail="Ошибка при обновлении остатков")
    
    return {"message": "Остатки обновлены", "category_id": category_id, "new_quantity": request.available_quantity} 