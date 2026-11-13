from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.modification import (
    ModificationProposalBatchResponse,
    LegalModificationProposalResponse,
    GenerateProposalsRequest,
    ReviewProposalItemRequest,
    CompileNewVersionRequest
)
from app.schemas.document import DocumentVersionResponse
from app.services.auth_service import get_current_user
from app.services.modifications.modification_service import ModificationService

router = APIRouter()


@router.post("/generate/{document_id}", response_model=ModificationProposalBatchResponse, status_code=status.HTTP_201_CREATED, summary="Generar lote de propuestas y alternativas de redacción")
def generate_proposals(
    document_id: UUID,
    data: GenerateProposalsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera propuestas de modificación de cláusulas, alternativas y redacción corregida
    conforme a la legislación mexicana. No inventa hechos y marca pendientes explícitos.
    """
    service = ModificationService(db)
    return service.generate_proposals_batch(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id,
        title=data.title,
        objective=data.objective,
        finding_ids=data.finding_ids
    )


@router.get("/batches/{document_id}", response_model=List[ModificationProposalBatchResponse], summary="Listar lotes de propuestas generadas para el documento")
def list_batches(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna el historial de lotes de modificación del documento."""
    service = ModificationService(db)
    return service.list_batches_for_document(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id
    )


@router.get("/batch/{batch_id}", response_model=ModificationProposalBatchResponse, summary="Consultar detalle de un lote con sus propuestas y diffs")
def get_batch_detail(
    batch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Consulta todas las propuestas granulares de un lote con sus alternativas y comparativas."""
    service = ModificationService(db)
    return service.get_batch(
        tenant_id=current_user.tenant_id,
        user=current_user,
        batch_id=batch_id
    )


@router.patch("/proposals/{proposal_id}/review", response_model=LegalModificationProposalResponse, summary="Aceptar, rechazar o ajustar redacción propuesta (HITL)")
def review_proposal(
    proposal_id: UUID,
    review_data: ReviewProposalItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permite que un abogado facultado acepte, rechace o modifique una propuesta de cláusula,
    registrando su cédula profesional y justificación.
    """
    service = ModificationService(db)
    return service.review_proposal_item(
        tenant_id=current_user.tenant_id,
        lawyer_user=current_user,
        proposal_id=proposal_id,
        status_val=review_data.status,
        lawyer_final_text=review_data.lawyer_final_text,
        lawyer_notes=review_data.lawyer_notes,
        reviewer_license=review_data.reviewer_license
    )


@router.post("/batch/{batch_id}/apply-version", response_model=DocumentVersionResponse, status_code=status.HTTP_201_CREATED, summary="Compilar cambios aprobados y crear una nueva versión oficial")
def apply_version(
    batch_id: UUID,
    comp_data: CompileNewVersionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aplica únicamente las modificaciones aceptadas por el abogado sobre el texto
    y genera una nueva versión inmutable con cálculo de hash SHA-256 y firma legal.
    """
    service = ModificationService(db)
    return service.compile_new_version(
        tenant_id=current_user.tenant_id,
        lawyer_user=current_user,
        batch_id=batch_id,
        version_notes=comp_data.version_notes,
        reviewer_license=comp_data.reviewer_license
    )


@router.get("/export/docx/{document_id}", summary="Exportar documento o versión a formato Microsoft Word (.docx)")
def export_docx(
    document_id: UUID,
    version: Optional[int] = Query(None, description="Número de versión a exportar (omita para original)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exporta el documento a DOCX profesional con estilos legales, márgenes y bloques de firma."""
    service = ModificationService(db)
    file_bytes, filename, media_type = service.export_document_file(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id,
        export_format="docx",
        version_number=version
    )
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/pdf/{document_id}", summary="Exportar documento o versión a formato PDF legal")
def export_pdf(
    document_id: UUID,
    version: Optional[int] = Query(None, description="Número de versión a exportar (omita para original)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exporta el documento a PDF legal con foliado 'Página X de Y', membrete y hash SHA-256."""
    service = ModificationService(db)
    file_bytes, filename, media_type = service.export_document_file(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id,
        export_format="pdf",
        version_number=version
    )
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
