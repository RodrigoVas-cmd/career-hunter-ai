from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import AuditLog


def record_audit_log(
    db: Session,
    *,
    user_id: Optional[str],
    actor_role: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details_json=details or {},
    )
    db.add(entry)
    return entry
