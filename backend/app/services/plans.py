from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.billing import Plan, PlanFeature, Subscription, UsageEvent
from app.models.user import User

PLAN_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "code": "free",
        "name": "Free",
        "price_brl_cents": 0,
        "features": {
            "target_roles": (1, "1 cargo-alvo ativo"),
            "favorite_companies": (2, "2 empresas preferidas"),
            "monthly_analyses": (5, "5 análises por mês"),
            "custom_resumes": (0, "Currículos personalizados sob upgrade"),
            "prepared_applications": (0, "Registro manual de candidaturas"),
        },
    },
    {
        "code": "pro",
        "name": "Pro",
        "price_brl_cents": 4990,
        "features": {
            "target_roles": (5, "5 cargos-alvo ativos"),
            "favorite_companies": (20, "20 empresas preferidas"),
            "monthly_analyses": (150, "150 análises por mês"),
            "custom_resumes": (30, "30 currículos personalizados"),
            "prepared_applications": (30, "30 candidaturas preparadas"),
        },
    },
    {
        "code": "premium",
        "name": "Premium",
        "price_brl_cents": 8990,
        "features": {
            "target_roles": (15, "15 cargos-alvo ativos"),
            "favorite_companies": (100, "100 empresas preferidas"),
            "monthly_analyses": (500, "500 análises por mês"),
            "custom_resumes": (100, "100 currículos personalizados"),
            "prepared_applications": (100, "100 candidaturas preparadas"),
        },
    },
]


def ensure_default_plans(db: Session) -> None:
    """Seeds or updates official plans and features (including Free = 5 monthly analyses)."""
    for item in PLAN_DEFINITIONS:
        plan = db.query(Plan).filter(Plan.code == item["code"]).first()
        if not plan:
            plan = Plan(
                code=item["code"],
                name=item["name"],
                price_brl_cents=item["price_brl_cents"],
                is_active=True,
            )
            db.add(plan)
            db.flush()
        else:
            plan.name = item["name"]
            plan.price_brl_cents = item["price_brl_cents"]
            plan.is_active = True

        for fkey, (limit_val, desc) in item["features"].items():
            feat = (
                db.query(PlanFeature)
                .filter(PlanFeature.plan_id == plan.id, PlanFeature.feature_key == fkey)
                .first()
            )
            if not feat:
                db.add(
                    PlanFeature(
                        plan_id=plan.id,
                        feature_key=fkey,
                        limit_value=limit_val,
                        description=desc,
                    )
                )
            else:
                feat.limit_value = limit_val
                feat.description = desc
    db.commit()


def promote_existing_users_to_pro(db: Session) -> int:
    """Upgrades all existing users on the platform to an active Pro subscription."""
    ensure_default_plans(db)
    pro_plan = db.query(Plan).filter(Plan.code == "pro").first()
    if not pro_plan:
        return 0

    users = db.query(User).all()
    upgraded = 0
    for u in users:
        sub = (
            db.query(Subscription)
            .filter(Subscription.user_id == u.id, Subscription.status == "active")
            .first()
        )
        if not sub:
            db.add(Subscription(user_id=u.id, plan_id=pro_plan.id, status="active"))
            upgraded += 1
        elif sub.plan_id != pro_plan.id:
            # Upgrade free subscriptions to Pro (keep premium if any)
            current_plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
            if not current_plan or current_plan.code == "free":
                sub.plan_id = pro_plan.id
                upgraded += 1
    if upgraded:
        db.commit()
    return upgraded


def _month_window_utc(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now or datetime.now(timezone.utc)
    start = datetime(current.year, current.month, 1, tzinfo=timezone.utc)
    if current.month == 12:
        next_month = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month = datetime(current.year, current.month + 1, 1, tzinfo=timezone.utc)
    return start, next_month


def get_user_plan_status(db: Session, user_id: str) -> Dict[str, Any]:
    ensure_default_plans(db)
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
        .first()
    )
    plan = db.query(Plan).filter(Plan.id == sub.plan_id).first() if sub else None
    if not plan:
        plan = db.query(Plan).filter(Plan.code == "free").first()

    feat_rows = db.query(PlanFeature).filter(PlanFeature.plan_id == plan.id).all()
    features = {f.feature_key: f.limit_value for f in feat_rows}
    limit_analyses = features.get("monthly_analyses")
    if limit_analyses is None:
        limit_analyses = 5 if plan.code == "free" else (150 if plan.code == "pro" else 500)

    month_start, next_month = _month_window_utc()
    used_analyses = (
        db.query(func.coalesce(func.sum(UsageEvent.quantity), 0))
        .filter(
            UsageEvent.user_id == user_id,
            UsageEvent.metric_key == "job_analysis",
            UsageEvent.created_at >= month_start,
        )
        .scalar()
        or 0
    )
    remaining = max(0, int(limit_analyses) - int(used_analyses))

    return {
        "plan_code": plan.code,
        "plan_name": plan.name,
        "price_brl_cents": plan.price_brl_cents,
        "monthly_analyses_limit": int(limit_analyses),
        "monthly_analyses_used": int(used_analyses),
        "monthly_analyses_remaining": remaining,
        "resets_at": next_month.isoformat(),
        "features": features,
    }


def record_analysis_usage(db: Session, user_id: str, quantity: int) -> None:
    if quantity <= 0:
        return
    db.add(
        UsageEvent(
            user_id=user_id,
            metric_key="job_analysis",
            quantity=quantity,
            estimated_cost_usd=0.0,
        )
    )
