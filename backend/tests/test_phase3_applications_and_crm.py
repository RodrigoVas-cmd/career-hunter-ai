import io
from docx import Document


def _setup_user_with_resume_and_job(client, email: str, full_name: str):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": full_name, "password": "SenhaForte123!"},
    ).json()
    headers = {"Authorization": f"Bearer {reg['access_token']}"}

    # Upload base resume DOCX
    doc = Document()
    doc.add_paragraph(full_name)
    doc.add_paragraph("Experiência Profissional")
    doc.add_paragraph("Gerente de Produto - Empresa Beta | 2020 - Atual")
    doc.add_paragraph("• Liderança de squad de produto e roadmap B2B.")
    doc.add_paragraph("Competências")
    doc.add_paragraph("Product Management, SQL, OKRs")
    buf = io.BytesIO()
    doc.save(buf)

    up = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={
            "file": (
                "cv.docx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert up.status_code == 201

    # Add a rejected skill to ensure ATS optimizer NEVER includes rejected items
    client.post(
        "/api/v1/profile/skills",
        headers=headers,
        json={"name": "Skill Rejeitada", "validation_status": "rejected"},
    )

    # Create a job posting
    job = client.post(
        "/api/v1/jobs/manual",
        headers=headers,
        json={
            "company_name": "Nuvem Corp",
            "title": "Product Manager Sênior",
            "description": "Buscamos Product Management, SQL e liderança de roadmap B2B.",
            "original_url": "https://nuvemcorp.com/vagas/pm",
            "modality": "remoto",
        },
    ).json()

    return headers, job


def test_supervised_application_flow_approval_invalidation_and_crm(client):
    headers_a, job = _setup_user_with_resume_and_job(client, "pm@exemplo.com", "Marina Costa")
    headers_b = {
        "Authorization": f"Bearer {client.post('/api/v1/auth/register', json={'email': 'other@exemplo.com', 'full_name': 'Outro', 'password': 'SenhaForte123!'}).json()['access_token']}"
    }

    # 1. Create application & verify duplicate block
    app_resp = client.post(
        "/api/v1/applications",
        headers=headers_a,
        json={"job_posting_id": job["id"]},
    )
    assert app_resp.status_code == 201
    app_id = app_resp.json()["id"]

    dup_resp = client.post(
        "/api/v1/applications",
        headers=headers_a,
        json={"job_posting_id": job["id"]},
    )
    assert dup_resp.status_code == 409

    # 2. Generate ATS Resume Version (must exclude rejected skill)
    rv_resp = client.post(f"/api/v1/applications/{app_id}/resume-version", headers=headers_a)
    assert rv_resp.status_code == 201
    rv = rv_resp.json()
    assert rv["approved_by_user"] is False
    assert "Skill Rejeitada" not in rv["content_json"]["skills"]
    assert "SQL" in rv["content_json"]["skills"]

    # Download generated DOCX & PDF (NomeOriginal-1.pdf)
    dl = client.get(f"/api/v1/applications/resume-versions/{rv['id']}/download", headers=headers_a)
    assert dl.status_code == 200
    assert len(dl.content) > 500

    dl_pdf = client.get(f"/api/v1/applications/resume-versions/{rv['id']}/download-pdf", headers=headers_a)
    assert dl_pdf.status_code == 200
    assert dl_pdf.content.startswith(b"%PDF-")
    assert "cv-1.pdf" in dl_pdf.headers.get("content-disposition", "")

    # Notifications: missing OpenAI key alert -> connect key -> success notification
    notifs_before = client.get("/api/v1/notifications", headers=headers_a).json()
    assert any(n["id"] == "system-openai-missing" for n in notifs_before)

    client.put(
        "/api/v1/profile/preferences",
        headers=headers_a,
        json={"openai_api_key": "sk-test-12345"},
    )
    notifs_after = client.get("/api/v1/notifications", headers=headers_a).json()
    assert not any(n["id"] == "system-openai-missing" for n in notifs_after)
    assert any("conectado com sucesso" in n["title"].lower() for n in notifs_after)

    # 3. Prepare questions (verified fact vs personal decision vs direct test)
    q_fact = client.post(
        f"/api/v1/applications/{app_id}/questions",
        headers=headers_a,
        json={"question_text": "Qual sua experiência com Product Management e roadmap B2B?"},
    ).json()
    assert q_fact["question_category"] == "respondivel_fatos_verificados"
    assert q_fact["requires_human_input"] is False
    assert len(q_fact["evidence_refs_json"]) >= 1

    q_salary = client.post(
        f"/api/v1/applications/{app_id}/questions",
        headers=headers_a,
        json={"question_text": "Qual sua pretensão salarial e disponibilidade de início?"},
    ).json()
    assert q_salary["question_category"] == "exige_decisao_pessoal"
    assert q_salary["draft_answer"] is None
    assert q_salary["requires_human_input"] is True

    q_test = client.post(
        f"/api/v1/applications/{app_id}/questions",
        headers=headers_a,
        json={"question_text": "Realize o teste técnico e comportamental anexo."},
    ).json()
    assert q_test["question_category"] == "exige_participacao_direta"
    assert q_test["requires_human_input"] is True

    # 4. Cannot approve or submit before resume approval and human answers
    assert client.post(f"/api/v1/applications/{app_id}/approve", headers=headers_a).status_code == 400
    assert (
        client.post(
            f"/api/v1/applications/{app_id}/confirm-submission",
            headers=headers_a,
            json={"confirmed": True},
        ).status_code
        == 400
    )

    # Approve resume version & answer pending human questions
    assert (
        client.post(
            f"/api/v1/applications/resume-versions/{rv['id']}/approve", headers=headers_a
        ).status_code
        == 200
    )
    client.patch(
        f"/api/v1/applications/answers/{q_salary['id']}",
        headers=headers_a,
        json={"approved_answer": "R$ 16.000/mês CLT, início imediato."},
    )
    client.patch(
        f"/api/v1/applications/answers/{q_test['id']}",
        headers=headers_a,
        json={"approved_answer": "Teste concluído diretamente pela candidata."},
    )

    # 5. Explicit human approval succeeds
    approve_resp = client.post(f"/api/v1/applications/{app_id}/approve", headers=headers_a)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["is_valid"] is True

    # 6. Editing an answer after approval MUST invalidate the approval
    client.patch(
        f"/api/v1/applications/answers/{q_salary['id']}",
        headers=headers_a,
        json={"approved_answer": "R$ 17.000/mês CLT."},
    )
    assert (
        client.post(
            f"/api/v1/applications/{app_id}/confirm-submission",
            headers=headers_a,
            json={"confirmed": True},
        ).status_code
        == 400
    )

    # Re-approve & test ambiguous -> pendente_confirmacao, then confirmed -> enviada_confirmada
    assert client.post(f"/api/v1/applications/{app_id}/approve", headers=headers_a).status_code == 200

    ambig = client.post(
        f"/api/v1/applications/{app_id}/confirm-submission",
        headers=headers_a,
        json={"ambiguous": True, "confirmation_note": "Página recarregou sem protocolo."},
    )
    assert ambig.status_code == 200
    assert ambig.json()["operational_status"] == "pendente_confirmacao"

    conf = client.post(
        f"/api/v1/applications/{app_id}/confirm-submission",
        headers=headers_a,
        json={"confirmed": True, "confirmation_note": "E-mail de confirmação recebido."},
    )
    assert conf.status_code == 200
    assert conf.json()["operational_status"] == "enviada_confirmada"
    assert conf.json()["submitted_at"] is not None

    # 7. Schedule interview & check isolation
    iv = client.post(
        f"/api/v1/applications/{app_id}/interviews",
        headers=headers_a,
        json={"stage_name": "Entrevista com Tech Lead", "scheduled_at": "2026-12-01T14:00:00Z"},
    )
    assert iv.status_code == 201
    assert len(client.get("/api/v1/applications/interviews/all", headers=headers_a).json()) == 1

    # User B cannot access User A's application or interviews
    assert client.get(f"/api/v1/applications/{app_id}", headers=headers_b).status_code == 404
    assert client.get("/api/v1/applications/interviews/all", headers=headers_b).json() == []
