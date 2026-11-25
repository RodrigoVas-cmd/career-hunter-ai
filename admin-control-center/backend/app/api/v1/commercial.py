from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_admin_roles
from app.core.database import get_db
from app.models.admin_models import (
    AdminAccount,
    AdminCoupon,
    AdminCourtesyGrant,
    AdminOperationalCost,
    AdminUserOverride,
)
from app.models.shared import (
    SharedBillingEvent,
    SharedPlan,
    SharedPlanFeature,
    SharedSubscription,
    SharedUsageEvent,
    SharedUser,
)
from app.services.audit import record_admin_audit

router = APIRouter(prefix="/commercial", tags=["Admin Commercial & Financial"])


class PlanUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    price_brl_cents: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    features: Optional[Dict[str, Optional[int]]] = None
    justification: str = Field(min_length=5, max_length=500)


class CouponCreateRequest(BaseModel):
    code: str = Field(min_length=3, max_length=48)
    discount_type: str = Field(pattern="^(percent|fixed)$")
    discount_value: int = Field(ge=1)
    applicable_plan: str = Field(default="all", pattern="^(all|pro|premium)$")
    max_uses: Optional[int] = Field(default=None, ge=1)


class OperationalCostCreateRequest(BaseModel):
    category: str = Field(min_length=2, max_length=64)
    provider_name: str = Field(min_length=2, max_length=120)
    monthly_cost_brl_cents: int = Field(ge=0)
    notes: Optional[str] = None


@router.get("/plans")
def list_plans(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "finance")),
    db: Session = Depends(get_db),
):
    plans = db.query(SharedPlan).all()
    res = []
    for p in plans:
        feats = db.query(SharedPlanFeature).filter(SharedPlanFeature.plan_id == p.id).all()
        active_subs = (
            db.query(SharedSubscription)
            .filter(SharedSubscription.plan_id == p.id, SharedSubscription.status == "active")
            .count()
        )
        res.append({
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "price_brl_cents": p.price_brl_cents,
            "is_active": p.is_active,
            "active_subscribers_count": active_subs,
            "features": {f.feature_key: f.limit_value for f in feats},
        })
    return res


@router.patch("/plans/{plan_code}")
def update_plan_config(
    plan_code: str,
    payload: PlanUpdateRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "finance")),
    db: Session = Depends(get_db),
):
    plan = db.query(SharedPlan).filter(SharedPlan.code == plan_code).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")

    impacted_users = (
        db.query(SharedSubscription)
        .filter(SharedSubscription.plan_id == plan.id, SharedSubscription.status == "active")
        .count()
    )
    if payload.name is not None:
        plan.name = payload.name
    if payload.price_brl_cents is not None:
        plan.price_brl_cents = payload.price_brl_cents
    if payload.is_active is not None:
        plan.is_active = payload.is_active

    if payload.features:
        for fkey, val in payload.features.items():
            feat = (
                db.query(SharedPlanFeature)
                .filter(SharedPlanFeature.plan_id == plan.id, SharedPlanFeature.feature_key == fkey)
                .first()
            )
            if feat:
                feat.limit_value = val
            else:
                db.add(
                    SharedPlanFeature(
                        plan_id=plan.id,
                        feature_key=fkey,
                        limit_value=val,
                    )
                )

    record_admin_audit(
        db,
        actor=actor,
        action="commercial.plan_updated",
        resource_type="plan",
        resource_id=plan.code,
        justification=payload.justification,
        metadata={"impacted_active_subscriptions": impacted_users},
    )
    db.commit()
    return {"code": plan.code, "impacted_users": impacted_users}


@router.get("/subscriptions")
def list_subscriptions(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "finance")),
    db: Session = Depends(get_db),
):
    plans_by_id = {p.id: p for p in db.query(SharedPlan).all()}
    users_by_id = {u.id: u for u in db.query(SharedUser).all()}
    overrides = {o.user_id: o for o in db.query(AdminUserOverride).all()}
    courtesies = {
        c.user_id: c
        for c in db.query(AdminCourtesyGrant).filter(AdminCourtesyGrant.status == "active").all()
    }
    paid_user_ids = {b.user_id for b in db.query(SharedBillingEvent).all() if b.user_id}

    subs = db.query(SharedSubscription).order_by(SharedSubscription.created_at.desc()).all()
    items = []
    for s in subs:
        u = users_by_id.get(s.user_id)
        p = plans_by_id.get(s.plan_id)
        if not u or not p:
            continue
        ov = overrides.get(u.id)
        c = courtesies.get(u.id)
        modality = (
            "courtesy"
            if c
            else (ov.access_modality if ov else ("free" if p.code == "free" else ("paid" if u.id in paid_user_ids else "unclassified")))
        )
        items.append({
            "id": s.id,
            "user_id": u.id,
            "user_name": u.full_name,
            "user_email": u.email,
            "plan_code": p.code,
            "plan_name": p.name,
            "value_brl_cents": p.price_brl_cents if modality == "paid" else 0,
            "status": s.status,
            "access_modality": modality,
            "created_at": s.created_at.isoformat(),
            "current_period_end": s.current_period_end.isoformat() if s.current_period_end else None,
        })
    return {
        "has_payment_provider": len(paid_user_ids) > 0,
        "items": items,
    }


@router.get("/coupons")
def list_coupons(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "finance")),
    db: Session = Depends(get_db),
):
    return db.query(AdminCoupon).order_by(AdminCoupon.created_at.desc()).all()


@router.post("/coupons")
def create_coupon(
    payload: CouponCreateRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "finance")),
    db: Session = Depends(get_db),
):
    code = payload.code.upper().strip()
    if db.query(AdminCoupon).filter(AdminCoupon.code == code).first():
        raise HTTPException(status_code=409, detail="Cupom já existente.")
    c = AdminCoupon(
        code=code,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        applicable_plan=payload.applicable_plan,
        max_uses=payload.max_uses,
        created_by_admin_id=actor.id,
    )
    db.add(c)
    record_admin_audit(
        db,
        actor=actor,
        action="commercial.coupon_created",
        resource_type="coupon",
        resource_id=code,
    )
    db.commit()
    db.refresh(c)
    return c


@router.get("/courtesies")
def list_courtesies(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "finance")),
    db: Session = Depends(get_db),
):
    users = {u.id: u for u in db.query(SharedUser).all()}
    rows = db.query(AdminCourtesyGrant).order_by(AdminCourtesyGrant.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_name": users[r.user_id].full_name if r.user_id in users else r.user_id,
            "user_email": users[r.user_id].email if r.user_id in users else "",
            "plan_code": r.plan_code,
            "duration_type": r.duration_type,
            "status": r.status,
            "starts_at": r.starts_at.isoformat(),
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            "reason": r.reason,
        }
        for r in rows
    ]


@router.get("/profitability")
def get_profitability(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "finance")),
    db: Session = Depends(get_db),
):
    plans = db.query(SharedPlan).all()
    subs = db.query(SharedSubscription).filter(SharedSubscription.status == "active").all()
    overrides = {o.user_id: o for o in db.query(AdminUserOverride).all()}
    courtesies = {
        c.user_id: c
        for c in db.query(AdminCourtesyGrant).filter(AdminCourtesyGrant.status == "active").all()
    }
    paid_user_ids = {b.user_id for b in db.query(SharedBillingEvent).all() if b.user_id}
    usage_rows = db.query(SharedUsageEvent).all()
    cost_by_user: Dict[str, float] = {}
    for u_ev in usage_rows:
        cost_by_user[u_ev.user_id] = cost_by_user.get(u_ev.user_id, 0.0) + float(
            u_ev.estimated_cost_usd or 0.0
        )

    plan_breakdown = []
    for p in plans:
        plan_subs = [s for s in subs if s.plan_id == p.id]
        paying_count = 0
        courtesy_count = 0
        unclassified_count = 0
        ia_usd = 0.0
        for s in plan_subs:
            ia_usd += cost_by_user.get(s.user_id, 0.0)
            ov = overrides.get(s.user_id)
            if s.user_id in courtesies or (ov and ov.access_modality == "courtesy"):
                courtesy_count += 1
            elif p.code != "free" and (s.user_id in paid_user_ids or (ov and ov.access_modality == "paid")):
                paying_count += 1
            elif p.code != "free":
                unclassified_count += 1
        revenue_cents = paying_count * p.price_brl_cents
        plan_breakdown.append({
            "plan_code": p.code,
            "plan_name": p.name,
            "price_brl_cents": p.price_brl_cents,
            "paying_users": paying_count,
            "courtesy_users": courtesy_count,
            "unclassified_users": unclassified_count,
            "verified_revenue_brl_cents": revenue_cents,
            "ai_cost_usd": round(ia_usd, 4),
        })

    op_costs = db.query(AdminOperationalCost).filter(AdminOperationalCost.is_active.is_(True)).all()
    return {
        "plans": plan_breakdown,
        "operational_costs": op_costs,
        "total_operational_costs_brl_cents": sum(c.monthly_cost_brl_cents for c in op_costs),
        "note": "Receita considera apenas assinantes pagantes comprovados; cortesias e não classificados não são somados como receita.",
    }


@router.post("/operational-costs")
def add_operational_cost(
    payload: OperationalCostCreateRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "finance")),
    db: Session = Depends(get_db),
):
    row = AdminOperationalCost(**payload.model_dump(), is_active=True)
    db.add(row)
    record_admin_audit(
        db,
        actor=actor,
        action="commercial.operational_cost_added",
        resource_type="operational_cost",
        metadata=payload.model_dump(),
    )
    db.commit()
    db.refresh(row)
    return row
