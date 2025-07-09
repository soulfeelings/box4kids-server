from sqlalchemy.orm import Session
from repositories.toy_box_repository import ToyBoxRepository
from repositories.subscription_repository import SubscriptionRepository
from repositories.child_repository import ChildRepository
from repositories.plan_toy_configuration_repository import PlanToyConfigurationRepository
from repositories.toy_category_repository import ToyCategoryRepository
from models.toy_box import ToyBox, ToyBoxItem, ToyBoxStatus
from models.subscription import SubscriptionStatus
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


class ToyBoxService:
    def __init__(self, db: Session):
        self.db = db
        self.box_repo = ToyBoxRepository(db)
        self.subscription_repo = SubscriptionRepository(db)
        self.child_repo = ChildRepository(db)
        self.config_repo = PlanToyConfigurationRepository(db)
        self.category_repo = ToyCategoryRepository(db)

    def create_box_for_subscription(self, subscription_id: int) -> ToyBox:
        """Создать набор для подписки на основе плана"""
        # Получаем подписку
        subscription = self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Подписка {subscription_id} не найдена")
        
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise ValueError(f"Подписка {subscription_id} не активна")

        # Получаем конфигурацию плана
        plan_configs = self.config_repo.get_by_plan_id(subscription.plan_id)
        if not plan_configs:
            raise ValueError(f"Конфигурация для плана {subscription.plan_id} не найдена")

        # Создаем набор
        box_data = {
            "subscription_id": subscription_id,
            "child_id": subscription.child_id,
            "delivery_info_id": subscription.delivery_info_id,
            "status": ToyBoxStatus.PLANNED,
            "delivery_date": datetime.utcnow() + timedelta(days=7),  # Через неделю
            "return_date": datetime.utcnow() + timedelta(days=21),   # Через 3 недели
        }
        
        box = self.box_repo.create_box(box_data)
        
        # Добавляем состав набора
        items_data = []
        for config in plan_configs:
            items_data.append({
                "toy_category_id": config.category_id,
                "quantity": config.quantity
            })
        
        self.box_repo.add_items(box.id, items_data)
        
        return box

    def get_current_box_by_child(self, child_id: int) -> Optional[ToyBox]:
        """Получить текущий набор ребёнка"""
        return self.box_repo.get_current_box_by_child(child_id)

    def get_current_box_by_user(self, user_id: int) -> Optional[ToyBox]:
        """Получить текущий набор для любого ребёнка пользователя"""
        children = self.child_repo.get_by_parent_id(user_id)
        
        for child in children:
            current_box = self.get_current_box_by_child(child.id)
            if current_box:
                return current_box
        
        return None

    def generate_next_box_for_child(self, child_id: int) -> Optional[ToyBox]:
        """Генерировать следующий набор на лету (не сохраняется в БД)"""
        child = self.child_repo.get_by_id(child_id)
        if not child:
            raise ValueError(f"Ребёнок {child_id} не найден")

        # Получаем активную подписку
        subscription = self.subscription_repo.get_active_by_child_id(child_id)
        if not subscription:
            return None

        # Получаем конфигурацию плана
        plan_configs = self.config_repo.get_by_plan_id(subscription.plan_id)
        if not plan_configs:
            return None

        # Рассчитываем даты
        current_box = self.get_current_box_by_child(child_id)
        if current_box and current_box.return_date:
            next_delivery = current_box.return_date + timedelta(days=1)
            next_return = next_delivery + timedelta(days=14)
        else:
            next_delivery = datetime.utcnow() + timedelta(days=7)
            next_return = next_delivery + timedelta(days=14)

        # Создаем ToyBox объект (не сохраняем в БД)
        next_box = ToyBox(
            subscription_id=subscription.id,
            child_id=child_id,
            status=ToyBoxStatus.PLANNED,
            delivery_date=next_delivery,
            return_date=next_return,
            created_at=datetime.utcnow()
        )

        # Формируем состав следующего набора
        items = []
        for config in plan_configs:
            category = self.category_repo.get_by_id(config.category_id)
            if category:
                item = ToyBoxItem(
                    toy_category_id=config.category_id,
                    quantity=config.quantity
                )
                # Добавляем связь с категорией для удобства
                item.category = category
                items.append(item)

        next_box.items = items
        return next_box

    def add_review(self, box_id: int, user_id: int, rating: int, comment: Optional[str] = None) -> bool:
        """Добавить отзыв к набору"""
        # Проверяем права доступа
        box = self.box_repo.get_by_id(box_id)
        if not box:
            return False

        # Проверяем, что пользователь является родителем ребёнка
        child = self.child_repo.get_by_id(box.child_id)
        if not child or child.parent_id != user_id:
            return False

        # Добавляем отзыв
        review_data = {
            "box_id": box_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment
        }
        
        self.box_repo.add_review(review_data)
        return True

    def get_box_history_by_user(self, user_id: int, limit: int = 10) -> List[ToyBox]:
        """Получить историю наборов для всех детей пользователя"""
        children = self.child_repo.get_by_parent_id(user_id)
        
        all_boxes = []
        for child in children:
            boxes = self.box_repo.get_boxes_by_child(child.id, limit)
            all_boxes.extend(boxes)
        
        # Сортируем по дате создания
        all_boxes.sort(key=lambda x: x.created_at, reverse=True)
        
        return all_boxes[:limit]

    def update_box_status(self, box_id: int, status: ToyBoxStatus) -> Optional[ToyBox]:
        """Обновить статус набора"""
        return self.box_repo.update_status(box_id, status) 