import csv
import io
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin_roles
from app.core.config import get_admin_settings
from app.core.database import get_db
from app.models.admin_models import (
    AdminAccount,
    AdminAuditLog,
    AdminCourtesyGrant,
    AdminCreditGrant,
    AdminUserOverride,
)
from app.models.shared import (
    SharedApplication,
    SharedAuditLog,
    SharedBillingEvent,
    SharedFavoriteCompany,
    SharedPlan,
    SharedPlanFeature,
    SharedResume,
    SharedResumeVersion,
    SharedSubscription,
    SharedTargetRole,
    SharedUsageEvent,
    SharedUser,
    SharedUserProfile,
)
from app.services.audit import record_admin_audit

router = APIRouter(prefix="/users", tags=["Admin Users"])


class ManagePlanRequest(BaseModel):
    action: str = Field(
        pattern="^(change_plan|grant_courtesy|revoke_courtesy|grant_credits|set_custom_limits)$"
    )
    plan_code: Optional[str] = Field(default=None, pattern="^(free|pro|premium)$")
    access_modality: Optional[str] = Field(
        default=None, pattern="^(free|paid|courtesy|unclassified)$"
    )
    duration_type: Optional[str] = Field(
        default=None, pattern="^(7d|15d|30d|90d|custom|indefinite)$"
    )
    custom_days: Optional[int] = Field(default=None, ge=1, le=3650)
    credit_metric: Optional[str] = Field(
        default=None, pattern="^(job_analysis|custom_resume|prepared_application)$"
    )
    credit_amount: Optional[int] = Field(default=None, ge=1, le=10000)
    custom_limits: Optional[Dict[str, Optional[int]]] = None
    justification: str = Field(min_length=5, max_length=500)


class UserStatusRequest(BaseModel):
    action: str = Field(pattern="^(activate|suspend|deactivate)$")
    justification: str = Field(min_length=5, max_length=500)


class UserDeleteRequest(BaseModel):
    confirmation_text: str
    justification: str = Field(min_length=8, max_length=500)


def _csv_safe(val: Any) -> str:
    s = "" if val is None else str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def _resolve_user_summary(
    u: SharedUser,
    plans_by_id: Dict[str, SharedPlan],
    sub: Optional[SharedSubscription],
    ov: Optional[AdminUserOverride],
    courtesy: Optional[AdminCourtesyGrant],
    has_payment: bool,
) -> Dict[str, Any]:
    plan_code = "free"
    plan_name = "Free"
    price_cents = 0
    if courtesy and courtesy.status == "active":
        plan_code = courtesy.plan_code
        matched = next((p for p in plans_by_id.values() if p.code == plan_code), None)
        plan_name = matched.name if matched else plan_code.title()
        price_cents = 0
    elif sub and sub.plan_id in plans_by_id:
        p = plans_by_id[sub.plan_id]
        plan_code = p.code
        plan_name = p.name
        price_cents = p.price_brl_cents

    if courtesy and courtesy.status == "active":
        modality = "courtesy"
    elif ov and ov.access_modality:
        modality = ov.access_modality
    elif plan_code == "free":
        modality = "free"
    elif has_payment:
        modality = "paid"
    else:
        modality = "unclassified"

    acc_status = ov.account_status if ov else ("active" if u.is_active else "suspended")
    return {
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "account_status": acc_status,
        "plan_code": plan_code,
        "plan_name": plan_name,
        "plan_price_brl_cents": price_cents if modality == "paid" else 0,
        "access_modality": modality,
        "subscription_status": sub.status if sub else "none",
        "subscription_start": sub.created_at.isoformat() if sub else None,
        "next_renewal": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
        "courtesy_expires_at": courtesy.expires_at.isoformat() if courtesy and courtesy.expires_at else None,
        "created_at": u.created_at.isoformat(),
        "onboarding_completed": u.onboarding_completed,
    }


@router.get("")
def list_users(
    q: str = Query(default="", max_length=120),
    plan: str = Query(default="all"),
    status_filter: str = Query(default="all"),
    modality: str = Query(default="all"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "support", "finance")),
    db: Session = Depends(get_db),
):
    plans_by_id = {p.id: p for p in db.query(SharedPlan).all()}
    query = db.query(SharedUser)
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            (SharedUser.full_name.ilike(term))
            | (SharedUser.email.ilike(term))
            | (SharedUser.id.ilike(term))
        )
    all_users = query.order_by(SharedUser.created_at.desc()).all()

    subs = (
        db.query(SharedSubscription)
        .filter(SharedSubscription.status == "active")
        .order_by(SharedSubscription.created_at.desc())
        .all()
    )
    sub_by_user = {}
    for s in subs:
        if s.user_id not in sub_by_user:
            sub_by_user[s.user_id] = s

    overrides = {o.user_id: o for o in db.query(AdminUserOverride).all()}
    courtesies = {
        c.user_id: c
        for c in db.query(AdminCourtesyGrant).filter(AdminCourtesyGrant.status == "active").all()
    }
    paid_user_ids = {
        b.user_id
        for b in db.query(SharedBillingEvent).all()
        if b.user_id and any(k in b.event_type.lower() for k in ("paid", "succeeded", "confirmed"))
    }

    rows: List[Dict[str, Any]] = []
    for u in all_users:
        item = _resolve_user_summary(
            u,
            plans_by_id,
            sub_by_user.get(u.id),
            overrides.get(u.id),
            courtesies.get(u.id),
            u.id in paid_user_ids,
        )
        if plan != "all" and item["plan_code"] != plan:
            continue
        if status_filter != "all" and item["account_status"] != status_filter:
            continue
        if modality != "all" and item["access_modality"] != modality:
            continue
        rows.append(item)

    total = len(rows)
    start = (page - 1) * page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": rows[start : start + page_size],
    }


@router.get("/export-csv")
def export_users_csv(
    justification: str = Query(..., min_length=5, max_length=300),
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "finance")),
    db: Session = Depends(get_db),
):
    data = list_users(page=1, page_size=100, _admin=actor, db=db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "nome", "email", "plano", "modalidade", "status_conta", "cadastro"])
    for r in data["items"]:
        writer.writerow([
            _csv_safe(r["id"]),
            _csv_safe(r["full_name"]),
            _csv_safe(r["email"]),
            _csv_safe(r["plan_code"]),
            _csv_safe(r["access_modality"]),
            _csv_safe(r["account_status"]),
            _csv_safe(r["created_at"]),
        ])
    record_admin_audit(
        db,
        actor=actor,
        action="users.export_csv",
        resource_type="user_list",
        justification=justification,
        metadata={"exported_rows": len(data["items"])},
    )
    db.commit()
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=usuarios_career_hunter.csv"},
    )


@router.get("/{user_id}")
def get_user_detail(
    user_id: str,
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "support", "finance")),
    db: Session = Depends(get_db),
):
    u = db.query(SharedUser).filter(SharedUser.id == user_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    plans_by_id = {p.id: p for p in db.query(SharedPlan).all()}
    sub = (
        db.query(SharedSubscription)
        .filter(SharedSubscription.user_id == u.id, SharedSubscription.status == "active")
        .order_by(SharedSubscription.created_at.desc())
        .first()
    )
    ov = db.query(AdminUserOverride).filter(AdminUserOverride.user_id == u.id).first()
    courtesy = (
        db.query(AdminCourtesyGrant)
        .filter(AdminCourtesyGrant.user_id == u.id, AdminCourtesyGrant.status == "active")
        .order_by(AdminCourtesyGrant.created_at.desc())
        .first()
    )
    has_payment = (
        db.query(SharedBillingEvent)
        .filter(SharedBillingEvent.user_id == u.id)
        .count()
        > 0
    )
    summary = _resolve_user_summary(u, plans_by_id, sub, ov, courtesy, has_payment)

    profile = db.query(SharedUserProfile).filter(SharedUserProfile.user_id == u.id).first()
    roles = db.query(SharedTargetRole).filter(SharedTargetRole.user_id == u.id).all()
    fav_count = db.query(SharedFavoriteCompany).filter(SharedFavoriteCompany.user_id == u.id).count()
    resumes = (
        db.query(SharedResume)
        .filter(SharedResume.user_id == u.id)
        .order_by(SharedResume.created_at.desc())
        .all()
    )
    resume_versions = (
        db.query(SharedResumeVersion)
        .filter(SharedResumeVersion.user_id == u.id)
        .order_by(SharedResumeVersion.created_at.desc())
        .all()
    )
    apps_count = db.query(SharedApplication).filter(SharedApplication.user_id == u.id).count()

    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    analyses_used = (
        db.query(func.coalesce(func.sum(SharedUsageEvent.quantity), 0))
        .filter(
            SharedUsageEvent.user_id == u.id,
            SharedUsageEvent.metric_key == "job_analysis",
            SharedUsageEvent.created_at >= month_start,
        )
        .scalar()
        or 0
    )

    plan_obj = next((p for p in plans_by_id.values() if p.code == summary["plan_code"]), None)
    feat_map: Dict[str, Optional[int]] = {}
    if plan_obj:
        for f in db.query(SharedPlanFeature).filter(SharedPlanFeature.plan_id == plan_obj.id).all():
            feat_map[f.feature_key] = f.limit_value
    if ov and ov.custom_limits_json:
        feat_map.update(ov.custom_limits_json)

    credits = db.query(AdminCreditGrant).filter(AdminCreditGrant.user_id == u.id).all()
    extra_analyses = sum(c.remaining for c in credits if c.metric_key == "job_analysis")

    user_audits = (
        db.query(SharedAuditLog)
        .filter(SharedAuditLog.user_id == u.id)
        .order_by(SharedAuditLog.created_at.desc())
        .limit(20)
        .all()
    )
    admin_audits = (
        db.query(AdminAuditLog)
        .filter(AdminAuditLog.resource_id == u.id)
        .order_by(AdminAuditLog.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        **summary,
        "profile": {
            "headline": profile.headline if profile else None,
            "city": profile.city if profile else None,
            "state": profile.state if profile else None,
            "phone": profile.phone if profile else None,
            "seniority_level": profile.seniority_level if profile else None,
            "target_roles": [r.title for r in roles if r.status == "ativo"],
            "favorite_companies_count": fav_count,
        },
        "documents": {
            "originals": [
                {
                    "id": r.id,
                    "name": r.original_filename,
                    "format": r.file_format,
                    "parse_status": r.parse_status,
                    "is_primary": r.is_primary,
                    "created_at": r.created_at.isoformat(),
                }
                for r in resumes
            ],
            "ats_versions": [
                {
                    "id": rv.id,
                    "label": rv.version_label,
                    "approved_by_user": rv.approved_by_user,
                    "has_pdf": bool(rv.pdf_path),
                    "has_docx": bool(rv.docx_path),
                    "created_at": rv.created_at.isoformat(),
                }
                for rv in resume_versions
            ],
        },
        "usage": {
            "analyses_used": int(analyses_used),
            "analyses_limit": (feat_map.get("monthly_analyses") or 5) + extra_analyses,
            "extra_analysis_credits": extra_analyses,
            "custom_resumes_used": len(resume_versions),
            "custom_resumes_limit": feat_map.get("custom_resumes") or 0,
            "applications_used": apps_count,
            "applications_limit": feat_map.get("prepared_applications") or 0,
            "custom_limits": ov.custom_limits_json if ov else {},
        },
        "courtesy": (
            {
                "id": courtesy.id,
                "plan_code": courtesy.plan_code,
                "duration_type": courtesy.duration_type,
                "starts_at": courtesy.starts_at.isoformat(),
                "expires_at": courtesy.expires_at.isoformat() if courtesy.expires_at else None,
                "reason": courtesy.reason,
            }
            if courtesy
            else None
        ),
        "history": [
            {
                "source": "admin",
                "action": a.action,
                "justification": a.justification,
                "actor": a.actor_email,
                "created_at": a.created_at.isoformat(),
            }
            for a in admin_audits
        ]
        + [
            {
                "source": "app",
                "action": a.action,
                "justification": None,
                "actor": u.email,
                "created_at": a.created_at.isoformat(),
            }
            for a in user_audits
        ],
    }


@router.get("/{user_id}/documents/{doc_kind}/{doc_id}")
def download_private_user_document(
    user_id: str,
    doc_kind: str,
    doc_id: str,
    justification: str = Query(..., min_length=5, max_length=300),
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin")),
    db: Session = Depends(get_db),
):
    file_path: Optional[Path] = None
    download_name = "documento"

    if doc_kind == "original":
        row = (
            db.query(SharedResume)
            .filter(SharedResume.id == doc_id, SharedResume.user_id == user_id)
            .first()
        )
        if row:
            file_path = Path(row.storage_path)
            download_name = row.original_filename
    elif doc_kind in ("ats_pdf", "ats_docx"):
        rv = (
            db.query(SharedResumeVersion)
            .filter(SharedResumeVersion.id == doc_id, SharedResumeVersion.user_id == user_id)
            .first()
        )
        if rv:
            raw = rv.pdf_path if doc_kind == "ats_pdf" else rv.docx_path
            if raw:
                file_path = Path(raw)
                download_name = file_path.name
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de documento inválido.")

    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    if not file_path.is_absolute():
        cfg = get_admin_settings()
        candidate = (cfg.uploads_base_path.parent / file_path).resolve()
        if candidate.exists():
            file_path = candidate

    record_admin_audit(
        db,
        actor=actor,
        action="document.private_access",
        resource_type=doc_kind,
        resource_id=doc_id,
        justification=justification,
        metadata={"target_user_id": user_id},
    )
    db.commit()

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico indisponível no armazenamento local.",
        )

    return FileResponse(path=str(file_path), filename=download_name)


@router.post("/{user_id}/manage-plan")
def manage_user_plan(
    user_id: str,
    payload: ManagePlanRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "finance")),
    db: Session = Depends(get_db),
):
    u = db.query(SharedUser).filter(SharedUser.id == user_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    ov = db.query(AdminUserOverride).filter(AdminUserOverride.user_id == u.id).first()
    if not ov:
        ov = AdminUserOverride(user_id=u.id)
        db.add(ov)
        db.flush()

    if payload.action == "change_plan":
        if not payload.plan_code:
            raise HTTPException(status_code=400, detail="Informe o plano de destino.")
        plan_obj = db.query(SharedPlan).filter(SharedPlan.code == payload.plan_code).first()
        if not plan_obj:
            raise HTTPException(status_code=404, detail="Plano não encontrado.")

        sub = (
            db.query(SharedSubscription)
            .filter(SharedSubscription.user_id == u.id, SharedSubscription.status == "active")
            .first()
        )
        if not sub:
            sub = SharedSubscription(
                id=str(uuid.uuid4()),
                user_id=u.id,
                plan_id=plan_obj.id,
                status="active",
            )
            db.add(sub)
        else:
            sub.plan_id = plan_obj.id

        if payload.access_modality:
            ov.access_modality = payload.access_modality
        elif payload.plan_code == "free":
            ov.access_modality = "free"

    elif payload.action == "grant_courtesy":
        if not payload.plan_code or payload.plan_code == "free":
            raise HTTPException(status_code=400, detail="Cortesia deve ser para Pro ou Premium.")
        dur = payload.duration_type or "30d"
        now = datetime.now(timezone.utc)
        days_map = {"7d": 7, "15d": 15, "30d": 30, "90d": 90, "custom": payload.custom_days or 30}
        expires_at = None if dur == "indefinite" else now + timedelta(days=days_map[dur])

        # Revoke prior active courtesies
        for old_c in (
            db.query(AdminCourtesyGrant)
            .filter(AdminCourtesyGrant.user_id == u.id, AdminCourtesyGrant.status == "active")
            .all()
        ):
            old_c.status = "revoked"
            old_c.revoked_by_admin_id = actor.id
            old_c.revoked_at = now

        db.add(
            AdminCourtesyGrant(
                user_id=u.id,
                plan_code=payload.plan_code,
                duration_type=dur,
                starts_at=now,
                expires_at=expires_at,
                status="active",
                reason=payload.justification,
                granted_by_admin_id=actor.id,
            )
        )
        plan_obj = db.query(SharedPlan).filter(SharedPlan.code == payload.plan_code).first()
        if plan_obj:
            sub = (
                db.query(SharedSubscription)
                .filter(SharedSubscription.user_id == u.id, SharedSubscription.status == "active")
                .first()
            )
            if not sub:
                db.add(
                    SharedSubscription(
                        id=str(uuid.uuid4()),
                        user_id=u.id,
                        plan_id=plan_obj.id,
                        status="active",
                        current_period_end=expires_at,
                    )
                )
            else:
                sub.plan_id = plan_obj.id
                sub.current_period_end = expires_at
        ov.access_modality = "courtesy"

    elif payload.action == "revoke_courtesy":
        now = datetime.now(timezone.utc)
        for old_c in (
            db.query(AdminCourtesyGrant)
            .filter(AdminCourtesyGrant.user_id == u.id, AdminCourtesyGrant.status == "active")
            .all()
        ):
            old_c.status = "revoked"
            old_c.revoked_by_admin_id = actor.id
            old_c.revoked_at = now
        free_plan = db.query(SharedPlan).filter(SharedPlan.code == "free").first()
        if free_plan:
            sub = (
                db.query(SharedSubscription)
                .filter(SharedSubscription.user_id == u.id, SharedSubscription.status == "active")
                .first()
            )
            if sub:
                sub.plan_id = free_plan.id
                sub.current_period_end = None
        ov.access_modality = "free"

    elif payload.action == "grant_credits":
        if not payload.credit_metric or not payload.credit_amount:
            raise HTTPException(status_code=400, detail="Informe métrica e quantidade de créditos.")
        db.add(
            AdminCreditGrant(
                user_id=u.id,
                metric_key=payload.credit_metric,
                amount=payload.credit_amount,
                remaining=payload.credit_amount,
                reason=payload.justification,
                granted_by_admin_id=actor.id,
            )
        )

    elif payload.action == "set_custom_limits":
        ov.custom_limits_json = payload.custom_limits or {}

    record_admin_audit(
        db,
        actor=actor,
        action=f"user.plan.{payload.action}",
        resource_type="user",
        resource_id=u.id,
        justification=payload.justification,
        metadata=payload.model_dump(exclude={"justification"}),
    )
    db.commit()
    return {"status": "ok", "action": payload.action}


@router.post("/{user_id}/status")
def update_user_account_status(
    user_id: str,
    payload: UserStatusRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin")),
    db: Session = Depends(get_db),
):
    u = db.query(SharedUser).filter(SharedUser.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    ov = db.query(AdminUserOverride).filter(AdminUserOverride.user_id == u.id).first()
    if not ov:
        ov = AdminUserOverride(user_id=u.id)
        db.add(ov)

    if payload.action == "activate":
        u.is_active = True
        ov.account_status = "active"
        ov.suspended_reason = None
    elif payload.action == "suspend":
        u.is_active = False
        ov.account_status = "suspended"
        ov.suspended_reason = payload.justification
    elif payload.action == "deactivate":
        u.is_active = False
        ov.account_status = "deactivated"
        ov.suspended_reason = payload.justification

    record_admin_audit(
        db,
        actor=actor,
        action=f"user.status.{payload.action}",
        resource_type="user",
        resource_id=u.id,
        justification=payload.justification,
    )
    db.commit()
    return {"id": u.id, "is_active": u.is_active, "account_status": ov.account_status}


@router.delete("/{user_id}")
def lgpd_delete_user(
    user_id: str,
    payload: UserDeleteRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin")),
    db: Session = Depends(get_db),
):
    if payload.confirmation_text.strip() != "EXCLUIR DEFINITIVAMENTE":
        raise HTTPException(
            status_code=400,
            detail="Confirmação explícita inválida. Digite: EXCLUIR DEFINITIVAMENTE",
        )
    u = db.query(SharedUser).filter(SharedUser.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Anonymize user identity and delete private documents while keeping audit trail
    anon_suffix = u.id[:8]
    u.email = f"deleted_{anon_suffix}@anonymized.local"
    u.full_name = f"Usuário Excluído ({anon_suffix})"
    u.is_active = False

    db.query(SharedResumeVersion).filter(SharedResumeVersion.user_id == u.id).delete()
    db.query(SharedResume).filter(SharedResume.user_id == u.id).delete()
    db.query(SharedTargetRole).filter(SharedTargetRole.user_id == u.id).delete()
    db.query(SharedFavoriteCompany).filter(SharedFavoriteCompany.user_id == u.id).delete()

    ov = db.query(AdminUserOverride).filter(AdminUserOverride.user_id == u.id).first()
    if not ov:
        ov = AdminUserOverride(user_id=u.id)
        db.add(ov)
    ov.account_status = "deleted"
    ov.suspended_reason = payload.justification

    record_admin_audit(
        db,
        actor=actor,
        action="user.lgpd_deleted",
        resource_type="user",
        resource_id=u.id,
        justification=payload.justification,
    )
    db.commit()
    return {"status": "deleted", "user_id": u.id}
