from fastapi import APIRouter
from api.admin_routes.auth import router as auth_router
from api.admin_routes.users import router as users_router
from api.admin_routes.inventory import router as inventory_router
from api.admin_routes.mappings import router as mappings_router
from api.admin_routes.delivery_dates import router as delivery_dates_router

# Создаем главный роутер для админки
router = APIRouter()

# Включаем все подроутеры
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(inventory_router)
router.include_router(mappings_router)
router.include_router(delivery_dates_router)

