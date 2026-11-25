from pathlib import Path
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.resume import Resume
from app.models.user import (
    EvidenceSource,
    ProfessionalExperience,
    User,
    UserProfile,
    VerifiedSkill,
)
from app.schemas.resume import ResumeResponse
from app.services.ats_optimizer import build_ats_resume_version
from app.services.audit import record_audit_log
from app.services.resume_parser import (
    analyze_profile_for_ats,
    compare_cv_with_linkedin,
    parse_resume_bytes,
)

router = APIRouter(prefix="/resumes", tags=["Currículos"])
settings = get_settings()

ALLOWED_EXTENSIONS = {"pdf", "docx"}


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename or "." not in file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo inválido. Envie um currículo em PDF ou DOCX.",
        )

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato não permitido. Aceitamos apenas PDF e DOCX.",
        )

    content = await file.read()
    max_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
    if not content or len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tamanho de arquivo inválido (máximo {settings.MAX_RESUME_SIZE_MB} MB).",
        )

    user_dir = settings.upload_path / current_user.id
    user_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}.{ext}"
    storage_path = user_dir / safe_name
    storage_path.write_bytes(content)

    try:
        raw_text, extracted_data, ambiguities = parse_resume_bytes(content, ext)
        parse_status = "parsed"
    except Exception as exc:
        raw_text = ""
        extracted_data = {"experiences": [], "skills": [], "education": [], "certifications": [], "languages": []}
        ambiguities = [{"field": "document", "message": f"Erro ao processar arquivo: {exc}", "excerpt": ""}]
        parse_status = "failed"

    # Mark previous primary resumes as secondary and refresh resume-extracted experiences/skills
    db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_primary.is_(True)).update(
        {"is_primary": False}
    )
    db.query(ProfessionalExperience).filter(
        ProfessionalExperience.user_id == current_user.id,
        ProfessionalExperience.origin.in_(["resume_pdf", "resume_docx"]),
    ).delete(synchronize_session=False)
    db.query(VerifiedSkill).filter(
        VerifiedSkill.user_id == current_user.id,
        VerifiedSkill.origin.in_(["resume_pdf", "resume_docx", "ats_suggestion_from_cv"]),
    ).delete(synchronize_session=False)

    resume = Resume(
        user_id=current_user.id,
        original_filename=file.filename[:255],
        file_format=ext,
        storage_path=str(storage_path),
        file_size_bytes=len(content),
        raw_text=raw_text,
        extracted_data_json=extracted_data,
        ambiguities_json=ambiguities,
        parse_status=parse_status,
        is_primary=True,
    )
    db.add(resume)
    db.flush()

    evidence = EvidenceSource(
        user_id=current_user.id,
        source_type="resume_upload",
        source_ref_id=resume.id,
        source_label=f"Currículo: {resume.original_filename}",
        excerpt=raw_text[:500] if raw_text else None,
    )
    db.add(evidence)
    db.flush()

    # Populate Verified Professional Profile items as pending_review
    origin_tag = f"resume_{ext}"
    for exp_item in extracted_data.get("experiences", []):
        db.add(
            ProfessionalExperience(
                user_id=current_user.id,
                company_name=exp_item.get("company_name", "Empresa não identificada"),
                role_title=exp_item.get("role_title", "Cargo não especificado"),
                sector=exp_item.get("sector"),
                raw_period_text=exp_item.get("raw_period_text"),
                is_current=bool(exp_item.get("is_current", False)),
                responsibilities=exp_item.get("responsibilities"),
                leadership_experience=bool(exp_item.get("leadership_experience", False)),
                origin=origin_tag,
                evidence_source_id=evidence.id,
                evidence_excerpt=exp_item.get("evidence_excerpt"),
                validation_status="pending_review",
                ambiguity_note=exp_item.get("ambiguity_note"),
            )
        )

    existing_skill_names = {
        s.name.lower()
        for s in db.query(VerifiedSkill).filter(VerifiedSkill.user_id == current_user.id).all()
    }
    for skill_item in extracted_data.get("skills", []):
        name = skill_item.get("name", "").strip()
        if name and name.lower() not in existing_skill_names:
            existing_skill_names.add(name.lower())
            db.add(
                VerifiedSkill(
                    user_id=current_user.id,
                    name=name,
                    category=skill_item.get("category", "technical"),
                    origin=origin_tag,
                    evidence_source_id=evidence.id,
                    evidence_excerpt=skill_item.get("evidence_excerpt"),
                    validation_status="pending_review",
                )
            )

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile:
        contact = extracted_data.get("contact", {})
        if contact.get("email"):
            profile.contact_email = contact["email"]
        if contact.get("phone"):
            profile.phone = contact["phone"]
        if contact.get("linkedin_url"):
            profile.linkedin_url = contact["linkedin_url"]
        profile.summary = extracted_data.get("summary") or None
        profile.education_json = extracted_data.get("education") or []
        profile.certifications_json = extracted_data.get("certifications") or []
        profile.languages_json = extracted_data.get("languages") or []

    record_audit_log(
        db,
        user_id=current_user.id,
        actor_role=current_user.role,
        action="resume.uploaded",
        entity_type="resume",
        entity_id=resume.id,
        details={"filename": resume.original_filename, "format": ext, "parse_status": parse_status},
    )
    db.commit()
    db.refresh(resume)
    return resume


@router.get("", response_model=List[ResumeResponse])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .all()
    )


@router.get("/ats-suggestions")
def get_ats_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    exps = (
        db.query(ProfessionalExperience)
        .filter(
            ProfessionalExperience.user_id == current_user.id,
            ProfessionalExperience.validation_status != "rejected",
        )
        .all()
    )
    skills = (
        db.query(VerifiedSkill)
        .filter(
            VerifiedSkill.user_id == current_user.id,
            VerifiedSkill.validation_status != "rejected",
        )
        .all()
    )
    resumes_rows = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    return analyze_profile_for_ats(
        summary=profile.summary if profile else None,
        experiences=[
            {
                "role_title": e.role_title,
                "company_name": e.company_name,
                "sector": e.sector,
                "raw_period_text": e.raw_period_text,
                "validation_status": e.validation_status,
                "proven_results": e.proven_results,
                "responsibilities": e.responsibilities,
            }
            for e in exps
        ],
        skills=[s.name for s in skills],
        raw_texts=[r.raw_text for r in resumes_rows if r.raw_text],
    )


@router.get("/preview-adjusted")
def preview_adjusted_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    exps = (
        db.query(ProfessionalExperience)
        .filter(ProfessionalExperience.user_id == current_user.id)
        .all()
    )
    skills = db.query(VerifiedSkill).filter(VerifiedSkill.user_id == current_user.id).all()
    if not exps and not skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adicione ou importe experiências antes de pré-visualizar o CV ajustado.",
        )

    from app.models.user import CareerPreference
    prefs = db.query(CareerPreference).filter(CareerPreference.user_id == current_user.id).first()
    base_res = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.is_primary.desc()).first()
    target_dir = settings.upload_path / current_user.id / "previews"
    content_json, changes_summary, _, _, _ = build_ats_resume_version(
        user=current_user,
        profile=profile,
        experiences=exps,
        skills=skills,
        job=None,
        target_dir=target_dir,
        openai_api_key=prefs.openai_api_key if prefs else None,
        base_filename=base_res.original_filename if base_res else None,
    )
    return {
        "content": content_json,
        "changes_summary": changes_summary,
    }


@router.post("/compare-linkedin")
async def compare_with_linkedin(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename or "." not in file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo inválido.")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Envie o PDF ou DOCX do LinkedIn.")

    content = await file.read()
    _, li_data, _ = parse_resume_bytes(content, ext)
    li_exps = li_data.get("experiences", [])

    cv_exps_rows = (
        db.query(ProfessionalExperience)
        .filter(
            ProfessionalExperience.user_id == current_user.id,
            ProfessionalExperience.validation_status != "rejected",
        )
        .all()
    )
    cv_exps = [
        {
            "company_name": e.company_name,
            "role_title": e.role_title,
            "raw_period_text": e.raw_period_text,
        }
        for e in cv_exps_rows
    ]
    return compare_cv_with_linkedin(cv_exps, li_exps)


@router.post("/build-adjusted", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def build_adjusted_resume(
    set_as_primary: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    exps = (
        db.query(ProfessionalExperience)
        .filter(ProfessionalExperience.user_id == current_user.id)
        .all()
    )
    skills = db.query(VerifiedSkill).filter(VerifiedSkill.user_id == current_user.id).all()
    if not exps and not skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adicione ou importe experiências antes de gerar um CV ajustado.",
        )

    from app.models.user import CareerPreference
    prefs = db.query(CareerPreference).filter(CareerPreference.user_id == current_user.id).first()
    base_res = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.is_primary.desc()).first()
    target_dir = settings.upload_path / current_user.id
    content_json, changes_summary, docx_path, _, _ = build_ats_resume_version(
        user=current_user,
        profile=profile,
        experiences=exps,
        skills=skills,
        job=None,
        target_dir=target_dir,
        openai_api_key=prefs.openai_api_key if prefs else None,
        base_filename=base_res.original_filename if base_res else None,
    )
    from pathlib import Path
    file_bytes = Path(docx_path).read_bytes()

    if set_as_primary:
        db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_primary.is_(True)).update(
            {"is_primary": False}
        )

    adjusted = Resume(
        user_id=current_user.id,
        original_filename=f"CV_Ajustado_{current_user.full_name.replace(' ', '_')}.docx",
        file_format="docx",
        storage_path=docx_path,
        file_size_bytes=len(file_bytes),
        raw_text="\n".join(changes_summary),
        extracted_data_json=content_json,
        ambiguities_json=[],
        parse_status="validated",
        is_primary=set_as_primary,
    )
    db.add(adjusted)
    db.commit()
    db.refresh(adjusted)
    return adjusted


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Currículo não encontrado.")
    return resume


@router.get("/{resume_id}/download")
def download_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume or not Path(resume.storage_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo do currículo não encontrado.")
    media_type = (
        "application/pdf"
        if resume.file_format == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(
        path=resume.storage_path,
        media_type=media_type,
        filename=resume.original_filename,
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Currículo não encontrado.")

    evidence_ids = [
        ev.id
        for ev in db.query(EvidenceSource)
        .filter(
            EvidenceSource.user_id == current_user.id,
            EvidenceSource.source_ref_id == resume.id,
        )
        .all()
    ]
    other_resumes_count = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id, Resume.id != resume.id)
        .count()
    )
    if evidence_ids:
        db.query(ProfessionalExperience).filter(
            ProfessionalExperience.user_id == current_user.id,
            ProfessionalExperience.evidence_source_id.in_(evidence_ids),
        ).delete(synchronize_session=False)
        db.query(VerifiedSkill).filter(
            VerifiedSkill.user_id == current_user.id,
            VerifiedSkill.evidence_source_id.in_(evidence_ids),
        ).delete(synchronize_session=False)
        db.query(EvidenceSource).filter(
            EvidenceSource.user_id == current_user.id,
            EvidenceSource.id.in_(evidence_ids),
        ).delete(synchronize_session=False)

    if other_resumes_count == 0:
        db.query(ProfessionalExperience).filter(
            ProfessionalExperience.user_id == current_user.id,
            ProfessionalExperience.origin.in_(["resume_pdf", "resume_docx"]),
        ).delete(synchronize_session=False)
        db.query(VerifiedSkill).filter(
            VerifiedSkill.user_id == current_user.id,
            VerifiedSkill.origin.in_(["resume_pdf", "resume_docx", "ats_suggestion_from_cv"]),
        ).delete(synchronize_session=False)
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if profile:
            profile.summary = None
            profile.education_json = []
            profile.certifications_json = []
            profile.languages_json = []

    was_primary = resume.is_primary
    storage_file = Path(resume.storage_path)
    db.delete(resume)
    db.flush()

    if was_primary:
        latest = (
            db.query(Resume)
            .filter(Resume.user_id == current_user.id)
            .order_by(Resume.created_at.desc())
            .first()
        )
        if latest:
            latest.is_primary = True

    record_audit_log(
        db,
        user_id=current_user.id,
        actor_role=current_user.role,
        action="resume.deleted",
        entity_type="resume",
        entity_id=resume_id,
    )
    db.commit()

    if storage_file.exists():
        try:
            storage_file.unlink()
        except OSError:
            pass
