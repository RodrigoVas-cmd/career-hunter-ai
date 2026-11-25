import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.billing import AgentRun
from app.models.jobs import (
    CompanyMonitoringRun,
    JobMatch,
    JobPosting,
    JobRequirement,
    JobSource,
)
from app.models.targeting import CompanyCareerSource, FavoriteCompany, TargetRole
from app.models.user import (
    CareerPreference,
    ProfessionalExperience,
    User,
    UserProfile,
    VerifiedSkill,
)
from app.schemas.jobs import (
    CompanyWatchCompanyResult,
    CompanyWatchRunResponse,
    ConnectorDiscoverRequest,
    DiscoverResultResponse,
    JobMatchResponse,
    JobPostingResponse,
    JobRequirementResponse,
    ManualJobCreate,
    MatchingWeights,
)
from app.services.connectors import (
    compute_dedup_hash,
    detect_connector_from_url,
    extract_requirements,
    fetch_greenhouse_jobs,
    fetch_jsonld_jobs,
    fetch_lever_jobs,
    fetch_remotive_jobs,
)
from app.services.matching_engine import evaluate_job_match

router = APIRouter(prefix="/jobs", tags=["Radar de Vagas & Motor de Aderência"])


def _get_or_create_source(db: Session, name: str, kind: str, base_url: Optional[str] = None) -> JobSource:
    src = db.query(JobSource).filter(JobSource.name == name).first()
    if not src:
        src = JobSource(name=name, source_kind=kind, base_url=base_url, is_active=True)
        db.add(src)
        db.flush()
    return src


def _upsert_job_posting(
    db: Session,
    *,
    source_id: Optional[str],
    company_id: Optional[str],
    item: Dict[str, Any],
) -> tuple[JobPosting, bool]:
    dedup = compute_dedup_hash(
        item["company_name"],
        item["title"],
        item["original_url"],
        item.get("external_id"),
    )
    existing = db.query(JobPosting).filter(JobPosting.dedup_hash == dedup).first()
    if existing:
        existing.description = item["description"]
        existing.location = item.get("location")
        existing.modality = item.get("modality")
        existing.seniority = item.get("seniority")
        existing.salary_range_text = item.get("salary_range_text")
        existing.availability_status = "active"
        if company_id and not existing.company_id:
            existing.company_id = company_id
        return existing, False

    posting = JobPosting(
        job_source_id=source_id,
        company_id=company_id,
        external_id=item.get("external_id"),
        dedup_hash=dedup,
        company_name=item["company_name"][:200],
        title=item["title"][:255],
        description=item["description"],
        original_url=item["original_url"][:800],
        location=item.get("location"),
        modality=item.get("modality"),
        seniority=item.get("seniority"),
        salary_range_text=item.get("salary_range_text"),
        benefits_json=item.get("benefits") or [],
        availability_status="active",
        published_at=item.get("published_at"),
    )
    db.add(posting)
    db.flush()

    for req in item.get("requirements", []):
        db.add(
            JobRequirement(
                job_posting_id=posting.id,
                requirement_type=req["requirement_type"],
                text=req["text"],
            )
        )
    return posting, True


def _user_favorite_company_ids(db: Session, user_id: str) -> tuple[set[str], set[str]]:
    favs = (
        db.query(FavoriteCompany)
        .options(joinedload(FavoriteCompany.company))
        .filter(FavoriteCompany.user_id == user_id)
        .all()
    )
    ids = {f.company_id for f in favs}
    names = {f.company.name.lower() for f in favs if f.company}
    return ids, names


def _is_fav_job(job: JobPosting, fav_ids: set[str], fav_names: set[str]) -> bool:
    if job.company_id and job.company_id in fav_ids:
        return True
    return job.company_name.lower() in fav_names


_STOPWORDS = {
    "de", "da", "do", "das", "dos", "em", "para", "com", "e", "ou", "a", "o",
    "the", "of", "and", "in", "for", "sr", "jr", "pl", "senior", "junior", "pleno",
}
_GENERIC_LEVEL_WORDS = {
    "gerente", "coordenador", "supervisor", "analista", "especialista", "assistente",
    "diretor", "head", "lead", "manager", "coordinator", "specialist", "director", "engineer",
}
_ROLE_SYNONYMS: Dict[str, set[str]] = {
    "producao": {"producao", "production", "manufacturing", "operations", "fabrica", "plant"},
    "manufatura": {"manufatura", "manufacturing", "production", "producao", "industrial", "operations"},
    "industrial": {"industrial", "manufacturing", "production", "producao"},
    "engenharia": {"engenharia", "engineering", "engineer"},
    "mecanica": {"mecanica", "mechanical"},
    "qualidade": {"qualidade", "quality"},
    "logistica": {"logistica", "logistics", "supply"},
    "produto": {"produto", "product"},
    "product": {"product", "produto"},
}
_REMOTE_GLOBAL_TERMS = {
    "worldwide", "anywhere", "global", "latam", "south america", "america latina", "brazil", "brasil",
}
_STATE_ABBR = {
    "sao paulo": "sp",
    "rio de janeiro": "rj",
    "minas gerais": "mg",
    "parana": "pr",
    "santa catarina": "sc",
    "rio grande do sul": "rs",
    "bahia": "ba",
    "pernambuco": "pe",
    "ceara": "ce",
    "goias": "go",
    "distrito federal": "df",
}


def _normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()


def _job_matches_roles(title: str, roles: List[TargetRole]) -> bool:
    if not roles:
        return True
    norm_title = _normalize_text(title)
    title_tokens = set(norm_title.replace("-", " ").replace("/", " ").split())

    for role in roles:
        tokens = [
            t for t in _normalize_text(role.title).replace("-", " ").replace("/", " ").split()
            if len(t) >= 3 and t not in _STOPWORDS
        ]
        if not tokens:
            continue
        domain_tokens = [t for t in tokens if t not in _GENERIC_LEVEL_WORDS] or tokens
        for dt in domain_tokens:
            synonyms = _ROLE_SYNONYMS.get(dt, {dt})
            if any(syn in title_tokens or syn in norm_title for syn in synonyms):
                # Avoid matching generic "product" alone against unrelated roles if "product" is paired with manager/owner
                if dt in {"product", "produto"} and not any(
                    k in norm_title for k in ("manager", "gerente", "owner", "lead", "product")
                ):
                    continue
                return True
    return False


def _job_matches_preferences(
    title: str,
    location: Optional[str],
    modality: Optional[str],
    roles: List[TargetRole],
    pref: Optional[CareerPreference],
) -> bool:
    if not _job_matches_roles(title, roles):
        return False
    if not pref:
        return True

    allowed_mods = {_normalize_text(m) for m in (pref.work_modalities or []) if m}
    job_mod = _normalize_text(modality or "")
    if allowed_mods and job_mod and job_mod not in allowed_mods:
        return False

    loc_terms: set[str] = set()
    if pref.current_city:
        loc_terms.add(_normalize_text(pref.current_city))
    if pref.current_state:
        norm_state = _normalize_text(pref.current_state)
        loc_terms.add(norm_state)
        if norm_state in _STATE_ABBR:
            loc_terms.add(_STATE_ABBR[norm_state])
    for dl in (pref.desired_locations or []):
        if dl:
            loc_terms.add(_normalize_text(dl))
    loc_terms.discard("")

    norm_loc = _normalize_text(location)
    if job_mod == "remoto":
        if norm_loc:
            allowed_remote = _REMOTE_GLOBAL_TERMS | loc_terms
            if not any(term in norm_loc for term in allowed_remote):
                return False
    elif loc_terms and norm_loc:
        if not any(term in norm_loc for term in loc_terms):
            return False

    return True


@router.post("/discover/auto")
def auto_discover_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    One-click automatic discovery for non-technical users:
    1) Checks monitorable favorite companies (Greenhouse, Lever, JSON-LD).
    2) Searches authorized public APIs (Remotive) ONLY if user accepts remote work.
    3) Filters discovered jobs by onboarding roles, work modalities, and location.
    4) Automatically runs the matching engine so results are ready in Vagas Recomendadas.
    """
    roles = (
        db.query(TargetRole)
        .filter(TargetRole.user_id == current_user.id, TargetRole.status == "ativo")
        .all()
    )
    pref = (
        db.query(CareerPreference)
        .filter(CareerPreference.user_id == current_user.id)
        .first()
    )
    favs = (
        db.query(FavoriteCompany)
        .options(joinedload(FavoriteCompany.company))
        .filter(FavoriteCompany.user_id == current_user.id)
        .all()
    )

    agent_run = AgentRun(
        user_id=current_user.id,
        agent_name="job_discovery_auto",
        trigger_type="on_demand",
        status="running",
    )
    db.add(agent_run)
    db.flush()

    created_count = 0
    updated_count = 0
    filtered_out_count = 0
    sources_checked: List[str] = []

    # 1. Favorite companies with supported connectors
    for fav in favs:
        url = fav.company.careers_page_url if fav.company else None
        if not url:
            continue
        source_type, target = detect_connector_from_url(url)
        try:
            if source_type == "greenhouse":
                raw_jobs = fetch_greenhouse_jobs(target, fav.company.name)
                src = _get_or_create_source(db, "Greenhouse", "greenhouse")
            elif source_type == "lever":
                raw_jobs = fetch_lever_jobs(target, fav.company.name)
                src = _get_or_create_source(db, "Lever", "lever")
            else:
                raw_jobs = fetch_jsonld_jobs(target, fav.company.name)
                src = _get_or_create_source(db, "JSON-LD Carreiras", "jsonld")

            for item in raw_jobs:
                if not _job_matches_preferences(
                    item.get("title", ""), item.get("location"), item.get("modality"), roles, pref
                ):
                    filtered_out_count += 1
                    continue
                _, is_new = _upsert_job_posting(
                    db, source_id=src.id, company_id=fav.company_id, item=item
                )
                if is_new:
                    created_count += 1
                else:
                    updated_count += 1
            fav.monitoring_status = "monitorada"
            sources_checked.append(fav.company.name)
        except Exception:
            fav.monitoring_status = "erro_integracao"

    # 2. Public keyword API (Remotive) ONLY when remote is accepted in onboarding preferences
    allowed_mods = {_normalize_text(m) for m in (pref.work_modalities or [])} if pref else set()
    allows_remote = (not allowed_mods) or ("remoto" in allowed_mods)
    if roles and allows_remote:
        src_rem = _get_or_create_source(db, "Remotive", "remotive", "https://remotive.com")
        for role in roles[:3]:
            try:
                raw_jobs = fetch_remotive_jobs(role.title, limit=8)
                for item in raw_jobs:
                    if not _job_matches_preferences(
                        item.get("title", ""), item.get("location"), item.get("modality"), roles, pref
                    ):
                        filtered_out_count += 1
                        continue
                    _, is_new = _upsert_job_posting(
                        db, source_id=src_rem.id, company_id=None, item=item
                    )
                    if is_new:
                        created_count += 1
                    else:
                        updated_count += 1
                sources_checked.append(f"Remotive ({role.title})")
            except Exception:
                pass

    agent_run.status = "completed"
    agent_run.finished_at = datetime.now(timezone.utc)
    db.commit()

    # Auto-run matching engine so Vagas Recomendadas is updated
    matches = run_matching_engine(weights=None, current_user=current_user, db=db)

    return {
        "created_count": created_count,
        "updated_count": updated_count,
        "filtered_out_count": filtered_out_count,
        "allows_remote": allows_remote,
        "sources_checked": sources_checked,
        "matched_count": len(matches),
    }


@router.post("/discover/connector", response_model=DiscoverResultResponse)
def discover_via_connector(
    payload: ConnectorDiscoverRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = AgentRun(
        user_id=current_user.id,
        agent_name="job_discovery",
        trigger_type="on_demand",
        status="running",
    )
    db.add(run)
    db.flush()

    try:
        if payload.source_kind == "greenhouse":
            raw_jobs = fetch_greenhouse_jobs(payload.target.strip(), payload.company_name)
            src = _get_or_create_source(db, "Greenhouse", "greenhouse", "https://boards-api.greenhouse.io")
        elif payload.source_kind == "lever":
            raw_jobs = fetch_lever_jobs(payload.target.strip(), payload.company_name)
            src = _get_or_create_source(db, "Lever", "lever", "https://api.lever.co")
        else:
            raw_jobs = fetch_jsonld_jobs(payload.target.strip(), payload.company_name)
            src = _get_or_create_source(db, "JSON-LD Carreiras", "jsonld")
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Não foi possível consultar a fonte {payload.source_kind}: {exc}",
        )

    created_count = 0
    updated_count = 0
    saved_jobs: List[JobPosting] = []
    for item in raw_jobs:
        posting, is_new = _upsert_job_posting(
            db, source_id=src.id, company_id=None, item=item
        )
        saved_jobs.append(posting)
        if is_new:
            created_count += 1
        else:
            updated_count += 1

    run.status = "completed"
    run.finished_at = datetime.now(timezone.utc)
    db.commit()

    fav_ids, fav_names = _user_favorite_company_ids(db, current_user.id)
    responses = [
        JobPostingResponse(
            id=j.id,
            company_name=j.company_name,
            title=j.title,
            description=j.description,
            original_url=j.original_url,
            location=j.location,
            modality=j.modality,
            seniority=j.seniority,
            salary_range_text=j.salary_range_text,
            availability_status=j.availability_status,
            published_at=j.published_at,
            discovered_at=j.discovered_at,
            is_favorite_company=_is_fav_job(j, fav_ids, fav_names),
        )
        for j in saved_jobs
    ]
    return DiscoverResultResponse(
        source_kind=payload.source_kind,
        fetched_count=len(raw_jobs),
        created_count=created_count,
        updated_count=updated_count,
        jobs=responses,
    )


@router.post("/manual", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
def create_manual_job(
    payload: ManualJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    src = _get_or_create_source(db, payload.source_name.strip() or "Manual", "manual")
    reqs = [
        {"requirement_type": "mandatory", "text": r} for r in payload.mandatory_requirements if r.strip()
    ] + [
        {"requirement_type": "desirable", "text": r} for r in payload.desirable_requirements if r.strip()
    ] + [
        {"requirement_type": "eliminatory", "text": r} for r in payload.eliminatory_requirements if r.strip()
    ]
    if not reqs:
        reqs = extract_requirements(payload.description)

    posting, _ = _upsert_job_posting(
        db,
        source_id=src.id,
        company_id=None,
        item={
            "external_id": None,
            "company_name": payload.company_name.strip(),
            "title": payload.title.strip(),
            "description": payload.description.strip(),
            "original_url": payload.original_url.strip(),
            "location": payload.location,
            "modality": payload.modality,
            "seniority": payload.seniority,
            "salary_range_text": payload.salary_range_text,
            "benefits": [],
            "published_at": None,
            "requirements": reqs,
        },
    )
    db.commit()
    db.refresh(posting)

    fav_ids, fav_names = _user_favorite_company_ids(db, current_user.id)
    req_rows = db.query(JobRequirement).filter(JobRequirement.job_posting_id == posting.id).all()
    return JobPostingResponse(
        id=posting.id,
        company_name=posting.company_name,
        title=posting.title,
        description=posting.description,
        original_url=posting.original_url,
        location=posting.location,
        modality=posting.modality,
        seniority=posting.seniority,
        salary_range_text=posting.salary_range_text,
        availability_status=posting.availability_status,
        published_at=posting.published_at,
        discovered_at=posting.discovered_at,
        is_favorite_company=_is_fav_job(posting, fav_ids, fav_names),
        requirements=[JobRequirementResponse.model_validate(r) for r in req_rows],
    )


@router.get("", response_model=List[JobPostingResponse])
def list_jobs(
    q: str = Query(default="", max_length=120),
    modality: Optional[str] = Query(default=None),
    only_favorites: bool = Query(default=False),
    respect_preferences: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(JobPosting).filter(JobPosting.availability_status == "active")
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            (JobPosting.title.ilike(term)) | (JobPosting.company_name.ilike(term))
        )
    if modality:
        query = query.filter(JobPosting.modality == modality)

    jobs = query.order_by(JobPosting.discovered_at.desc()).limit(100).all()
    fav_ids, fav_names = _user_favorite_company_ids(db, current_user.id)
    roles = (
        db.query(TargetRole)
        .filter(TargetRole.user_id == current_user.id, TargetRole.status == "ativo")
        .all()
        if respect_preferences
        else []
    )
    pref = (
        db.query(CareerPreference)
        .filter(CareerPreference.user_id == current_user.id)
        .first()
        if respect_preferences
        else None
    )

    results: List[JobPostingResponse] = []
    for j in jobs:
        is_fav = _is_fav_job(j, fav_ids, fav_names)
        if only_favorites and not is_fav:
            continue
        if respect_preferences and not _job_matches_preferences(
            j.title, j.location, j.modality, roles, pref
        ):
            continue
        results.append(
            JobPostingResponse(
                id=j.id,
                company_name=j.company_name,
                title=j.title,
                description=j.description,
                original_url=j.original_url,
                location=j.location,
                modality=j.modality,
                seniority=j.seniority,
                salary_range_text=j.salary_range_text,
                availability_status=j.availability_status,
                published_at=j.published_at,
                discovered_at=j.discovered_at,
                is_favorite_company=is_fav,
            )
        )
    return results


@router.get("/{job_id}", response_model=JobPostingResponse)
def get_job_detail(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada.")

    fav_ids, fav_names = _user_favorite_company_ids(db, current_user.id)
    req_rows = db.query(JobRequirement).filter(JobRequirement.job_posting_id == job.id).all()
    return JobPostingResponse(
        id=job.id,
        company_name=job.company_name,
        title=job.title,
        description=job.description,
        original_url=job.original_url,
        location=job.location,
        modality=job.modality,
        seniority=job.seniority,
        salary_range_text=job.salary_range_text,
        availability_status=job.availability_status,
        published_at=job.published_at,
        discovered_at=job.discovered_at,
        is_favorite_company=_is_fav_job(job, fav_ids, fav_names),
        requirements=[JobRequirementResponse.model_validate(r) for r in req_rows],
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada.")

    db.query(JobMatch).filter(
        JobMatch.user_id == current_user.id,
        JobMatch.job_posting_id == job_id,
    ).delete()
    job.availability_status = "archived"
    db.commit()
    return None


@router.post("/company-watch/run", response_model=CompanyWatchRunResponse)
def run_company_watch(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Monitors favorite companies' career URLs using authorized public connectors."""
    favs = (
        db.query(FavoriteCompany)
        .options(joinedload(FavoriteCompany.company))
        .filter(FavoriteCompany.user_id == current_user.id)
        .all()
    )

    agent_run = AgentRun(
        user_id=current_user.id,
        agent_name="company_watch",
        trigger_type="on_demand",
        status="running",
    )
    db.add(agent_run)
    db.flush()

    results: List[CompanyWatchCompanyResult] = []
    monitored_count = 0
    error_count = 0
    total_jobs_found = 0

    for fav in favs:
        comp = fav.company
        url = comp.careers_page_url
        if not url:
            fav.monitoring_status = "cadastrada"
            results.append(
                CompanyWatchCompanyResult(
                    favorite_company_id=fav.id,
                    company_name=comp.name,
                    careers_page_url=None,
                    status="cadastrada",
                    jobs_found=0,
                    error_message="Página de carreiras não informada; cadastre a URL para monitorar.",
                )
            )
            continue

        source_type, target = detect_connector_from_url(url)
        career_source = (
            db.query(CompanyCareerSource)
            .filter(
                CompanyCareerSource.company_id == comp.id,
                CompanyCareerSource.source_url == url,
            )
            .first()
        )
        if not career_source:
            career_source = CompanyCareerSource(
                company_id=comp.id,
                source_type=source_type,
                source_url=url,
            )
            db.add(career_source)
            db.flush()

        mon_run = CompanyMonitoringRun(career_source_id=career_source.id, status="running")
        db.add(mon_run)
        db.flush()

        try:
            if source_type == "greenhouse":
                raw_jobs = fetch_greenhouse_jobs(target, comp.name)
                src = _get_or_create_source(db, "Greenhouse", "greenhouse")
            elif source_type == "lever":
                raw_jobs = fetch_lever_jobs(target, comp.name)
                src = _get_or_create_source(db, "Lever", "lever")
            else:
                raw_jobs = fetch_jsonld_jobs(target, comp.name)
                src = _get_or_create_source(db, "JSON-LD Carreiras", "jsonld")

            for item in raw_jobs:
                _upsert_job_posting(db, source_id=src.id, company_id=comp.id, item=item)

            career_source.is_verified = True
            career_source.monitorable = True
            career_source.integration_status = "monitorada"
            career_source.last_error = None
            fav.monitoring_status = "monitorada"

            mon_run.status = "completed"
            mon_run.jobs_found = len(raw_jobs)
            mon_run.finished_at = datetime.now(timezone.utc)

            monitored_count += 1
            total_jobs_found += len(raw_jobs)
            results.append(
                CompanyWatchCompanyResult(
                    favorite_company_id=fav.id,
                    company_name=comp.name,
                    careers_page_url=url,
                    status="monitorada",
                    jobs_found=len(raw_jobs),
                )
            )
        except Exception as exc:
            err_msg = f"Fonte inacessível para automação ({exc}). Consulte manualmente pelo link."
            career_source.monitorable = False
            career_source.integration_status = "erro_integracao"
            career_source.last_error = err_msg
            fav.monitoring_status = "erro_integracao"

            mon_run.status = "failed"
            mon_run.error_message = err_msg
            mon_run.finished_at = datetime.now(timezone.utc)

            error_count += 1
            results.append(
                CompanyWatchCompanyResult(
                    favorite_company_id=fav.id,
                    company_name=comp.name,
                    careers_page_url=url,
                    status="erro_integracao",
                    jobs_found=0,
                    error_message=err_msg,
                )
            )

    agent_run.status = "completed"
    agent_run.finished_at = datetime.now(timezone.utc)
    db.commit()

    return CompanyWatchRunResponse(
        monitored_count=monitored_count,
        error_count=error_count,
        total_jobs_found=total_jobs_found,
        results=results,
    )


@router.post("/matching/run", response_model=List[JobMatchResponse])
def run_matching_engine(
    weights: Optional[MatchingWeights] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    experiences = (
        db.query(ProfessionalExperience)
        .filter(ProfessionalExperience.user_id == current_user.id)
        .all()
    )
    skills = db.query(VerifiedSkill).filter(VerifiedSkill.user_id == current_user.id).all()
    target_roles = db.query(TargetRole).filter(TargetRole.user_id == current_user.id).all()
    preferences = (
        db.query(CareerPreference).filter(CareerPreference.user_id == current_user.id).first()
    )

    fav_ids, fav_names = _user_favorite_company_ids(db, current_user.id)
    active_jobs = (
        db.query(JobPosting)
        .filter(JobPosting.availability_status == "active")
        .order_by(JobPosting.discovered_at.desc())
        .limit(100)
        .all()
    )

    agent_run = AgentRun(
        user_id=current_user.id,
        agent_name="job_matching",
        trigger_type="on_demand",
        status="running",
    )
    db.add(agent_run)
    db.flush()

    weights_dict = weights.model_dump() if weights else None
    responses: List[JobMatchResponse] = []

    for job in active_jobs:
        reqs = db.query(JobRequirement).filter(JobRequirement.job_posting_id == job.id).all()
        is_fav = _is_fav_job(job, fav_ids, fav_names)
        eval_res = evaluate_job_match(
            job=job,
            requirements=reqs,
            profile=profile,
            experiences=experiences,
            skills=skills,
            target_roles=target_roles,
            preferences=preferences,
            is_favorite_company=is_fav,
            weights=weights_dict,
        )

        match_row = (
            db.query(JobMatch)
            .filter(
                JobMatch.user_id == current_user.id,
                JobMatch.job_posting_id == job.id,
            )
            .first()
        )
        if not match_row:
            match_row = JobMatch(
                user_id=current_user.id,
                job_posting_id=job.id,
                total_score=eval_res["total_score"],
                classification=eval_res["classification"],
                is_eligible=eval_res["is_eligible"],
                dimension_scores_json=eval_res["dimension_scores"],
                explanation_json=eval_res["explanation"],
                confidence_level=eval_res["confidence_level"],
            )
            db.add(match_row)
            db.flush()
        else:
            match_row.total_score = eval_res["total_score"]
            match_row.classification = eval_res["classification"]
            match_row.is_eligible = eval_res["is_eligible"]
            match_row.dimension_scores_json = eval_res["dimension_scores"]
            match_row.explanation_json = eval_res["explanation"]
            match_row.confidence_level = eval_res["confidence_level"]

        responses.append(
            JobMatchResponse(
                id=match_row.id,
                job_posting_id=job.id,
                company_name=job.company_name,
                job_title=job.title,
                original_url=job.original_url,
                location=job.location,
                modality=job.modality,
                seniority=job.seniority,
                is_favorite_company=is_fav,
                total_score=match_row.total_score,
                priority_score=eval_res["priority_score"],
                classification=match_row.classification,
                is_eligible=match_row.is_eligible,
                confidence_level=match_row.confidence_level,
                dimension_scores=match_row.dimension_scores_json,
                explanation=match_row.explanation_json,
            )
        )

    agent_run.status = "completed"
    agent_run.finished_at = datetime.now(timezone.utc)
    db.commit()

    responses.sort(key=lambda r: (r.is_eligible, r.priority_score, r.total_score), reverse=True)
    return responses


@router.get("/matches/list", response_model=List[JobMatchResponse])
def list_job_matches(
    only_favorites: bool = Query(default=False),
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    include_ineligible: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(JobMatch, JobPosting)
        .join(JobPosting, JobMatch.job_posting_id == JobPosting.id)
        .filter(JobMatch.user_id == current_user.id)
        .all()
    )
    fav_ids, fav_names = _user_favorite_company_ids(db, current_user.id)

    results: List[JobMatchResponse] = []
    for match_row, job in rows:
        if not include_ineligible and not match_row.is_eligible:
            continue
        if match_row.total_score < min_score:
            continue
        is_fav = _is_fav_job(job, fav_ids, fav_names)
        if only_favorites and not is_fav:
            continue
        priority_score = (
            round(match_row.total_score + (10.0 if is_fav else 0.0), 2)
            if match_row.is_eligible
            else 0.0
        )
        results.append(
            JobMatchResponse(
                id=match_row.id,
                job_posting_id=job.id,
                company_name=job.company_name,
                job_title=job.title,
                original_url=job.original_url,
                location=job.location,
                modality=job.modality,
                seniority=job.seniority,
                is_favorite_company=is_fav,
                total_score=match_row.total_score,
                priority_score=priority_score,
                classification=match_row.classification,
                is_eligible=match_row.is_eligible,
                confidence_level=match_row.confidence_level,
                dimension_scores=match_row.dimension_scores_json,
                explanation=match_row.explanation_json,
            )
        )

    results.sort(key=lambda r: (r.is_eligible, r.priority_score, r.total_score), reverse=True)
    return results
