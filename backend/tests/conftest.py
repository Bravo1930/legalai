import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.config import settings
from app.db.session import Base, get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash, LegalRoles, create_access_token


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
    """Token para el usuario SUPER_ADMIN maestro de la plataforma."""
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


@pytest.fixture(scope="session")
def lawyer_headers(db_session):
    """Token para un Abogado Titular (LAWYER) dentro del despacho demo."""
    demo_tenant = db_session.query(Tenant).filter(Tenant.slug == "despacho-demo").first()
    
    lawyer_user = db_session.query(User).filter(User.email == "abogado@bufetemexico.demo").first()
    if not lawyer_user:
        lawyer_user = User(
            tenant_id=demo_tenant.id,
            email="abogado@bufetemexico.demo",
            hashed_password=get_password_hash("Abogado2026!"),
            full_name="Lic. Sofía Valenzuela Márquez",
            role=LegalRoles.SENIOR_LAWYER,
            professional_license="98765432"
        )
        db_session.add(lawyer_user)
        db_session.commit()
        db_session.refresh(lawyer_user)

    token = create_access_token({
        "sub": str(lawyer_user.id),
        "email": lawyer_user.email,
        "tenant_id": str(demo_tenant.id),
        "tenant_slug": demo_tenant.slug,
        "role": lawyer_user.role,
        "professional_license": lawyer_user.professional_license
    })
    return {"Authorization": f"Bearer {token}"}
