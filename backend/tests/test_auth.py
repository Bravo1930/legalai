def test_login_successful(client):
    """Verifica inicio de sesión exitoso con credenciales válidas."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@legalai.mx",
            "password": "Admin1234!",
            "tenant_slug": "despacho-demo"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@legalai.mx"
    assert data["user"]["role"] == "SUPER_ADMIN"


def test_login_invalid_password(client):
    """Verifica rechazo con contraseña incorrecta."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@legalai.mx",
            "password": "PasswordIncorrecta999!",
            "tenant_slug": "despacho-demo"
        }
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_get_me(client, auth_headers):
    """Verifica endpoint /me con token JWT válido."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@legalai.mx"
    assert data["tenant_slug"] == "despacho-demo"
