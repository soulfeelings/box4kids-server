from typing import List
from datetime import date
from sqlalchemy.orm import Session
from models.allowed_delivery_date import AllowedDeliveryDate


class AllowedDeliveryDateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> List[AllowedDeliveryDate]:
        return (
            self.db.query(AllowedDeliveryDate)
            .order_by(AllowedDeliveryDate.date.asc())
            .all()
        )

    def add(self, target_date: date) -> AllowedDeliveryDate:
        existing = (
            self.db.query(AllowedDeliveryDate)
            .filter(AllowedDeliveryDate.date == target_date)
            .first()
        )
        if existing:
            return existing
        entity = AllowedDeliveryDate(date=target_date)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def remove(self, target_date: date) -> bool:
        entity = (
            self.db.query(AllowedDeliveryDate)
            .filter(AllowedDeliveryDate.date == target_date)
            .first()
        )
        if not entity:
            return False
        self.db.delete(entity)
        return True

