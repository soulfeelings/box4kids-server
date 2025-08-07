from datetime import date as date_type
from typing import List

from sqlalchemy.orm import Session

from repositories.delivery_date_exclusion_repository import DeliveryDateExclusionRepository


class DeliveryDateExclusionService:
    """Business logic for delivery date exclusions."""

    def __init__(self, db: Session):
        self._repo = DeliveryDateExclusionRepository(db)

    def list_exclusions(self) -> List[date_type]:
        return [item.date for item in self._repo.get_all()]

    def add_exclusion(self, date_value: date_type) -> None:
        if not self._repo.exists(date_value):
            self._repo.add(date_value)

    def remove_exclusion(self, date_value: date_type) -> bool:
        return self._repo.remove(date_value)

    def is_date_allowed(self, date_value: date_type) -> bool:
        """Return True if date is NOT excluded."""
        return not self._repo.exists(date_value)
