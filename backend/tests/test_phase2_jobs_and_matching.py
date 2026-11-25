from app.services.connectors import detect_connector_from_url, extract_jsonld_jobs_from_html


def _register_and_auth(client, email: str, full_name: str):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": full_name, "password": "SenhaForte123!"},
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_connector_detection_and_jsonld_extraction():
    assert detect_connector_from_url("https://boards.greenhouse.io/nubank") == ("greenhouse", "nubank")
    assert detect_connector_from_url("https://jobs.lever.co/ifood") == ("lever", "ifood")
    assert detect_connector_from_url("https://carreiras.empresa.com.br") == (
        "jsonld",
        "https://carreiras.empresa.com.br",
    )

    sample_html = """
    <html><head>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org/",
      "@type": "JobPosting",
      "title": "Engenheiro de Dados Sênior",
      "description": "<p>Requisito obrigatório: Python e SQL avançado. Desejável: Apache Spark.</p>",
      "hiringOrganization": {"@type": "Organization", "name": "Banco Horizonte"},
      "jobLocationType": "TELECOMMUTE",
      "url": "https://carreiras.bancohorizonte.com.br/vagas/123"
    }
    </script>
    </head><body></body></html>
    """
    jobs = extract_jsonld_jobs_from_html(sample_html, "https://carreiras.bancohorizonte.com.br")
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Engenheiro de Dados Sênior"
    assert jobs[0]["company_name"] == "Banco Horizonte"
    assert jobs[0]["modality"] == "remoto"
    assert len(jobs[0]["requirements"]) >= 1


def test_manual_job_deduplication_and_matching_engine(client):
    headers_a = _register_and_auth(client, "analista@exemplo.com", "Lucas Martins")
    headers_b = _register_and_auth(client, "outro@exemplo.com", "Outro Usuário")

    # Setup User A verified profile
    client.put(
        "/api/v1/profile",
        headers=headers_a,
        json={"seniority_level": "Sênior", "sectors_json": ["Tecnologia", "Financeiro"]},
    )
    client.post(
        "/api/v1/profile/experiences",
        headers=headers_a,
        json={
            "company_name": "Tech Pagamentos",
            "role_title": "Engenheiro de Dados Sênior",
            "responsibilities": "Arquitetura de pipelines em Python, SQL e Spark no setor financeiro.",
            "sector": "Financeiro",
            "validation_status": "verified",
        },
    )
    for skill in ["Python", "SQL", "Apache Spark"]:
        client.post(
            "/api/v1/profile/skills",
            headers=headers_a,
            json={"name": skill, "validation_status": "verified"},
        )
    client.post(
        "/api/v1/targeting/roles",
        headers=headers_a,
        json={"title": "Engenheiro de Dados Sênior", "priority": "alta"},
    )
    client.put(
        "/api/v1/profile/preferences",
        headers=headers_a,
        json={
            "work_modalities": ["remoto"],
            "excluded_companies": ["Empresa Bloqueada"],
        },
    )

    # Register a favorite company
    client.post(
        "/api/v1/targeting/companies",
        headers=headers_a,
        json={"name": "Banco Favorito", "priority": "alta"},
    )

    # 1. Compatible job at favorite company
    j1 = client.post(
        "/api/v1/jobs/manual",
        headers=headers_a,
        json={
            "company_name": "Banco Favorito",
            "title": "Engenheiro de Dados Sênior",
            "description": "Atuação no setor financeiro com Python, SQL e arquitetura de dados.",
            "original_url": "https://bancofavorito.com/vagas/eng-dados",
            "modality": "remoto",
            "seniority": "Sênior",
            "mandatory_requirements": ["Experiência sólida com Python e SQL"],
        },
    )
    assert j1.status_code == 201

    # Duplicate submission of same job must deduplicate (same id)
    j1_dup = client.post(
        "/api/v1/jobs/manual",
        headers=headers_a,
        json={
            "company_name": "Banco Favorito",
            "title": "Engenheiro de Dados Sênior",
            "description": "Atuação no setor financeiro com Python, SQL e arquitetura de dados.",
            "original_url": "https://bancofavorito.com/vagas/eng-dados",
            "modality": "remoto",
            "seniority": "Sênior",
        },
    )
    assert j1_dup.status_code == 201
    assert j1_dup.json()["id"] == j1.json()["id"]

    # 2. Identical job at NON-favorite company (must have identical total_score, lower priority_score)
    j2 = client.post(
        "/api/v1/jobs/manual",
        headers=headers_a,
        json={
            "company_name": "Banco Comum",
            "title": "Engenheiro de Dados Sênior",
            "description": "Atuação no setor financeiro com Python, SQL e arquitetura de dados.",
            "original_url": "https://bancocomum.com/vagas/eng-dados",
            "modality": "remoto",
            "seniority": "Sênior",
            "mandatory_requirements": ["Experiência sólida com Python e SQL"],
        },
    )
    assert j2.status_code == 201

    # 3. Excluded company job (must be marked inelegivel)
    j3 = client.post(
        "/api/v1/jobs/manual",
        headers=headers_a,
        json={
            "company_name": "Empresa Bloqueada",
            "title": "Engenheiro de Dados Sênior",
            "description": "Python e SQL.",
            "original_url": "https://bloqueada.com/vagas/1",
            "modality": "remoto",
        },
    )
    assert j3.status_code == 201

    # Run matching engine
    matches = client.post("/api/v1/jobs/matching/run", headers=headers_a)
    assert matches.status_code == 200
    data = matches.json()
    assert len(data) == 3

    fav_match = next(m for m in data if m["company_name"] == "Banco Favorito")
    common_match = next(m for m in data if m["company_name"] == "Banco Comum")
    blocked_match = next(m for m in data if m["company_name"] == "Empresa Bloqueada")

    # Favorite company does NOT inflate total_score, only priority_score
    assert fav_match["total_score"] == common_match["total_score"]
    assert fav_match["priority_score"] > common_match["priority_score"]
    assert fav_match["is_eligible"] is True
    assert fav_match["total_score"] >= 75.0
    assert len(fav_match["explanation"]["verifiable_evidence"]) >= 1

    # Excluded company is ineligible
    assert blocked_match["is_eligible"] is False
    assert blocked_match["classification"] == "inelegivel"

    # User B has no matches of User A
    assert client.get("/api/v1/jobs/matches/list", headers=headers_b).json() == []


def test_company_watch_handles_success_and_inaccessible_sources(client, monkeypatch):
    headers = _register_and_auth(client, "watch@exemplo.com", "Watch User")

    client.post(
        "/api/v1/targeting/companies",
        headers=headers,
        json={
            "name": "Nubank",
            "careers_page_url": "https://boards.greenhouse.io/nubank",
            "priority": "alta",
        },
    )
    client.post(
        "/api/v1/targeting/companies",
        headers=headers,
        json={
            "name": "Empresa Sem Link",
            "priority": "media",
        },
    )

    def fake_greenhouse(token, company_name=None):
        return [
            {
                "external_id": "gh-101",
                "company_name": company_name or "Nubank",
                "title": "Product Manager Sênior",
                "description": "Liderança de produto digital.",
                "original_url": "https://boards.greenhouse.io/nubank/jobs/101",
                "location": "São Paulo, SP",
                "modality": "hibrido",
                "seniority": "Sênior",
                "salary_range_text": None,
                "benefits": [],
                "published_at": None,
                "requirements": [],
            }
        ]

    monkeypatch.setattr("app.api.v1.jobs.fetch_greenhouse_jobs", fake_greenhouse)

    run_resp = client.post("/api/v1/jobs/company-watch/run", headers=headers)
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body["monitored_count"] == 1
    assert body["total_jobs_found"] == 1
    assert any(r["company_name"] == "Nubank" and r["status"] == "monitorada" for r in body["results"])
    assert any(r["company_name"] == "Empresa Sem Link" and r["status"] == "cadastrada" for r in body["results"])


def test_free_plan_five_monthly_analyses_limit(client):
    headers = _register_and_auth(client, "quota_free@exemplo.com", "Candidato Free")
    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["plan"]["plan_code"] == "free"
    assert summary.json()["plan"]["monthly_analyses_limit"] == 5

    # Create 1 active job and run matching 5 times (consuming 5 monthly analyses)
    j = client.post(
        "/api/v1/jobs/manual",
        headers=headers,
        json={
            "company_name": "Empresa Teste",
            "title": "Analista de Operações",
            "description": "Gestão operacional e melhoria contínua.",
            "original_url": "https://exemplo.com/vagas/op-1",
            "modality": "hibrido",
        },
    )
    assert j.status_code == 201

    for _ in range(5):
        r = client.post("/api/v1/jobs/matching/run", headers=headers)
        assert r.status_code == 200

    # 6th analysis in the same month must be blocked with 402
    blocked = client.post("/api/v1/jobs/matching/run", headers=headers)
    assert blocked.status_code == 402
    assert "5 análises" in blocked.json()["detail"]
