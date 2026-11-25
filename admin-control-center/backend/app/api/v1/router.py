from fastapi import APIRouter

from app.api.v1 import auth, commercial, dashboard, operations, users

admin_router = APIRouter()
admin_router.include_router(auth.router)
admin_router.include_router(dashboard.router)
admin_router.include_router(users.router)
admin_router.include_router(commercial.router)
admin_router.include_router(operations.router)
