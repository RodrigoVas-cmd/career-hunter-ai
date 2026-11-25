from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, require_admin_roles
from app.core.config import get_admin_settings
from app.core.database import get_db
from app.core.security import (
    create_admin_token,
    generate_totp_secret,
    hash_password,
    verify_password,
    verify_totp_code,
)
from app.models.admin_models import AdminAccount
from app.services.audit import record_admin_audit

router = APIRouter(prefix="/auth", tags=["Admin Auth & RBAC"])


class BootstrapSuperAdminRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=10, max_length=128)
    bootstrap_token: Optional[str] = None


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class AdminCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=10, max_length=128)
    admin_role: str = Field(pattern="^(superadmin|ops_admin|support|finance)$")


class AdminToggleRequest(BaseModel):
    is_active: bool
    justification: str = Field(min_length=5, max_length=500)


class MfaVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


@router.get("/bootstrap-status")
def bootstrap_status(db: Session = Depends(get_db)):
    count = db.query(AdminAccount).filter(AdminAccount.admin_role == "superadmin").count()
    return {"has_superadmin": count > 0}


@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
def bootstrap_first_superadmin(payload: BootstrapSuperAdminRequest, db: Session = Depends(get_db)):
    existing_super = (
        db.query(AdminAccount).filter(AdminAccount.admin_role == "superadmin").count()
    )
    if existing_super > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O superadministrador inicial já foi configurado.",
        )

    cfg = get_admin_settings()
    if cfg.ADMIN_ENVIRONMENT == "production":
        if not cfg.ADMIN_BOOTSTRAP_TOKEN or payload.bootstrap_token != cfg.ADMIN_BOOTSTRAP_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de bootstrap inválido.",
            )
    elif cfg.ADMIN_BOOTSTRAP_TOKEN and payload.bootstrap_token != cfg.ADMIN_BOOTSTRAP_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de bootstrap inválido.",
        )

    admin = AdminAccount(
        email=payload.email.lower().strip(),
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        admin_role="superadmin",
        is_active=True,
        mfa_enabled=False,
    )
    db.add(admin)
    db.flush()
    record_admin_audit(
        db,
        actor=admin,
        action="admin.bootstrap_superadmin",
        resource_type="admin_account",
        resource_id=admin.id,
        justification="Bootstrap inicial do primeiro superadministrador.",
    )
    db.commit()
    db.refresh(admin)

    token = create_admin_token(admin.id, admin.admin_role, mfa_verified=True)
    return {
        "access_token": token,
        "admin": {
            "id": admin.id,
            "email": admin.email,
            "full_name": admin.full_name,
            "admin_role": admin.admin_role,
            "mfa_enabled": admin.mfa_enabled,
        },
    }


@router.post("/login")
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    admin = db.query(AdminAccount).filter(AdminAccount.email == email).first()
    if not admin or not verify_password(payload.password, admin.hashed_password):
        record_admin_audit(
            db,
            actor=None,
            fallback_email=email,
            action="admin.login_failed",
            resource_type="admin_auth",
            result="failed",
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais administrativas inválidas.",
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta administrativa suspensa ou desativada.",
        )

    if admin.mfa_enabled:
        if not payload.totp_code:
            return {"mfa_required": True, "access_token": None}
        if not verify_totp_code(admin.mfa_secret or "", payload.totp_code):
            record_admin_audit(
                db,
                actor=admin,
                action="admin.mfa_failed",
                resource_type="admin_auth",
                result="failed",
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código MFA inválido.",
            )

    admin.last_login_at = datetime.now(timezone.utc)
    record_admin_audit(
        db,
        actor=admin,
        action="admin.logged_in",
        resource_type="admin_auth",
        resource_id=admin.id,
    )
    db.commit()

    token = create_admin_token(admin.id, admin.admin_role, mfa_verified=True)
    return {
        "mfa_required": False,
        "access_token": token,
        "admin": {
            "id": admin.id,
            "email": admin.email,
            "full_name": admin.full_name,
            "admin_role": admin.admin_role,
            "mfa_enabled": admin.mfa_enabled,
        },
    }


@router.get("/me")
def admin_me(admin: AdminAccount = Depends(get_current_admin)):
    return {
        "id": admin.id,
        "email": admin.email,
        "full_name": admin.full_name,
        "admin_role": admin.admin_role,
        "mfa_enabled": admin.mfa_enabled,
        "last_login_at": admin.last_login_at,
    }


@router.post("/mfa/setup")
def setup_mfa(admin: AdminAccount = Depends(get_current_admin), db: Session = Depends(get_db)):
    secret = generate_totp_secret()
    admin.mfa_secret = secret
    db.commit()
    otpauth_uri = (
        f"otpauth://totp/CareerHunterAdmin:{admin.email}?secret={secret}&issuer=CareerHunterAdmin"
    )
    return {"secret": secret, "otpauth_uri": otpauth_uri}


@router.post("/mfa/enable")
def enable_mfa(
    payload: MfaVerifyRequest,
    admin: AdminAccount = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if not admin.mfa_secret or not verify_totp_code(admin.mfa_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código TOTP inválido.")
    admin.mfa_enabled = True
    record_admin_audit(
        db,
        actor=admin,
        action="admin.mfa_enabled",
        resource_type="admin_account",
        resource_id=admin.id,
    )
    db.commit()
    return {"mfa_enabled": True}


@router.get("/accounts")
def list_admin_accounts(
    _admin: AdminAccount = Depends(require_admin_roles("superadmin")),
    db: Session = Depends(get_db),
):
    rows = db.query(AdminAccount).order_by(AdminAccount.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "email": r.email,
            "full_name": r.full_name,
            "admin_role": r.admin_role,
            "is_active": r.is_active,
            "mfa_enabled": r.mfa_enabled,
            "last_login_at": r.last_login_at,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
def create_admin_account(
    payload: AdminCreateRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin")),
    db: Session = Depends(get_db),
):
    email = payload.email.lower().strip()
    if db.query(AdminAccount).filter(AdminAccount.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin já cadastrado.")
    acc = AdminAccount(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        admin_role=payload.admin_role,
        is_active=True,
    )
    db.add(acc)
    db.flush()
    record_admin_audit(
        db,
        actor=actor,
        action="admin.account_created",
        resource_type="admin_account",
        resource_id=acc.id,
        metadata={"role": acc.admin_role, "email": acc.email},
    )
    db.commit()
    return {"id": acc.id, "email": acc.email, "admin_role": acc.admin_role}


@router.patch("/accounts/{account_id}/status")
def toggle_admin_status(
    account_id: str,
    payload: AdminToggleRequest,
    actor: AdminAccount = Depends(require_admin_roles("superadmin")),
    db: Session = Depends(get_db),
):
    target = db.query(AdminAccount).filter(AdminAccount.id == account_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada.")

    if not payload.is_active and target.admin_role == "superadmin":
        active_supers = (
            db.query(AdminAccount)
            .filter(AdminAccount.admin_role == "superadmin", AdminAccount.is_active.is_(True))
            .count()
        )
        if active_supers <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é permitido desativar o último superadministrador ativo.",
            )

    target.is_active = payload.is_active
    record_admin_audit(
        db,
        actor=actor,
        action="admin.account_status_changed",
        resource_type="admin_account",
        resource_id=target.id,
        justification=payload.justification,
        metadata={"is_active": payload.is_active},
    )
    db.commit()
    return {"id": target.id, "is_active": target.is_active}
