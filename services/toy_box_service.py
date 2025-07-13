from sqlalchemy.orm import Session
from repositories.toy_box_repository import ToyBoxRepository
from repositories.subscription_repository import SubscriptionRepository
from repositories.child_repository import ChildRepository
from repositories.plan_toy_configuration_repository import PlanToyConfigurationRepository
from repositories.toy_category_repository import ToyCategoryRepository
from models.toy_box import ToyBox, ToyBoxItem, ToyBoxReview, ToyBoxStatus
from models.subscription import SubscriptionStatus
from schemas.toy_box_schemas import NextBoxResponse, NextBoxItemResponse
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

    def generate_next_box_for_child(self, child_id: int) -> Optional[NextBoxResponse]:
        """Генерировать следующий набор на лету (не сохраняется в БД)"""
        child = self.child_repo.get_by_id(child_id)
        print(f"generate_next_box_for_child: Child: {child}")
        if not child:
            raise ValueError(f"Ребёнок {child_id} не найден")

        # Получаем активную подписку
        subscription = self.subscription_repo.get_active_by_child_id(child_id)
        print(f"generate_next_box_for_child: Subscription: {subscription}")
        if not subscription:
            return None

        # Получаем конфигурацию плана
        plan_configs = self.config_repo.get_by_plan_id(subscription.plan_id)
        print(f"generate_next_box_for_child: Plan configs: {plan_configs}")
        if not plan_configs:
            return None

        # Рассчитываем даты
        current_box = self.get_current_box_by_child(child_id)
        print(f"generate_next_box_for_child: Current box: {current_box}")
        if current_box and current_box.return_date:
            next_delivery = current_box.return_date + timedelta(days=1)
            next_return = next_delivery + timedelta(days=14)
        else:
            next_delivery = datetime.utcnow() + timedelta(days=7)
            next_return = next_delivery + timedelta(days=14)

        # Формируем состав следующего набора
        items = []
        for config in plan_configs:
            category = self.category_repo.get_by_id(config.category_id)
            print(f"generate_next_box_for_child: Category: {category}")
            if category:
                item = NextBoxItemResponse(
                    category_id=config.category_id,
                    category_name=getattr(category, 'name'),
                    category_icon=getattr(category, 'icon'),
                    quantity=config.quantity
                )
                items.append(item)
                print(f"generate_next_box_for_child: Item: {item}")

        next_box_response = NextBoxResponse(
            items=items,
            delivery_date=next_delivery,
            return_date=next_return,
            message=f"Следующий набор для {child.name}"
        )
        
        print(f"generate_next_box_for_child: Next box response: {next_box_response}")
        return next_box_response

    def add_review(self, box_id: int, user_id: int, rating: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """Добавить отзыв к набору"""
        # Проверяем права доступа
        box = self.box_repo.get_by_id(box_id)
        if not box:
            return {"success": False, "error": "Набор не найден"}

        # Проверяем, что пользователь является родителем ребёнка
        child = self.child_repo.get_by_id(box.child_id)
        if not child or child.parent_id != user_id:
            return {"success": False, "error": "Нет прав доступа к этому набору"}

        # Проверяем статус набора (только доставленные можно оценивать)
        if box.status != ToyBoxStatus.DELIVERED:
            return {"success": False, "error": "Отзыв можно оставить только на доставленный набор"}

        # Проверяем, что пользователь ещё не оставлял отзыв на этот набор
        existing_review = self.db.query(ToyBoxReview).filter(
            ToyBoxReview.box_id == box_id,
            ToyBoxReview.user_id == user_id
        ).first()
        
        if existing_review:
            return {"success": False, "error": "Вы уже оставили отзыв на этот набор"}

        # Добавляем отзыв
        review_data = {
            "box_id": box_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment
        }
        
        review = self.box_repo.add_review(review_data)
        return {"success": True, "review": review}

    def get_box_reviews(self, box_id: int) -> List[ToyBoxReview]:
        """Получить все отзывы для набора"""
        return self.box_repo.get_reviews_by_box(box_id)

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