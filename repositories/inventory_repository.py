from typing import List, Optional
from sqlalchemy.orm import Session
from models.inventory import Inventory
from repositories.toy_category_repository import ToyCategoryRepository
import logging

logger = logging.getLogger(__name__)


class InventoryRepository:
    """Репозиторий для работы со складом"""
    
    def __init__(self, db: Session):
        self._db = db
        self.category_repo = ToyCategoryRepository(db)
    
    def get_all(self) -> List[Inventory]:
        """Получить все категории на складе"""
        return self._db.query(Inventory).all()
    
    def get_by_ids(self, ids: List[int]) -> List[Inventory]:
        """Получить категории на складе по списку ID"""
        return self._db.query(Inventory).filter(Inventory.id.in_(ids)).all()
    
    def get_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """Получить элемент склада по ID"""
        return self._db.query(Inventory).filter(Inventory.id == inventory_id).first()
    
    def get_by_category_id(self, category_id: int) -> Optional[Inventory]:
        """Получить категорию на складе по ID категории"""
        return self._db.query(Inventory).filter(Inventory.category_id == category_id).first()
    
    def create(self, category_id: int, quantity: int) -> Inventory:
        """Создать новую категорию на складе"""
        inventory = Inventory(category_id=category_id, available_quantity=quantity)
        self._db.add(inventory)
        self._db.flush()  # Только flush для получения ID
        self._db.refresh(inventory)
        logger.info(f"Создан элемент склада для категории {category_id} с количеством {quantity}")
        return inventory

    def create_many(self, categories_data: List[dict]) -> List[Inventory]:
        """Создать множество категорий на складе"""
        inventories = []
        for category_data in categories_data:
            # Найти категорию по имени
            category = self.category_repo.get_by_name(category_data["category_name"])
            if not category:
                logger.warning(f"Категория {category_data['category_name']} не найдена, пропускаем")
                continue
                
            inventory = Inventory(
                category_id=category.id,
                available_quantity=category_data["available_quantity"]
            )
            self._db.add(inventory)
            inventories.append(inventory)
            logger.debug(f"Добавлен элемент склада для категории {category.name}")
        
        self._db.flush()  # Только flush для получения ID
        
        for inventory in inventories:
            self._db.refresh(inventory)
        
        logger.info(f"Создано {len(inventories)} элементов склада")
        return inventories 