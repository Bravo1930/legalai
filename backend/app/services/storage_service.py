import os
import hashlib
import io
import re
from typing import Tuple, Optional
from fastapi import UploadFile
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import ValidationException, AppException

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


# Firmas binarias (Magic Bytes) para validación de tipo real
MAGIC_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "docx": [b"PK\x03\x04"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpeg": [b"\xff\xd8\xff"],
    "jpg": [b"\xff\xd8\xff"],
    "tiff": [b"II*\x00", b"MM\x00*"],
    "txt": None  # Validación por decodificación UTF-8
}


class StorageService:
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitiza el nombre del archivo para prevenir ataques de Path Traversal."""
        clean = os.path.basename(filename)
        clean = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', clean)
        return clean.strip() or "documento_sin_nombre.pdf"

    @staticmethod
    def detect_file_type(header_bytes: bytes, filename: str) -> str:
        """Verifica el tipo MIME real mediante Magic Bytes y no solo la extensión."""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        # Comprobar firmas mágicas
        for file_type, signatures in MAGIC_SIGNATURES.items():
            if signatures:
                for sig in signatures:
                    if header_bytes.startswith(sig):
                        return file_type

        # Caso texto plano
        if ext in ["txt", "log", "csv"]:
            try:
                header_bytes[:1024].decode("utf-8")
                return "txt"
            except UnicodeDecodeError:
                pass

        return "unknown"

    @staticmethod
    def validate_file_integrity(file_bytes: bytes, file_type: str) -> None:
        """Verifica que el archivo no esté corrupto, truncado o dañado."""
        if file_type == "pdf":
            try:
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                if doc.page_count < 1:
                    raise ValidationException("El archivo PDF no contiene páginas válidas.")
                doc.close()
            except Exception as e:
                raise ValidationException(f"El archivo PDF está dañado o no pudo abrirse: {str(e)}")

        elif file_type == "docx":
            try:
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
            except Exception as e:
                raise ValidationException(f"El archivo DOCX está dañado o es inválido: {str(e)}")

        elif file_type in ["png", "jpeg", "jpg", "tiff"]:
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(file_bytes))
                img.verify()
            except Exception as e:
                raise ValidationException(f"El archivo de imagen está dañado: {str(e)}")

    @staticmethod
    async def save_uploaded_file(
        upload_file: UploadFile,
        tenant_id: str
    ) -> Tuple[str, str, int, str, str]:
        """
        Lee, valida, calcula SHA-256 y almacena de forma inmutable (WORM) el archivo.
        Retorna: (storage_path, sha256_hash, file_size_bytes, mime_type, safe_filename)
        """
        safe_filename = StorageService.sanitize_filename(upload_file.filename or "archivo.pdf")
        content = await upload_file.read()
        file_size = len(content)

        if file_size == 0:
            raise ValidationException("El archivo cargado se encuentra vacío (0 bytes).")

        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValidationException(f"El tamaño del archivo ({file_size / (1024*1024):.2f} MB) excede el límite permitido de 50 MB.")

        # Detección de tipo real
        detected_type = StorageService.detect_file_type(content[:32], safe_filename)
        if detected_type == "unknown":
            raise ValidationException(
                f"Formato no permitido o firma binaria no reconocida para '{safe_filename}'. "
                "Formatos permitidos: PDF, DOCX, TXT, PNG, JPEG, TIFF."
            )

        # Validación de integridad de archivo
        StorageService.validate_file_integrity(content, detected_type)

        # Cálculo criptográfico SHA-256
        sha256_hash = hashlib.sha256(content).hexdigest()

        # Determinar MIME Type canónico
        mime_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
            "png": "image/png",
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "tiff": "image/tiff"
        }
        mime_type = mime_map.get(detected_type, "application/octet-stream")

        # Almacenamiento seguro aislado por despacho
        tenant_vault_dir = os.path.join(settings.LOCAL_STORAGE_PATH, str(tenant_id), "documents")
        os.makedirs(tenant_vault_dir, exist_ok=True)

        target_file_path = os.path.join(tenant_vault_dir, f"{sha256_hash}.{detected_type}")

        # Principio WORM: Si ya existe el archivo con idéntico SHA-256, se conserva intacto
        if not os.path.exists(target_file_path):
            with open(target_file_path, "wb") as f:
                f.write(content)
            logger.info(f"Documento almacenado en bóveda inmutable: {target_file_path} (SHA-256: {sha256_hash})")
        else:
            logger.info(f"Documento con idéntico hash SHA-256 ya existe en bóveda: {target_file_path}")

        # Integración S3 / MinIO (si STORAGE_BACKEND=s3)
        if settings.STORAGE_BACKEND == "s3":
            StorageService._upload_to_s3(
                content=content,
                tenant_id=str(tenant_id),
                sha256_hash=sha256_hash,
                detected_type=detected_type,
                mime_type=mime_type,
                safe_filename=safe_filename
            )

        return target_file_path, sha256_hash, file_size, mime_type, safe_filename

    @classmethod
    def _get_s3_client(cls):
        """Inicializa el cliente de boto3 con soporte para AWS S3 o MinIO."""
        if not BOTO3_AVAILABLE:
            raise AppException("boto3 no está instalado en el entorno.")
        client_kwargs = {
            "region_name": settings.AWS_REGION,
        }
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        return boto3.client("s3", **client_kwargs)

    @classmethod
    def _upload_to_s3(
        cls,
        content: bytes,
        tenant_id: str,
        sha256_hash: str,
        detected_type: str,
        mime_type: str,
        safe_filename: str
    ) -> str:
        """Sube el objeto a S3/MinIO con cifrado en reposo (SSE-S3 o KMS) y metadata WORM."""
        s3 = cls._get_s3_client()
        s3_key = f"tenants/{tenant_id}/documents/{sha256_hash}.{detected_type}"
        
        extra_args = {
            "ContentType": mime_type,
            "Metadata": {
                "sha256": sha256_hash,
                "tenant_id": tenant_id,
                "filename": safe_filename
            }
        }
        if settings.S3_SERVER_SIDE_ENCRYPTION:
            extra_args["ServerSideEncryption"] = settings.S3_SERVER_SIDE_ENCRYPTION
            if settings.S3_KMS_KEY_ID:
                extra_args["SSEKMSKeyId"] = settings.S3_KMS_KEY_ID

        try:
            s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=s3_key,
                Body=content,
                **extra_args
            )
            logger.info(f"Documento sincronizado con bóveda S3 ({settings.S3_BUCKET_NAME}/{s3_key})")
            return f"s3://{settings.S3_BUCKET_NAME}/{s3_key}"
        except Exception as e:
            logger.error(f"Error al subir documento a S3: {e}")
            raise AppException(f"Fallo en persistencia de bóveda S3: {str(e)}")

    @classmethod
    def generate_presigned_download_url(cls, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """Genera una URL prefirmada para descarga autorizada temporal sin exponer credenciales."""
        if settings.STORAGE_BACKEND != "s3":
            return None
        try:
            s3 = cls._get_s3_client()
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Error al generar URL prefirmada S3: {e}")
            return None
