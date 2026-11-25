from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.notifications import create_user_notification
from app.core.database import get_db
from app.models.user import (
    CareerPreference,
    ProfessionalExperience,
    User,
    UserProfile,
    VerifiedSkill,
)
from app.schemas.profile import (
    CareerPreferenceResponse,
    CareerPreferenceUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    SkillCreate,
    SkillResponse,
    SkillUpdate,
    UserProfileResponse,
    UserProfileUpdate,
)

router = APIRouter(prefix="/profile", tags=["Perfil Verificado & Preferências"])


@router.get("", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("", response_model=UserProfileResponse)
def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/experiences", response_model=List[ExperienceResponse])
def list_experiences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ProfessionalExperience)
        .filter(ProfessionalExperience.user_id == current_user.id)
        .order_by(ProfessionalExperience.created_at.desc())
        .all()
    )


@router.post("/experiences", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
def create_experience(
    payload: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = ProfessionalExperience(user_id=current_user.id, **payload.model_dump())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.patch("/experiences/{experience_id}", response_model=ExperienceResponse)
def update_experience(
    experience_id: str,
    payload: ExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = (
        db.query(ProfessionalExperience)
        .filter(
            ProfessionalExperience.id == experience_id,
            ProfessionalExperience.user_id == current_user.id,
        )
        .first()
    )
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiência não encontrada.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exp, field, value)

    db.commit()
    db.refresh(exp)
    return exp


@router.delete("/experiences/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(
    experience_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = (
        db.query(ProfessionalExperience)
        .filter(
            ProfessionalExperience.id == experience_id,
            ProfessionalExperience.user_id == current_user.id,
        )
        .first()
    )
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiência não encontrada.")
    db.delete(exp)
    db.commit()


@router.get("/skills", response_model=List[SkillResponse])
def list_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(VerifiedSkill)
        .filter(VerifiedSkill.user_id == current_user.id)
        .order_by(VerifiedSkill.created_at.desc())
        .all()
    )


@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skill = VerifiedSkill(user_id=current_user.id, **payload.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.patch("/skills/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: str,
    payload: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skill = (
        db.query(VerifiedSkill)
        .filter(VerifiedSkill.id == skill_id, VerifiedSkill.user_id == current_user.id)
        .first()
    )
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competência não encontrada.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)

    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skill = (
        db.query(VerifiedSkill)
        .filter(VerifiedSkill.id == skill_id, VerifiedSkill.user_id == current_user.id)
        .first()
    )
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competência não encontrada.")
    db.delete(skill)
    db.commit()


@router.get("/preferences", response_model=CareerPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = db.query(CareerPreference).filter(CareerPreference.user_id == current_user.id).first()
    if not pref:
        pref = CareerPreference(user_id=current_user.id, application_mode="supervised")
        db.add(pref)
        db.commit()
        db.refresh(pref)
    resp = CareerPreferenceResponse.model_validate(pref)
    resp.has_openai_key = bool(pref.openai_api_key)
    return resp


@router.put("/preferences", response_model=CareerPreferenceResponse)
def update_preferences(
    payload: CareerPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = db.query(CareerPreference).filter(CareerPreference.user_id == current_user.id).first()
    if not pref:
        pref = CareerPreference(user_id=current_user.id, application_mode="supervised")
        db.add(pref)

    data = payload.model_dump(exclude_unset=True)
    if "openai_api_key" in data:
        key_val = (data.pop("openai_api_key") or "").strip()
        old_key = pref.openai_api_key
        pref.openai_api_key = key_val or None
        if key_val and key_val != old_key:
            create_user_notification(
                db,
                user_id=current_user.id,
                title="ChatGPT (OpenAI) conectado com sucesso!",
                body="Sua chave API da OpenAI foi salva. Agora a geração de currículos ATS em PDF e respostas de recrutamento usarão o Agente Especialista Estratégico.",
                category="success",
            )
    for field, value in data.items():
        setattr(pref, field, value)
    # Invariant: application mode is always supervised
    pref.application_mode = "supervised"

    db.commit()
    db.refresh(pref)
    resp = CareerPreferenceResponse.model_validate(pref)
    resp.has_openai_key = bool(pref.openai_api_key)
    return resp
