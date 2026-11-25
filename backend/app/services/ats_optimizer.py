import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from docx import Document
from fpdf import FPDF
import httpx

from app.models.jobs import JobPosting
from app.models.user import (
    CareerPreference,
    ProfessionalExperience,
    User,
    UserProfile,
    VerifiedSkill,
)
from app.services.ats_prompt import (
    QUESTION_ASSISTANT_SYSTEM_PROMPT,
    STRATEGIC_ATS_SYSTEM_PROMPT,
)


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-ZÀ-ÿ0-9+#]{2,}", text.lower())}


def _safe_latin1(text: str) -> str:
    replacements = {
        "—": "-",
        "–": "-",
        "•": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _generate_ats_pdf(content_json: Dict[str, Any], pdf_path: Path) -> None:
    """
    Generates an A4 single-column, searchable ATS-compliant PDF.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    arial_reg = Path("C:/Windows/Fonts/arial.ttf")
    arial_bold = Path("C:/Windows/Fonts/arialbd.ttf")
    arial_ital = Path("C:/Windows/Fonts/ariali.ttf")

    use_unicode = arial_reg.exists() and arial_bold.exists()
    if use_unicode:
        pdf.add_font("ArialUni", "", str(arial_reg))
        pdf.add_font("ArialUni", "B", str(arial_bold))
        if arial_ital.exists():
            pdf.add_font("ArialUni", "I", str(arial_ital))
        font_family = "ArialUni"
    else:
        font_family = "Helvetica"

    def txt(s: str) -> str:
        return s if use_unicode else _safe_latin1(s)

    def mc(h: float, text_val: str) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, h, txt(text_val), new_x="LMARGIN", new_y="NEXT")

    # Nome (18 pt bold)
    pdf.set_font(font_family, "B", 18)
    pdf.set_text_color(15, 23, 42)
    mc(9, content_json["full_name"])

    # Contato
    contact_parts = [
        p
        for p in [
            content_json.get("location"),
            content_json.get("phone"),
            content_json.get("email"),
            content_json.get("linkedin_url"),
        ]
        if p
    ]
    if contact_parts:
        pdf.set_font(font_family, "", 10)
        pdf.set_text_color(51, 65, 85)
        mc(5, " | ".join(contact_parts))
        pdf.ln(2)

    def section_heading(title: str) -> None:
        pdf.ln(2)
        pdf.set_x(pdf.l_margin)
        pdf.set_font(font_family, "B", 11.5)
        pdf.set_text_color(15, 35, 85)
        pdf.cell(pdf.epw, 6, txt(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(203, 213, 225)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(2)
        pdf.set_text_color(15, 23, 42)

    # Objetivo Profissional
    if content_json.get("objective"):
        section_heading("OBJETIVO PROFISSIONAL")
        pdf.set_font(font_family, "B", 11)
        mc(5.5, content_json["objective"])

    # Resumo Profissional
    if content_json.get("summary"):
        section_heading("RESUMO PROFISSIONAL")
        pdf.set_font(font_family, "", 10.5)
        for line in content_json["summary"].splitlines():
            if line.strip():
                mc(5.2, line.strip())
                pdf.ln(1)

    # Competências-Chave
    if content_json.get("skills"):
        section_heading("COMPETÊNCIAS-CHAVE")
        pdf.set_font(font_family, "", 10.5)
        mc(5.2, " | ".join(content_json["skills"]))

    # Experiência Profissional
    if content_json.get("experiences"):
        section_heading("EXPERIÊNCIA PROFISSIONAL")
        for exp in content_json["experiences"]:
            pdf.set_font(font_family, "B", 10.5)
            comp_line = exp["company_name"]
            if exp.get("sector"):
                comp_line += f" — {exp['sector']}"
            mc(5.2, comp_line)

            pdf.set_font(font_family, "B" if not use_unicode or not arial_ital.exists() else "I", 10.5)
            role_line = exp["role_title"]
            if exp.get("raw_period_text"):
                role_line += f" | {exp['raw_period_text']}"
            mc(5, role_line)

            pdf.set_font(font_family, "", 10)
            for bullet in exp.get("responsibilities_list") or []:
                mc(4.8, f"• {bullet}")
            if exp.get("proven_results"):
                mc(4.8, f"• Resultados comprovados: {exp['proven_results']}")
            pdf.ln(2)

    # Formação Acadêmica
    if content_json.get("education"):
        section_heading("FORMAÇÃO ACADÊMICA")
        pdf.set_font(font_family, "", 10.5)
        for ed in content_json["education"]:
            mc(5, f"• {ed.get('raw') or ed}")

    # Certificações
    if content_json.get("certifications"):
        section_heading("CERTIFICAÇÕES")
        pdf.set_font(font_family, "", 10.5)
        for cert in content_json["certifications"]:
            mc(5, f"• {cert.get('raw') or cert}")

    # Idiomas
    if content_json.get("languages"):
        section_heading("IDIOMAS")
        pdf.set_font(font_family, "", 10.5)
        for lang in content_json["languages"]:
            mc(5, f"• {lang.get('raw') or lang}")

    pdf.output(str(pdf_path))


def _adapt_cv_with_openai(
    *,
    api_key: str,
    target_role_title: str,
    job_description: str,
    base_summary: str,
    experiences: List[Dict[str, Any]],
    skills: List[str],
    education: List[Any],
) -> Tuple[Optional[Dict[str, Any]], str]:
    user_payload = {
        "cargo_pretendido": target_role_title,
        "descricao_da_vaga": job_description[:3500],
        "resumo_original": base_summary,
        "experiencias_reais": experiences[:8],
        "competencias_verificadas": skills[:25],
        "formacao_academica": education[:8],
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": STRATEGIC_ATS_SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                    ],
                },
            )
            if resp.status_code in (401, 403):
                return None, "auth_error"
            resp.raise_for_status()
            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_content)
            return parsed, "ok"
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (401, 403):
            return None, "auth_error"
        return None, "error"
    except Exception:
        return None, "error"


def build_ats_resume_version(
    *,
    user: User,
    profile: Optional[UserProfile],
    experiences: List[ProfessionalExperience],
    skills: List[VerifiedSkill],
    job: Optional[JobPosting],
    target_dir: Path,
    openai_api_key: Optional[str] = None,
    base_filename: Optional[str] = None,
    target_role_override: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[str], str, str, str]:
    """
    Builds an ATS-optimized resume version (DOCX + PDF) using ONLY verified facts.
    Returns (content_json, changes_summary, docx_path, pdf_path, ai_status).
    """
    usable_exps = [e for e in experiences if e.validation_status != "rejected"]
    usable_skills = [s for s in skills if s.validation_status != "rejected"]

    job_text = f"{job.title} {job.description}".lower() if job else ""
    job_tokens = _tokenize(job_text)
    changes_summary: List[str] = []

    def exp_relevance(exp: ProfessionalExperience) -> tuple[int, int]:
        exp_tokens = _tokenize(f"{exp.role_title} {exp.responsibilities or ''} {exp.sector or ''}")
        overlap = len(exp_tokens & job_tokens)
        verified_bonus = 1 if exp.validation_status in ("verified", "corrected") else 0
        return (overlap, verified_bonus)

    sorted_exps = sorted(usable_exps, key=exp_relevance, reverse=True)
    if job and len(sorted_exps) > 1 and sorted_exps != usable_exps:
        changes_summary.append(
            f"Experiências reorganizadas por aderência aos requisitos da vaga '{job.title}'."
        )

    matched_skills = [s.name for s in usable_skills if s.name.lower() in job_text] if job else []
    other_skills = [s.name for s in usable_skills if s.name not in matched_skills]
    ordered_skills = matched_skills + other_skills

    if matched_skills:
        changes_summary.append(
            f"Competências comprovadas em destaque para ATS: {', '.join(matched_skills[:8])}."
        )

    exp_entries: List[Dict[str, Any]] = []
    for e in sorted_exps:
        raw_resp = (e.responsibilities or "").strip()
        bullets = [line.lstrip("•-*▪ ").strip() for line in raw_resp.splitlines() if line.strip()]
        exp_entries.append({
            "company_name": e.company_name,
            "role_title": e.role_title,
            "sector": e.sector,
            "raw_period_text": e.raw_period_text,
            "is_current": e.is_current,
            "responsibilities": raw_resp,
            "responsibilities_list": bullets,
            "proven_results": e.proven_results,
            "validation_status": e.validation_status,
        })

    base_summary = (profile.summary if profile and profile.summary else "") or ""
    target_role_title = target_role_override or (job.title if job else (profile.headline if profile else None)) or ""
    adapted_summary = base_summary
    objective = target_role_title.upper() if target_role_title else ""
    ai_status = "none"

    if openai_api_key and target_role_title:
        ai_res, ai_status = _adapt_cv_with_openai(
            api_key=openai_api_key,
            target_role_title=target_role_title,
            job_description=job.description if job else f"Adequação geral para {target_role_title}",
            base_summary=base_summary,
            experiences=exp_entries,
            skills=ordered_skills,
            education=profile.education_json if profile else [],
        )
        if ai_res:
            objective = (ai_res.get("objetivo_profissional") or target_role_title).upper()
            if ai_res.get("resumo_profissional"):
                adapted_summary = ai_res["resumo_profissional"]
            if isinstance(ai_res.get("competencias_chave"), list) and ai_res["competencias_chave"]:
                # Only keep skills that actually exist in user's verified skills
                allowed_lower = {s.lower(): s for s in ordered_skills}
                filtered = [allowed_lower[s.lower()] for s in ai_res["competencias_chave"] if isinstance(s, str) and s.lower() in allowed_lower]
                if filtered:
                    ordered_skills = filtered + [s for s in ordered_skills if s not in filtered]
            if isinstance(ai_res.get("experiencias"), list) and ai_res["experiencias"]:
                # Merge rewritten bullets back onto real experience entries by company/role
                by_key = {(e["company_name"].lower(), e["role_title"].lower()): e for e in exp_entries}
                for ai_exp in ai_res["experiencias"]:
                    if not isinstance(ai_exp, dict):
                        continue
                    k = ((ai_exp.get("company_name") or "").lower(), (ai_exp.get("role_title") or "").lower())
                    if k in by_key and isinstance(ai_exp.get("responsibilities_list"), list) and ai_exp["responsibilities_list"]:
                        by_key[k]["responsibilities_list"] = [str(b).strip() for b in ai_exp["responsibilities_list"] if str(b).strip()]
            changes_summary.append(
                f"Currículo adaptado estrategicamente via ChatGPT (OpenAI) para o cargo '{target_role_title}'."
            )

    if ai_status != "ok":
        if job and base_summary:
            changes_summary.append(
                f"Objetivo profissional definido para '{target_role_title}' mantendo fatos verificados."
            )
        elif not base_summary:
            changes_summary.append(
                "Resumo profissional não preenchido no perfil; mantido em branco sem invenção de texto."
            )

    contact_email = (profile.contact_email if profile and profile.contact_email else None) or user.email
    city_val = profile.city if profile else None
    state_val = profile.state if profile else None
    loc_str = " - ".join([p for p in [city_val, state_val] if p])

    content_json = {
        "full_name": user.full_name,
        "email": contact_email,
        "phone": profile.phone if profile else None,
        "city": city_val,
        "state": state_val,
        "location": loc_str,
        "linkedin_url": profile.linkedin_url if profile else None,
        "headline": profile.headline if profile else None,
        "objective": objective,
        "summary": adapted_summary,
        "skills": ordered_skills,
        "matched_ats_keywords": matched_skills,
        "experiences": exp_entries,
        "education": profile.education_json if profile else [],
        "certifications": profile.certifications_json if profile else [],
        "languages": profile.languages_json if profile else [],
    }

    target_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(base_filename).stem if base_filename else f"Curriculo_{user.full_name.replace(' ', '_')}"
    docx_path = target_dir / f"{stem}-1.docx"
    pdf_filename = f"{stem}-1.pdf"
    pdf_path = target_dir / pdf_filename

    # 1. Build DOCX
    doc = Document()
    title_para = doc.add_heading(user.full_name, level=1)
    title_para.paragraph_format.space_after = 2
    contact_parts = [p for p in [contact_email, content_json["phone"], loc_str, content_json["linkedin_url"]] if p]
    if contact_parts:
        c_para = doc.add_paragraph(" | ".join(contact_parts))
        c_para.paragraph_format.space_after = 8

    if objective:
        doc.add_heading("Objetivo Profissional", level=2)
        p_obj = doc.add_paragraph()
        r_obj = p_obj.add_run(objective)
        r_obj.bold = True

    if adapted_summary:
        doc.add_heading("Resumo Profissional", level=2)
        for p_line in adapted_summary.splitlines():
            if p_line.strip():
                doc.add_paragraph(p_line.strip())

    if ordered_skills:
        doc.add_heading("Competências-Chave", level=2)
        doc.add_paragraph(" • ".join(ordered_skills))

    if exp_entries:
        doc.add_heading("Experiência Profissional", level=2)
        for exp in exp_entries:
            header_p = doc.add_paragraph()
            header_p.paragraph_format.space_before = 6
            header_p.paragraph_format.space_after = 1
            comp_run = header_p.add_run(exp["company_name"])
            comp_run.bold = True
            if exp.get("sector"):
                header_p.add_run(f" — {exp['sector']}")

            role_p = doc.add_paragraph()
            role_p.paragraph_format.space_after = 3
            role_run = role_p.add_run(exp["role_title"])
            role_run.bold = True
            if exp.get("raw_period_text"):
                per_run = role_p.add_run(f" | {exp['raw_period_text']}")
                per_run.italic = True

            for bullet in exp.get("responsibilities_list") or []:
                doc.add_paragraph(bullet, style="List Bullet")

            if exp.get("proven_results"):
                res_p = doc.add_paragraph(style="List Bullet")
                r_lbl = res_p.add_run("Resultados comprovados: ")
                r_lbl.bold = True
                res_p.add_run(exp["proven_results"])

    if content_json["education"]:
        doc.add_heading("Formação Acadêmica", level=2)
        for ed in content_json["education"]:
            doc.add_paragraph(str(ed.get("raw") or ed), style="List Bullet")

    if content_json["languages"]:
        doc.add_heading("Idiomas", level=2)
        for lang in content_json["languages"]:
            doc.add_paragraph(str(lang.get("raw") or lang))

    doc.save(str(docx_path))

    # 2. Build A4 ATS PDF (NomeOriginal-1.pdf)
    _generate_ats_pdf(content_json, pdf_path)

    return content_json, changes_summary, str(docx_path), str(pdf_path), ai_status


def prepare_question_draft(
    *,
    question_text: str,
    experiences: List[ProfessionalExperience],
    skills: List[VerifiedSkill],
    preferences: Optional[CareerPreference],
    profile: Optional[UserProfile] = None,
    base_resume_raw: Optional[str] = None,
    tailored_resume_content: Optional[Dict[str, Any]] = None,
    role_title: Optional[str] = None,
    company_name: Optional[str] = None,
    field_type: str = "texto_longo",
    options: Optional[List[str]] = None,
    max_chars: Optional[int] = None,
    job: Optional[JobPosting] = None,
    openai_api_key: Optional[str] = None,
    target_role_salary: Optional[tuple[Optional[int], Optional[int]]] = None,
) -> Dict[str, Any]:
    """
    Classifies a recruitment form question and drafts an answer ONLY from verified facts
    or approved preferences using the V3.0 Strategic Intelligence module when OpenAI is connected.
    """
    q_low = question_text.lower()

    if any(k in q_low for k in ["teste técnico", "desafio técnico", "live coding", "teste comportamental", "personalidade", "disc", "fit cultural", "case"]):
        return {
            "question_category": "exige_participacao_direta",
            "draft_answer": None,
            "evidence_refs": [],
            "requires_human_input": True,
            "ai_status": "none",
        }

    salary_kw = [
        "salário", "salario", "salarial", "pretensão", "pretensao",
        "remuneração", "remuneracao", "expectativa", "salary", "compensation",
    ]
    if any(k in q_low for k in salary_kw):
        r_min, r_max = target_role_salary or (None, None)
        desired = r_max if r_max is not None else (preferences.desired_salary_brl if preferences else None)
        minimum = r_min if r_min is not None else (preferences.min_salary_brl if preferences else None)
        if desired or minimum:
            if field_type == "numero":
                draft = str(desired or minimum)
            elif desired and minimum and desired != minimum:
                low_v, high_v = min(minimum, desired), max(minimum, desired)
                draft = (
                    f"Minha expectativa salarial está entre R$ {low_v:,.0f} e R$ {high_v:,.0f} mensais, "
                    "considerando o escopo de responsabilidades da posição, os desafios da função e o pacote "
                    "total de remuneração e benefícios. Estou aberto a conversar para encontrarmos uma "
                    "proposta que seja adequada para ambas as partes."
                ).replace(",", ".")
            else:
                val = desired or minimum
                draft = (
                    f"Minha expectativa salarial é em torno de R$ {val:,.0f} mensais, "
                    "considerando o escopo de responsabilidades da posição, os desafios da função e o pacote "
                    "total de remuneração e benefícios. Estou aberto a conversar para encontrarmos uma "
                    "proposta que seja adequada para ambas as partes."
                ).replace(",", ".")
            if max_chars and len(draft) > max_chars:
                if desired and minimum and desired != minimum:
                    low_v, high_v = min(minimum, desired), max(minimum, desired)
                    short_draft = f"Entre R$ {low_v:,.0f} e R$ {high_v:,.0f} mensais, aberto a negociação conforme pacote.".replace(",", ".")
                else:
                    short_draft = f"Em torno de R$ {(desired or minimum):,.0f} mensais, aberto a negociação.".replace(",", ".")
                draft = short_draft if len(short_draft) <= max_chars else f"R$ {(desired or minimum):,.0f}".replace(",", ".")[:max_chars]
            source_ref = (
                "Cargo-Alvo: pretensão salarial da posição"
                if (r_min is not None or r_max is not None)
                else "Preferências do Onboarding: pretensão salarial"
            )
            return {
                "question_category": "respondivel_preferencias_aprovadas",
                "draft_answer": draft,
                "evidence_refs": [source_ref],
                "requires_human_input": False,
                "ai_status": "none",
            }
        return {
            "question_category": "exige_decisao_pessoal",
            "draft_answer": None,
            "evidence_refs": [],
            "requires_human_input": True,
            "ai_status": "none",
        }

    if any(k in q_low for k in ["mudança", "mudanca", "realocação", "realocacao", "relocation"]) and preferences and preferences.relocation_available is not None:
        draft = (
            "Sim, tenho disponibilidade para mudança/realocação."
            if preferences.relocation_available
            else "No momento não tenho disponibilidade para mudança de cidade/estado."
        )
        return {
            "question_category": "respondivel_preferencias_aprovadas",
            "draft_answer": draft,
            "evidence_refs": ["Preferências do Onboarding: disponibilidade para mudança"],
            "requires_human_input": False,
            "ai_status": "none",
        }

    if any(k in q_low for k in ["viagem", "viajar", "travel"]) and preferences and preferences.travel_available is not None:
        draft = (
            "Sim, tenho disponibilidade para viagens a trabalho."
            if preferences.travel_available
            else "No momento tenho preferência por atuação sem viagens frequentes."
        )
        return {
            "question_category": "respondivel_preferencias_aprovadas",
            "draft_answer": draft,
            "evidence_refs": ["Preferências do Onboarding: disponibilidade para viagens"],
            "requires_human_input": False,
            "ai_status": "none",
        }

    if any(k in q_low for k in ["disponibilidade", "início", "inicio", "mudança", "mudanca", "viagem", "viajar", "cpf", "rg", "consentimento", "lgpd", "declaro", "aceito"]):
        return {
            "question_category": "exige_decisao_pessoal",
            "draft_answer": None,
            "evidence_refs": [],
            "requires_human_input": True,
            "ai_status": "none",
        }

    usable_exps = [e for e in experiences if e.validation_status != "rejected"]
    usable_skills = [s for s in skills if s.validation_status != "rejected"]
    ai_status = "none"

    if openai_api_key and (usable_exps or usable_skills or profile):
        payload = {
            "perfil_profissional_validado": {
                "headline": profile.headline if profile else None,
                "resumo": profile.summary if profile else None,
                "senioridade": profile.seniority_level if profile else None,
                "cidade": profile.city if profile else None,
                "estado": profile.state if profile else None,
                "formacao": profile.education_json if profile else [],
                "certificacoes": profile.certifications_json if profile else [],
                "idiomas": profile.languages_json if profile else [],
                "experiencias_reais": [
                    {
                        "empresa": e.company_name,
                        "setor": e.sector,
                        "cargo": e.role_title,
                        "periodo": e.raw_period_text,
                        "responsabilidades": (e.responsibilities or "")[:450],
                        "resultados": e.proven_results,
                    }
                    for e in usable_exps[:7]
                ],
                "competencias_verificadas": [s.name for s in usable_skills[:25]],
                "preferencias_aprovadas": {
                    "cidade_atual": preferences.current_city if preferences else None,
                    "estado_atual": preferences.current_state if preferences else None,
                    "modalidades_aceitas": preferences.work_modalities if preferences else [],
                    "pretensao_minima_brl": preferences.min_salary_brl if preferences else None,
                    "pretensao_desejada_brl": preferences.desired_salary_brl if preferences else None,
                    "salario_negociavel": preferences.salary_negotiable if preferences else None,
                    "disponivel_mudanca": preferences.relocation_available if preferences else None,
                    "disponivel_viagens": preferences.travel_available if preferences else None,
                },
            },
            "curriculo_original_trecho": (base_resume_raw or "")[:1800],
            "curriculo_personalizado_vaga": tailored_resume_content,
            "contexto_candidatura": {
                "cargo_pretendido": role_title or (job.title if job else None),
                "nivel_senioridade": job.seniority if job else (profile.seniority_level if profile else None),
                "empresa_contratante": company_name or (job.company_name if job else None),
                "descricao_completa_vaga": (job.description[:2500] if job else None),
            },
            "formulario": {
                "pergunta_exata": question_text,
                "tipo_de_campo": field_type,
                "alternativas_disponiveis": options or [],
                "limite_de_caracteres": max_chars,
            },
        }
        try:
            with httpx.Client(timeout=25.0) as client:
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_api_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "temperature": 0.2,
                        "messages": [
                            {"role": "system", "content": QUESTION_ASSISTANT_SYSTEM_PROMPT},
                            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                        ],
                    },
                )
                if resp.status_code in (401, 403):
                    ai_status = "auth_error"
                else:
                    resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"].strip()
                if text.startswith("VALIDACAO_NECESSARIA"):
                    clarification = text.replace("VALIDACAO_NECESSARIA", "", 1).strip(" :\n-")
                    return {
                        "question_category": "necessita_esclarecimento",
                        "draft_answer": None,
                        "evidence_refs": [clarification or "Validação humana necessária para responder com precisão."],
                        "requires_human_input": True,
                        "ai_status": "ok",
                    }
                if text:
                    if max_chars and len(text) > max_chars:
                        text = text[:max_chars].rstrip()
                    return {
                        "question_category": "respondivel_fatos_verificados",
                        "draft_answer": text,
                        "evidence_refs": ["Módulo Estratégico V3.0 (ChatGPT + Perfil Verificado)"],
                        "requires_human_input": False,
                        "ai_status": "ok",
                    }
        except Exception:
            pass

    q_tokens = _tokenize(question_text)
    evidence_refs: List[str] = []
    snippets: List[str] = []

    for exp in usable_exps:
        exp_tokens = _tokenize(f"{exp.role_title} {exp.company_name} {exp.responsibilities or ''}")
        if q_tokens & exp_tokens:
            evidence_refs.append(f"Experiência: {exp.role_title} em {exp.company_name}")
            snippets.append(f"Atuação como {exp.role_title} na {exp.company_name}: {exp.responsibilities or 'experiência registrada no perfil.'}")

    matched_skills = [s.name for s in usable_skills if s.name.lower() in q_low]
    if matched_skills:
        evidence_refs.append(f"Competências verificadas: {', '.join(matched_skills)}")

    if evidence_refs:
        draft = " ".join(snippets[:2]) if snippets else f"Possuo experiência comprovada com {', '.join(matched_skills)}."
        return {
            "question_category": "respondivel_fatos_verificados",
            "draft_answer": draft.strip(),
            "evidence_refs": evidence_refs,
            "requires_human_input": False,
            "ai_status": ai_status,
        }

    return {
        "question_category": "necessita_esclarecimento",
        "draft_answer": None,
        "evidence_refs": [],
        "requires_human_input": True,
        "ai_status": ai_status,
    }


def compute_approval_payload_hash(
    *,
    application_id: str,
    company_name: str,
    role_title: str,
    resume_version_id: Optional[str],
    source_url: Optional[str],
    answers: List[Dict[str, Any]],
) -> str:
    payload = {
        "application_id": application_id,
        "company_name": company_name,
        "role_title": role_title,
        "resume_version_id": resume_version_id,
        "source_url": source_url,
        "answers": sorted(answers, key=lambda a: a["id"]),
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
