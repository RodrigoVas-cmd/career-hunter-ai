from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class CompanyMonitoringRun(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "company_monitoring_runs"

    career_source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("company_career_sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    jobs_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class JobSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_sources"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    source_kind: Mapped[str] = mapped_column(String(48), nullable=False)  # greenhouse | lever | jsonld | manual
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class JobPosting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Public normalized job posting (strictly separated from private candidate data)."""
    __tablename__ = "job_postings"

    job_source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("job_sources.id", ondelete="SET NULL"), index=True, nullable=True
    )
    company_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="SET NULL"), index=True, nullable=True
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(200), index=True, nullable=True)
    dedup_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    original_url: Mapped[str] = mapped_column(String(800), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    modality: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    seniority: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    salary_range_text: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    benefits_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    availability_status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class JobRequirement(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "job_requirements"

    job_posting_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_postings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    requirement_type: Mapped[str] = mapped_column(String(24), default="mandatory", nullable=False)  # mandatory | desirable | eliminatory
    text: Mapped[str] = mapped_column(Text, nullable=False)


class JobMatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_matches"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_posting_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_postings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    target_role_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True
    )
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String(48), nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dimension_scores_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    explanation_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
