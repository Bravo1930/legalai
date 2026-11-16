import time
import uuid
import asyncio
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
from app.models.rule import LegalRule, RuleCategory, RuleSeverity, RuleOperator
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

        # Seed inicial: Usuarios con los 4 roles del despacho demo
        demo_roles_users = [
            ("admin@bufetemexico.demo", "Lic. Roberto González Garza", LegalRoles.ADMIN, "11223344"),
            ("abogado@bufetemexico.demo", "Lic. Sofía Valenzuela Márquez", LegalRoles.SENIOR_LAWYER, "98765432"),
            ("revisor@bufetemexico.demo", "Lic. Carlos Mendoza Silva", LegalRoles.REVIEWER, "77889900"),
            ("asistente@bufetemexico.demo", "Pasante Mariana Estrada Ríos", LegalRoles.ASSISTANT, None),
        ]
        for demo_email, demo_name, demo_role, demo_cedula in demo_roles_users:
            existing_user = db.query(User).filter(User.email == demo_email).first()
            if not existing_user:
                db_user = User(
                    tenant_id=demo_tenant.id,
                    email=demo_email,
                    hashed_password=get_password_hash("Password1234!"),
                    full_name=demo_name,
                    role=demo_role,
                    professional_license=demo_cedula
                )
                db.add(db_user)
                logger.info(f"Usuario del despacho creado: {demo_email} con rol {demo_role}")
            else:
                # Asegurar contraseña consistente para el entorno de desarrollo
                existing_user.hashed_password = get_password_hash("Password1234!")
                existing_user.role = demo_role
        db.commit()

        # Seed inicial: Reglas Deterministas Estándar de la Legislación Mexicana
        existing_rules_count = db.query(LegalRule).filter(LegalRule.tenant_id == demo_tenant.id).count()
        if existing_rules_count == 0:
            logger.info("Sembrando catálogo maestro de reglas deterministas (México)...")
            initial_rules = [
                LegalRule(
                    id=uuid.uuid4(),
                    tenant_id=demo_tenant.id,
                    rule_code="REG-JUR-CDMX",
                    name="Sometimiento Expreso a Tribunales de la Ciudad de México",
                    description="Verifica que las controversias se sometan a los juzgados de la CDMX con renuncia a cualquier otro fuero.",
                    category=RuleCategory.JURISDICTION,
                    severity=RuleSeverity.CRITICAL,
                    is_active=True,
                    scope={"doc_types": ["*"]},
                    condition_definition={
                        "operator": RuleOperator.CONTAINS_ALL_KEYWORDS,
                        "parameters": {"keywords": ["tribunales", "ciudad de méxico"]}
                    },
                    expected_outcome="Sometimiento formal y expreso a los tribunales de la CDMX.",
                    legal_foundation="Art. 1093 del Código de Comercio",
                    version=1,
                    created_by_id=admin_user.id if admin_user else None,
                ),
                LegalRule(
                    id=uuid.uuid4(),
                    tenant_id=demo_tenant.id,
                    rule_code="REG-PROH-RENUNCIA",
                    name="Prohibición de Renuncia a Prestaciones o Derechos Laborales",
                    description="Detecta cláusulas ilícitas que pretendan eximir al patrón de indemnizaciones o finiquitos de ley.",
                    category=RuleCategory.PROHIBITED_CLAUSE,
                    severity=RuleSeverity.CRITICAL,
                    is_active=True,
                    scope={"doc_types": ["*"]},
                    condition_definition={
                        "operator": RuleOperator.PROHIBITS_KEYWORDS,
                        "parameters": {"prohibited_keywords": ["renuncia irrevocable de prestaciones", "sin derecho a liquidación", "renuncia a derechos laborales"]}
                    },
                    expected_outcome="No contener renuncia a prestaciones mínimas constitucionales.",
                    legal_foundation="Art. 33 de la Ley Federal del Trabajo y Art. 123 Constitucional",
                    version=1,
                    created_by_id=admin_user.id if admin_user else None,
                ),
                LegalRule(
                    id=uuid.uuid4(),
                    tenant_id=demo_tenant.id,
                    rule_code="REG-CONF-LFPPI",
                    name="Cláusula de Confidencialidad y Secreto Industrial",
                    description="Obligación contractual de guardar reserva absoluta sobre secretos comerciales y técnicos.",
                    category=RuleCategory.CONFIDENTIALITY,
                    severity=RuleSeverity.HIGH,
                    is_active=True,
                    scope={"doc_types": ["CONTRATO", "CONVENIO"]},
                    condition_definition={
                        "operator": RuleOperator.CONTAINS_ALL_KEYWORDS,
                        "parameters": {"keywords": ["información confidencial", "secreto industrial"]}
                    },
                    expected_outcome="Pacto expreso de confidencialidad y protección de secretos industriales.",
                    legal_foundation="Art. 82 y 85 de la Ley Federal de Protección a la Propiedad Industrial",
                    version=1,
                    created_by_id=admin_user.id if admin_user else None,
                ),
                LegalRule(
                    id=uuid.uuid4(),
                    tenant_id=demo_tenant.id,
                    rule_code="REG-DATOS-LFPDPPP",
                    name="Cumplimiento de Protección de Datos Personales (LFPDPPP)",
                    description="Verifica la existencia del aviso de privacidad y tratamiento de datos personales.",
                    category=RuleCategory.DATA_PROTECTION,
                    severity=RuleSeverity.HIGH,
                    is_active=True,
                    scope={"doc_types": ["*"]},
                    condition_definition={
                        "operator": RuleOperator.CONTAINS_ANY_KEYWORD,
                        "parameters": {"keywords": ["aviso de privacidad", "datos personales", "lfpdppp"]}
                    },
                    expected_outcome="Referencia a aviso de privacidad conforme a la LFPDPPP.",
                    legal_foundation="Ley Federal de Protección de Datos Personales en Posesión de los Particulares",
                    version=1,
                    created_by_id=admin_user.id if admin_user else None,
                )
            ]
            db.add_all(initial_rules)
            db.commit()
            logger.info(f"{len(initial_rules)} reglas iniciales sembradas exitosamente.")

        # Seed de demostración jurídica condicional (controlado por settings.SEED_DEMO)
        from app.db.seed_demo import seed_demo_legal_data
        seed_demo_legal_data(db, demo_tenant.id)
    except Exception as e:
        logger.error(f"Error durante el seed inicial: {e}")
        db.rollback()
    finally:
        db.close()


async def background_queue_worker():
    """Worker asíncrono en segundo plano que procesa tareas encoladas en PostgreSQL/Redis."""
    from app.services.task_service import TaskService
    logger.info("Iniciando LegalAI Async Task Queue Worker en FastAPI...")
    while True:
        try:
            def _run_batch():
                db = SessionLocal()
                try:
                    return TaskService.process_pending_tasks_batch(db, max_tasks=5)
                finally:
                    db.close()

            processed = await asyncio.to_thread(_run_batch)
            if processed > 0:
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            logger.info("Deteniendo LegalAI Async Task Queue Worker...")
            break
        except Exception as e:
            logger.error(f"Error en worker asíncrono en segundo plano: {e}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicio: inicialización de BD y recursos
    logger.info(f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    init_database_and_seed()
    worker_task = asyncio.create_task(background_queue_worker())
    yield
    # Cierre: limpieza
    logger.info(f"Deteniendo {settings.PROJECT_NAME}...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


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


# Configuración de CORS (Outermost Middleware en FastAPI/Starlette)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time", "Content-Disposition"],
    max_age=600,
)


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
