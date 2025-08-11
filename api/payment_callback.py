from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.click_callback_service import ClickCallbackService
import logging

router = APIRouter(prefix="/payment/callback", tags=["Payment Callbacks"])


@router.post("/click")
async def click_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Обработать Click callback"""
    try:
        body = await request.json()
        service = ClickCallbackService(db)
        result = await service.handle_callback(body)
        return result
    except Exception as e:
        logging.error(f"Click callback error: {e}")
        return {
            "error": -8,
            "error_note": "System error"
        }


@router.post("/payme")
async def payme_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Обработать Payme callback"""
    try:
        body = await request.json()
        signature = request.headers.get("x-paycom-signature", "")

        # TODO: Реализовать PaymeCallbackService
        logging.info(f"Payme callback received: {body}")
        
        return {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {"allow": True}
        }
    except Exception as e:
        logging.error(f"Payme callback error: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32400,
                "message": "System error"
            }
        }
