# Admin API routes 
from .auth import router as auth_router
from .users import router as users_router
from .inventory import router as inventory_router
from .mappings import router as mappings_router

__all__ = ["auth_router", "users_router", "inventory_router", "mappings_router"]