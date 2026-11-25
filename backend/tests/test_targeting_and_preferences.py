def test_target_roles_suggestions_csv_import_and_preferences(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "maria@exemplo.com", "full_name": "Maria Souza", "password": "SenhaForte123!"},
    ).json()
    headers = {"Authorization": f"Bearer {reg['access_token']}"}

    # Add verified experience so suggestions have real evidence
    client.post(
        "/api/v1/profile/experiences",
        headers=headers,
        json={
            "company_name": "Nubank",
            "role_title": "Analista de Dados Sênior",
            "leadership_experience": True,
            "validation_status": "verified",
        },
    )

    # AI suggestions should be grounded in evidence and NOT auto-added
    suggestions = client.get("/api/v1/targeting/roles/suggestions", headers=headers).json()
    assert len(suggestions) >= 1
    assert "Nubank" in suggestions[0]["justification"]
    assert client.get("/api/v1/targeting/roles", headers=headers).json() == []

    # User explicitly approves/creates target role
    created_role = client.post(
        "/api/v1/targeting/roles",
        headers=headers,
        json={
            "title": "Coordenador de Dados",
            "desired_seniority": "Coordenação",
            "priority": "alta",
            "synonyms": ["Data Lead", "Analytics Manager"],
            "modalities": ["remoto", "hibrido"],
            "desired_salary_brl": 18000,
        },
    )
    assert created_role.status_code == 201
    assert created_role.json()["status"] == "ativo"

    # CSV import for favorite companies
    csv_content = (
        "nome,site,carreiras,cidade,estado,setor,prioridade\n"
        "Itau Unibanco,https://itau.com.br,https://carreiras.itau.com.br,Sao Paulo,SP,Financeiro,alta\n"
        "Mercado Livre,https://mercadolivre.com.br,https://careers.mercadolibre.com,Osasco,SP,Tecnologia,alta\n"
    ).encode("utf-8")

    csv_resp = client.post(
        "/api/v1/targeting/companies/import-csv",
        headers=headers,
        files={"file": ("empresas.csv", csv_content, "text/csv")},
    )
    assert csv_resp.status_code == 200
    assert csv_resp.json()["imported_count"] == 2

    companies = client.get("/api/v1/targeting/companies", headers=headers).json()
    assert len(companies) == 2

    # Preferences & Agent config (application_mode must remain supervised)
    pref_resp = client.put(
        "/api/v1/profile/preferences",
        headers=headers,
        json={
            "current_city": "São Paulo",
            "current_state": "SP",
            "work_modalities": ["remoto", "hibrido"],
            "min_salary_brl": 15000,
            "desired_salary_brl": 18000,
            "search_frequency_hours": 12,
            "min_match_score": 75,
        },
    )
    assert pref_resp.status_code == 200
    assert pref_resp.json()["application_mode"] == "supervised"
    assert pref_resp.json()["min_match_score"] == 75
