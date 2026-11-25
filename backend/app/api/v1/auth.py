from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import CareerPreference, User, UserProfile
from app.schemas.auth import (
    OnboardingProgressUpdate,
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
