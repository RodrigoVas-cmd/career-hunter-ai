def _register_user(client, email: str, full_name: str, password: str = "SenhaForte123!"):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_register_login_and_me(client):
    reg = _register_user(client, "ana@exemplo.com", "Ana Silva")
    assert reg["email"] == "ana@exemplo.com"
    assert reg["role"] == "user"
    assert reg["onboarding_step"] == 1
    assert reg["onboarding_completed"] is False

    # Duplicate email returns 409
    dup = client.post(
        "/api/v1/auth/register",
        json={"email": "ana@exemplo.com", "full_name": "Ana 2", "password": "SenhaForte123!"},
    )
    assert dup.status_code == 409

    # Wrong password returns 401
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@exemplo.com", "password": "wrong"},
    )
    assert bad_login.status_code == 401

    # Valid login
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@exemplo.com", "password": "SenhaForte123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # Protected /me
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["full_name"] == "Ana Silva"

    # Unauthenticated /me returns 401
    no_auth = client.get("/api/v1/auth/me")
    assert no_auth.status_code == 401


def test_strict_multiuser_isolation(client):
    user_a = _register_user(client, "usera@exemplo.com", "Usuário A")
    user_b = _register_user(client, "userb@exemplo.com", "Usuário B")
    headers_a = {"Authorization": f"Bearer {user_a['access_token']}"}
    headers_b = {"Authorization": f"Bearer {user_b['access_token']}"}

    # User A creates experience, skill, target role, and favorite company
    exp = client.post(
        "/api/v1/profile/experiences",
        headers=headers_a,
        json={"company_name": "Empresa Alfa", "role_title": "Gerente de Produto"},
    )
    assert exp.status_code == 201
    exp_id = exp.json()["id"]

    role = client.post(
        "/api/v1/targeting/roles",
        headers=headers_a,
        json={"title": "Head de Produto", "priority": "alta"},
    )
    assert role.status_code == 201
    role_id = role.json()["id"]

    comp = client.post(
        "/api/v1/targeting/companies",
        headers=headers_a,
        json={"name": "Tech Brasil", "priority": "alta"},
    )
    assert comp.status_code == 201
    fav_id = comp.json()["id"]

    # User B sees empty lists for all private resources
    assert client.get("/api/v1/profile/experiences", headers=headers_b).json() == []
    assert client.get("/api/v1/targeting/roles", headers=headers_b).json() == []
    assert client.get("/api/v1/targeting/companies", headers=headers_b).json() == []

    # User B cannot update or delete User A's records
    assert (
        client.patch(
            f"/api/v1/profile/experiences/{exp_id}",
            headers=headers_b,
            json={"validation_status": "verified"},
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/api/v1/targeting/roles/{role_id}", headers=headers_b).status_code == 404
    )
    assert (
        client.delete(f"/api/v1/targeting/companies/{fav_id}", headers=headers_b).status_code == 404
    )
