import os
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document, DocumentClassification
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentPreviewResponse, DocumentVersionResponse
from app.services.document_service import DocumentService
from app.services.auth_service import get_current_user
from app.core.errors import NotFoundException, ForbiddenException, ValidationException

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, summary="Cargar y procesar documento jurídico inmutable")
async def upload_document(
    file: UploadFile = File(..., description="Archivo en formato PDF, DOCX, TXT o imagen"),
    title: Optional[str] = Form(None),
    doc_type: str = Form(DocumentClassification.CONTRATO),
    case_id: Optional[UUID] = Form(None),
    client_id: Optional[UUID] = Form(None),
    is_confidential: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Carga un documento en la bóveda inmutable (WORM).
    Calcula SHA-256, valida firma mágica binaria, extrae texto y metadatos legales.
    """
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("El administrador de plataforma no puede cargar documentos a despachos ajenos.")

    return await DocumentService.upload_document(
        db=db,
        tenant_id=current_user.tenant_id,
        upload_file=file,
        title=title,
        doc_type=doc_type,
        case_id=case_id,
        client_id=client_id,
        uploaded_by_id=current_user.id,
        is_confidential=is_confidential
    )


@router.post("/upload-multiple", response_model=List[DocumentResponse], summary="Cargar múltiples documentos en lote")
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    doc_type: str = Form(DocumentClassification.CONTRATO),
    case_id: Optional[UUID] = Form(None),
    client_id: Optional[UUID] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Carga y procesa una lista de documentos en una sola operación."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("Acceso restringido al plano de control.")

    uploaded_docs = []
    for f in files:
        doc = await DocumentService.upload_document(
            db=db,
            tenant_id=current_user.tenant_id,
            upload_file=f,
            title=None,
            doc_type=doc_type,
            case_id=case_id,
            client_id=client_id,
            uploaded_by_id=current_user.id
        )
        uploaded_docs.append(doc)
    return uploaded_docs


@router.get("", response_model=DocumentListResponse, summary="Búsqueda y consulta de documentos")
def search_documents(
    query: Optional[str] = Query(None, description="Búsqueda por texto en contenido, título o nombre"),
    case_id: Optional[UUID] = Query(None, description="Filtrar por expediente"),
    client_id: Optional[UUID] = Query(None, description="Filtrar por cliente"),
    doc_type: Optional[str] = Query(None, description="Filtrar por tipo jurídico (CONTRATO, DEMANDA, etc.)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Búsqueda avanzada con aislamiento multi-tenant y protección contra IDOR."""
    docs, total = DocumentService.search_documents(
        db=db,
        tenant_id=current_user.tenant_id,
        user_role=current_user.role,
        user_id=current_user.id,
        query=query,
        case_id=case_id,
        client_id=client_id,
        doc_type=doc_type,
        skip=skip,
        limit=limit
    )
    return DocumentListResponse(items=docs, total=total)


@router.get("/{document_id}", response_model=DocumentResponse, summary="Obtener metadatos y detalle de documento")
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consulta la ficha completa de un documento y sus metadatos extraídos."""
    return DocumentService.get_document(
        db=db,
        document_id=document_id,
        tenant_id=current_user.tenant_id,
        user_role=current_user.role,
        user_id=current_user.id
    )


@router.get("/{document_id}/preview", response_model=DocumentPreviewResponse, summary="Vista previa del contenido de texto")
def preview_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el texto sanitizado y los metadatos para vista previa en el frontend."""
    doc = DocumentService.get_document(
        db=db,
        document_id=document_id,
        tenant_id=current_user.tenant_id,
        user_role=current_user.role,
        user_id=current_user.id
    )

    raw_text = doc.metadata_record.raw_text if doc.metadata_record else "No hay texto extraído disponible."
    
    return DocumentPreviewResponse(
        id=doc.id,
        title=doc.title,
        filename=doc.filename,
        doc_type=doc.doc_type,
        sha256_hash=doc.sha256_hash,
        page_count=doc.page_count,
        raw_text=raw_text,
        metadata=doc.metadata_record
    )


@router.get("/{document_id}/download", summary="Descarga autorizada de archivo inmutable")
def download_document(
    document_id: UUID,
    version_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Descarga el archivo físico validando la sesión del usuario del despacho."""
    doc = DocumentService.get_document(
        db=db,
        document_id=document_id,
        tenant_id=current_user.tenant_id,
        user_role=current_user.role,
        user_id=current_user.id
    )

    file_path = doc.storage_path
    filename = doc.filename

    if version_id:
        version = next((v for v in doc.versions if v.id == version_id), None)
        if not version:
            raise NotFoundException("La versión solicitada no existe")
        file_path = version.storage_path
        filename = f"v{version.version_number}_{doc.filename}"

    if not os.path.exists(file_path):
        raise NotFoundException("El archivo físico no se encuentra en el almacenamiento")

    return FileResponse(
        path=file_path,
        media_type=doc.mime_type,
        filename=filename
    )


@router.post("/{document_id}/versions", response_model=DocumentVersionResponse, summary="Registrar versión derivada de un documento")
async def create_document_version(
    document_id: UUID,
    file: UploadFile = File(...),
    change_summary: str = Form(..., min_length=5, description="Justificación del cambio o revisión"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una versión adicional conservando el documento original intacto."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("Acceso restringido al plano de control.")

    return await DocumentService.create_document_version(
        db=db,
        document_id=document_id,
        tenant_id=current_user.tenant_id,
        upload_file=file,
        created_by_id=current_user.id,
        change_summary=change_summary
    )
