from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TargetRole(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "target_roles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    desired_seniority: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    area: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    priority: Mapped[str] = mapped_column(String(24), default="media", nullable=False)  # alta | media | baixa
    synonyms: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    desired_sectors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    min_salary_brl: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    desired_salary_brl: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    locations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    modalities: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    mandatory_criteria: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="ativo", nullable=False)  # ativo | pausado
    is_ai_suggested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Public company catalog entity (shared reference, no private user data)."""
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    official_website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    careers_page_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    country: Mapped[str] = mapped_column(String(80), default="Brasil", nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    career_sources: Mapped[list["CompanyCareerSource"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class FavoriteCompany(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Private user-company relationship ('Minhas Empresas')."""
    __tablename__ = "favorite_companies"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_favorite_company"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    priority: Mapped[str] = mapped_column(String(24), default="media", nullable=False)  # alta | media | baixa
    roles_of_interest: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    departments: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    monitoring_status: Mapped[str] = mapped_column(
        String(32), default="cadastrada", nullable=False
    )  # cadastrada | monitorada | erro_integracao | pausada

    company: Mapped["Company"] = relationship()


class CompanyCareerSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "company_career_sources"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(48), default="career_page", nullable=False)  # greenhouse | lever | jsonld | manual
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    monitorable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    integration_status: Mapped[str] = mapped_column(String(48), default="pending_check", nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="career_sources")
