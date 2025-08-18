import httpx
import json
import logging
from typing import List, Dict
from core.config import settings

logger = logging.getLogger(__name__)


class SMSPayload:
    """Данные для отправки SMS"""
    
    def __init__(self, phone: str, text: str):
        self.phone = phone
        self.text = text


class SMSGateway:
    """Сервис для отправки SMS через getsms.uz"""
    
    ENDPOINT = "https://getsms.uz/smsgateway/"
    
    @classmethod
    async def send_sms_batch(cls, data: List[SMSPayload]) -> Dict:
        """Отправляет пакет SMS сообщений"""
        if not settings.SMS_ENABLED:
            logger.info("[DEV MODE] SMS отправка отключена")
            return {"success": True, "dev_mode": True}
        
        if not all([settings.SMS_LOGIN, settings.SMS_PASSWORD]):
            logger.error("SMS Gateway: Отсутствуют учетные данные")
            raise Exception("SMS Gateway credentials not configured")
        
        payload_data = [{"phone": item.phone, "text": item.text} for item in data]
        
        form_data = {
            "login": settings.SMS_LOGIN,
            "password": settings.SMS_PASSWORD,
            "data": json.dumps(payload_data)
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    cls.ENDPOINT,
                    data=form_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if not response.is_success:
                    logger.error(f"SMS Gateway HTTP {response.status_code}. Response: {response.text[:500]}")
                    raise Exception(f"SMS gateway HTTP {response.status_code}")
                
                try:
                    json_response = response.json()
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from SMS gateway. Response: {response.text[:500]}")
                    raise Exception("Invalid JSON response from SMS gateway")
                
                # Проверка ошибок от шлюза
                if isinstance(json_response, list) and json_response and json_response[0].get("error"):
                    error = json_response[0].get("error_no", json_response[0].get("error"))
                    logger.error(f"SMS gateway error: {error}")
                    raise Exception(f"SMS gateway error: {error}")
                
                if isinstance(json_response, dict) and json_response.get("error"):
                    error = json_response.get("error_no", json_response.get("error"))
                    logger.error(f"SMS gateway error: {error}")
                    raise Exception(f"SMS gateway error: {error}")
                
                logger.info(f"SMS отправлена успешно на {len(data)} номеров")
                return json_response
                
        except httpx.TimeoutException:
            logger.error("SMS Gateway timeout")
            raise Exception("SMS gateway timeout")
        except Exception as e:
            logger.error(f"SMS Gateway error: {str(e)}")
            raise
    
    @classmethod
    async def send_single_sms(cls, phone: str, text: str) -> Dict:
        """Отправляет одно SMS сообщение"""
        return await cls.send_sms_batch([SMSPayload(phone, text)])
