from typing import List
from sqlalchemy.orm import Session
from models.allowed_delivery_time import AllowedDeliveryTime


class AllowedDeliveryTimeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> List[AllowedDeliveryTime]:
        return (
            self.db.query(AllowedDeliveryTime)
            .order_by(AllowedDeliveryTime.time.asc())
            .all()
        )

    def add(self, time_value: str) -> AllowedDeliveryTime:
        existing = (
            self.db.query(AllowedDeliveryTime)
            .filter(AllowedDeliveryTime.time == time_value)
            .first()
        )
        if existing:
            return existing
        entity = AllowedDeliveryTime(time=time_value)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def remove(self, time_value: str) -> bool:
        entity = (
            self.db.query(AllowedDeliveryTime)
            .filter(AllowedDeliveryTime.time == time_value)
            .first()
        )
        if not entity:
            return False
        self.db.delete(entity)
        return True


