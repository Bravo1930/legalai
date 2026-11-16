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


@pytest.fixture(scope="session")
def setup_second_tenant(db_session):
    """Crea o reutiliza un segundo despacho y abogado para probar aislamiento horizontal sin duplicados."""
    slug_b = "despacho-b-test"
    tenant_b = db_session.query(Tenant).filter(Tenant.slug == slug_b).first()
    if not tenant_b:
        tenant_b = Tenant(
            name="Corporativo Jurídico del Norte S.C.",
            slug=slug_b,
            rfc="CJN220303XY9",
            contact_email="contacto@despacho-b-test.com"
        )
        db_session.add(tenant_b)
        db_session.commit()
        db_session.refresh(tenant_b)

    email_b = "abogado@despacho-b-test.com"
    user_b = db_session.query(User).filter(User.email == email_b).first()
    if not user_b:
        user_b = User(
            tenant_id=tenant_b.id,
            email=email_b,
            hashed_password=get_password_hash("Password1234!"),
            full_name="Lic. Roberto Garza Treviño",
            role=LegalRoles.SENIOR_LAWYER,
            professional_license="87654321"
        )
        db_session.add(user_b)
        db_session.commit()
        db_session.refresh(user_b)

    token_b = create_access_token({
        "sub": str(user_b.id),
        "email": user_b.email,
        "tenant_id": str(tenant_b.id),
        "tenant_slug": tenant_b.slug,
        "role": user_b.role
    })

    return {
        "tenant": tenant_b,
        "user": user_b,
        "headers": {"Authorization": f"Bearer {token_b}"}
    }
