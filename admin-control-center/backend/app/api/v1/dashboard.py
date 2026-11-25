from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin_roles
from app.core.database import get_db
from app.models.admin_models import (
    AdminAccount,
    AdminCourtesyGrant,
    AdminOperationalCost,
    AdminUserOverride,
)
from app.models.shared import (
    SharedAgentRun,
    SharedApplication,
    SharedBillingEvent,
    SharedFavoriteCompany,
    SharedJobPosting,
    SharedPlan,
    SharedResumeVersion,
    SharedSubscription,
    SharedUsageEvent,
    SharedUser,
)

router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard"])


def _resolve_period(period: str, start_date: Optional[str], end_date: Optional[str]) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if period == "today":
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        return start, now
    if period == "yesterday":
        end = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        return end - timedelta(days=1), end
    if period == "7d":
        return now - timedelta(days=7), now
    if period == "90d":
        return now - timedelta(days=90), now
    if period == "month":
        return datetime(now.year, now.month, 1, tzinfo=timezone.utc), now
    if period == "prev_month":
        first_this = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        prev_end = first_this
        prev_month = 12 if now.month == 1 else now.month - 1
        prev_year = now.year - 1 if now.month == 1 else now.year
        return datetime(prev_year, prev_month, 1, tzinfo=timezone.utc), prev_end
    if period == "year":
        return datetime(now.year, 1, 1, tzinfo=timezone.utc), now
    if period == "custom" and start_date and end_date:
        try:
            s = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
            e = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc) + timedelta(days=1)
            return s, e
        except ValueError:
            pass
    return now - timedelta(days=30), now


@router.get("/executive")
def get_executive_dashboard(
    period: str = Query(default="30d"),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "support", "finance")),
    db: Session = Depends(get_db),
):
    p_start, p_end = _resolve_period(period, start_date, end_date)
    plans_by_id = {p.id: p for p in db.query(SharedPlan).all()}
    plans_by_code = {p.code: p for p in plans_by_id.values()}

    users = db.query(SharedUser).all()
    subs = (
        db.query(SharedSubscription)
        .filter(SharedSubscription.status == "active")
        .order_by(SharedSubscription.created_at.desc())
        .all()
    )
    sub_by_user: Dict[str, SharedSubscription] = {}
    for s in subs:
        if s.user_id not in sub_by_user:
            sub_by_user[s.user_id] = s

    overrides = {o.user_id: o for o in db.query(AdminUserOverride).all()}
    courtesies = (
        db.query(AdminCourtesyGrant)
        .filter(AdminCourtesyGrant.status == "active")
        .all()
    )
    courtesy_by_user = {c.user_id: c for c in courtesies}

    # Payment proof: any billing event with payment_succeeded / invoice.paid
    paid_user_ids = {
        b.user_id
        for b in db.query(SharedBillingEvent).all()
        if b.user_id and any(k in b.event_type.lower() for k in ("paid", "succeeded", "confirmed"))
    }

    plan_counts = {"free": 0, "pro": 0, "premium": 0}
    modality_counts = {"free": 0, "paid": 0, "courtesy": 0, "unclassified": 0}
    status_counts = {"active": 0, "suspended": 0, "deactivated": 0}
    new_users_period = 0
    verified_mrr_cents = 0

    for u in users:
        ov = overrides.get(u.id)
        acc_status = ov.account_status if ov else ("active" if u.is_active else "deactivated")
        if acc_status in status_counts:
            status_counts[acc_status] += 1
        elif not u.is_active:
            status_counts["suspended"] += 1
        else:
            status_counts["active"] += 1

        c_at = u.created_at.replace(tzinfo=timezone.utc) if u.created_at.tzinfo is None else u.created_at
        if p_start <= c_at <= p_end:
            new_users_period += 1

        # Effective plan (unique user counting)
        courtesy = courtesy_by_user.get(u.id)
        sub = sub_by_user.get(u.id)
        eff_code = "free"
        if courtesy:
            eff_code = courtesy.plan_code if courtesy.plan_code in plan_counts else "pro"
        elif sub and sub.plan_id in plans_by_id:
            eff_code = plans_by_id[sub.plan_id].code
        if eff_code not in plan_counts:
            eff_code = "free"
        plan_counts[eff_code] += 1

        # Modality classification (never assume Pro/Premium without payment proof is paid)
        if courtesy:
            modality = "courtesy"
        elif ov and ov.access_modality in modality_counts:
            modality = ov.access_modality
        elif eff_code == "free":
            modality = "free"
        elif u.id in paid_user_ids:
            modality = "paid"
        else:
            modality = "unclassified"
        modality_counts[modality] += 1

        if modality == "paid" and eff_code in plans_by_code:
            verified_mrr_cents += plans_by_code[eff_code].price_brl_cents

    total_users = len(users)
    paid_users = modality_counts["paid"]
    conversion_pct = round((paid_users / total_users) * 100, 1) if total_users > 0 else 0.0

    # AI costs & telemetry
    usage_rows = db.query(SharedUsageEvent).all()
    analyses_count = sum(r.quantity for r in usage_rows if r.metric_key == "job_analysis")
    ai_cost_usd = sum(float(r.estimated_cost_usd or 0.0) for r in usage_rows)
    agent_runs = db.query(SharedAgentRun).all()
    total_tokens = sum(int(r.tokens_used or 0) for r in agent_runs)
    has_ai_cost_telemetry = any(float(r.estimated_cost_usd or 0.0) > 0 for r in usage_rows) or total_tokens > 0

    op_costs_cents = (
        db.query(func.coalesce(func.sum(AdminOperationalCost.monthly_cost_brl_cents), 0))
        .filter(AdminOperationalCost.is_active.is_(True))
        .scalar()
        or 0
    )

    tailored_resumes_count = db.query(SharedResumeVersion).count()
    applications_count = db.query(SharedApplication).count()
    jobs_count = db.query(SharedJobPosting).filter(SharedJobPosting.availability_status == "active").count()
    monitored_companies = db.query(SharedFavoriteCompany).count()

    # Monthly evolution (real data grouped by YYYY-MM)
    monthly_map: Dict[str, int] = {}
    for u in users:
        key = u.created_at.strftime("%Y-%m")
        monthly_map[key] = monthly_map.get(key, 0) + 1
    evolution = [{"month": k, "users": monthly_map[k]} for k in sorted(monthly_map.keys())]

    return {
        "period": {"code": period, "start": p_start.isoformat(), "end": p_end.isoformat()},
        "users": {
            "total": total_users,
            "free": plan_counts["free"],
            "pro": plan_counts["pro"],
            "premium": plan_counts["premium"],
            "active": status_counts["active"],
            "suspended": status_counts["suspended"],
            "deactivated": status_counts["deactivated"],
            "new_in_period": new_users_period,
            "modalities": modality_counts,
            "conversion_paid_pct": conversion_pct,
        },
        "financial": {
            "verified_mrr_brl_cents": verified_mrr_cents,
            "verified_arr_brl_cents": verified_mrr_cents * 12,
            "operational_costs_brl_cents": int(op_costs_cents),
            "ai_cost_usd": round(ai_cost_usd, 4),
            "total_tokens": total_tokens,
            "has_ai_cost_telemetry": has_ai_cost_telemetry,
            "has_payment_provider": len(paid_user_ids) > 0,
            "ticket_medio_brl_cents": (verified_mrr_cents // paid_users) if paid_users > 0 else 0,
        },
        "usage": {
            "analyses": int(analyses_count),
            "tailored_resumes": int(tailored_resumes_count),
            "applications": int(applications_count),
            "active_jobs": int(jobs_count),
            "monitored_companies": int(monitored_companies),
            "agent_runs": len(agent_runs),
        },
        "evolution": evolution,
    }
