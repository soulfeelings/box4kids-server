import uuid
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict


class MockPaymentGateway:
    """Имитация внешнего платежного API (ЮKassa, Stripe, etc.)"""
    
    def __init__(self):
        self.base_url = "https://mock-payment.gateway.com"
    
    def create_payment(self, amount: float, currency: str = "RUB", 
                      return_url: str = None, notification_url: str = None) -> Dict:
        """Имитация создания платежа во внешнем API"""
        external_payment_id = f"PAY_{uuid.uuid4().hex[:12].upper()}"
        
        # Имитация ответа от реального API
        return {
            "id": external_payment_id,
            "status": "pending",
            "amount": amount,
            "currency": currency,
            "payment_url": f"{self.base_url}/pay/{external_payment_id}",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "return_url": return_url,
            "notification_url": notification_url
        }
    
    async def process_payment_async(self, external_payment_id: str, 
                                   simulate_delay: bool = True) -> Dict:
        """Асинхронная обработка платежа с реалистичной задержкой"""
        
        # Имитация времени обработки банком (5-15 секунд)
        if simulate_delay:
            delay = random.uniform(5, 15)
            await asyncio.sleep(delay)

            
        
        # Имитация результата (90% успех как в реальности)
        success = random.random() < 0.9
        print(f"Processing payment {external_payment_id} with status {success}")
        return {
            "id": external_payment_id,
            "status": "succeeded" if success else "failed",
            "processed_at": datetime.utcnow().isoformat()
        }
    
    def process_payment_sync(self, external_payment_id: str) -> Dict:
        """Синхронная обработка (для простых тестов)"""
        success = random.random() < 0.9
        
        return {
            "id": external_payment_id,
            "status": "succeeded" if success else "failed",
            "processed_at": datetime.utcnow().isoformat()
        }
    
    def simulate_user_return(self, external_payment_id: str, status: str = "success") -> Dict:
        """Имитация возврата пользователя с платежной страницы"""
        gateway_status = "succeeded" if status == "success" else "failed"
        
        return {
            "id": external_payment_id,
            "status": gateway_status,
            "return_url_visited": True,
            "user_action": status,
            "returned_at": datetime.utcnow().isoformat()
        }
    
    def simulate_webhook(self, external_payment_id: str, status: str) -> Dict:
        """Имитация webhook от платежного API"""
        return {
            "event": "payment.status.changed",
            "payment_id": external_payment_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "signature": f"mock_signature_{uuid.uuid4().hex[:8]}"
        }
    
    def get_payment_status(self, external_payment_id: str) -> Dict:
        """Имитация проверки статуса платежа"""
        # В реальности здесь был бы GET запрос к API
        statuses = ["pending", "succeeded", "failed", "refunded"]
        random_status = random.choice(statuses)
        
        return {
            "id": external_payment_id,
            "status": random_status,
            "checked_at": datetime.utcnow().isoformat()
        }
    
    def refund_payment(self, external_payment_id: str, amount: float = None) -> Dict:
        """Имитация возврата платежа"""
        refund_id = f"REF_{uuid.uuid4().hex[:12].upper()}"
        
        return {
            "id": refund_id,
            "payment_id": external_payment_id,
            "status": "succeeded",
            "amount": amount,
            "refunded_at": datetime.utcnow().isoformat()
        } 