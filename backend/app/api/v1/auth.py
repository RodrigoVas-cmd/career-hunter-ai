import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
)
from app.models.user import CareerPreference, User, UserProfile
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    OnboardingProgressUpdate,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserMeResponse,
    UserRegister,
)
from app.services.audit import record_audit_log

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta cadastrada com este e-mail.",
        )

    user = User(
        email=normalized_email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role="user",
        onboarding_step=1,
        onboarding_completed=False,
    )
    db.add(user)
    db.flush()

    db.add(UserProfile(user_id=user.id))
    db.add(CareerPreference(user_id=user.id, application_mode="supervised"))

    record_audit_log(
        db,
        user_id=user.id,
        actor_role=user.role,
        action="user.registered",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        onboarding_step=user.onboarding_step,
        onboarding_completed=user.onboarding_completed,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada.",
        )

    record_audit_log(
        db,
        user_id=user.id,
        actor_role=user.role,
        action="user.logged_in",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        onboarding_step=user.onboarding_step,
        onboarding_completed=user.onboarding_completed,
    )


@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/onboarding", response_model=UserMeResponse)
def update_onboarding_progress(
    payload: OnboardingProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.onboarding_step = payload.onboarding_step
    if payload.onboarding_completed is not None:
        current_user.onboarding_completed = payload.onboarding_completed
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


def _send_reset_email(to_email: str, reset_url: str) -> None:
    cfg = get_settings()
    msg = EmailMessage()
    msg["Subject"] = "Career Hunter AI — Redefinição de senha"
    msg["From"] = cfg.SMTP_FROM or cfg.SMTP_USER
    msg["To"] = to_email
    msg.set_content(
        "Você solicitou a redefinição da sua senha no Career Hunter AI.\n\n"
        f"Acesse o link abaixo (válido por 15 minutos):\n{reset_url}\n\n"
        "Se você não solicitou essa alteração, ignore este e-mail."
    )
    with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        if cfg.SMTP_USER and cfg.SMTP_PASSWORD:
            smtp.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
        smtp.send_message(msg)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    cfg = get_settings()
    normalized_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email, User.is_active.is_(True)).first()

    smtp_ready = bool(cfg.SMTP_HOST and (cfg.SMTP_FROM or cfg.SMTP_USER))
    if not smtp_ready and cfg.ENVIRONMENT == "production":
        return {
            "email_sent": False,
            "smtp_configured": False,
            "message": (
                "O envio automático de e-mail ainda não está configurado no servidor (SMTP). "
                "Configure as variáveis SMTP no backend ou entre em contato com o suporte."
            ),
        }

    dev_token = None
    if user:
        token = create_password_reset_token(user.id, user.hashed_password[:12])
        reset_url = f"{cfg.FRONTEND_URL.rstrip('/')}/auth?mode=reset&token={token}"
        if smtp_ready:
            try:
                _send_reset_email(user.email, reset_url)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Não foi possível enviar o e-mail de recuperação: {exc}",
                )
        elif cfg.ENVIRONMENT != "production":
            dev_token = token

    resp = {
        "email_sent": smtp_ready,
        "smtp_configured": smtp_ready,
        "message": (
            "Se este e-mail estiver cadastrado, enviamos um link de redefinição válido por 15 minutos."
        ),
    }
    if dev_token:
        resp["dev_reset_token"] = dev_token
    return resp


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_password_reset_token(payload.token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link ou token de redefinição inválido ou expirado.",
        )

    user = db.query(User).filter(User.id == decoded.get("sub")).first()
    if not user or not user.is_active or user.hashed_password[:12] != decoded.get("ph"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link ou token de redefinição inválido ou já utilizado.",
        )

    user.hashed_password = hash_password(payload.new_password)
    record_audit_log(
        db,
        user_id=user.id,
        actor_role=user.role,
        action="user.password_reset",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    return {"message": "Senha redefinida com sucesso! Você já pode entrar com a nova senha."}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta.",
        )
    current_user.hashed_password = hash_password(payload.new_password)
    record_audit_log(
        db,
        user_id=current_user.id,
        actor_role=current_user.role,
        action="user.password_changed",
        entity_type="user",
        entity_id=current_user.id,
    )
    db.commit()
    return {"message": "Senha atualizada com sucesso."}
