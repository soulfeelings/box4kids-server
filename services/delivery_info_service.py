from sqlalchemy.orm import Session
from repositories.delivery_info_repository import DeliveryInfoRepository
from schemas.delivery_info_schemas import (
    DeliveryInfoCreate, 
    DeliveryInfoUpdate,
    DeliveryInfoResponse,
    DeliveryInfoListResponse
)
from typing import Optional


class DeliveryInfoService:
    """Сервис для работы с адресами доставки"""
    
    def __init__(self, db: Session):
        self._repository = DeliveryInfoRepository(db)
    
    def get_user_addresses(self, user_id: int, limit: Optional[int] = None) -> DeliveryInfoListResponse:
        """Получить адреса доставки пользователя"""
        addresses = self._repository.get_by_user_id(user_id, limit)
        address_responses = [
            DeliveryInfoResponse.model_validate(address) for address in addresses
        ]
        return DeliveryInfoListResponse(addresses=address_responses)
    
    def create_address(self, user_id: int, address_data: DeliveryInfoCreate) -> DeliveryInfoResponse:
        """Создать новый адрес доставки для пользователя"""
        create_data = address_data.model_dump()
        create_data["user_id"] = user_id
        
        address = self._repository.create(create_data)
        return DeliveryInfoResponse.model_validate(address)
    
    def update_address(self, user_id: int, address_id: int, update_data: DeliveryInfoUpdate) -> Optional[DeliveryInfoResponse]:
        """Обновить адрес доставки пользователя"""
        # Фильтруем только поля с значениями
        filtered_data = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not filtered_data:
            return None
        
        updated_address = self._repository.update(address_id, user_id, filtered_data)
        if not updated_address:
            return None
        
        return DeliveryInfoResponse.model_validate(updated_address)
    
    def delete_address(self, user_id: int, address_id: int) -> bool:
        """Удалить адрес доставки пользователя"""
        return self._repository.delete(address_id, user_id) 