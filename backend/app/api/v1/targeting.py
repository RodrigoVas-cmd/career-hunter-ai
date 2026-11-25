import csv
import io
import re
import unicodedata
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.targeting import Company, FavoriteCompany, TargetRole
from app.models.user import ProfessionalExperience, User, VerifiedSkill
from app.schemas.targeting import (
    CSVImportResult,
    CompanyInfo,
    FavoriteCompanyCreate,
    FavoriteCompanyResponse,
    FavoriteCompanyUpdate,
    TargetRoleCreate,
    TargetRoleResponse,
    TargetRoleSuggestion,
    TargetRoleUpdate,
)

router = APIRouter(prefix="/targeting", tags=["Cargos-Alvo & Minhas Empresas"])


def _normalize_company_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


# --- Cargos-Alvo ---

@router.get("/roles", response_model=List[TargetRoleResponse])
def list_target_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(TargetRole)
        .filter(TargetRole.user_id == current_user.id)
        .order_by(TargetRole.created_at.desc())
        .all()
    )


@router.post("/roles", response_model=TargetRoleResponse, status_code=status.HTTP_201_CREATED)
def create_target_role(
    payload: TargetRoleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = TargetRole(
        user_id=current_user.id,
        is_ai_suggested=False,
        user_approved=True,
        **payload.model_dump(),
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.patch("/roles/{role_id}", response_model=TargetRoleResponse)
def update_target_role(
    role_id: str,
    payload: TargetRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = (
        db.query(TargetRole)
        .filter(TargetRole.id == role_id, TargetRole.user_id == current_user.id)
        .first()
    )
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo-alvo não encontrado.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target_role(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = (
        db.query(TargetRole)
        .filter(TargetRole.id == role_id, TargetRole.user_id == current_user.id)
        .first()
    )
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo-alvo não encontrado.")
    db.delete(role)
    db.commit()


@router.get("/roles/suggestions", response_model=List[TargetRoleSuggestion])
def suggest_target_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Suggests correlated roles grounded strictly in the user's verified/extracted experiences and skills.
    Suggestions are never added automatically without user approval.
    """
    experiences = (
        db.query(ProfessionalExperience)
        .filter(ProfessionalExperience.user_id == current_user.id)
        .all()
    )
    skills = (
        db.query(VerifiedSkill)
        .filter(VerifiedSkill.user_id == current_user.id)
        .all()
    )
    existing_titles = {
        r.title.lower()
        for r in db.query(TargetRole).filter(TargetRole.user_id == current_user.id).all()
    }

    suggestions: List[TargetRoleSuggestion] = []
    for exp in experiences:
        title_lower = exp.role_title.lower()
        if exp.role_title.lower() not in existing_titles:
            suggestions.append(
                TargetRoleSuggestion(
                    title=exp.role_title,
                    justification=f"Baseado diretamente na sua experiência como {exp.role_title} em {exp.company_name}.",
                    based_on_evidence=f"Experiência: {exp.role_title} ({exp.company_name})",
                    synonyms=[],
                )
            )
            existing_titles.add(title_lower)

        if any(k in title_lower for k in ["analista", "desenvolvedor", "engenheiro", "product", "dados"]):
            if exp.leadership_experience and f"coordenador de {exp.role_title}".lower() not in existing_titles:
                suggestions.append(
                    TargetRoleSuggestion(
                        title=f"Líder / Coordenador ({exp.role_title})",
                        justification="Seu histórico indica atuação com liderança na função.",
                        based_on_evidence=f"Liderança registrada em {exp.company_name}",
                        synonyms=["Tech Lead", "Coordenador"],
                    )
                )

    if not suggestions and skills:
        top_skills = ", ".join(s.name for s in skills[:3])
        suggestions.append(
            TargetRoleSuggestion(
                title="Especialista na área principal",
                justification=f"Sugestão baseada nas competências registradas: {top_skills}.",
                based_on_evidence=f"Competências: {top_skills}",
                synonyms=[],
            )
        )

    return suggestions[:5]


# --- Minhas Empresas (Empresas Preferidas) ---

COMPANY_DIRECTORY_SEED = [
    {"name": "Vedacit", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Indústria Química / Construção Civil", "official_website": "https://www.vedacit.com.br", "careers_page_url": "https://vedacit.gupy.io"},
    {"name": "Vedacit", "city": "Salvador", "state": "BA", "country": "Brasil", "sector": "Indústria Química / Construção Civil", "official_website": "https://www.vedacit.com.br", "careers_page_url": "https://vedacit.gupy.io"},
    {"name": "Dexco (Duratex)", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Materiais de Construção / Deca", "official_website": "https://www.dex.co", "careers_page_url": "https://dexco.gupy.io"},
    {"name": "Dexco (Duratex)", "city": "Jundiaí", "state": "SP", "country": "Brasil", "sector": "Materiais de Construção / Deca", "official_website": "https://www.dex.co", "careers_page_url": "https://dexco.gupy.io"},
    {"name": "Eternit S/A", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Materiais de Construção", "official_website": "https://www.eternit.com.br", "careers_page_url": "https://eternit.gupy.io"},
    {"name": "Saint-Gobain", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Materiais de Construção", "official_website": "https://www.saint-gobain.com.br", "careers_page_url": "https://saintgobain.gupy.io"},
    {"name": "Tigre", "city": "Joinville", "state": "SC", "country": "Brasil", "sector": "Materiais de Construção", "official_website": "https://www.tigre.com.br", "careers_page_url": "https://tigre.gupy.io"},
    {"name": "WEG", "city": "Jaraguá do Sul", "state": "SC", "country": "Brasil", "sector": "Equipamentos Elétricos / Indústria", "official_website": "https://www.weg.net", "careers_page_url": "https://www.weg.net/institutional/BR/pt/people-and-careers"},
    {"name": "Gerdau", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Siderurgia", "official_website": "https://www2.gerdau.com.br", "careers_page_url": "https://gerdau.gupy.io"},
    {"name": "Votorantim Cimentos", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Materiais de Construção", "official_website": "https://www.votorantimcimentos.com.br", "careers_page_url": "https://votorantimcimentos.gupy.io"},
    {"name": "Ambev", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Bebidas / Bens de Consumo", "official_website": "https://www.ambev.com.br", "careers_page_url": "https://ambev.gupy.io"},
    {"name": "Ambev", "city": "Jaguariúna", "state": "SP", "country": "Brasil", "sector": "Bebidas / Bens de Consumo", "official_website": "https://www.ambev.com.br", "careers_page_url": "https://ambev.gupy.io"},
    {"name": "Embraer", "city": "São José dos Campos", "state": "SP", "country": "Brasil", "sector": "Aeroespacial", "official_website": "https://embraer.com", "careers_page_url": "https://embraer.gupy.io"},
    {"name": "Bosch", "city": "Campinas", "state": "SP", "country": "Brasil", "sector": "Indústria / Tecnologia", "official_website": "https://www.bosch.com.br", "careers_page_url": "https://www.bosch.com.br/carreiras"},
    {"name": "3M do Brasil", "city": "Sumaré", "state": "SP", "country": "Brasil", "sector": "Indústria Química / Manufatura", "official_website": "https://www.3m.com.br", "careers_page_url": "https://www.3m.com.br/3M/pt_BR/carreiras/"},
    {"name": "Natura", "city": "Cajamar", "state": "SP", "country": "Brasil", "sector": "Cosméticos e Beleza / Bens de Consumo", "official_website": "https://www.natura.com.br", "careers_page_url": "https://natura.gupy.io"},
    {"name": "Avon", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Cosméticos e Beleza / Bens de Consumo", "official_website": "https://www.avon.com.br", "careers_page_url": "https://natura.gupy.io"},
    {"name": "Grupo Boticário", "city": "São José dos Pinhais", "state": "PR", "country": "Brasil", "sector": "Cosméticos e Beleza / Varejo", "official_website": "https://www.grupoboticario.com.br", "careers_page_url": "https://grupoboticario.gupy.io"},
    {"name": "L'Oréal Brasil", "city": "Rio de Janeiro", "state": "RJ", "country": "Brasil", "sector": "Cosméticos e Beleza", "official_website": "https://www.loreal.com.br", "careers_page_url": "https://careers.loreal.com"},
    {"name": "EMS", "city": "Hortolândia", "state": "SP", "country": "Brasil", "sector": "Saúde e Farmacêutica", "official_website": "https://www.ems.com.br", "careers_page_url": "https://ems.gupy.io"},
    {"name": "Eurofarma", "city": "Itapevi", "state": "SP", "country": "Brasil", "sector": "Saúde e Farmacêutica", "official_website": "https://www.eurofarma.com.br", "careers_page_url": "https://eurofarma.gupy.io"},
    {"name": "Hypera Pharma", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Saúde e Farmacêutica", "official_website": "https://www.hypera.com.br", "careers_page_url": "https://hypera.gupy.io"},
    {"name": "Johnson & Johnson", "city": "São José dos Campos", "state": "SP", "country": "Brasil", "sector": "Saúde e Farmacêutica / Bens de Consumo", "official_website": "https://www.jnjbrasil.com.br", "careers_page_url": "https://jobs.jnj.com"},
    {"name": "Cargill", "city": "Mairinque", "state": "SP", "country": "Brasil", "sector": "Agronegócio e Alimentos", "official_website": "https://www.cargill.com.br", "careers_page_url": "https://careers.cargill.com"},
    {"name": "DHL Supply Chain", "city": "Louveira", "state": "SP", "country": "Brasil", "sector": "Logística e Supply Chain", "official_website": "https://www.dhl.com/br-pt", "careers_page_url": "https://careers.dhl.com"},
    {"name": "Suzano", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Papel e Celulose", "official_website": "https://www.suzano.com.br", "careers_page_url": "https://suzano.gupy.io"},
    {"name": "Klabin", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Papel e Celulose", "official_website": "https://klabin.com.br", "careers_page_url": "https://klabin.gupy.io"},
    {"name": "Nubank", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Tecnologia / Financeiro", "official_website": "https://nubank.com.br", "careers_page_url": "https://boards.greenhouse.io/nubank"},
    {"name": "Itaú Unibanco", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Financeiro", "official_website": "https://www.itau.com.br", "careers_page_url": "https://carreiras.itau.com.br"},
    {"name": "Mercado Livre", "city": "Osasco", "state": "SP", "country": "Brasil", "sector": "E-commerce / Tecnologia", "official_website": "https://www.mercadolivre.com.br", "careers_page_url": "https://careers-meli.mercadolibre.com"},
    {"name": "LG Electronics", "city": "Taubaté", "state": "SP", "country": "Brasil", "sector": "Eletrônicos / Manufatura", "official_website": "https://www.lg.com/br", "careers_page_url": "https://lgelectronics.gupy.io"},
    {"name": "LG Electronics", "city": "Manaus", "state": "AM", "country": "Brasil", "sector": "Eletrônicos / Manufatura", "official_website": "https://www.lg.com/br", "careers_page_url": "https://lgelectronics.gupy.io"},
    {"name": "Samsung", "city": "Campinas", "state": "SP", "country": "Brasil", "sector": "Eletrônicos / Manufatura", "official_website": "https://www.samsung.com/br", "careers_page_url": "https://sec.wd3.myworkdayjobs.com/Samsung_Careers"},
    {"name": "Samsung", "city": "Manaus", "state": "AM", "country": "Brasil", "sector": "Eletrônicos / Manufatura", "official_website": "https://www.samsung.com/br", "careers_page_url": "https://sec.wd3.myworkdayjobs.com/Samsung_Careers"},
    {"name": "Whirlpool", "city": "Joinville", "state": "SC", "country": "Brasil", "sector": "Eletrodomésticos / Manufatura", "official_website": "https://www.whirlpool.com.br", "careers_page_url": "https://whirlpool.gupy.io"},
    {"name": "Electrolux", "city": "Curitiba", "state": "PR", "country": "Brasil", "sector": "Eletrodomésticos / Manufatura", "official_website": "https://www.electrolux.com.br", "careers_page_url": "https://electrolux.gupy.io"},
    {"name": "BASF", "city": "Guaratinguetá", "state": "SP", "country": "Brasil", "sector": "Indústria Química", "official_website": "https://www.basf.com/br", "careers_page_url": "https://basf.gupy.io"},
    {"name": "Braskem", "city": "Camaçari", "state": "BA", "country": "Brasil", "sector": "Petroquímica / Indústria Química", "official_website": "https://www.braskem.com.br", "careers_page_url": "https://braskem.gupy.io"},
    {"name": "Unilever", "city": "Vinhedo", "state": "SP", "country": "Brasil", "sector": "Bens de Consumo", "official_website": "https://www.unilever.com.br", "careers_page_url": "https://unilever.gupy.io"},
    {"name": "Nestlé", "city": "São Paulo", "state": "SP", "country": "Brasil", "sector": "Alimentos / Bens de Consumo", "official_website": "https://www.nestle.com.br", "careers_page_url": "https://nestle.gupy.io"},
    {"name": "Heineken", "city": "Jacareí", "state": "SP", "country": "Brasil", "sector": "Bebidas / Bens de Consumo", "official_website": "https://www.heinekenbrasil.com.br", "careers_page_url": "https://heinekenbrasil.gupy.io"},
    {"name": "Siemens", "city": "Jundiaí", "state": "SP", "country": "Brasil", "sector": "Automação / Indústria", "official_website": "https://www.siemens.com/br", "careers_page_url": "https://jobs.siemens.com"},
    {"name": "Schneider Electric", "city": "Guararema", "state": "SP", "country": "Brasil", "sector": "Automação / Energia", "official_website": "https://www.se.com/br", "careers_page_url": "https://careers.se.com"},
    {"name": "Toyota", "city": "Sorocaba", "state": "SP", "country": "Brasil", "sector": "Automotivo", "official_website": "https://www.toyota.com.br", "careers_page_url": "https://toyota.gupy.io"},
    {"name": "Volkswagen", "city": "São Bernardo do Campo", "state": "SP", "country": "Brasil", "sector": "Automotivo", "official_website": "https://www.vw.com.br", "careers_page_url": "https://volkswagen.gupy.io"},
    {"name": "Stellantis", "city": "Betim", "state": "MG", "country": "Brasil", "sector": "Automotivo", "official_website": "https://www.stellantis.com", "careers_page_url": "https://stellantis.gupy.io"},
    {"name": "Vale", "city": "Rio de Janeiro", "state": "RJ", "country": "Brasil", "sector": "Mineração", "official_website": "https://www.vale.com", "careers_page_url": "https://vale.gupy.io"},
    {"name": "Petrobras", "city": "Rio de Janeiro", "state": "RJ", "country": "Brasil", "sector": "Óleo e Gás / Energia", "official_website": "https://petrobras.com.br", "careers_page_url": "https://petrobras.com.br/quem-somos/carreiras"},
    {"name": "Raízen", "city": "Piracicaba", "state": "SP", "country": "Brasil", "sector": "Energia / Sucroenergético", "official_website": "https://www.raizen.com.br", "careers_page_url": "https://raizen.gupy.io"},
]


def _fold(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(ch)
    )


@router.get("/companies/catalog", response_model=List[CompanyInfo])
def search_company_catalog(
    q: str = Query(default="", max_length=120),
    sector: str = Query(default="", max_length=120),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    term = q.strip()
    sec = sector.strip()
    query = db.query(Company)
    if term:
        query = query.filter(Company.name.ilike(f"%{term}%"))
    if sec:
        query = query.filter(Company.sector.ilike(f"%{sec}%"))
    db_matches = query.order_by(Company.name.asc()).limit(10).all()

    results: List[CompanyInfo] = [CompanyInfo.model_validate(c) for c in db_matches]
    seen = {(c.name.lower(), (c.city or "").lower()) for c in results}

    if term or sec:
        low_q = _fold(term)
        low_s = _fold(sec)
        for idx, item in enumerate(COMPANY_DIRECTORY_SEED):
            match_q = not low_q or low_q in _fold(item["name"]) or low_q in _fold(item["city"] or "")
            match_s = not low_s or low_s in _fold(item["sector"] or "")
            if match_q and match_s:
                key = (item["name"].lower(), (item["city"] or "").lower())
                if key not in seen:
                    seen.add(key)
                    results.append(
                        CompanyInfo(
                            id=f"seed-{idx}",
                            name=item["name"],
                            official_website=item["official_website"],
                            careers_page_url=item["careers_page_url"],
                            city=item["city"],
                            state=item["state"],
                            country=item["country"],
                            sector=item["sector"],
                        )
                    )
    return results[:12]


@router.get("/companies", response_model=List[FavoriteCompanyResponse])
def list_favorite_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(FavoriteCompany)
        .options(joinedload(FavoriteCompany.company))
        .filter(FavoriteCompany.user_id == current_user.id)
        .order_by(FavoriteCompany.created_at.desc())
        .all()
    )


def _get_or_create_company(db: Session, payload: FavoriteCompanyCreate) -> Company:
    norm = _normalize_company_name(payload.name)
    company = db.query(Company).filter(Company.normalized_name == norm).first()
    if not company:
        company = Company(
            name=payload.name.strip(),
            normalized_name=norm,
            official_website=payload.official_website,
            careers_page_url=payload.careers_page_url,
            city=payload.city,
            state=payload.state,
            country=payload.country,
            sector=payload.sector,
        )
        db.add(company)
        db.flush()
    return company


@router.post("/companies", response_model=FavoriteCompanyResponse, status_code=status.HTTP_201_CREATED)
def add_favorite_company(
    payload: FavoriteCompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = _get_or_create_company(db, payload)
    existing = (
        db.query(FavoriteCompany)
        .filter(
            FavoriteCompany.user_id == current_user.id,
            FavoriteCompany.company_id == company.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta empresa já está na sua lista de empresas preferidas.",
        )

    fav = FavoriteCompany(
        user_id=current_user.id,
        company_id=company.id,
        priority=payload.priority,
        roles_of_interest=payload.roles_of_interest,
        departments=payload.departments,
        notes=payload.notes,
        monitoring_status="cadastrada",
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return (
        db.query(FavoriteCompany)
        .options(joinedload(FavoriteCompany.company))
        .filter(FavoriteCompany.id == fav.id)
        .first()
    )


@router.post("/companies/import-csv", response_model=CSVImportResult)
async def import_companies_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Envie um arquivo .csv válido.")

    raw = (await file.read()).decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))

    imported = 0
    skipped = 0
    errors: List[str] = []

    for idx, row in enumerate(reader, start=2):
        name = (row.get("name") or row.get("empresa") or row.get("nome") or "").strip()
        if not name:
            skipped += 1
            errors.append(f"Linha {idx}: coluna 'nome'/'empresa' vazia.")
            continue

        priority = (row.get("priority") or row.get("prioridade") or "media").strip().lower()
        if priority not in {"alta", "media", "baixa"}:
            priority = "media"

        payload = FavoriteCompanyCreate(
            name=name,
            official_website=(row.get("website") or row.get("site") or None),
            careers_page_url=(row.get("careers_url") or row.get("carreiras") or None),
            city=(row.get("city") or row.get("cidade") or None),
            state=(row.get("state") or row.get("estado") or None),
            sector=(row.get("sector") or row.get("setor") or None),
            priority=priority,
        )
        company = _get_or_create_company(db, payload)
        exists = (
            db.query(FavoriteCompany)
            .filter(
                FavoriteCompany.user_id == current_user.id,
                FavoriteCompany.company_id == company.id,
            )
            .first()
        )
        if exists:
            skipped += 1
            continue

        db.add(
            FavoriteCompany(
                user_id=current_user.id,
                company_id=company.id,
                priority=priority,
                monitoring_status="cadastrada",
            )
        )
        imported += 1

    db.commit()
    return CSVImportResult(imported_count=imported, skipped_count=skipped, errors=errors)


@router.patch("/companies/{favorite_id}", response_model=FavoriteCompanyResponse)
def update_favorite_company(
    favorite_id: str,
    payload: FavoriteCompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fav = (
        db.query(FavoriteCompany)
        .options(joinedload(FavoriteCompany.company))
        .filter(
            FavoriteCompany.id == favorite_id,
            FavoriteCompany.user_id == current_user.id,
        )
        .first()
    )
    if not fav:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa favorita não encontrada.")

    data = payload.model_dump(exclude_unset=True)
    if "careers_page_url" in data:
        fav.company.careers_page_url = data.pop("careers_page_url")
    for field, value in data.items():
        setattr(fav, field, value)

    db.commit()
    db.refresh(fav)
    return fav


@router.delete("/companies/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorite_company(
    favorite_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fav = (
        db.query(FavoriteCompany)
        .filter(
            FavoriteCompany.id == favorite_id,
            FavoriteCompany.user_id == current_user.id,
        )
        .first()
    )
    if not fav:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa favorita não encontrada.")
    db.delete(fav)
    db.commit()
