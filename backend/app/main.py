from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.models import Base

settings = get_settings()


def _ensure_sqlite_columns():
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(user_profiles)")).fetchall()]
        if cols and "contact_email" not in cols:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN contact_email VARCHAR(255)"))
        pref_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(career_preferences)")).fetchall()]
        if pref_cols and "salary_negotiable" not in pref_cols:
            conn.execute(text("ALTER TABLE career_preferences ADD COLUMN salary_negotiable BOOLEAN NOT NULL DEFAULT 0"))
        if pref_cols and "openai_api_key" not in pref_cols:
            conn.execute(text("ALTER TABLE career_preferences ADD COLUMN openai_api_key VARCHAR(255)"))
        role_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(target_roles)")).fetchall()]
        if role_cols and "min_salary_brl" not in role_cols:
            conn.execute(text("ALTER TABLE target_roles ADD COLUMN min_salary_brl INTEGER"))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API da plataforma SaaS Career Hunter AI",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Sistema"])
def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
