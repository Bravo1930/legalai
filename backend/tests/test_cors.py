import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cors_direct_health_check():
    """1. Petición directa al backend (health check) sin cabecera Origin."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data


def test_cors_origin_localhost_3001():
    """2. Petición con Origin: http://localhost:3001 al endpoint health."""
    origin = "http://localhost:3001"
    response = client.get("/api/v1/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_origin_127_0_0_1_3001():
    """3. Petición con Origin: http://127.0.0.1:3001 al endpoint health."""
    origin = "http://127.0.0.1:3001"
    response = client.get("/api/v1/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_options_health():
    """4. Petición preflight OPTIONS al endpoint health con cabeceras CORS."""
    origin = "http://localhost:3001"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Request-ID, Content-Type"
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "GET" in allow_methods
    allow_headers = response.headers.get("access-control-allow-headers", "")
    assert "X-Request-ID" in allow_headers or "*" in allow_headers


def test_cors_preflight_options_auth_login():
    """5. Petición preflight OPTIONS a endpoints de autenticación (/auth/login)."""
    origin = "http://localhost:3001"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization, X-Request-ID"
    }
    response = client.options("/api/v1/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods


def test_cors_exposed_headers():
    """6. Verificación de cabeceras expuestas en respuestas exitosas y de error."""
    origin = "http://localhost:3001"
    # Petición exitosa
    response = client.get("/api/v1/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers

    # Petición con error (404 Not Found)
    err_response = client.get("/api/v1/non-existent-endpoint", headers={"Origin": origin})
    assert err_response.status_code == 404
    assert err_response.headers.get("access-control-allow-origin") == origin


def test_cors_unauthorized_origin_rejection():
    """7. Verificación de rechazo de orígenes no autorizados."""
    bad_origin = "http://malicious-site.com"
    
    # Simple GET request: el backend procesa pero NO añade Access-Control-Allow-Origin
    response = client.get("/api/v1/health", headers={"Origin": bad_origin})
    assert "access-control-allow-origin" not in response.headers
    
    # Preflight OPTIONS request: Starlette rechaza explícitamente con 400 Bad Request
    headers = {
        "Origin": bad_origin,
        "Access-Control-Request-Method": "GET"
    }
    preflight = client.options("/api/v1/health", headers=headers)
    assert preflight.status_code == 400
    assert "access-control-allow-origin" not in preflight.headers
    assert "Disallowed CORS" in preflight.text


def test_cors_authenticated_workflow():
    """8. Flujo de autenticación funcional con token Bearer y Origin permitido."""
    origin = "http://localhost:3001"
    
    # 1. Login con Origin
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@legalai.mx", "password": "Admin1234!"},
        headers={"Origin": origin}
    )
    assert login_resp.status_code == 200
    assert login_resp.headers.get("access-control-allow-origin") == origin
    tokens = login_resp.json()
    token = tokens["access_token"]
    assert token

    # 2. Consultar /auth/me con Bearer token y Origin
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={
            "Origin": origin,
            "Authorization": f"Bearer {token}"
        }
    )
    assert me_resp.status_code == 200
    assert me_resp.headers.get("access-control-allow-origin") == origin
    assert me_resp.headers.get("access-control-allow-credentials") == "true"
    user_data = me_resp.json()
    assert user_data["email"] == "admin@legalai.mx"
