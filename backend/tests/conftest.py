import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.config import settings
from app.db.session import Base, get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash, LegalRoles

# Configuración de cliente de pruebas para FastAPI
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def db_session():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def auth_headers(client):
    """Genera token de autenticación para el usuario administrador de pruebas."""
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={
            "email": "admin@legalai.mx",
            "password": "Admin1234!",
            "tenant_slug": "despacho-demo"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
