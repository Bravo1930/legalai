from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

# Creación de motor SQLAlchemy 2.0
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Generador de sesión de base de datos con manejo transaccional."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> dict:
    """Verifica el estado de conexión real con PostgreSQL y la presencia de pgvector."""
    try:
        with engine.connect() as conn:
            # Versión de PostgreSQL
            pg_version = conn.execute(text("SELECT version();")).scalar()
            
            # Verificar si la extensión vector está instalada
            vector_installed = conn.execute(
                text("SELECT count(*) FROM pg_extension WHERE extname = 'vector';")
            ).scalar()
            
            return {
                "status": "healthy",
                "version": pg_version,
                "pgvector_enabled": bool(vector_installed > 0)
            }
    except Exception as e:
        logger.error(f"Fallo al conectar con PostgreSQL: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "pgvector_enabled": False
        }
