import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


class AdminBase(DeclarativeBase):
    """Isolated metadata for admin_* tables."""
    pass


class SharedBase(DeclarativeBase):
    """Read/write mappings for existing main-app tables (never create/drop in production)."""
    pass


class AdminTimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class AdminUUIDMixin:
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid
    )
