import re
from typing import Any, Dict, List, Optional

from app.models.jobs import JobPosting, JobRequirement
from app.models.targeting import TargetRole
from app.models.user import (
    CareerPreference,
    ProfessionalExperience,
    UserProfile,
    VerifiedSkill,
)

DEFAULT_WEIGHTS = {
    "functional_experience": 25.0,
    "mandatory_skills": 25.0,
    "seniority_scope": 15.0,
    "desirable_skills": 10.0,
    "sector_transferable": 10.0,
    "location_modality": 10.0,
    "career_objectives": 5.0,
}

SENIORITY_ORDER = {
    "analista": 1,
    "pleno": 2,
    "sênior": 3,
    "senior": 3,
    "especialista": 4,
    "coordenação": 5,
    "coordenacao": 5,
    "gerência": 6,
    "gerencia": 6,
    "diretoria": 7,
}


STOPWORDS = {
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "e", "ou", "com", "para", "por", "sem", "sob", "afins", "etc",
    "um", "uma", "uns", "umas", "ao", "aos", "à", "às", "que", "se",
}


def _tokenize(text: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-zA-ZÀ-ÿ0-9+#]{2,}", text.lower())
        if t not in STOPWORDS
    }


def classify_score(score: float, is_eligible: bool) -> str:
    if not is_eligible:
        return "inelegivel"
    if score >= 85:
        return "excelente_aderencia"
    if score >= 75:
        return "alta_aderencia"
    if score >= 65:
        return "aderencia_moderada"
    return "baixa_prioridade"


def evaluate_job_match(
    *,
    job: JobPosting,
    requirements: List[JobRequirement],
    profile: Optional[UserProfile],
    experiences: List[ProfessionalExperience],
    skills: List[VerifiedSkill],
    target_roles: List[TargetRole],
    preferences: Optional[CareerPreference],
    is_favorite_company: bool,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Explainable 0-100 professional match engine.
    Note: Favorite company status never inflates `total_score`; it only affects
    application priority (`priority_score`).
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    job_text = f"{job.title} {job.description}".lower()
    job_tokens = _tokenize(job_text)

    skill_names = [s.name for s in skills]
    skill_lower = {s.lower() for s in skill_names}
    exp_titles = [e.role_title for e in experiences]

    edu_text = " ".join(str(ed.get("raw") or ed) for ed in (profile.education_json or [])) if profile else ""
    cert_text = " ".join(str(c.get("raw") or c) for c in (profile.certifications_json or [])) if profile else ""
    lang_text = " ".join(str(l.get("raw") or l) for l in (profile.languages_json or [])) if profile else ""
    profile_text = f"{profile.headline or ''} {profile.summary or ''} {edu_text} {cert_text} {lang_text}" if profile else ""

    exp_text = " ".join(
        [
            *[
                f"{e.role_title} {e.company_name} {e.responsibilities or ''} {e.proven_results or ''} {e.sector or ''}"
                for e in experiences
            ],
            profile_text,
        ]
    ).lower()
    exp_tokens = _tokenize(exp_text) | _tokenize(" ".join(skill_names))

    verifiable_evidence: List[str] = []
    met_requirements: List[str] = []
    partial_requirements: List[str] = []
    unproven_requirements: List[str] = []
    eliminatory_flags: List[str] = []
    transferable_skills: List[str] = []
    gaps: List[str] = []

    # --- Eliminatory checks ---
    if preferences:
        excluded = [c.lower().strip() for c in (preferences.excluded_companies or []) if c.strip()]
        if any(ex in job.company_name.lower() for ex in excluded):
            eliminatory_flags.append(f"Empresa '{job.company_name}' está na sua lista de empresas excluídas.")

        for crit in preferences.eliminatory_criteria or []:
            c_low = crit.lower().strip()
            if c_low and c_low in job_text:
                eliminatory_flags.append(f"Critério eliminatório configurado encontrado na vaga: {crit}")

    for req in requirements:
        if req.requirement_type == "eliminatory":
            req_tokens = _tokenize(req.text)
            overlap = req_tokens & (exp_tokens | skill_lower)
            if not overlap:
                eliminatory_flags.append(f"Requisito eliminatório não comprovado: {req.text}")

    is_eligible = len(eliminatory_flags) == 0

    # --- 1. Experiência funcional (25 pts) ---
    title_tokens = _tokenize(job.title)
    matching_exp_titles = [
        t for t in exp_titles if len(_tokenize(t) & title_tokens) > 0
    ]
    if matching_exp_titles:
        func_ratio = min(1.0, 0.65 + 0.35 * (len(title_tokens & exp_tokens) / max(1, len(title_tokens))))
        verifiable_evidence.append(f"Experiência prévia alinhada: {', '.join(matching_exp_titles[:2])}")
    elif exp_tokens & title_tokens:
        func_ratio = 0.55
        transferable_skills.append("Atuação funcional correlata no histórico profissional")
    else:
        func_ratio = 0.2 if experiences else 0.0
        gaps.append(f"Sem experiência direta comprovada com o título '{job.title}'.")
    functional_score = round(w["functional_experience"] * func_ratio, 2)

    # --- 2. Competências obrigatórias (25 pts) ---
    mandatory_reqs = [r for r in requirements if r.requirement_type == "mandatory"]
    if mandatory_reqs:
        matched_count = 0
        for req in mandatory_reqs:
            r_tokens = _tokenize(req.text)
            matched_skills = [s for s in skill_names if s.lower() in req.text.lower()]
            if matched_skills or len(r_tokens & exp_tokens) >= 2:
                matched_count += 1
                met_requirements.append(req.text)
                if matched_skills:
                    verifiable_evidence.append(f"Competência comprovada: {matched_skills[0]}")
            elif len(r_tokens & exp_tokens) == 1:
                matched_count += 0.5
                partial_requirements.append(req.text)
            else:
                unproven_requirements.append(req.text)
                gaps.append(f"Requisito obrigatório não comprovado no perfil: {req.text}")
        mand_ratio = matched_count / len(mandatory_reqs)
    else:
        matched_skills = [s for s in skill_names if s.lower() in job_text]
        mand_ratio = min(1.0, len(matched_skills) / 4.0) if skill_names else 0.0
        if matched_skills:
            verifiable_evidence.append(f"Competências presentes na vaga: {', '.join(matched_skills[:5])}")
        else:
            gaps.append("Poucas competências cadastradas correspondem ao texto da vaga.")
    mandatory_score = round(w["mandatory_skills"] * mand_ratio, 2)

    # --- 3. Senioridade e escopo (15 pts) ---
    user_sen_str = (profile.seniority_level or "").lower() if profile else ""
    job_sen_str = (job.seniority or "").lower()
    if user_sen_str and job_sen_str:
        u_lvl = SENIORITY_ORDER.get(user_sen_str, 3)
        j_lvl = SENIORITY_ORDER.get(job_sen_str, 3)
        diff = abs(u_lvl - j_lvl)
        sen_ratio = 1.0 if diff == 0 else (0.7 if diff == 1 else 0.3)
        if diff == 0:
            verifiable_evidence.append(f"Senioridade alinhada ({job.seniority})")
        else:
            gaps.append(f"Diferença de senioridade: perfil '{profile.seniority_level}' vs vaga '{job.seniority}'.")
    else:
        sen_ratio = 0.65
    seniority_score = round(w["seniority_scope"] * sen_ratio, 2)

    # --- 4. Competências desejáveis (10 pts) ---
    desirable_reqs = [r for r in requirements if r.requirement_type == "desirable"]
    if desirable_reqs:
        des_hits = sum(1 for r in desirable_reqs if (_tokenize(r.text) & (exp_tokens | skill_lower)))
        des_ratio = des_hits / len(desirable_reqs)
    else:
        des_ratio = min(1.0, len([s for s in skill_names if s.lower() in job_text]) / 6.0)
    desirable_score = round(w["desirable_skills"] * des_ratio, 2)

    # --- 5. Setor e competências transferíveis (10 pts) ---
    user_sectors = {s.lower() for s in (profile.sectors_json or [])} if profile else set()
    user_sectors |= {e.sector.lower() for e in experiences if e.sector}
    if user_sectors and any(sec in job_text for sec in user_sectors):
        sec_ratio = 1.0
        verifiable_evidence.append("Experiência prévia no setor da vaga")
    elif exp_tokens & job_tokens:
        sec_ratio = 0.65
        transferable_skills.append("Competências analíticas/operacionais transferíveis identificadas")
    else:
        sec_ratio = 0.3
    sector_score = round(w["sector_transferable"] * sec_ratio, 2)

    # --- 6. Localização e modalidade (10 pts) ---
    loc_ratio = 0.7
    if preferences:
        pref_mods = {m.lower() for m in (preferences.work_modalities or [])}
        desired_locs = {d.lower() for d in (preferences.desired_locations or [])}
        all_brazil = "brasil" in desired_locs or "brasil todo" in desired_locs
        job_loc = (job.location or "").lower()
        city_low = (preferences.current_city or "").lower()
        state_low = (preferences.current_state or "").lower()

        mod_ok = True
        if job.modality and pref_mods:
            mod_ok = job.modality.lower() in pref_mods

        loc_ok = True
        if job.modality != "remoto" and job_loc and not all_brazil:
            if city_low and city_low in job_loc:
                loc_ok = True
                if preferences.max_commute_km:
                    verifiable_evidence.append(
                        f"Localidade compatível ({job.location}, raio configurado de {preferences.max_commute_km} km)"
                    )
            elif state_low and state_low in job_loc:
                loc_ok = True
            elif any(dl in job_loc for dl in desired_locs if dl):
                loc_ok = True
            elif city_low or state_low:
                loc_ok = False
                gaps.append(
                    f"Localidade da vaga ({job.location}) fora de {preferences.current_city or ''}/{preferences.current_state or ''}."
                )

        if mod_ok and loc_ok:
            loc_ratio = 1.0
            if job.modality:
                verifiable_evidence.append(
                    f"Modalidade compatível ({job.modality})"
                    + (" · abrangência Brasil" if all_brazil else "")
                )
        elif not mod_ok:
            loc_ratio = 0.25
            gaps.append(f"Modalidade da vaga ({job.modality}) diverge das suas preferências.")
        else:
            loc_ratio = 0.45
    location_score = round(w["location_modality"] * loc_ratio, 2)

    # --- 7. Objetivos de carreira (5 pts) ---
    active_roles = [r for r in target_roles if r.status == "ativo"]
    role_match = any(
        (_tokenize(r.title) & title_tokens) or any(_tokenize(syn) & title_tokens for syn in (r.synonyms or []))
        for r in active_roles
    )
    obj_ratio = 1.0 if role_match else (0.4 if active_roles else 0.5)
    if role_match:
        verifiable_evidence.append("Alinhado aos seus cargos-alvo ativos")
    objectives_score = round(w["career_objectives"] * obj_ratio, 2)

    total_score = round(
        functional_score
        + mandatory_score
        + seniority_score
        + desirable_score
        + sector_score
        + location_score
        + objectives_score,
        2,
    )
    total_score = max(0.0, min(100.0, total_score))
    classification = classify_score(total_score, is_eligible)

    # Prioridade de candidatura (distinta da aderência profissional)
    priority_bonus = 10.0 if is_favorite_company else 0.0
    priority_score = round(total_score + priority_bonus, 2) if is_eligible else 0.0

    if not is_eligible:
        recommendation = "Não recomendada (critério eliminatório identificado)."
    elif total_score >= 85:
        recommendation = "Alta prioridade para revisão e candidatura supervisionada."
    elif total_score >= 75:
        recommendation = "Boa aderência; vale preparar currículo personalizado para ATS."
    elif total_score >= 65:
        recommendation = "Aderência moderada; avalie as lacunas antes de prosseguir."
    else:
        recommendation = "Baixa prioridade neste momento."

    confidence = 0.85 if (experiences and skills) else 0.55

    return {
        "total_score": total_score,
        "priority_score": priority_score,
        "classification": classification,
        "is_eligible": is_eligible,
        "confidence_level": confidence,
        "dimension_scores": {
            "experiencia_funcional": functional_score,
            "competencias_obrigatorias": mandatory_score,
            "senioridade_escopo": seniority_score,
            "competencias_desejaveis": desirable_score,
            "setor_transferiveis": sector_score,
            "localizacao_modalidade": location_score,
            "objetivos_carreira": objectives_score,
        },
        "explanation": {
            "met_requirements": met_requirements,
            "partial_requirements": partial_requirements,
            "unproven_requirements": unproven_requirements,
            "eliminatory_flags": eliminatory_flags,
            "verifiable_evidence": verifiable_evidence,
            "transferable_skills": transferable_skills,
            "gaps": gaps,
            "justification": (
                f"Pontuação {total_score}/100 ({classification.replace('_', ' ')}). "
                "Esta nota mede compatibilidade documental, não probabilidade de contratação."
            ),
            "recommendation": recommendation,
        },
    }
