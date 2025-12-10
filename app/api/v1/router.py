"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.cart import router as cart_router
from app.api.v1.catalog import router as catalog_router
from app.api.v1.farmers import router as farmers_router
from app.api.v1.health import router as health_router
from app.api.v1.products import router as products_router
from app.api.v1.users import router as users_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(farmers_router)
api_router.include_router(products_router)
api_router.include_router(catalog_router)
api_router.include_router(cart_router)
api_router.include_router(admin_router)
