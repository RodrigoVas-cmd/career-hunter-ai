from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.notifications import OPENAI_KEYS_URL, create_user_notification
from app.core.config import get_settings
from app.core.database import get_db
from app.models.applications import (
    Application,
    ApplicationAnswer,
    ApplicationApproval,
    ApplicationEvent,
    Interview,
)
from app.models.billing import AgentRun
from app.models.jobs import JobPosting
from app.models.resume import Resume, ResumeVersion
from app.models.targeting import TargetRole
from app.models.user import (
    CareerPreference,
    ProfessionalExperience,
    User,
    UserProfile,
    VerifiedSkill,
)
from app.schemas.applications import (
    AnswerUpdate,
    ApplicationAnswerResponse,
    ApplicationApprovalResponse,
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationEventResponse,
    ApplicationResponse,
    ApplicationUpdate,
    InterviewCreate,
    InterviewResponse,
    InterviewUpdate,
    QuestionCreate,
    ResumeVersionResponse,
    SubmissionConfirmRequest,
    VALID_OPERATIONAL_STATUSES,
)
from app.services.ats_optimizer import (
    build_ats_resume_version,
    compute_approval_payload_hash,
    prepare_question_draft,
)
from app.services.audit import record_audit_log

router = APIRouter(prefix="/applications", tags=["Candidaturas Supervisionadas & CRM"])
settings = get_settings()


def _get_user_app_or_404(db: Session, app_id: str, user_id: str) -> Application:
    app = (
        db.query(Application)
        .filter(Application.id == app_id, Application.user_id == user_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidatura não encontrada.")
    return app


def _invalidate_approvals(db: Session, app_id: str, user_id: str) -> None:
    db.query(ApplicationApproval).filter(
        ApplicationApproval.application_id == app_id,
        ApplicationApproval.user_id == user_id,
        ApplicationApproval.is_valid.is_(True),
    ).update({"is_valid": False})


def _current_payload_hash(db: Session, app: Application) -> str:
    answers = (
        db.query(ApplicationAnswer)
        .filter(
            ApplicationAnswer.application_id == app.id,
            ApplicationAnswer.user_id == app.user_id,
        )
        .all()
    )
    ans_list = [
        {
            "id": a.id,
            "question_text": a.question_text,
            "approved_answer": a.approved_answer or a.draft_answer or "",
        }
        for a in answers
    ]
    return compute_approval_payload_hash(
        application_id=app.id,
        company_name=app.company_name,
        role_title=app.role_title,
        resume_version_id=app.resume_version_id,
        source_url=app.source_url,
        answers=ans_list,
    )


def _has_valid_approval(db: Session, app: Application) -> bool:
    current_hash = _current_payload_hash(db, app)
    return (
        db.query(ApplicationApproval)
        .filter(
            ApplicationApproval.application_id == app.id,
            ApplicationApproval.user_id == app.user_id,
            ApplicationApproval.is_valid.is_(True),
            ApplicationApproval.payload_hash == current_hash,
        )
        .first()
        is not None
    )


def _record_event(
    db: Session,
    *,
    user_id: str,
    app_id: str,
    event_type: str,
    description: str,
) -> None:
    db.add(
        ApplicationEvent(
            user_id=user_id,
            application_id=app_id,
            event_type=event_type,
            description=description,
        )
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = None
    if payload.job_posting_id:
        job = db.query(JobPosting).filter(JobPosting.id == payload.job_posting_id).first()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada.")

        dup = (
            db.query(Application)
            .filter(
                Application.user_id == current_user.id,
                Application.job_posting_id == job.id,
                Application.operational_status != "descartada",
            )
            .first()
        )
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma candidatura registrada para esta vaga.",
            )

    company_name = (job.company_name if job else (payload.company_name or "")).strip()
    role_title = (job.title if job else (payload.role_title or "")).strip()
    source_url = job.original_url if job else payload.source_url

    if not company_name or not role_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe job_posting_id ou empresa e cargo.",
        )

    if not payload.job_posting_id:
        dup_manual = (
            db.query(Application)
            .filter(
                Application.user_id == current_user.id,
                Application.company_name == company_name,
                Application.role_title == role_title,
                Application.operational_status != "descartada",
            )
            .first()
        )
        if dup_manual:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Candidatura duplicada bloqueada para esta empresa e cargo.",
            )

    app_row = Application(
        user_id=current_user.id,
        job_posting_id=job.id if job else None,
        company_name=company_name,
        role_title=role_title,
        source_url=source_url,
        operational_status="em_preparacao",
        is_manual=payload.is_manual or (job is None),
    )
    db.add(app_row)
    db.flush()

    _record_event(
        db,
        user_id=current_user.id,
        app_id=app_row.id,
        event_type="application_created",
        description=f"Candidatura iniciada para {role_title} em {company_name}.",
    )
    db.commit()
    db.refresh(app_row)

    resp = ApplicationResponse.model_validate(app_row)
    resp.has_valid_approval = False
    return resp


@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.updated_at.desc())
        .all()
    )
    results: List[ApplicationResponse] = []
    for row in rows:
        item = ApplicationResponse.model_validate(row)
        item.has_valid_approval = _has_valid_approval(db, row)
        results.append(item)
    return results


@router.get("/interviews/all", response_model=List[InterviewResponse])
def list_all_user_interviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.scheduled_at.asc())
        .all()
    )


@router.get("/{app_id}", response_model=ApplicationDetailResponse)
def get_application_detail(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_row = _get_user_app_or_404(db, app_id, current_user.id)
    rv = None
    if app_row.resume_version_id:
        rv = (
            db.query(ResumeVersion)
            .filter(
                ResumeVersion.id == app_row.resume_version_id,
                ResumeVersion.user_id == current_user.id,
            )
            .first()
        )
    answers = (
        db.query(ApplicationAnswer)
        .filter(
            ApplicationAnswer.application_id == app_row.id,
            ApplicationAnswer.user_id == current_user.id,
        )
        .all()
    )
    approvals = (
        db.query(ApplicationApproval)
        .filter(
            ApplicationApproval.application_id == app_row.id,
            ApplicationApproval.user_id == current_user.id,
        )
        .order_by(ApplicationApproval.approved_at.desc())
        .all()
    )
    events = (
        db.query(ApplicationEvent)
        .filter(
            ApplicationEvent.application_id == app_row.id,
            ApplicationEvent.user_id == current_user.id,
        )
        .order_by(ApplicationEvent.occurred_at.desc())
        .all()
    )
    interviews = (
        db.query(Interview)
        .filter(
            Interview.application_id == app_row.id,
            Interview.user_id == current_user.id,
        )
        .order_by(Interview.scheduled_at.asc())
        .all()
    )

    detail = ApplicationDetailResponse.model_validate(app_row)
    detail.has_valid_approval = _has_valid_approval(db, app_row)
    detail.resume_version = ResumeVersionResponse.model_validate(rv) if rv else None
    detail.answers = [ApplicationAnswerResponse.model_validate(a) for a in answers]
    detail.approvals = [ApplicationApprovalResponse.model_validate(ap) for ap in approvals]
    detail.events = [ApplicationEventResponse.model_validate(ev) for ev in events]
    detail.interviews = [InterviewResponse.model_validate(iv) for iv in interviews]
    return detail


@router.patch("/{app_id}", response_model=ApplicationResponse)
def update_application(
    app_id: str,
    payload: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_row = _get_user_app_or_404(db, app_id, current_user.id)
    if payload.operational_status:
        if payload.operational_status not in VALID_OPERATIONAL_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status operacional inválido.",
            )
        # Never allow jumping directly to enviada_confirmada without confirm-submission + approval
        if payload.operational_status == "enviada_confirmada" and not _has_valid_approval(db, app_row):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível marcar como enviada sem aprovação humana e confirmação.",
            )
        app_row.operational_status = payload.operational_status

    if payload.process_stage is not None:
        app_row.process_stage = payload.process_stage

    _record_event(
        db,
        user_id=current_user.id,
        app_id=app_row.id,
        event_type="status_updated",
        description=payload.note or f"Status atualizado para {app_row.operational_status}.",
    )
    db.commit()
    db.refresh(app_row)

    resp = ApplicationResponse.model_validate(app_row)
    resp.has_valid_approval = _has_valid_approval(db, app_row)
    return resp


@router.post("/{app_id}/resume-version", response_model=ResumeVersionResponse, status_code=status.HTTP_201_CREATED)
def generate_ats_resume_version(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_row = _get_user_app_or_404(db, app_id, current_user.id)
    base_resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.is_primary.desc(), Resume.created_at.desc())
        .first()
    )
    if not base_resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Importe um currículo base antes de gerar uma versão ATS.",
        )

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    experiences = (
        db.query(ProfessionalExperience)
        .filter(ProfessionalExperience.user_id == current_user.id)
        .all()
    )
    skills = db.query(VerifiedSkill).filter(VerifiedSkill.user_id == current_user.id).all()
    job = (
        db.query(JobPosting).filter(JobPosting.id == app_row.job_posting_id).first()
        if app_row.job_posting_id
        else None
    )

    agent_run = AgentRun(
        user_id=current_user.id,
        agent_name="ats_resume_optimizer",
        trigger_type="on_demand",
        status="running",
    )
    db.add(agent_run)
    db.flush()

    prefs = db.query(CareerPreference).filter(CareerPreference.user_id == current_user.id).first()
    target_dir = settings.upload_path / current_user.id / "versions"
    content_json, changes_summary, docx_path, pdf_path, ai_status = build_ats_resume_version(
        user=current_user,
        profile=profile,
        experiences=experiences,
        skills=skills,
        job=job,
        target_dir=target_dir,
        openai_api_key=prefs.openai_api_key if prefs else None,
        base_filename=base_resume.original_filename,
        target_role_override=app_row.role_title,
    )

    if ai_status == "auth_error":
        create_user_notification(
            db,
            user_id=current_user.id,
            title="Chave API da OpenAI expirada ou inválida",
            body=(
                "A geração via ChatGPT falhou por erro de autenticação/expiração (401/403). "
                f"Atualize sua chave em Configurações ou gere uma nova em {OPENAI_KEYS_URL}."
            ),
            category="warning",
        )

    rv = ResumeVersion(
        user_id=current_user.id,
        base_resume_id=base_resume.id,
        job_posting_id=app_row.job_posting_id,
        version_label=f"ATS - {app_row.role_title} ({app_row.company_name})"[:160],
        content_json=content_json,
        changes_summary_json=changes_summary,
        approved_by_user=False,
        docx_path=docx_path,
        pdf_path=pdf_path,
    )
    db.add(rv)
    db.flush()

    app_row.resume_version_id = rv.id
    app_row.operational_status = "aguardando_revisao"
    _invalidate_approvals(db, app_row.id, current_user.id)
    _record_event(
        db,
        user_id=current_user.id,
        app_id=app_row.id,
        event_type="ats_resume_generated",
        description="Versão de currículo ATS gerada exclusivamente com fatos verificados.",
    )
    agent_run.status = "completed"
    agent_run.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rv)
    return rv


@router.post("/resume-versions/{version_id}/approve", response_model=ResumeVersionResponse)
def approve_resume_version(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rv = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.id == version_id, ResumeVersion.user_id == current_user.id)
        .first()
    )
    if not rv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Versão de currículo não encontrada.")
    rv.approved_by_user = True
    db.commit()
    db.refresh(rv)
    return rv


@router.get("/resume-versions/{version_id}/download")
def download_resume_version_docx(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rv = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.id == version_id, ResumeVersion.user_id == current_user.id)
        .first()
    )
    if not rv or not rv.docx_path or not Path(rv.docx_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo DOCX não encontrado.")
    return FileResponse(
        path=rv.docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=Path(rv.docx_path).name,
    )


@router.get("/resume-versions/{version_id}/download-pdf")
def download_resume_version_pdf(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rv = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.id == version_id, ResumeVersion.user_id == current_user.id)
        .first()
    )
    if not rv or not rv.pdf_path or not Path(rv.pdf_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo PDF não encontrado.")
    return FileResponse(
        path=rv.pdf_path,
        media_type="application/pdf",
        filename=Path(rv.pdf_path).name,
    )


@router.post("/{app_id}/questions", response_model=ApplicationAnswerResponse, status_code=status.HTTP_201_CREATED)
def prepare_question_answer(
    app_id: str,
    payload: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_row = _get_user_app_or_404(db, app_id, current_user.id)
    experiences = (
        db.query(ProfessionalExperience)
        .filter(ProfessionalExperience.user_id == current_user.id)
        .all()
    )
    skills = db.query(VerifiedSkill).filter(VerifiedSkill.user_id == current_user.id).all()
    preferences = (
        db.query(CareerPreference).filter(CareerPreference.user_id == current_user.id).first()
    )

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    base_resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.is_primary.desc(), Resume.created_at.desc())
        .first()
    )
    tailored_rv = (
        db.query(ResumeVersion)
        .filter(
            ResumeVersion.id == app_row.resume_version_id,
            ResumeVersion.user_id == current_user.id,
        )
        .first()
        if app_row.resume_version_id
        else None
    )
    job = (
        db.query(JobPosting).filter(JobPosting.id == app_row.job_posting_id).first()
        if app_row.job_posting_id
        else None
    )
    target_roles = (
        db.query(TargetRole)
        .filter(TargetRole.user_id == current_user.id, TargetRole.status == "ativo")
        .all()
    )
    role_lower = (app_row.role_title or "").lower()
    matched_role = next(
        (
            r for r in target_roles
            if (r.min_salary_brl or r.desired_salary_brl)
            and (r.title.lower() in role_lower or role_lower in r.title.lower())
        ),
        None,
    )
    target_role_salary = (
        (matched_role.min_salary_brl, matched_role.desired_salary_brl)
        if matched_role
        else None
    )
    prep = prepare_question_draft(
        question_text=payload.question_text.strip(),
        experiences=experiences,
        skills=skills,
        preferences=preferences,
        profile=profile,
        base_resume_raw=base_resume.raw_text if base_resume else None,
        tailored_resume_content=tailored_rv.content_json if tailored_rv else None,
        role_title=app_row.role_title,
        company_name=app_row.company_name,
        field_type=payload.field_type,
        options=payload.options,
        max_chars=payload.max_chars,
        job=job,
        openai_api_key=preferences.openai_api_key if preferences else None,
        target_role_salary=target_role_salary,
    )
    if prep.get("ai_status") == "auth_error":
        create_user_notification(
            db,
            user_id=current_user.id,
            title="Chave API da OpenAI expirada ou inválida",
            body=(
                "A geração de resposta via ChatGPT falhou por erro de autenticação/expiração (401/403). "
                f"Atualize sua chave em Configurações ou gere uma nova em {OPENAI_KEYS_URL}."
            ),
            category="warning",
        )
    ans = ApplicationAnswer(
        user_id=current_user.id,
        application_id=app_row.id,
        question_text=payload.question_text.strip(),
        question_category=prep["question_category"],
        draft_answer=prep["draft_answer"],
        approved_answer=None,
        evidence_refs_json=prep["evidence_refs"],
        requires_human_input=prep["requires_human_input"],
    )
    db.add(ans)
    _invalidate_approvals(db, app_row.id, current_user.id)
    db.commit()
    db.refresh(ans)
    return ans


@router.patch("/answers/{answer_id}", response_model=ApplicationAnswerResponse)
def approve_or_edit_answer(
    answer_id: str,
    payload: AnswerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ans = (
        db.query(ApplicationAnswer)
        .filter(ApplicationAnswer.id == answer_id, ApplicationAnswer.user_id == current_user.id)
        .first()
    )
    if not ans:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resposta não encontrada.")

    ans.approved_answer = payload.approved_answer.strip()
    ans.requires_human_input = False
    _invalidate_approvals(db, ans.application_id, current_user.id)
    db.commit()
    db.refresh(ans)
    return ans


@router.post("/{app_id}/approve", response_model=ApplicationApprovalResponse)
def approve_application(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_row = _get_user_app_or_404(db, app_id, current_user.id)

    if app_row.resume_version_id:
        rv = (
            db.query(ResumeVersion)
            .filter(
                ResumeVersion.id == app_row.resume_version_id,
                ResumeVersion.user_id == current_user.id,
            )
            .first()
        )
        if not rv or not rv.approved_by_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aprove a versão personalizada do currículo antes de aprovar a candidatura.",
            )

    pending_answers = (
        db.query(ApplicationAnswer)
        .filter(
            ApplicationAnswer.application_id == app_row.id,
            ApplicationAnswer.user_id == current_user.id,
            ApplicationAnswer.requires_human_input.is_(True),
            ApplicationAnswer.approved_answer.is_(None),
        )
        .count()
    )
    if pending_answers > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Existem perguntas que exigem decisão/resposta humana antes da aprovação.",
        )

    _invalidate_approvals(db, app_row.id, current_user.id)
    payload_hash = _current_payload_hash(db, app_row)
    approval = ApplicationApproval(
        user_id=current_user.id,
        application_id=app_row.id,
        payload_hash=payload_hash,
        is_valid=True,
    )
    db.add(approval)
    app_row.operational_status = "aguardando_aprovacao"
    _record_event(
        db,
        user_id=current_user.id,
        app_id=app_row.id,
        event_type="human_approved",
        description="Candidatura aprovada explicitamente pelo usuário para envio supervisionado.",
    )
    record_audit_log(
        db,
        user_id=current_user.id,
        actor_role=current_user.role,
        action="application.approved",
        entity_type="application",
        entity_id=app_row.id,
        details={"payload_hash": payload_hash},
    )
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/{app_id}/confirm-submission", response_model=ApplicationResponse)
def confirm_submission(
    app_id: str,
    payload: SubmissionConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_row = _get_user_app_or_404(db, app_id, current_user.id)

    if not _has_valid_approval(db, app_row):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aprovação humana explícita inválida ou ausente para os dados atuais.",
        )

    if payload.ambiguous:
        app_row.operational_status = "pendente_confirmacao"
        _record_event(
            db,
            user_id=current_user.id,
            app_id=app_row.id,
            event_type="submission_ambiguous",
            description=payload.confirmation_note or "Envio com retorno ambíguo; aguardando confirmação.",
        )
    elif payload.confirmed:
        app_row.operational_status = "enviada_confirmada"
        app_row.submitted_at = datetime.now(timezone.utc)
        _record_event(
            db,
            user_id=current_user.id,
            app_id=app_row.id,
            event_type="submission_confirmed",
            description=payload.confirmation_note or "Envio supervisionado confirmado pelo usuário.",
        )
    else:
        app_row.operational_status = "falha_envio"
        _record_event(
            db,
            user_id=current_user.id,
            app_id=app_row.id,
            event_type="submission_failed",
            description=payload.confirmation_note or "Falha no envio registrada.",
        )

    db.commit()
    db.refresh(app_row)
    resp = ApplicationResponse.model_validate(app_row)
    resp.has_valid_approval = _has_valid_approval(db, app_row)
    return resp


@router.post("/{app_id}/interviews", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def create_interview(
    app_id: str,
    payload: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_row = _get_user_app_or_404(db, app_id, current_user.id)
    iv = Interview(
        user_id=current_user.id,
        application_id=app_row.id,
        stage_name=payload.stage_name.strip(),
        scheduled_at=payload.scheduled_at,
        status="scheduled",
        notes=payload.notes,
    )
    db.add(iv)
    app_row.process_stage = "entrevista_agendada"
    _record_event(
        db,
        user_id=current_user.id,
        app_id=app_row.id,
        event_type="interview_scheduled",
        description=f"Entrevista agendada: {iv.stage_name}.",
    )
    db.commit()
    db.refresh(iv)
    return iv


@router.patch("/interviews/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: str,
    payload: InterviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    iv = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.user_id == current_user.id)
        .first()
    )
    if not iv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrevista não encontrada.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(iv, field, value)
    db.commit()
    db.refresh(iv)
    return iv
