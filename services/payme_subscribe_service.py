import httpx
from datetime import datetime
from typing import Dict
from core.config import settings


class PaymeSubscribeService:
    """Клиент для работы с Payme Subscribe API"""

    def __init__(self):
        self.endpoint = settings.PAYME_SUBSCRIBE_API_URL
        self.merchant_id = settings.PAYME_MERCHANT_ID
        self.secret_key = settings.PAYME_SECRET_KEY

    async def _rpc_call(self, method: str, params: Dict) -> Dict:
        """Универсальный RPC вызов к Payme API"""
        body = {
            "jsonrpc": "2.0",
            "id": int(datetime.now().timestamp() * 1000),
            "method": method,
            "params": params
        }

        headers = {
            "Content-Type": "application/json",
            "X-Auth": f"{self.merchant_id}:{self.secret_key}"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.endpoint, headers=headers, json=body)

            if not response.is_success:
                raise Exception(f"Payme API error: {response.status_code} - {response.text}")

            data = response.json()
            if "error" in data:
                raise Exception(f"Payme {method} error: {data['error']['message']}")

            return data["result"]

    async def create_card(self, card_number: str, expire_date: str, cvc: str) -> Dict:
        """Создать токен карты"""
        params = {
            "card": {
                "number": card_number,
                "expire": expire_date,
                "cvc": cvc
            }
        }
        return await self._rpc_call("cards.create", params)

    async def get_verify_code(self, token: str) -> Dict:
        """Запросить SMS код для верификации"""
        params = {"token": token}
        return await self._rpc_call("cards.get_verify_code", params)

    async def verify_card(self, token: str, code: str) -> Dict:
        """Подтвердить карту SMS кодом"""
        params = {"token": token, "code": code}
        return await self._rpc_call("cards.verify", params)

    async def check_card(self, token: str) -> Dict:
        """Проверить статус карты"""
        params = {"token": token}
        return await self._rpc_call("cards.check", params)

    async def remove_card(self, token: str) -> Dict:
        """Удалить токен карты"""
        params = {"token": token}
        return await self._rpc_call("cards.remove", params)

    async def create_receipt(self, amount: int, account: Dict, description: str = "", detail: Dict = None) -> Dict:
        """Создать чек для списания"""
        params = {
            "amount": amount,
            "account": account,
            "description": description
        }
        if detail:
            params["detail"] = detail

        return await self._rpc_call("receipts.create", params)

    async def pay_receipt(self, receipt_id: str, token: str) -> Dict:
        """Списать деньги по чеку и токену карты"""
        params = {
            "id": receipt_id,
            "token": token
        }
        return await self._rpc_call("receipts.pay", params)

    async def check_receipt(self, receipt_id: str) -> Dict:
        """Проверить статус чека"""
        params = {"id": receipt_id}
        return await self._rpc_call("receipts.check", params)
