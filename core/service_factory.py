from functools import lru_cache
from sqlalchemy.orm import Session
from ..repositories.user_repository import UserRepository
from ..repositories.child_repository import ChildRepository
from services.otp_service import OTPService
from services.payment_service import MockPaymentService
from ..use_cases.register_user_use_case import RegisterUserUseCase
from core.interfaces import IUserRepository, IChildRepository, IOTPService, IPaymentService


class ServiceFactory:
    """Фабрика для создания сервисов с внедрением зависимостей"""
    
    def __init__(self, db: Session):
        self._db = db
    
    @lru_cache()
    def get_user_repository(self) -> IUserRepository:
        return UserRepository(self._db)
    
    @lru_cache()
    def get_child_repository(self) -> IChildRepository:
        return ChildRepository(self._db)
    
    @lru_cache()
    def get_otp_service(self) -> IOTPService:
        return OTPService()
    
    @lru_cache()
    def get_payment_service(self) -> IPaymentService:
        return MockPaymentService(self._db)
    
    def get_register_user_use_case(self) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            user_repo=self.get_user_repository(),
            otp_service=self.get_otp_service()
        ) 