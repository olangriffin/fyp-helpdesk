from fastapi import APIRouter

from app.api import admin, auth, public, tickets

api_router = APIRouter()
api_router.include_router(public.router)
api_router.include_router(auth.router)
api_router.include_router(tickets.router)
api_router.include_router(admin.router)

__all__ = ["api_router"]
