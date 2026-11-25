import io
import re
from typing import Any, Dict, List, Optional, Tuple

from docx import Document
from pypdf import PdfReader

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9?\d{4}[-.\s]?\d{4})")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?", re.IGNORECASE)
DATE_RANGE_RE = re.compile(
    r"((?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?[/\s.-]*(?:19|20)\d{2})\s*[-–aàaté]+\s*((?:atual|presente|present|current|hoje)|(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?[/\s.-]*(?:19|20)\d{2})",
    re.IGNORECASE,
)

SECTION_ALIASES = {
    "summary": ["resumo", "sobre", "perfil profissional", "objetivo", "summary", "about"],
    "experience": [
        "experiência",
        "experiências",
        "experiência profissional",
        "histórico profissional",
        "work experience",
        "experience",
    ],
    "education": ["formação", "formação acadêmica", "educação", "academic", "education"],
    "skills": [
        "competências",
        "habilidades",
        "skills",
        "tecnologias",
        "conhecimentos",
        "hard skills",
        "soft skills",
    ],
    "certifications": ["certificações", "certificados", "certifications", "cursos"],
    "languages": ["idiomas", "línguas", "languages"],
    "projects": ["projetos", "projects"],
}


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return "\n".join(pages).strip()


def extract_text_from_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    lines: List[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            lines.append(para.text.strip())
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                lines.append(row_text)
    return "\n".join(lines).strip()


def _detect_section(line: str) -> str | None:
    cleaned = re.sub(r"[:\-•*#]+", "", line).strip().lower()
    if len(cleaned) > 45:
        return None
    for section_key, aliases in SECTION_ALIASES.items():
        if cleaned in aliases:
            return section_key
    return None


def _split_sections(raw_text: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {"header": []}
    current = "header"
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        detected = _detect_section(line)
        if detected:
            current = detected
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def parse_resume_bytes(content: bytes, file_format: str) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Extracts structured information strictly from the provided resume bytes.
    Flags ambiguous entries rather than guessing or inventing facts.
    """
    if file_format == "pdf":
        raw_text = extract_text_from_pdf(content)
    elif file_format == "docx":
        raw_text = extract_text_from_docx(content)
    else:
        raise ValueError(f"Formato não suportado: {file_format}")

    ambiguities: List[Dict[str, Any]] = []
    if not raw_text:
        ambiguities.append({
            "field": "document",
            "message": "Não foi possível extrair texto legível do arquivo (pode ser PDF digitalizado como imagem).",
            "excerpt": "",
        })
        return "", {"experiences": [], "skills": [], "education": [], "certifications": [], "languages": []}, ambiguities

    sections = _split_sections(raw_text)

    emails = EMAIL_RE.findall(raw_text)
    phones = PHONE_RE.findall(raw_text)
    linkedins = LINKEDIN_RE.findall(raw_text)

    experiences: List[Dict[str, Any]] = []
    exp_lines = sections.get("experience", [])
    current_exp: Dict[str, Any] | None = None
    pending_company_header: Tuple[str, Optional[str], str] | None = None

    ROLE_HINT_RE = re.compile(
        r"\b(analista|consultor|gerente|gestor|coordenador|diretor|desenvolvedor|engenheiro|especialista|supervisor|estagi[áa]rio|l[íi]der|head|manager|developer|engineer|analyst)\b",
        re.IGNORECASE,
    )

    idx = 0
    while idx < len(exp_lines):
        line = exp_lines[idx]
        date_match = DATE_RANGE_RE.search(line)
        has_separator = any(sep in line for sep in [" | ", " - ", " — ", " na ", " at "])
        is_bullet = line.startswith(("•", "-", "*", "▪"))
        looks_like_standalone_role = (
            not is_bullet
            and not line.endswith(".")
            and len(line) < 60
            and bool(ROLE_HINT_RE.search(line))
        )

        # Lookahead: "Company — Sector" followed by "Role | Period"
        next_line = exp_lines[idx + 1] if idx + 1 < len(exp_lines) else ""
        next_has_date = bool(DATE_RANGE_RE.search(next_line))
        if (
            not date_match
            and not is_bullet
            and has_separator
            and len(line) < 120
            and next_has_date
            and not looks_like_standalone_role
        ):
            comp_name = line
            sector_val = None
            for sep in [" — ", " | ", " - "]:
                if sep in line:
                    parts = [p.strip() for p in line.split(sep, 1)]
                    comp_name = parts[0] or line
                    sector_val = parts[1] or None
                    break
            pending_company_header = (comp_name, sector_val, line)
            idx += 1
            continue

        if date_match or (not is_bullet and has_separator and len(line) < 120) or looks_like_standalone_role:
            if current_exp:
                experiences.append(current_exp)

            period_text = date_match.group(0).strip() if date_match else None
            title_part = DATE_RANGE_RE.sub("", line).strip(" |-–—")

            role_title = title_part
            company_name = "Empresa não identificada"
            sector_val = None
            evidence_line = line
            ambig_note = None

            if pending_company_header:
                company_name, sector_val, header_line = pending_company_header
                role_title = title_part or "Cargo não especificado"
                evidence_line = f"{header_line} | {line}"
                pending_company_header = None
            else:
                for sep in [" | ", " — ", " - ", " na ", " em ", " at "]:
                    if sep in title_part:
                        parts = [p.strip() for p in title_part.split(sep, 1)]
                        # If second part looks like a role, swap (e.g. "Dexco — Supervisor de Produção")
                        if ROLE_HINT_RE.search(parts[1]) and not ROLE_HINT_RE.search(parts[0]):
                            company_name, role_title = parts[0], parts[1]
                        else:
                            role_title, company_name = parts[0] or role_title, parts[1] or company_name
                        break

            if company_name == "Empresa não identificada":
                ambig_note = "Empresa não identificada claramente na linha; confirme o nome da empresa."
                ambiguities.append({
                    "field": "experience.company_name",
                    "message": ambig_note,
                    "excerpt": evidence_line,
                })
            if not period_text:
                period_note = "Período (início/fim) não identificado automaticamente; informe as datas."
                ambig_note = f"{ambig_note} {period_note}".strip() if ambig_note else period_note
                ambiguities.append({
                    "field": "experience.period",
                    "message": period_note,
                    "excerpt": evidence_line,
                })

            is_current = bool(period_text and any(k in period_text.lower() for k in ["atual", "presente", "present", "current", "hoje"]))
            leadership = any(k in role_title.lower() for k in ["líder", "lider", "lead", "gerente", "gestor", "coordenador", "diretor", "head", "manager", "supervisor"])

            current_exp = {
                "company_name": company_name[:200],
                "role_title": (role_title or "Cargo não especificado")[:200],
                "sector": sector_val[:120] if sector_val else None,
                "raw_period_text": period_text,
                "is_current": is_current,
                "responsibilities": "",
                "leadership_experience": leadership,
                "evidence_excerpt": evidence_line,
                "ambiguity_note": ambig_note,
            }
        elif current_exp:
            clean_line = line.lstrip("•-*▪ ").strip()
            current_exp["responsibilities"] = (
                f"{current_exp['responsibilities']}\n{clean_line}".strip()
                if current_exp["responsibilities"]
                else clean_line
            )
        idx += 1

    if current_exp:
        experiences.append(current_exp)

    if not experiences and exp_lines:
        ambiguities.append({
            "field": "experiences",
            "message": "Seção de experiência detectada, mas o formato não permitiu separar cargos automaticamente. Revise manualmente.",
            "excerpt": " | ".join(exp_lines[:3]),
        })

    skills: List[Dict[str, Any]] = []
    seen_skills = set()
    for line in sections.get("skills", []):
        tokens = re.split(r"[,;•|]+", line)
        for token in tokens:
            name = token.strip(" .-*")
            if 2 <= len(name) <= 60 and name.lower() not in seen_skills:
                seen_skills.add(name.lower())
                skills.append({
                    "name": name,
                    "category": "technical",
                    "evidence_excerpt": line,
                })

    education = [{"raw": line} for line in sections.get("education", [])]
    certifications = [{"raw": line} for line in sections.get("certifications", [])]
    languages = [{"raw": line} for line in sections.get("languages", [])]
    projects = [{"raw": line} for line in sections.get("projects", [])]

    summary_text = "\n".join(sections.get("summary", []))
    headline = sections["header"][1] if len(sections.get("header", [])) > 1 else None

    extracted_data = {
        "contact": {
            "email": emails[0] if emails else None,
            "phone": phones[0] if phones else None,
            "linkedin_url": linkedins[0] if linkedins else None,
        },
        "headline": headline,
        "summary": summary_text or None,
        "experiences": experiences,
        "skills": skills,
        "education": education,
        "certifications": certifications,
        "languages": languages,
        "projects": projects,
    }
    return raw_text, extracted_data, ambiguities


def _norm_company(name: str) -> str:
    cleaned = re.sub(r"\b(s/?a|ltda|inc|corp|divis[ãa]o|grupo)\b", "", name.lower())
    return re.sub(r"[^a-z0-9]+", " ", cleaned).strip()


def _norm_period(period: Optional[str]) -> str:
    if not period:
        return ""
    return re.sub(r"[\s–—-]+", "-", period.lower().strip())


def compare_cv_with_linkedin(
    cv_experiences: List[Dict[str, Any]],
    linkedin_experiences: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compares start/end periods between CV and LinkedIn PDF without altering any facts.
    """
    divergences: List[Dict[str, Any]] = []
    matched_companies: List[str] = []
    only_in_cv: List[Dict[str, Any]] = []
    only_in_linkedin: List[Dict[str, Any]] = []

    li_by_comp: Dict[str, List[Dict[str, Any]]] = {}
    for item in linkedin_experiences:
        key = _norm_company(item.get("company_name", ""))
        if key:
            li_by_comp.setdefault(key, []).append(item)

    matched_li_keys = set()
    for cv_item in cv_experiences:
        cv_comp = cv_item.get("company_name", "")
        key = _norm_company(cv_comp)
        if not key or key not in li_by_comp:
            only_in_cv.append({
                "company_name": cv_comp,
                "role_title": cv_item.get("role_title"),
                "period": cv_item.get("raw_period_text"),
            })
            continue

        matched_li_keys.add(key)
        matched_companies.append(cv_comp)
        li_items = li_by_comp[key]
        cv_period = _norm_period(cv_item.get("raw_period_text"))

        # Compare against best matching role at same company
        best_li = li_items[0]
        for cand in li_items:
            if (cand.get("role_title") or "").lower() == (cv_item.get("role_title") or "").lower():
                best_li = cand
                break

        li_period = _norm_period(best_li.get("raw_period_text"))
        if cv_period != li_period:
            divergences.append({
                "company_name": cv_comp,
                "role_title": cv_item.get("role_title"),
                "cv_period": cv_item.get("raw_period_text") or "Não informado no CV",
                "linkedin_period": best_li.get("raw_period_text") or "Não informado no LinkedIn",
                "message": "Divergência de datas de início/fim entre o currículo e o LinkedIn.",
            })

    for key, items in li_by_comp.items():
        if key not in matched_li_keys:
            for item in items:
                only_in_linkedin.append({
                    "company_name": item.get("company_name"),
                    "role_title": item.get("role_title"),
                    "period": item.get("raw_period_text"),
                })

    return {
        "matched_count": len(matched_companies),
        "divergences": divergences,
        "only_in_cv": only_in_cv,
        "only_in_linkedin": only_in_linkedin,
    }


ATS_COMPETENCY_CATALOG = [
    "Gestão de Produção",
    "Manufatura Enxuta",
    "Lean Manufacturing",
    "Kaizen",
    "5S",
    "Six Sigma",
    "PCP",
    "Planejamento e Controle da Produção",
    "Gestão de Qualidade",
    "Controle de Qualidade",
    "ISO 9001",
    "KPIs",
    "Indicadores de Desempenho",
    "Melhoria Contínua",
    "Gestão de Equipes",
    "Liderança",
    "Redução de Custos",
    "Segurança do Trabalho",
    "Manutenção Industrial",
    "TPM",
    "SAP",
    "ERP",
    "Excel",
    "Power BI",
    "SQL",
    "Python",
    "Product Management",
    "Scrum",
    "Kanban",
    "OKRs",
    "Supply Chain",
    "Logística",
    "Compras",
]


def analyze_profile_for_ats(
    *,
    summary: Optional[str],
    experiences: List[Dict[str, Any]],
    skills: List[str],
    raw_texts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Provides honest, actionable ATS algorithm alignment suggestions based solely
    on existing profile data (never inventing metrics, skills, or experiences).
    """
    score = 0
    strengths: List[str] = []
    suggestions: List[str] = []

    existing_skills_lower = {s.lower().strip() for s in skills}
    evidence_corpus = " ".join(
        [
            *(raw_texts or []),
            *[
                f"{e.get('role_title', '')} {e.get('company_name', '')} {e.get('sector', '')} {e.get('responsibilities', '')} {e.get('proven_results', '')}"
                for e in experiences
            ],
        ]
    )
    corpus_lower = evidence_corpus.lower()

    suggested_skills: List[Dict[str, str]] = []
    for term in ATS_COMPETENCY_CATALOG:
        if term.lower() in existing_skills_lower:
            continue
        if re.search(rf"\b{re.escape(term.lower())}\b", corpus_lower):
            suggested_skills.append({
                "name": term,
                "evidence": "Termo encontrado diretamente nas suas experiências/currículo.",
            })

    suggested_summary: Optional[Dict[str, str]] = None
    if summary and len(summary.strip()) >= 60:
        score += 20
        strengths.append("Resumo profissional preenchido com contexto suficiente para indexação ATS.")
    else:
        suggestions.append(
            "Adicione um resumo profissional objetivo (3 a 4 linhas) destacando sua área de atuação, senioridade e especialidades comprovadas."
        )
        if experiences:
            roles = []
            sectors = []
            for e in experiences:
                r = e.get("role_title")
                s = e.get("sector")
                if r and r not in roles:
                    roles.append(r)
                if s and s not in sectors:
                    sectors.append(s)
            roles_txt = ", ".join(roles[:3])
            sectors_txt = f" com atuação nos setores de {', '.join(sectors[:3])}" if sectors else ""
            skills_txt = f" Competências principais: {', '.join(skills[:6])}." if skills else ""
            suggested_summary = {
                "text": f"Profissional com experiência como {roles_txt}{sectors_txt}.{skills_txt}".strip(),
                "evidence": "Gerado estritamente a partir dos cargos, setores e competências já registrados no seu perfil.",
            }

    if len(skills) >= 6:
        score += 25
        strengths.append(f"{len(skills)} competências registradas para correspondência direta de palavras-chave.")
    else:
        suggestions.append(
            "Cadastre pelo menos 6 a 10 competências técnicas e de gestão que você realmente domina (ex.: metodologias, ferramentas, normas)."
        )

    dated_exps = [e for e in experiences if e.get("raw_period_text")]
    if experiences and len(dated_exps) == len(experiences):
        score += 20
        strengths.append("Todas as experiências possuem datas de início/fim identificáveis para cálculo de tempo de experiência pelo ATS.")
    elif experiences:
        score += 10
        suggestions.append(
            "Padronize as datas de início e fim em todas as experiências (ex.: Abr/2018 – Mai/2023) para que algoritmos não subestimem seu tempo de atuação."
        )

    pending_exps = [
        e for e in experiences if e.get("validation_status") not in ("verified", "corrected")
    ]
    if experiences and not pending_exps:
        score += 15
        strengths.append("Todas as experiências estão validadas no Verified Professional Profile.")
    elif pending_exps:
        suggestions.append(
            f"Revise e valide as {len(pending_exps)} experiência(s) pendente(s) para garantir consistência factual."
        )

    with_results = [e for e in experiences if e.get("proven_results") or (e.get("responsibilities") and any(ch.isdigit() for ch in e["responsibilities"]))]
    if with_results:
        score += 20
        strengths.append("Experiências contêm resultados ou indicadores comprovados (alta relevância para triagem).")
    else:
        suggestions.append(
            "Inclua resultados reais e mensuráveis nas experiências onde você tiver dados comprovados (ex.: redução de custos, ganho de eficiência, volume gerido)."
        )

    return {
        "ats_readiness_score": min(100, score),
        "strengths": strengths,
        "suggestions": suggestions,
        "actionable_options": {
            "suggested_skills": suggested_skills[:10],
            "suggested_summary": suggested_summary,
        },
    }
