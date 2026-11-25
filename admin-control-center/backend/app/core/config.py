from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    APP_NAME: str = "Career Hunter AI — Admin Control Center"
    APP_VERSION: str = "1.0.0"
    ADMIN_ENVIRONMENT: str = "development"
    ADMIN_DATABASE_URL: str = "sqlite:///../../backend/career_hunter.db"
    ADMIN_JWT_SECRET_KEY: str = "admin-dev-secret-change-in-production-48chars"
    ADMIN_JWT_ALGORITHM: str = "HS256"
    ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ADMIN_BOOTSTRAP_TOKEN: str = ""
    ADMIN_CORS_ORIGINS: str = "http://localhost:3001,http://127.0.0.1:3001"
    ADMIN_UPLOADS_BASE_DIR: str = "../../backend/uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ADMIN_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def uploads_base_path(self) -> Path:
        return Path(self.ADMIN_UPLOADS_BASE_DIR).resolve()


@lru_cache
def get_admin_settings() -> AdminSettings:
    return AdminSettings()
