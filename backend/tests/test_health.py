def test_root_endpoint(client):
    """Verifica que el endpoint raíz responda correctamente."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "LegalAI México"
    assert "version" in data
    assert "docs_url" in data


def test_health_check_endpoint(client):
    """Verifica que el health check audite la base de datos y los servicios."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "ollama" in data
    assert data["database"]["status"] == "healthy"
