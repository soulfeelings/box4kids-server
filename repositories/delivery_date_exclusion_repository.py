from datetime import date as date_type
from typing import List

from sqlalchemy.orm import Session

from models.delivery_date_exclusion import DeliveryDateExclusion


class DeliveryDateExclusionRepository:
    """Repo for delivery date exclusions."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[DeliveryDateExclusion]:
        return self.db.query(DeliveryDateExclusion).order_by(DeliveryDateExclusion.date.asc()).all()

    def add(self, date_value: date_type) -> DeliveryDateExclusion:
        exclusion = DeliveryDateExclusion(date=date_value)
        self.db.add(exclusion)
        self.db.flush()
        self.db.refresh(exclusion)
        return exclusion

    def remove(self, date_value: date_type) -> bool:
        exclusion = (
            self.db.query(DeliveryDateExclusion)
            .filter(DeliveryDateExclusion.date == date_value)
            .first()
        )
        if not exclusion:
            return False
        self.db.delete(exclusion)
        self.db.flush()
        return True

    def exists(self, date_value: date_type) -> bool:
        return (
            self.db.query(DeliveryDateExclusion)
            .filter(DeliveryDateExclusion.date == date_value)
            .first()
            is not None
        )
