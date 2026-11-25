from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.admin_models import AdminAccount, AdminAuditLog


def record_admin_audit(
    db: Session,
    *,
    actor: Optional[AdminAccount],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    justification: Optional[str] = None,
    result: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
    fallback_email: Optional[str] = None,
    fallback_role: str = "anonymous",
) -> AdminAuditLog:
    row = AdminAuditLog(
        actor_admin_id=actor.id if actor else None,
        actor_email=actor.email if actor else fallback_email,
        actor_role=actor.admin_role if actor else fallback_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        justification=justification,
        result=result,
        metadata_json=metadata or {},
    )
    db.add(row)
    return row
