import io

from docx import Document


def _build_sample_docx() -> bytes:
    doc = Document()
    doc.add_paragraph("Carlos Eduardo Mendes")
    doc.add_paragraph("Gerente de Engenharia de Dados | carlos@exemplo.com | (11) 99999-8888")
    doc.add_paragraph("Resumo")
    doc.add_paragraph("Profissional com 8 anos de experiência em dados e liderança de equipes.")
    doc.add_paragraph("Experiência Profissional")
    doc.add_paragraph("Gerente de Dados - Banco Horizonte | 2021 - Atual")
    doc.add_paragraph("• Liderança de equipe de 12 engenheiros de dados e arquitetura em nuvem.")
    doc.add_paragraph("Consultor Independente de BI")  # Ambiguous: no company/date
    doc.add_paragraph("Competências")
    doc.add_paragraph("Python, SQL, Apache Spark, Liderança, Arquitetura Cloud")
    doc.add_paragraph("Formação Acadêmica")
    doc.add_paragraph("Bacharelado em Ciência da Computação - USP")
    doc.add_paragraph("Idiomas")
    doc.add_paragraph("Português (Nativo), Inglês (Avançado)")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_docx_upload_parsing_and_verification(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "carlos@exemplo.com",
            "full_name": "Carlos Mendes",
            "password": "SenhaForte123!",
        },
    ).json()
    headers = {"Authorization": f"Bearer {reg['access_token']}"}

    docx_bytes = _build_sample_docx()
    upload = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={
            "file": (
                "curriculo_carlos.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload.status_code == 201, upload.text
    data = upload.json()
    assert data["file_format"] == "docx"
    assert data["parse_status"] == "parsed"
    assert len(data["ambiguities_json"]) >= 1  # Ambiguous line flagged

    # Check Verified Professional Profile items created with pending_review
    exps = client.get("/api/v1/profile/experiences", headers=headers).json()
    assert len(exps) >= 1
    assert any(e["company_name"] == "Banco Horizonte" and e["validation_status"] == "pending_review" for e in exps)
    assert all(e["origin"] == "resume_docx" for e in exps)

    skills = client.get("/api/v1/profile/skills", headers=headers).json()
    skill_names = {s["name"] for s in skills}
    assert {"Python", "SQL"}.issubset(skill_names)

    # User validates an experience
    exp_id = exps[0]["id"]
    validated = client.patch(
        f"/api/v1/profile/experiences/{exp_id}",
        headers=headers,
        json={"validation_status": "verified"},
    )
    assert validated.status_code == 200
    assert validated.json()["validation_status"] == "verified"


def test_reject_invalid_resume_format(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "badfile@exemplo.com", "full_name": "Teste", "password": "SenhaForte123!"},
    ).json()
    headers = {"Authorization": f"Bearer {reg['access_token']}"}

    resp = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("virus.exe", b"MZ...", "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_two_line_company_role_parsing_linkedin_diff_and_adjusted_cv(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "ind@exemplo.com", "full_name": "Roberto Vasconcelos", "password": "SenhaForte123!"},
    ).json()
    headers = {"Authorization": f"Bearer {reg['access_token']}"}

    # Two-line format matching real Brazilian CV
    doc_cv = Document()
    doc_cv.add_paragraph("Roberto Vasconcelos")
    doc_cv.add_paragraph("Experiência Profissional")
    doc_cv.add_paragraph("Vedacit — Indústria Química / Construção Civil")
    doc_cv.add_paragraph("Coordenador de Produção | Abr/2018 – Mai/2023")
    doc_cv.add_paragraph("• Gestão de manufatura enxuta e redução de perdas em 15%.")
    doc_cv.add_paragraph("Duratex S/A — Divisão Deca Louças")
    doc_cv.add_paragraph("Coordenador de Produção | Mai/2007 – Set/2015")
    buf_cv = io.BytesIO()
    doc_cv.save(buf_cv)

    up = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={
            "file": (
                "cv_roberto.docx",
                buf_cv.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert up.status_code == 201
    # Zero false ambiguities for two-line Company — Sector + Role | Period
    assert up.json()["ambiguities_json"] == []

    exps = client.get("/api/v1/profile/experiences", headers=headers).json()
    assert len(exps) == 2
    vedacit = next(e for e in exps if e["company_name"] == "Vedacit")
    assert vedacit["role_title"] == "Coordenador de Produção"
    assert vedacit["raw_period_text"] == "Abr/2018 – Mai/2023"
    assert vedacit["sector"] == "Indústria Química / Construção Civil"

    # Compare with LinkedIn DOCX having divergent end date on Vedacit
    doc_li = Document()
    doc_li.add_paragraph("Experiência")
    doc_li.add_paragraph("Vedacit — Indústria Química")
    doc_li.add_paragraph("Coordenador de Produção | Abr/2018 – Jul/2023")
    buf_li = io.BytesIO()
    doc_li.save(buf_li)

    cmp_resp = client.post(
        "/api/v1/resumes/compare-linkedin",
        headers=headers,
        files={
            "file": (
                "linkedin.docx",
                buf_li.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert cmp_resp.status_code == 200
    cmp_data = cmp_resp.json()
    assert len(cmp_data["divergences"]) == 1
    assert cmp_data["divergences"][0]["company_name"] == "Vedacit"

    # Build adjusted CV & get ATS suggestions
    adj = client.post("/api/v1/resumes/build-adjusted?set_as_primary=true", headers=headers)
    assert adj.status_code == 201
    assert adj.json()["is_primary"] is True

    sug = client.get("/api/v1/resumes/ats-suggestions", headers=headers)
    assert sug.status_code == 200
    assert "ats_readiness_score" in sug.json()
    assert isinstance(sug.json()["suggestions"], list)
    assert "actionable_options" in sug.json()
    assert sug.json()["actionable_options"]["suggested_summary"] is not None

    prev_resp = client.get("/api/v1/resumes/preview-adjusted", headers=headers)
    assert prev_resp.status_code == 200
    assert prev_resp.json()["content"]["full_name"] == "Roberto Vasconcelos"

    dl_adj = client.get(f"/api/v1/resumes/{adj.json()['id']}/download", headers=headers)
    assert dl_adj.status_code == 200
    assert len(dl_adj.content) > 500

    # Delete original CV and verify it's removed cleanly
    del_resp = client.delete(f"/api/v1/resumes/{up.json()['id']}", headers=headers)
    assert del_resp.status_code == 204
    remaining = client.get("/api/v1/resumes", headers=headers).json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == adj.json()["id"]
