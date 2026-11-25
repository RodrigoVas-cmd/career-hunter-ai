from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.applications import Application, Notification
from app.models.jobs import JobMatch, JobPosting
from app.models.resume import Resume
from app.models.targeting import FavoriteCompany, TargetRole
from app.models.user import CareerPreference, ProfessionalExperience, User, VerifiedSkill

router = APIRouter(prefix="/dashboard", tags=["Visão Geral"])


@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resumes_count = db.query(Resume).filter(Resume.user_id == current_user.id).count()
    experiences_count = (
        db.query(ProfessionalExperience)
        .filter(ProfessionalExperience.user_id == current_user.id)
        .count()
    )
    verified_experiences = (
        db.query(ProfessionalExperience)
        .filter(
            ProfessionalExperience.user_id == current_user.id,
            ProfessionalExperience.validation_status == "verified",
        )
        .count()
    )
    skills_count = db.query(VerifiedSkill).filter(VerifiedSkill.user_id == current_user.id).count()
    target_roles_count = db.query(TargetRole).filter(TargetRole.user_id == current_user.id).count()
    favorite_companies_count = (
        db.query(FavoriteCompany).filter(FavoriteCompany.user_id == current_user.id).count()
    )
    discovered_jobs_count = (
        db.query(JobPosting).filter(JobPosting.availability_status == "active").count()
    )
    compatible_jobs_count = (
        db.query(JobMatch)
        .filter(
            JobMatch.user_id == current_user.id,
            JobMatch.is_eligible.is_(True),
            JobMatch.total_score >= 65.0,
        )
        .count()
    )
    apps = db.query(Application).filter(Application.user_id == current_user.id).all()
    applications_count = len(apps)
    sent_statuses = {
        "enviada_confirmada",
        "resposta_recebida",
        "teste_solicitado",
        "entrevista_agendada",
        "entrevista_realizada",
        "proxima_etapa",
        "proposta_recebida",
        "contratado",
    }
    pending_statuses = {
        "descoberta",
        "qualificada",
        "favorita",
        "em_preparacao",
        "aguardando_revisao",
        "aguardando_aprovacao",
        "envio_em_andamento",
        "pendente_confirmacao",
    }
    interview_statuses = {"entrevista_agendada", "entrevista_realizada", "proxima_etapa"}
    rejected_statuses = {"reprovado", "desistencia", "encerrada", "descartada"}

    sent_applications = sum(
        1 for a in apps if a.operational_status in sent_statuses or a.submitted_at is not None
    )
    pending_applications = sum(
        1 for a in apps if a.operational_status in pending_statuses and a.submitted_at is None
    )
    interview_applications = sum(
        1
        for a in apps
        if a.operational_status in interview_statuses
        or (a.process_stage and "entrevista" in a.process_stage.lower())
    )
    rejected_applications = sum(1 for a in apps if a.operational_status in rejected_statuses)
    offer_applications = sum(
        1 for a in apps if a.operational_status in {"proposta_recebida", "contratado"}
    )
    unread_notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .count()
    )
    prefs = (
        db.query(CareerPreference).filter(CareerPreference.user_id == current_user.id).first()
    )
    if not (prefs and prefs.openai_api_key):
        unread_notifications += 1

    return {
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "onboarding_step": current_user.onboarding_step,
            "onboarding_completed": current_user.onboarding_completed,
        },
        "counts": {
            "resumes": resumes_count,
            "experiences": experiences_count,
            "verified_experiences": verified_experiences,
            "skills": skills_count,
            "target_roles": target_roles_count,
            "favorite_companies": favorite_companies_count,
            "discovered_jobs": discovered_jobs_count,
            "compatible_jobs": compatible_jobs_count,
            "applications": applications_count,
            "sent_applications": sent_applications,
            "pending_applications": pending_applications,
            "interview_applications": interview_applications,
            "rejected_applications": rejected_applications,
            "offer_applications": offer_applications,
            "unread_notifications": unread_notifications,
        },
    }
