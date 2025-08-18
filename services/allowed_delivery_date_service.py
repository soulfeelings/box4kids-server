from typing import List
from datetime import date
from sqlalchemy.orm import Session
from repositories.allowed_delivery_date_repository import AllowedDeliveryDateRepository


class AllowedDeliveryDateService:
    def __init__(self, db: Session) -> None:
        self.repo = AllowedDeliveryDateRepository(db)

    def list_dates(self) -> List[date]:
        return [row.date for row in self.repo.list_all()]

    def add_date(self, target_date: date) -> date:
        return self.repo.add(target_date).date

    def remove_date(self, target_date: date) -> bool:
        return self.repo.remove(target_date)

