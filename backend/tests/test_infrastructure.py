import os
import pytest
from unittest.mock import MagicMock, patch
from app.services.ai.ollama_client import OllamaClient
from app.services.storage_service import StorageService
from app.core.errors import ForbiddenException

def test_ollama_private_endpoint_security_guard():
    """Valida la política de Soberanía de Datos y Secreto Profesional (Zero Cloud Egress)."""
    # 1. Endpoints privados autorizados permitidos
    allowed_urls = [
        "http://localhost:11434",
        "http://127.0.0.1:11434",
        "http://192.168.1.100:11434",
        "http://10.0.1.50:11434",
        "http://172.20.0.5:11434",
        "http://ollama:11434",
        "http://ollama-service.internal:11434",
    ]
    for url in allowed_urls:
        client = OllamaClient(base_url=url, allow_public_ips=False)
        assert client.base_url == url.rstrip("/")

    # 2. Endpoints públicos o nubes comerciales prohibidos
    forbidden_urls = [
        "https://api.openai.com/v1",
        "https://api.anthropic.com/v1",
        "http://8.8.8.8:11434",
        "http://1.1.1.1:11434",
        "https://ai-instance.us-east-1.amazonaws.com",
        "http://public-server.com:11434",
    ]
    for url in forbidden_urls:
        with pytest.raises(ForbiddenException) as exc_info:
            OllamaClient(base_url=url, allow_public_ips=False)
        err_msg = str(exc_info.value).lower()
        assert any(k in err_msg for k in ["confidencialidad", "soberan", "prohibido", "pública", "publica"])

    # 3. Admisión explícita si se autoriza explícitamente allow_public_ips=True
    client_allowed = OllamaClient(base_url="https://api.custom-private-cloud.com", allow_public_ips=True)
    assert client_allowed.allow_public_ips is True

def test_storage_service_s3_mocked():
    """Valida la interacción con almacenamiento S3/MinIO compatible."""
    with patch("app.services.storage_service.boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        with patch("app.core.config.settings.STORAGE_BACKEND", "s3"), \
             patch("app.core.config.settings.S3_BUCKET_NAME", "legal-vault"), \
             patch("app.core.config.settings.S3_SERVER_SIDE_ENCRYPTION", "AES256"):

            s3_uri = StorageService._upload_to_s3(
                content=b"CONTENIDO JURIDICO CONFIDENCIAL",
                tenant_id="tenant-123",
                sha256_hash="abc123hash",
                detected_type="pdf",
                mime_type="application/pdf",
                safe_filename="contrato.pdf"
            )

            assert s3_uri == "s3://legal-vault/tenants/tenant-123/documents/abc123hash.pdf"
            assert mock_s3.put_object.called
            call_kwargs = mock_s3.put_object.call_args[1]
            assert call_kwargs["Bucket"] == "legal-vault"
            assert call_kwargs["Key"] == "tenants/tenant-123/documents/abc123hash.pdf"
            assert call_kwargs["ServerSideEncryption"] == "AES256"
            assert call_kwargs["Metadata"]["sha256"] == "abc123hash"
            assert call_kwargs["Metadata"]["tenant_id"] == "tenant-123"

            # Validar URL prefirmada
            mock_s3.generate_presigned_url.return_value = "https://legal-vault.s3.amazonaws.com/test?token=signed"
            url = StorageService.generate_presigned_download_url("tenants/tenant-123/documents/abc123hash.pdf", expires_in=3600)
            assert url is not None
            assert "token=signed" in url
            mock_s3.generate_presigned_url.assert_called_with(
                "get_object",
                Params={"Bucket": "legal-vault", "Key": "tenants/tenant-123/documents/abc123hash.pdf"},
                ExpiresIn=3600
            )

def test_infrastructure_artifacts_exist():
    """Valida la existencia de todos los artefactos requeridos para despliegue y DRP."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    expected_files = [
        "docker-compose.prod.yml",
        ".env.production.example",
        ".env.hybrid.example",
        "DEPLOYMENT.md",
        "DISASTER_RECOVERY.md",
        "NETWORK_ARCHITECTURE.md",
        "SECURITY.md",
        os.path.join("nginx", "nginx.conf"),
        os.path.join("scripts", "backup_db.sh"),
        os.path.join("scripts", "restore_db.sh"),
        os.path.join("scripts", "backup_db.ps1"),
        os.path.join("scripts", "restore_db.ps1"),
        os.path.join("backend", "Dockerfile"),
        os.path.join("frontend", "Dockerfile"),
    ]

    for rel_path in expected_files:
        full_path = os.path.join(repo_root, rel_path)
        assert os.path.exists(full_path), f"Falta el archivo de infraestructura requerido: {rel_path}"
