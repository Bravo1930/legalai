from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Entorno
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "LegalAI México"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Servidor
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Seguridad & Criptografía
    SECRET_KEY: str = "legal_ai_default_secret_key_change_in_production_32chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 horas
    ALGORITHM: str = "HS256"

    # PostgreSQL
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "legal_ai_db"
    DATABASE_URL: str = "postgresql://postgres@localhost:5432/legal_ai_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    # Ollama Local (IA Soberana en Localhost o Servidor Privado)
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_API_KEY: str = ""  # Bearer token para proxy autenticado mTLS/Nginx
    OLLAMA_EMBEDDING_MODEL: str = "bge-m3:latest"
    OLLAMA_LLM_MODEL: str = "qwen3.5:4b"
    OLLAMA_CODER_MODEL: str = "qwen2.5-coder:7b"
    OLLAMA_TIMEOUT_SECONDS: int = 120
    OLLAMA_ALLOW_PUBLIC_IPS: bool = False  # Barrera de datos: bloqueo estricto de exfiltración a IPs públicas o nubes externas
    OLLAMA_VERIFY_SSL: bool = True

    # Almacenamiento Documental Inmutable (WORM Local / S3 / MinIO)
    STORAGE_BACKEND: str = "local"  # "local" | "s3"
    LOCAL_STORAGE_PATH: str = "./storage/tenants"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "legal-ai-documents-vault"
    S3_ENDPOINT_URL: str = ""  # Para MinIO local (e.g. http://minio:9000) o AWS S3
    S3_SERVER_SIDE_ENCRYPTION: str = "AES256"  # "AES256" | "aws:kms"
    S3_KMS_KEY_ID: str = ""  # ARN de llave KMS de AWS cuando corresponda
    STORAGE_WORM_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/legal_ai.log"


settings = Settings()
