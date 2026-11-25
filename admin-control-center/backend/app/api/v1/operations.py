from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_admin_roles
from app.core.database import get_db
from app.models.admin_models import (
    AdminAccount,
    AdminAuditLog,
    AdminCommunication,
    AdminPromptVersion,
    AdminSetting,
    AdminSupportTicket,
)
from app.models.shared import SharedAgentRun, SharedJobPosting, SharedUsageEvent, SharedUser
from app.services.audit import record_admin_audit

router = APIRouter(prefix="/ops", tags=["Admin Operations, AI, Support & Security"])


class PromptDraftRequest(BaseModel):
    agent_key: str = Field(min_length=2, max_length=64)
    prompt_text: str = Field(min_length=10)
    description: Optional[str] = None


class SupportCreateRequest(BaseModel):
    user_id: str
    subject: str = Field(min_length=3, max_length=200)
    priority: str = Field(default="media", pattern="^(baixa|media|alta|urgente)$")
    message: str = Field(min_length=2)


class SupportUpdateRequest(BaseModel):
    status: Optional[str] = Field(
        default=None, pattern="^(aberto|em_atendimento|aguardando_usuario|resolvido|encerrado)$"
    )
    reply: Optional[str] = None


class CommunicationCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    kind: str = Field(default="transacional", pattern="^(transacional|promocional)$")
    target_plan: str = Field(default="all")
    target_status: str = Field(default="all")
    body: str = Field(min_length=5)


@router.get("/ai-center")
def ai_center_summary(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "finance")),
    db: Session = Depends(get_db),
):
    runs = db.query(SharedAgentRun).order_by(SharedAgentRun.started_at.desc()).limit(100).all()
    usage = db.query(SharedUsageEvent).all()
    by_agent: Dict[str, Dict[str, Any]] = {}
    for r in runs:
        entry = by_agent.setdefault(r.agent_name, {"runs": 0, "failed": 0, "tokens": 0})
        entry["runs"] += 1
        if r.status == "failed":
            entry["failed"] += 1
        entry["tokens"] += int(r.tokens_used or 0)

    total_cost_usd = sum(float(u.estimated_cost_usd or 0.0) for u in usage)
    return {
        "total_runs": len(runs),
        "total_tokens": sum(int(r.tokens_used or 0) for r in runs),
        "total_estimated_cost_usd": round(total_cost_usd, 4),
        "has_cost_telemetry": any(float(u.estimated_cost_usd or 0.0) > 0 for u in usage),
        "by_agent": by_agent,
        "recent_runs": [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "status": r.status,
                "tokens_used": r.tokens_used,
                "error_message": r.error_message,
                "started_at": r.started_at.isoformat(),
            }
            for r in runs[:25]
        ],
    }


@router.get("/searches")
def search_monitoring(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin")),
    db: Session = Depends(get_db),
):
    runs = (
        db.query(SharedAgentRun)
        .filter(SharedAgentRun.agent_name.in_(["job_discovery", "job_discovery_auto", "company_watch"]))
        .order_by(SharedAgentRun.started_at.desc())
        .limit(50)
        .all()
    )
    active_jobs = db.query(SharedJobPosting).filter(SharedJobPosting.availability_status == "active").count()
    return {
        "active_jobs_count": active_jobs,
        "sources_note": "Automação oficial via Greenhouse, Lever, JSON-LD e Remotive; portais externos (LinkedIn, Indeed, Gupy, Catho, Vagas.com.br) operam via atalhos direcionados.",
        "runs": [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "status": r.status,
                "error_message": r.error_message,
                "started_at": r.started_at.isoformat(),
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            }
            for r in runs
        ],
    }


@router.get("/prompts")
def list_prompt_versions(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin")),
    db: Session = Depends(get_db),
):
    return db.query(AdminPromptVersion).order_by(AdminPromptVersion.created_at.desc()).all()


@router.post("/prompts")
def create_prompt_draft(
    payload: PromptDraftRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin")),
    db: Session = Depends(get_db),
):
    latest = (
        db.query(AdminPromptVersion)
        .filter(AdminPromptVersion.agent_key == payload.agent_key)
        .order_by(AdminPromptVersion.version_number.desc())
        .first()
    )
    next_v = (latest.version_number + 1) if latest else 1
    row = AdminPromptVersion(
        agent_key=payload.agent_key,
        version_number=next_v,
        status="rascunho",
        prompt_text=payload.prompt_text,
        description=payload.description,
        author_admin_id=actor.id,
    )
    db.add(row)
    record_admin_audit(
        db,
        actor=actor,
        action="prompts.draft_created",
        resource_type="prompt",
        resource_id=payload.agent_key,
        metadata={"version": next_v},
    )
    db.commit()
    db.refresh(row)
    return row


@router.post("/prompts/{prompt_id}/publish")
def publish_prompt_version(
    prompt_id: str,
    actor: AdminAccount = Depends(require_admin_roles("superadmin")),
    db: Session = Depends(get_db),
):
    row = db.query(AdminPromptVersion).filter(AdminPromptVersion.id == prompt_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Versão não encontrada.")
    for prev in (
        db.query(AdminPromptVersion)
        .filter(AdminPromptVersion.agent_key == row.agent_key, AdminPromptVersion.status == "publicado")
        .all()
    ):
        prev.status = "arquivado"
    row.status = "publicado"
    row.published_at = datetime.now(timezone.utc)
    record_admin_audit(
        db,
        actor=actor,
        action="prompts.published",
        resource_type="prompt",
        resource_id=row.id,
        justification="Publicação explícita de versão de prompt no painel.",
    )
    db.commit()
    return row


@router.get("/support")
def list_support_tickets(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "support")),
    db: Session = Depends(get_db),
):
    users = {u.id: u for u in db.query(SharedUser).all()}
    rows = db.query(AdminSupportTicket).order_by(AdminSupportTicket.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_email": users[r.user_id].email if r.user_id in users else "",
            "subject": r.subject,
            "priority": r.priority,
            "status": r.status,
            "messages": r.messages_json,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/support")
def create_support_ticket(
    payload: SupportCreateRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "support")),
    db: Session = Depends(get_db),
):
    row = AdminSupportTicket(
        user_id=payload.user_id,
        subject=payload.subject,
        priority=payload.priority,
        status="aberto",
        assigned_admin_id=actor.id,
        messages_json=[{"author": actor.email, "text": payload.message, "at": datetime.now(timezone.utc).isoformat()}],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/communications")
def list_communications(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "support")),
    db: Session = Depends(get_db),
):
    return db.query(AdminCommunication).order_by(AdminCommunication.created_at.desc()).all()


@router.post("/communications")
def create_communication_draft(
    payload: CommunicationCreateRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin")),
    db: Session = Depends(get_db),
):
    row = AdminCommunication(**payload.model_dump(), status="rascunho")
    db.add(row)
    record_admin_audit(
        db,
        actor=actor,
        action="communications.draft_created",
        resource_type="communication",
        metadata={"title": payload.title, "kind": payload.kind},
    )
    db.commit()
    db.refresh(row)
    return row


@router.get("/audit-logs")
def list_admin_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    _admin: AdminAccount = Depends(require_admin_roles("superadmin", "ops_admin", "finance")),
    db: Session = Depends(get_db),
):
    return (
        db.query(AdminAuditLog)
        .order_by(AdminAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/settings")
def get_admin_settings_map(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin")),
    db: Session = Depends(get_db),
):
    rows = db.query(AdminSetting).all()
    return {r.key: r.value_json for r in rows}


@router.put("/settings/{key}")
def update_admin_setting(
    key: str,
    value: Dict[str, Any],
    actor: AdminAccount = Depends(require_admin_roles("superadmin")),
    db: Session = Depends(get_db),
):
    row = db.query(AdminSetting).filter(AdminSetting.key == key).first()
    if not row:
        row = AdminSetting(key=key, value_json=value, updated_by_admin_id=actor.id)
        db.add(row)
    else:
        row.value_json = value
        row.updated_by_admin_id = actor.id
    record_admin_audit(
        db,
        actor=actor,
        action="settings.updated",
        resource_type="setting",
        resource_id=key,
    )
    db.commit()
    return {"key": key, "value": row.value_json}
