from sqlalchemy.orm import Session
from repositories.toy_box_repository import ToyBoxRepository
from repositories.subscription_repository import SubscriptionRepository
from repositories.child_repository import ChildRepository
from repositories.plan_toy_configuration_repository import PlanToyConfigurationRepository
from repositories.toy_category_repository import ToyCategoryRepository
from repositories.delivery_info_repository import DeliveryInfoRepository
from models.toy_box import ToyBox, ToyBoxReview, ToyBoxStatus
from models.subscription import SubscriptionStatus
from schemas.toy_box_schemas import NextBoxResponse, NextBoxItemResponse
from core.config import settings
from typing import List, Optional, Dict, Any
from datetime import timedelta, date
from services.inventory_service import InventoryService
from services.category_mapping_service import CategoryMappingService


class ToyBoxService:
    def __init__(self, db: Session):
        self.db = db
        self.box_repo = ToyBoxRepository(db)
        self.subscription_repo = SubscriptionRepository(db)
        self.child_repo = ChildRepository(db)
        self.config_repo = PlanToyConfigurationRepository(db)
        self.category_repo = ToyCategoryRepository(db)
        self.delivery_repo = DeliveryInfoRepository(db)
        self.inventory_service = InventoryService(db)
        self.mapping_service = CategoryMappingService(db)

    def create_box_for_subscription(self, subscription_id: int) -> ToyBox:
        """Создать набор для подписки с автоматическим распределением по интересам"""
        # Получаем подписку
        subscription = self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Подписка {subscription_id} не найдена")
        
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise ValueError(f"Подписка {subscription_id} не активна")

        # Получаем ребенка и его интересы/навыки
        child = self.child_repo.get_by_id(child_id=subscription.child_id)
        if not child:
            raise ValueError(f"Не найден ребенок для создания бокса при подписке {subscription.id}")

        # Получаем информацию о доставке
        delivery_info = None
        delivery_time = None
        if subscription.delivery_info_id:
            delivery_info = self.delivery_repo.get_by_id(subscription.delivery_info_id)
            if delivery_info:
                delivery_time = delivery_info.time

        # Создаем набор с использованием конфигурации
        if delivery_info and delivery_info.date:
            delivery_date = delivery_info.date
        else:
            delivery_date = date.today() + timedelta(days=settings.INITIAL_DELIVERY_PERIOD)
        
        return_date = delivery_date + timedelta(days=settings.RENTAL_PERIOD)

        # Генерируем состав набора на основе интересов и навыков
        items_data = self._generate_box_items(child, subscription.plan_id)
        
        # Создаем теги на основе интересов и навыков ребенка
        interest_tags = self._generate_interest_tags(child)

        box_data = {
            "subscription_id": subscription_id,
            "child_id": subscription.child_id,
            "delivery_info_id": subscription.delivery_info_id,
            "status": ToyBoxStatus.PLANNED,
            "delivery_date": delivery_date,
            "return_date": return_date,
            "delivery_time": delivery_time,
            "return_time": delivery_time,  # Используем то же время для возврата
            "interest_tags": interest_tags,
        }
        
        box = self.box_repo.create_box(box_data)
        
        # Добавляем состав набора
        self.box_repo.add_items(box.id, items_data)
        
        return box

    def _generate_interest_tags(self, child) -> List[str]:
        """Генерировать теги на основе интересов и навыков ребенка"""
        tags = []
        
        # Добавляем интересы ребенка
        if child.interests:
            for interest in child.interests:
                tags.append(interest.name)
        
        # Добавляем навыки ребенка
        if child.skills:
            for skill in child.skills:
                tags.append(skill.name)
        
        # Возвращаем список тегов (JSONB автоматически сериализует в JSON)
        return tags if tags else None

    def _generate_box_items(self, child, plan_id: int) -> List[Dict[str, Any]]:
        """Генерировать состав набора на основе интересов и навыков ребенка"""
        # Получаем конфигурацию плана для определения общего количества игрушек
        plan_configs = self.config_repo.get_by_plan_id(plan_id)
        if not plan_configs:
            raise ValueError(f"Конфигурация для плана {plan_id} не найдена")
        
        total_toys = sum(config.quantity for config in plan_configs)
        max_categories = 6  # X = 6 (максимальное разнообразие)
        
        # Получаем историю наборов ребенка для избежания повторений
        recent_boxes = self.box_repo.get_boxes_by_child(child.id, limit=3)
        recent_categories = set()
        for box in recent_boxes:
            for item in box.items:
                recent_categories.add(item.toy_category_id)
        
        # Получаем категории с скорингом
        child_interests = list(child.interests) if child.interests else []
        child_skills = list(child.skills) if child.skills else []
        
        scored_categories = self.mapping_service.get_categories_with_scores(
            child_interests, child_skills
        )
        
        # Применяем штраф за повторения
        for scored_category in scored_categories:
            if scored_category["category"].id in recent_categories:
                scored_category["score"] *= 0.3  # Штраф 70%
        
        # Сортируем по скорингу
        scored_categories.sort(key=lambda x: x["score"], reverse=True)
        
        # Распределяем игрушки
        items_data = []
        remaining_toys = total_toys
        used_categories = 0
        
        for scored_category in scored_categories:
            if remaining_toys <= 0 or used_categories >= max_categories:
                break
                
            category = scored_category["category"]
            max_count = self.inventory_service.get_max_count(category.id)
            
            # Определяем количество для этой категории
            if remaining_toys <= max_count:
                quantity = remaining_toys
            else:
                quantity = max_count
            
            if quantity > 0:
                items_data.append({
                    "toy_category_id": category.id,
                    "quantity": quantity
                })
                remaining_toys -= quantity
                used_categories += 1
        
        # Если остались игрушки, распределяем по оставшимся категориям
        if remaining_toys > 0:
            all_categories = self.category_repo.get_all()
            for category in all_categories:
                if remaining_toys <= 0:
                    break
                    
                # Проверяем, не использовали ли уже эту категорию
                if any(item["toy_category_id"] == category.id for item in items_data):
                    continue
                
                max_count = self.inventory_service.get_max_count(category.id)
                quantity = min(remaining_toys, max_count)
                
                if quantity > 0:
                    items_data.append({
                        "toy_category_id": category.id,
                        "quantity": quantity
                    })
                    remaining_toys -= quantity
        
        return items_data

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

        # Рассчитываем даты и берем время из текущего набора
        current_box = self.get_current_box_by_child(child_id)
        print(f"generate_next_box_for_child: Current box: {current_box}")
        
        # Рассчитываем даты и время ТОЛЬКО на основе текущего набора
        if current_box and current_box.return_date:
            # Есть текущий набор - можем рассчитать следующий
            next_delivery_date = current_box.return_date + timedelta(days=settings.NEXT_DELIVERY_PERIOD)
            next_return_date = next_delivery_date + timedelta(days=settings.RENTAL_PERIOD)
            delivery_time = current_box.delivery_time
            return_time = current_box.return_time
        else:
            # Нет текущего набора - нельзя рассчитать даты
            next_delivery_date = None
            next_return_date = None
            delivery_time = None
            return_time = None

        # Формируем состав следующего набора
        items = []
        for config in plan_configs:
            category = self.category_repo.get_by_id(config.category_id)
            if category:
                items.append(NextBoxItemResponse(
                    category_id=category.id,
                    category_name=category.name,
                    category_icon=category.icon,
                    quantity=config.quantity
                ))

        next_box_response = NextBoxResponse(
            items=items,
            delivery_date=next_delivery_date,
            return_date=next_return_date,
            delivery_time=delivery_time,
            return_time=return_time,
            message="Следующий набор будет создан после возврата текущего"
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

    def get_box_history_by_user(self, user_id: int, limit: int = 10, statuses: Optional[List[ToyBoxStatus]] = None) -> List[ToyBox]:
        """Получить историю наборов для всех детей пользователя"""
        children = self.child_repo.get_by_parent_id(user_id)
        
        all_boxes = []
        for child in children:
            boxes = self.box_repo.get_boxes_by_child(child.id, limit)
            all_boxes.extend(boxes)
        
        # Фильтруем по статусам если указаны
        if statuses:
            all_boxes = [box for box in all_boxes if box.status in statuses]
        
        # Сортируем по дате создания
        all_boxes.sort(key=lambda x: x.created_at, reverse=True)
        
        return all_boxes[:limit]

    def update_box_status(self, box_id: int, status: ToyBoxStatus) -> Optional[ToyBox]:
        """Обновить статус набора"""
        return self.box_repo.update_status(box_id, status)

    def sync_active_boxes_with_delivery_date(self, delivery_info_id: int, user_id: int, new_date: date) -> List[ToyBox]:
        """Синхронизировать активные наборы с обновленной датой доставки"""
        from datetime import timedelta
        
        # Получаем только активные наборы пользователя с этим delivery_info_id
        active_boxes = self.box_repo.get_active_boxes_by_delivery_info_id(delivery_info_id, user_id)
        
        updated_boxes = []
        for box in active_boxes:
            # Рассчитываем новую дату возврата
            return_date = new_date + timedelta(days=settings.RENTAL_PERIOD)
            
            # Обновляем дату доставки
            updated_box = self.box_repo.update_delivery_date(box.id, new_date, return_date)
            if updated_box:
                updated_boxes.append(updated_box)
        
        return updated_boxes

    def sync_active_boxes_with_delivery_time(self, delivery_info_id: int, user_id: int, new_time: str) -> List[ToyBox]:
        """Синхронизировать активные наборы с обновленным временем доставки"""
        
        # Получаем только активные наборы пользователя с этим delivery_info_id
        active_boxes = self.box_repo.get_active_boxes_by_delivery_info_id(delivery_info_id, user_id)
        
        updated_boxes = []
        for box in active_boxes:
            # Обновляем время доставки
            updated_box = self.box_repo.update_delivery_time(box.id, new_time)
            if updated_box:
                updated_boxes.append(updated_box)
        
        return updated_boxes

    def sync_active_boxes_with_delivery_date_and_time(self, delivery_info_id: int, user_id: int, new_date: date, new_time: str) -> List[ToyBox]:
        """Синхронизирует активные наборы с новой датой и временем доставки"""
        active_boxes = self.box_repo.get_active_boxes_by_user(user_id)
        
        updated_boxes = []
        for box in active_boxes:
            if box.delivery_info_id == delivery_info_id:
                box.delivery_date = new_date
                box.delivery_time = new_time
                box.return_time = new_time
                self.db.commit()
                updated_boxes.append(box)
        
        return updated_boxes

    def get_active_boxes_count(self) -> int:
        """Получает количество активных наборов для админки"""
        return self.box_repo.get_active_boxes_count() 