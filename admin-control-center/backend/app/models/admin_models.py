from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AdminBase, AdminTimestampMixin, AdminUUIDMixin, utcnow


class AdminAccount(AdminBase, AdminUUIDMixin, AdminTimestampMixin):
    __tablename__ = "admin_accounts"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_role: Mapped[str] = mapped_column(
        String(32), default="ops_admin", nullable=False
    )  # superadmin | ops_admin | support | finance
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminCourtesyGrant(AdminBase, AdminUUIDMixin, AdminTimestampMixin):
    __tablename__ = "admin_courtesy_grants"

    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    plan_code: Mapped[str] = mapped_column(String(32), nullable=False)  # pro | premium
    duration_type: Mapped[str] = mapped_column(
        String(24), nullable=False
    )  # 7d | 15d | 30d | 90d | custom | indefinite
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(24), default="active", nullable=False
    )  # active | revoked | expired
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    granted_by_admin_id: Mapped[str] = mapped_column(String(36), nullable=False)
    revoked_by_admin_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminCreditGrant(AdminBase, AdminUUIDMixin, AdminTimestampMixin):
    __tablename__ = "admin_credit_grants"

    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    metric_key: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # job_analysis | custom_resume | prepared_application
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    granted_by_admin_id: Mapped[str] = mapped_column(String(36), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminUserOverride(AdminBase, AdminUUIDMixin, AdminTimestampMixin):
    __tablename__ = "admin_user_overrides"

    user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    access_modality: Mapped[str] = mapped_column(
        String(32), default="unclassified", nullable=False
    )  # free | paid | courtesy | unclassified
    account_status: Mapped[str] = mapped_column(
        String(32), default="active", nullable=False
    )  # active | suspended | deactivated | deleted
    suspended_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_limits_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AdminCoupon(AdminBase, AdminUUIDMixin, AdminTimestampMixin):
    __tablename__ = "admin_coupons"

    code: Mapped[str] = mapped_column(String(48), unique=True, index=True, nullable=False)
    discount_type: Mapped[str] = mapped_column(String(16), nullable=False)  # percent | fixed
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    applicable_plan: Mapped[str] = mapped_column(String(32), default="all", nullable=False)
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_admin_id: Mapped[str] = mapped_column(String(36), nullable=False)


class AdminOperationalCost(AdminBase, AdminUUIDMixin, AdminTimestampMixin):
    __tablename__ = "admin_operational_costs"

    category: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    monthly_cost_brl_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AdminSupportTicket(AdminBase, AdminUUIDMixin, AdminTimestampMixin):
    __tablename__ = "admin_support_tickets"

    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    priority: Mapped[str] = mapped_column(String(24), default="media", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="aberto", nullable=False
    )  # aberto | em_atendimento | aguardando_usuario | resolvido | encerrado
    assigned_admin_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    messages_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AdminCommunication(AdminBase, AdminUUIDMixin, AdminTimestampMixin):
    __tablename__ = "admin_communications"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(24), default="transacional", nullable=False)
    target_plan: Mapped[str] = mapped_column(String(32), default="all", nullable=False)
    target_status: Mapped[str] = mapped_column(String(32), default="all", nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="rascunho", nullable=False)
    sent_by_admin_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminPromptVersion(AdminBase, AdminUUIDMixin, AdminTimestampMixin):
    __tablename__ = "admin_prompt_versions"

    agent_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="rascunho", nullable=False
    )  # rascunho | publicado | arquivado
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_admin_id: Mapped[str] = mapped_column(String(36), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminSetting(AdminBase):
    __tablename__ = "admin_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    updated_by_admin_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class AdminAuditLog(AdminBase, AdminUUIDMixin):
    __tablename__ = "admin_audit_logs"

    actor_admin_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[str] = mapped_column(String(32), default="success", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
