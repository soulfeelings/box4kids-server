
import random
from sqlalchemy.orm.session import Session
from core.config import settings
from repositories.inventory_repository import InventoryRepository
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """Сервис для работы со складом"""
    
    def __init__(self, db: Session):
        self.inventory_repository = InventoryRepository(db)
    
    def get_by_category_id(self, category_id: int):
        """Получить остатки по категории"""
        inventory = self.inventory_repository.get_by_category_id(category_id)
        if not inventory:
            logger.warning(f"Остатки для категории {category_id} не найдены")
        return inventory
    
    def get_all(self):
        """Получить все остатки на складе"""
        return self.inventory_repository.get_all()
    
    def update_inventory(self, inventory):
        """Обновить остатки на складе"""
        if not inventory:
            logger.warning("Попытка обновить несуществующий элемент склада")
            return False
        
        try:
            self.inventory_repository._db.flush()
            logger.info(f"Обновлены остатки для категории {inventory.category_id}: {inventory.available_quantity}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении остатков: {e}")
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