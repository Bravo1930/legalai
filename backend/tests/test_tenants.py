import uuid


def test_list_tenants(client, auth_headers):
    """Verifica listado de despachos por superadministrador."""
    response = client.get("/api/v1/tenants", headers=auth_headers)
    assert response.status_code == 200
    tenants = response.json()
    assert isinstance(tenants, list)
    assert any(t["slug"] == "despacho-demo" for t in tenants)


def test_create_tenant(client, auth_headers):
    """Verifica registro de un nuevo despacho jurídico."""
    slug_test = f"despacho-test-{uuid.uuid4().hex[:6]}"
    payload = {
        "name": "Firma Jurídica y Litigio Civil S.C.",
        "slug": slug_test,
        "rfc": "FJL210202XY8",
        "contact_email": f"contacto@{slug_test}.mx"
    }
    response = client.post("/api/v1/tenants", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == slug_test
    assert data["name"] == payload["name"]


def test_unauthorized_access_denied(client):
    """Verifica que sin token no se permita el acceso a rutas protegidas."""
    response = client.get("/api/v1/tenants")
    assert response.status_code == 401
