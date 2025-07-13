from sqlalchemy.orm import Session, joinedload
from models.toy_box import ToyBox, ToyBoxItem, ToyBoxReview, ToyBoxStatus
from typing import List, Optional


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
            .options(joinedload(ToyBox.items))
            .filter(ToyBox.id == box_id)
            .first()
        )

    def get_current_box_by_child(self, child_id: int) -> Optional[ToyBox]:
        """Получить текущий набор ребёнка (последний созданный)"""
        return (
            self.db.query(ToyBox)
            .options(joinedload(ToyBox.items))
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