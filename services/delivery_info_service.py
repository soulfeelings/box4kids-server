from sqlalchemy.orm import Session
from repositories.delivery_info_repository import DeliveryInfoRepository
from services.toy_box_service import ToyBoxService
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
        self._toy_box_service = ToyBoxService(db)
    
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
        
        # Синхронизируем активные toy boxes если изменились дата или время
        date_changed = 'date' in filtered_data and filtered_data['date'] is not None
        time_changed = 'time' in filtered_data and filtered_data['time'] is not None
        
        if date_changed and time_changed:
            # Изменились и дата, и время
            new_date = filtered_data['date']
            new_time = filtered_data['time']
            self._toy_box_service.sync_active_boxes_with_delivery_date_and_time(
                address_id, user_id, new_date, new_time
            )
        elif date_changed:
            # Изменилась только дата
            new_date = filtered_data['date']
            self._toy_box_service.sync_active_boxes_with_delivery_date(
                address_id, user_id, new_date
            )
        elif time_changed:
            # Изменилось только время
            new_time = filtered_data['time']
            self._toy_box_service.sync_active_boxes_with_delivery_time(
                address_id, user_id, new_time
            )
        
        return DeliveryInfoResponse.model_validate(updated_address)
    
    def delete_address(self, user_id: int, address_id: int) -> bool:
        """Удалить адрес доставки пользователя"""
        return self._repository.delete(address_id, user_id) 