import httpx
import hashlib
from datetime import datetime
from typing import Dict, Optional
from core.config import settings


class ClickMerchantService:
    """HTTP клиент для работы с Click Merchant API"""

    def __init__(self):
        self.base_url = "https://api.click.uz/v2/merchant"
        self.merchant_id = settings.CLICK_MERCHANT_ID
        self.service_id = settings.CLICK_SERVICE_ID
        self.secret_key = settings.CLICK_SECRET_KEY
        self.merchant_user_id = settings.CLICK_MERCHANT_USER_ID

    def _generate_auth_header(self) -> str:
        """Генерирует Auth заголовок согласно Click API документации"""
        timestamp = str(int(datetime.now().timestamp()))
        digest = hashlib.sha1(f"{timestamp}{self.secret_key}".encode()).hexdigest()
        return f"{self.merchant_user_id}:{digest}:{timestamp}"

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Универсальный метод для запросов к Click API"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Auth": self._generate_auth_header()
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                response = await client.get(url, headers=headers)

            if not response.is_success:
                raise Exception(f"Click API error: {response.status_code} - {response.text}")

            return response.json()

    async def create_card_token(self, card_number: str, expire_date: str) -> Dict:
        """Создать токен карты"""
        data = {
            "service_id": self.service_id,
            "card_number": card_number,
            "expire_date": expire_date,
            "temporary": 0  # всегда 0 для гибкости платежей
        }
        return await self._make_request("POST", "/card_token/request", data)

    async def verify_card_token(self, card_token: str, sms_code: str) -> Dict:
        """Верифицировать токен карты SMS кодом"""
        data = {
            "service_id": self.service_id,
            "card_token": card_token,
            "sms_code": sms_code
        }
        return await self._make_request("POST", "/card_token/verify", data)

    async def payment_with_token(self, card_token: str, amount: int, merchant_trans_id: str) -> Dict:
        """Оплата по токену карты"""
        data = {
            "service_id": int(self.service_id),
            "card_token": card_token,
            "amount": str(amount),
            "transaction_parameter": merchant_trans_id
        }
        return await self._make_request("POST", "/card_token/payment", data)

    async def delete_card_token(self, card_token: str) -> Dict:
        """Удалить токен карты"""
        endpoint = f"/card_token/{self.service_id}/{card_token}"
        return await self._make_request("DELETE", endpoint)
