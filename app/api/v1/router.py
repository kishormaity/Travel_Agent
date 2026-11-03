from fastapi import APIRouter
from app.api.v1.endpoints import chat, trips, health

api_v1_router = APIRouter(prefix="/api/v1")

# Mount endpoints
api_v1_router.include_router(chat.router)
api_v1_router.include_router(trips.router)
api_v1_router.include_router(health.router)

__all__ = ["api_v1_router"]

