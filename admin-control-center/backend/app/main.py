from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import admin_router
from app.core.config import get_admin_settings
from app.core.database import engine
from app.models.base import AdminBase

settings = get_admin_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Only create isolated admin_* tables; never overwrite or mutate main app tables
    AdminBase.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API administrativa independente do Career Hunter AI",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router, prefix="/api/v1/admin")


@app.get("/health", tags=["Sistema"])
def admin_health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
