from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)  # user | admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    onboarding_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    preferences: Mapped[Optional["CareerPreference"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    country: Mapped[str] = mapped_column(String(80), default="Brasil", nullable=False)
    seniority_level: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    education_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    certifications_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    languages_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    projects_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    sectors_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    user: Mapped["User"] = relationship(back_populates="profile")


class EvidenceSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks origin and documentary evidence for Verified Professional Profile items."""
    __tablename__ = "evidence_sources"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # resume_upload | user_input | certification_doc
    source_ref_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    source_label: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ProfessionalExperience(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "professional_experiences"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_period_text: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proven_results: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    leadership_experience: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    # Verified Professional Profile metadata
    origin: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)  # resume_pdf | resume_docx | manual
    evidence_source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence_sources.id", ondelete="SET NULL"), nullable=True
    )
    evidence_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str] = mapped_column(
        String(32), default="pending_review", nullable=False
    )  # pending_review | verified | corrected | rejected
    ambiguity_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class VerifiedSkill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "verified_skills"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="technical", nullable=False)  # technical | behavioral | language | tool
    proficiency: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    years_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Verified Professional Profile metadata
    origin: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
    evidence_source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence_sources.id", ondelete="SET NULL"), nullable=True
    )
    evidence_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str] = mapped_column(
        String(32), default="pending_review", nullable=False
    )
    ambiguity_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class CareerPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "career_preferences"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    current_city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    current_state: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    desired_locations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    work_modalities: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # presencial | hibrido | remoto
    max_commute_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_commute_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    relocation_available: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    travel_available: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    min_salary_brl: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    desired_salary_brl: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_negotiable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contract_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # CLT | PJ | Estatutario | Temporario
    excluded_companies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    preferred_sectors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    professional_restrictions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    application_languages: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Etapa 6 — Configuração dos agentes (modo sempre supervisionado)
    search_frequency_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    monitoring_windows: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    max_recommended_jobs: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    min_match_score: Mapped[int] = mapped_column(Integer, default=65, nullable=False)
    eliminatory_criteria: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    notification_preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    prioritize_favorite_companies: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    application_mode: Mapped[str] = mapped_column(String(32), default="supervised", nullable=False)
    openai_api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="preferences")


class AuditLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    actor_role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    action: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
