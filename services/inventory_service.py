
from sqlalchemy.orm.session import Session
from repositories.inventory_repository import InventoryRepository
from repositories.toy_box_repository import ToyBoxRepository
from models.toy_box import ToyBoxStatus
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """Сервис для работы со складом"""
    
    def __init__(self, db: Session):
        self.inventory_repository = InventoryRepository(db)
        self.toy_box_repository = ToyBoxRepository(db)
        self.db = db  # Сохраняем прямую ссылку на сессию БД
    
    def get_by_category_id(self, category_id: int):
        """Получить остатки по категории"""
        inventory = self.inventory_repository.get_by_category_id(category_id)
        if not inventory:
            logger.warning(f"Остатки для категории {category_id} не найдены")
        return inventory
    
    def get_all(self):
        """Получить все остатки на складе с подсчетом зарезервированных товаров"""
        inventory_items = self.inventory_repository.get_all()
        
        # Подсчитываем зарезервированные товары для каждой категории
        for item in inventory_items:
            reserved_count = self._calculate_reserved_quantity(item.category_id)
            item.reserved_quantity = reserved_count
        
        return inventory_items
    
    def _calculate_reserved_quantity(self, category_id: int) -> int:
        """Подсчитать количество зарезервированных товаров для категории"""
        try:
            # Зарезервированными считаются товары из наборов со статусом PLANNED
            # (запланированные наборы - товары зарезервированы на складе)
            from models.toy_box import ToyBox
            from sqlalchemy.orm import joinedload
            
            planned_boxes = self.db.query(ToyBox).options(
                joinedload(ToyBox.items)
            ).filter(ToyBox.status == ToyBoxStatus.PLANNED).all()
            
            reserved_count = 0
            for box in planned_boxes:
                # Подсчитываем товары данной категории в наборе
                for item in box.items:
                    if item.toy_category_id == category_id:
                        reserved_count += item.quantity
            
            logger.debug(f"Зарезервировано {reserved_count} товаров категории {category_id} (из {len(planned_boxes)} запланированных наборов)")
            return reserved_count
            
        except Exception as e:
            logger.error(f"Ошибка при подсчете зарезервированных товаров для категории {category_id}: {e}")
            return 0
    
    def update_inventory(self, inventory):
        """Обновить остатки на складе"""
        if not inventory:
            logger.warning("Попытка обновить несуществующий элемент склада")
            return False
        
        try:
            # Обновляем через репозиторий
            success = self.inventory_repository.update(inventory)
            if success:
                # Сохраняем изменения в базе данных
                self.inventory_repository._db.commit()
                logger.info(f"Обновлены остатки для категории {inventory.category_id}: {inventory.available_quantity}")
                return True
            else:
                logger.error(f"Не удалось обновить остатки для категории {inventory.category_id}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении остатков: {e}")
            # Откатываем изменения в случае ошибки
            self.inventory_repository._db.rollback()
            return False
    
    # Динамические лимиты на основе остатков
    def get_max_count(self, category_id: int):
        """Получить максимальное количество игрушек для категории на основе остатков"""
        inventory = self.inventory_repository.get_by_category_id(category_id)
        if not inventory:
            logger.warning(f"Остатки для категории {category_id} не найдены, используем лимит по умолчанию")
            return 1  # По умолчанию low

        available = inventory.available_quantity
        if available <= 5:
            logger.debug(f"Категория {category_id}: низкие остатки ({available}), лимит: 1")
            return 1      # low
        elif available <= 15:
            logger.debug(f"Категория {category_id}: средние остатки ({available}), лимит: 2")
            return 2      # medium (X//3 для X=6)
        else:
            logger.debug(f"Категория {category_id}: высокие остатки ({available}), лимит: 3")
            return 3      # high (X//2 для X=6)
    
    def reserve_inventory(self, items_data: List[Dict[str, Any]]) -> bool:
        """Зарезервировать товары со склада для набора"""
        try:
            for item in items_data:
                category_id = item["toy_category_id"]
                quantity = item["quantity"]
                
                inventory = self.inventory_repository.get_by_category_id(category_id)
                if not inventory:
                    logger.error(f"Остатки для категории {category_id} не найдены")
                    return False
                
                if inventory.available_quantity < quantity:
                    logger.error(f"Недостаточно остатков для категории {category_id}: требуется {quantity}, доступно {inventory.available_quantity}")
                    return False
                
                # Списываем товары со склада
                inventory.available_quantity -= quantity
                logger.info(f"Зарезервировано {quantity} товаров категории {category_id}, осталось: {inventory.available_quantity}")
            
            # Сохраняем изменения в базе данных
            self.inventory_repository._db.commit()
            logger.info(f"Успешно зарезервировано товаров для набора")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при резервировании товаров: {e}")
            # Откатываем изменения в случае ошибки
            self.inventory_repository._db.rollback()
            return False
    
    def return_inventory(self, items_data: List[Dict[str, Any]]) -> bool:
        """Вернуть товары на склад при возврате набора"""
        try:
            for item in items_data:
                category_id = item["toy_category_id"]
                quantity = item["quantity"]
                
                inventory = self.inventory_repository.get_by_category_id(category_id)
                if not inventory:
                    logger.error(f"Остатки для категории {category_id} не найдены")
                    return False
                
                # Возвращаем товары на склад
                inventory.available_quantity += quantity
                logger.info(f"Возвращено {quantity} товаров категории {category_id}, теперь доступно: {inventory.available_quantity}")
            
            # Сохраняем изменения в базе данных
            self.inventory_repository._db.commit()
            logger.info(f"Успешно возвращены товары на склад")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при возврате товаров на склад: {e}")
            # Откатываем изменения в случае ошибки
            self.inventory_repository._db.rollback()
            return False 