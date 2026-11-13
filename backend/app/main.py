import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import setup_exception_handlers
from app.core.security import get_password_hash, LegalRoles
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.api.v1.api import api_router


def init_database_and_seed():
    """Inicializa el esquema de base de datos y crea el seed maestro inicial."""
    logger.info("Verificando e inicializando tablas en PostgreSQL...")
    Base.metadata.create_all(bind=engine)

    # Seed inicial: Despacho Demo y Superadministrador
    db = SessionLocal()
    try:
        demo_tenant = db.query(Tenant).filter(Tenant.slug == "despacho-demo").first()
        if not demo_tenant:
            logger.info("Creando despacho inicial de demostración...")
            demo_tenant = Tenant(
                name="Bufete Jurídico México & Asociados",
                slug="despacho-demo",
                rfc="BJM200101AB1",
                contact_email="contacto@bufetemexico.demo"
            )
            db.add(demo_tenant)
            db.commit()
            db.refresh(demo_tenant)

        # Crear Superadministrador si no existe
        admin_user = db.query(User).filter(User.email == "admin@legalai.mx").first()
        if not admin_user:
            logger.info("Creando usuario administrador maestro (admin@legalai.mx)...")
            admin_user = User(
                tenant_id=demo_tenant.id,
                email="admin@legalai.mx",
                hashed_password=get_password_hash("Admin1234!"),
                full_name="Lic. Alejandro Morales Garza",
                role=LegalRoles.SUPER_ADMIN,
                professional_license="12345678"
            )
            db.add(admin_user)
            db.commit()
            logger.info("Usuario maestro creado exitosamente con rol SUPER_ADMIN.")
    except Exception as e:
        logger.error(f"Error durante el seed inicial: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicio: inicialización de BD y recursos
    logger.info(f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    init_database_and_seed()
    yield
    # Cierre: limpieza
    logger.info(f"Deteniendo {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Plataforma Empresarial de Inteligencia Artificial para Revisión y Gestión Documental Jurídica (México)",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# Configuración de Errores Centralizados
setup_exception_handlers(app)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de Trazabilidad, Request-ID y Logging
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Latency: {process_time:.2f}ms",
        extra={"request_id": request_id}
    )
    return response


# Montar Enrutadores v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": f"{settings.API_V1_PREFIX}/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health"
    }
