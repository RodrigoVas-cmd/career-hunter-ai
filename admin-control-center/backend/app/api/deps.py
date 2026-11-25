from typing import Callable, Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_admin_token
from app.models.admin_models import AdminAccount
from app.services.audit import record_admin_audit

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AdminAccount:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação administrativa necessária.",
        )
    try:
        payload = decode_admin_token(credentials.credentials)
        admin_id = payload.get("sub")
        if not admin_id:
            raise ValueError("Missing sub")
        if not payload.get("mfa_verified", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Verificação MFA obrigatória para concluir o acesso.",
            )
    except HTTPException:
        raise
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão administrativa inválida ou expirada.",
        )

    admin = (
        db.query(AdminAccount)
        .filter(AdminAccount.id == admin_id, AdminAccount.is_active.is_(True))
        .first()
    )
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta administrativa inativa ou sem permissão.",
        )
    return admin


def require_admin_roles(*allowed_roles: str) -> Callable[[AdminAccount], AdminAccount]:
    allowed = set(allowed_roles)

    def _checker(
        admin: AdminAccount = Depends(get_current_admin),
        db: Session = Depends(get_db),
    ) -> AdminAccount:
        if admin.admin_role == "superadmin" or admin.admin_role in allowed:
            return admin
        record_admin_audit(
            db,
            actor=admin,
            action="admin.access_denied",
            resource_type="rbac",
            result="denied",
            metadata={"required_roles": sorted(allowed), "actual_role": admin.admin_role},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente para esta operação administrativa.",
        )

    return _checker
