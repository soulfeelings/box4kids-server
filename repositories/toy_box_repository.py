from sqlalchemy.orm import Session, joinedload
from models.toy_box import ToyBox, ToyBoxItem, ToyBoxReview, ToyBoxStatus
from models.child import Child
from typing import List, Optional
from datetime import date


class ToyBoxRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_box(self, box_data: dict) -> ToyBox:
        """Создать новый набор"""
        box = ToyBox(**box_data)
        self.db.add(box)
        self.db.flush()
        self.db.refresh(box)
        return box

    def get_by_id(self, box_id: int) -> Optional[ToyBox]:
        """Получить набор по ID с составом"""
        return (
            self.db.query(ToyBox)
            .options(joinedload(ToyBox.items), joinedload(ToyBox.reviews))
            .filter(ToyBox.id == box_id)
            .first()
        )

    def get_current_box_by_child(self, child_id: int) -> Optional[ToyBox]:
        """Получить текущий набор ребёнка (последний созданный)"""
        return (
            self.db.query(ToyBox)
            .options(joinedload(ToyBox.items), joinedload(ToyBox.reviews))
            .filter(ToyBox.child_id == child_id)
            .order_by(ToyBox.created_at.desc())
            .first()
        )

    def get_boxes_by_child(self, child_id: int, limit: Optional[int] = None) -> List[ToyBox]:
        """Получить все наборы ребёнка"""
        query = (
            self.db.query(ToyBox)
            .options(joinedload(ToyBox.items))
            .filter(ToyBox.child_id == child_id)
            .order_by(ToyBox.created_at.desc())
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_active_boxes_by_delivery_info_id(self, delivery_info_id: int, user_id: int) -> List[ToyBox]:
        """Получить активные наборы по ID адреса доставки для конкретного пользователя"""
        active_statuses = [ToyBoxStatus.PLANNED, ToyBoxStatus.ASSEMBLED, ToyBoxStatus.SHIPPED]
        return (
            self.db.query(ToyBox)
            .options(joinedload(ToyBox.items))
            .join(Child, ToyBox.child_id == Child.id)  # Присоединяем ребенка
            .filter(
                ToyBox.delivery_info_id == delivery_info_id,
                ToyBox.status.in_(active_statuses),
                Child.parent_id == user_id  # Проверяем что ребенок принадлежит пользователю
            )
            .order_by(ToyBox.created_at.desc())
            .all()
        )

    def update_delivery_date(self, box_id: int, delivery_date: date, return_date: date) -> Optional[ToyBox]:
        """Обновить дату доставки и возврата набора"""
        box = self.get_by_id(box_id)
        if box:
            box.delivery_date = delivery_date
            box.return_date = return_date
            self.db.flush()
            self.db.refresh(box)
        return box

    def update_delivery_time(self, box_id: int, delivery_time: str) -> Optional[ToyBox]:
        """Обновить время доставки и возврата набора"""
        box = self.get_by_id(box_id)
        if box:
            box.delivery_time = delivery_time
            box.return_time = delivery_time  # Используем то же время для возврата
            self.db.flush()
            self.db.refresh(box)
        return box

    def update_delivery_date_and_time(self, box_id: int, delivery_date: date, delivery_time: str, return_date: date) -> Optional[ToyBox]:
        """Обновить дату и время доставки и возврата набора"""
        box = self.get_by_id(box_id)
        if box:
            box.delivery_date = delivery_date
            box.delivery_time = delivery_time
            box.return_date = return_date
            box.return_time = delivery_time  # Используем то же время для возврата
            self.db.flush()
            self.db.refresh(box)
        return box

    def update_status(self, box_id: int, status: ToyBoxStatus) -> Optional[ToyBox]:
        """Обновить статус набора"""
        box = self.get_by_id(box_id)
        if box:
            box.status = status
            self.db.flush()
            self.db.refresh(box)
        return box

    def add_items(self, box_id: int, items_data: List[dict]) -> List[ToyBoxItem]:
        """Добавить состав в набор"""
        items = []
        for item_data in items_data:
            item = ToyBoxItem(box_id=box_id, **item_data)
            self.db.add(item)
            items.append(item)
        
        self.db.flush()
        for item in items:
            self.db.refresh(item)
        return items

    def add_review(self, review_data: dict) -> ToyBoxReview:
        """Добавить отзыв к набору"""
        review = ToyBoxReview(**review_data)
        self.db.add(review)
        self.db.flush()
        self.db.refresh(review)
        return review

    def get_reviews_by_box(self, box_id: int) -> List[ToyBoxReview]:
        """Получить все отзывы для набора"""
        return (
            self.db.query(ToyBoxReview)
            .filter(ToyBoxReview.box_id == box_id)
            .order_by(ToyBoxReview.created_at.desc())
            .all()
        ) 