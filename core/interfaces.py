from typing import Protocol, Optional, List, Dict
from abc import ABC, abstractmethod
from models.user import User
from models.child import Child
from models.subscription import Subscription


class IUserRepository(Protocol):
    """Интерфейс репозитория пользователей"""
    
    def get_by_id(self, user_id: int) -> Optional[User]: ...
    def get_by_phone(self, phone: str) -> Optional[User]: ...
    def create(self, user: User) -> User: ...
    def update(self, user: User) -> User: ...
    def get_all(self) -> List[User]: ...


class IChildRepository(Protocol):
    """Интерфейс репозитория детей"""
    
    def create(self, child: Child) -> Child: ...
    def get_by_id(self, child_id: int) -> Optional[Child]: ...
    def get_by_parent_id(self, parent_id: int) -> List[Child]: ...
    def update(self, child: Child) -> Child: ...
    def delete(self, child_id: int) -> bool: ...


class ISubscriptionRepository(Protocol):
    """Интерфейс репозитория подписок"""
    
    def create(self, subscription: Subscription) -> Subscription: ...
    def get_by_user_id(self, user_id: int) -> List[Subscription]: ...
    def get_active_by_user_id(self, user_id: int) -> Optional[Subscription]: ...
    def deactivate_user_subscriptions(self, user_id: int) -> None: ...


class IOTPStorage(ABC):
    """Абстрактный класс хранилища OTP кодов"""
    
    @abstractmethod
    def store_code(self, phone: str, code: str) -> bool:
        """Сохраняет код для телефона"""
        pass
    
    @abstractmethod
    def get_code_data(self, phone: str) -> Optional[Dict]:
        """Получает данные кода для телефона"""
        pass
    
    @abstractmethod
    def increment_attempts(self, phone: str) -> int:
        """Увеличивает счетчик попыток"""
        pass
    
    @abstractmethod
    def delete_code(self, phone: str) -> bool:
        """Удаляет код для телефона"""
        pass


class IOTPService(Protocol):
    """Интерфейс OTP сервиса"""
    
    def send_code(self, phone: str) -> bool: ...
    def verify_code(self, phone: str, code: str) -> bool: ...


class IPaymentService(Protocol):
    """Интерфейс платежного сервиса"""
    
    def create_payment(self, user_id: int, subscription_id: int, amount: float) -> int: ...
    def process_payment(self, payment_id: int) -> bool: ...
    def get_payment_status(self, payment_id: int) -> Optional[str]: ... 