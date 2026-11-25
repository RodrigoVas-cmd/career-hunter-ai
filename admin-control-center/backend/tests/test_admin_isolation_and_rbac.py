def _bootstrap_superadmin(client):
    r = client.post(
        "/api/v1/admin/auth/bootstrap",
        json={
            "email": "owner@careerhunter.ai",
            "full_name": "Proprietário",
            "password": "AdminSenhaForte123!",
        },
    )
    assert r.status_code == 201
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_rbac_and_last_superadmin_protection(client):
    # Unauthenticated blocked
    assert client.get("/api/v1/admin/dashboard/executive").status_code == 401

    super_headers = _bootstrap_superadmin(client)
    # Second bootstrap blocked
    r2 = client.post(
        "/api/v1/admin/auth/bootstrap",
        json={"email": "hacker@x.com", "full_name": "Hacker", "password": "AdminSenhaForte123!"},
    )
    assert r2.status_code == 403

    # Create support admin
    sup_resp = client.post(
        "/api/v1/admin/auth/accounts",
        headers=super_headers,
        json={
            "email": "suporte@careerhunter.ai",
            "full_name": "Suporte",
            "password": "SuporteSenha123!",
            "admin_role": "support",
        },
    )
    assert sup_resp.status_code == 201

    sup_login = client.post(
        "/api/v1/admin/auth/login",
        json={"email": "suporte@careerhunter.ai", "password": "SuporteSenha123!"},
    )
    sup_headers = {"Authorization": f"Bearer {sup_login.json()['access_token']}"}

    # Support can read users, but CANNOT change plans or delete users
    assert client.get("/api/v1/admin/users", headers=sup_headers).status_code == 200
    assert (
        client.post(
            "/api/v1/admin/users/user-free-1/manage-plan",
            headers=sup_headers,
            json={"action": "change_plan", "plan_code": "pro", "justification": "Teste RBAC"},
        ).status_code
        == 403
    )

    # Cannot disable the last active superadmin
    me = client.get("/api/v1/admin/auth/me", headers=super_headers).json()
    last_disable = client.patch(
        f"/api/v1/admin/auth/accounts/{me['id']}/status",
        headers=super_headers,
        json={"is_active": False, "justification": "Teste de proteção"},
    )
    assert last_disable.status_code == 400


def test_existing_pro_preserved_courtesies_and_plan_management(client):
    headers = _bootstrap_superadmin(client)

    # Executive dashboard counts existing Pro as unclassified (NOT paid revenue)
    dash = client.get("/api/v1/admin/dashboard/executive", headers=headers).json()
    assert dash["users"]["total"] == 2
    assert dash["users"]["pro"] == 1
    assert dash["users"]["free"] == 1
    assert dash["users"]["modalities"]["unclassified"] == 1
    assert dash["financial"]["verified_mrr_brl_cents"] == 0

    # Grant 30-day courtesy Premium to Free user (no billing generated)
    courtesy = client.post(
        "/api/v1/admin/users/user-free-1/manage-plan",
        headers=headers,
        json={
            "action": "grant_courtesy",
            "plan_code": "premium",
            "duration_type": "30d",
            "justification": "Cortesia para testador beta aprovado.",
        },
    )
    assert courtesy.status_code == 200

    detail = client.get("/api/v1/admin/users/user-free-1", headers=headers).json()
    assert detail["plan_code"] == "premium"
    assert detail["access_modality"] == "courtesy"
    assert detail["plan_price_brl_cents"] == 0
    assert detail["courtesy"]["duration_type"] == "30d"

    # Grant 20 extra analysis credits
    cred = client.post(
        "/api/v1/admin/users/user-free-1/manage-plan",
        headers=headers,
        json={
            "action": "grant_credits",
            "credit_metric": "job_analysis",
            "credit_amount": 20,
            "justification": "Créditos extras de teste.",
        },
    )
    assert cred.status_code == 200
    detail_after = client.get("/api/v1/admin/users/user-free-1", headers=headers).json()
    assert detail_after["usage"]["extra_analysis_credits"] == 20

    # Revoke courtesy -> returns to Free
    rev = client.post(
        "/api/v1/admin/users/user-free-1/manage-plan",
        headers=headers,
        json={"action": "revoke_courtesy", "justification": "Fim do período de cortesia."},
    )
    assert rev.status_code == 200
    detail_rev = client.get("/api/v1/admin/users/user-free-1", headers=headers).json()
    assert detail_rev["plan_code"] == "free"
    assert detail_rev["access_modality"] == "free"


def test_suspend_reactivate_lgpd_delete_and_audit_logs(client):
    headers = _bootstrap_superadmin(client)

    susp = client.post(
        "/api/v1/admin/users/user-free-1/status",
        headers=headers,
        json={"action": "suspend", "justification": "Suspeita de abuso de API."},
    )
    assert susp.status_code == 200
    assert susp.json()["is_active"] is False

    react = client.post(
        "/api/v1/admin/users/user-free-1/status",
        headers=headers,
        json={"action": "activate", "justification": "Verificação concluída."},
    )
    assert react.status_code == 200
    assert react.json()["is_active"] is True

    # LGPD delete requires exact confirmation phrase
    bad_del = client.request(
        "DELETE",
        "/api/v1/admin/users/user-free-1",
        headers=headers,
        json={"confirmation_text": "apagar", "justification": "Solicitação do titular"},
    )
    assert bad_del.status_code == 400

    ok_del = client.request(
        "DELETE",
        "/api/v1/admin/users/user-free-1",
        headers=headers,
        json={
            "confirmation_text": "EXCLUIR DEFINITIVAMENTE",
            "justification": "Solicitação LGPD validada para conta de teste.",
        },
    )
    assert ok_del.status_code == 200

    audits = client.get("/api/v1/admin/ops/audit-logs", headers=headers).json()
    assert any(a["action"] == "user.lgpd_deleted" for a in audits)
