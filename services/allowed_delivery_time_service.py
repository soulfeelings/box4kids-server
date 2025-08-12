from typing import List, Tuple
from sqlalchemy.orm import Session
from repositories.allowed_delivery_time_repository import AllowedDeliveryTimeRepository


class AllowedDeliveryTimeService:
    def __init__(self, db: Session) -> None:
        self.repo = AllowedDeliveryTimeRepository(db)

    def list_times(self) -> List[str]:
        return [row.time for row in self.repo.list_all()]

    def add_time(self, value: str) -> str:
        return self.repo.add(value).time

    def remove_time(self, value: str) -> bool:
        return self.repo.remove(value)


