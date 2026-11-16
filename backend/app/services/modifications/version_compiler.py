import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from app.models.document import Document, DocumentVersion
from app.models.modification import (
    ModificationProposalBatch, LegalModificationProposal,
    ProposalBatchStatus, ProposalItemStatus
)
from app.models.approval import LegalApproval, ApprovalStatus
from app.models.user import User
from app.core.security import LegalRoles
from app.core.config import settings


class VersionCompiler:
    """
    Compilador de nuevas versiones documentales a partir de propuestas aprobadas por abogados.
    
    GARANTÍAS:
    1. Inmutabilidad del original: El documento base jamás se sobreescribe.
    2. Trazabilidad absoluta: Se registra qué abogado autorizó cada cambio y su cédula profesional.
    3. Cero aplicación silenciosa: Solo los cambios expresamente aceptados o modificados por el abogado
       se incorporan a la nueva versión compilada.
    """

    def __init__(self, db: Session):
        self.db = db

    def compile_new_version_from_batch(
        self,
        tenant_id: uuid.UUID,
        lawyer_user: User,
        batch_id: uuid.UUID,
        version_notes: str,
        reviewer_license: str
    ) -> Tuple[DocumentVersion, str]:
        # 1. Validar facultades del abogado (HITL)
        if lawyer_user.role not in [LegalRoles.SENIOR_LAWYER, LegalRoles.LAWYER, LegalRoles.MANAGING_PARTNER, LegalRoles.ADMIN, LegalRoles.ASSOCIATE_LAWYER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un abogado autorizado con cédula profesional puede aprobar y compilar nuevas versiones vinculantes."
            )

        # 2. Obtener lote de propuestas
        batch = self.db.query(ModificationProposalBatch).filter(
            ModificationProposalBatch.id == batch_id,
            ModificationProposalBatch.tenant_id == tenant_id
        ).first()
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote de propuestas no encontrado.")

        # 3. Obtener propuestas aprobadas o ajustadas
        approved_proposals = [
            item for item in batch.items
            if item.status in [ProposalItemStatus.ACCEPTED, ProposalItemStatus.MODIFIED_BY_LAWYER]
        ]
        if not approved_proposals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay propuestas marcadas como ACEPTADAS en este lote para compilar una nueva versión."
            )

        # 4. Obtener documento y texto base
        document = batch.document
        base_text = ""
        if document.metadata_record and document.metadata_record.raw_text:
            base_text = document.metadata_record.raw_text
        elif document.storage_path and os.path.exists(document.storage_path):
            with open(document.storage_path, "r", encoding="utf-8", errors="ignore") as f:
                base_text = f.read()

        if not base_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se localizó el texto base del documento para compilar la nueva versión."
            )

        # 5. Aplicar modificaciones aprobadas sobre el texto
        compiled_text = base_text
        applied_changes_summary = []
        omissions_to_append = []

        for prop in approved_proposals:
            replacement_text = prop.lawyer_final_text if prop.lawyer_final_text else prop.proposed_text
            
            # Si es sustitución de texto existente
            if prop.original_text and prop.original_text in compiled_text and not prop.original_text.startswith("[CLÁUSULA NO EXISTENTE"):
                compiled_text = compiled_text.replace(prop.original_text, replacement_text, 1)
                applied_changes_summary.append(f"Cláusula '{prop.clause_title}': Modificación aprobada.")
            else:
                # Si fue una omisión añadida (ej. Confidencialidad o Datos Personales)
                omissions_to_append.append(replacement_text)
                applied_changes_summary.append(f"Cláusula '{prop.clause_title}': Adición incorporada.")

        # Si hay cláusulas omitidas que fueron añadidas, insertarlas ordenadamente antes del cierre
        if omissions_to_append:
            # Buscar sección de firmas o jurisdicción para insertar antes
            signature_pos = compiled_text.lower().find("firmas")
            if signature_pos == -1:
                signature_pos = compiled_text.lower().find("enteradas las partes")
            
            addition_block = "\n\n" + "\n\n".join(omissions_to_append) + "\n\n"
            if signature_pos != -1:
                compiled_text = compiled_text[:signature_pos] + addition_block + compiled_text[signature_pos:]
            else:
                compiled_text = compiled_text + addition_block

        # 6. Calcular nuevo hash SHA-256 del texto compilado
        compiled_bytes = compiled_text.encode("utf-8")
        new_sha256 = hashlib.sha256(compiled_bytes).hexdigest()

        # 7. Determinar siguiente número de versión
        latest_version = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document.id
        ).order_by(desc(DocumentVersion.version_number)).first()

        next_version_num = (latest_version.version_number + 1) if latest_version else 2

        # 8. Guardar archivo compilado en el almacenamiento inmutable
        tenant_storage_dir = os.path.join(settings.LOCAL_STORAGE_PATH, str(tenant_id), "documents")
        os.makedirs(tenant_storage_dir, exist_ok=True)
        version_filename = f"v{next_version_num}_{new_sha256[:16]}.txt"
        version_filepath = os.path.join(tenant_storage_dir, version_filename)

        with open(version_filepath, "wb") as f:
            f.write(compiled_bytes)

        # 9. Crear registro DocumentVersion
        change_summary_full = f"{version_notes} | Cambios aplicados: {len(applied_changes_summary)} propuesta(s) aprobada(s)."
        doc_version = DocumentVersion(
            id=uuid.uuid4(),
            document_id=document.id,
            version_number=next_version_num,
            storage_path=version_filepath,
            sha256_hash=new_sha256,
            file_size_bytes=len(compiled_bytes),
            created_by_id=lawyer_user.id,
            change_summary=change_summary_full,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(doc_version)

        # 10. Actualizar lote de propuestas
        batch.status = ProposalBatchStatus.APPLIED_TO_NEW_VERSION
        batch.applied_version_number = next_version_num
        batch.updated_at = datetime.now(timezone.utc)

        # 10.5 Regla de aprobación: Invalidar automáticamente aprobaciones de versiones anteriores
        from app.services.workflow.approval_service import ApprovalService
        approval_srv = ApprovalService(self.db)
        approval_srv.invalidate_approvals_on_change(
            document_id=document.id,
            new_version_number=next_version_num,
            reason=f"Se compiló la versión oficial {next_version_num} alterando el contenido de las versiones previas."
        )

        # 11. Registro formal de aprobación humana (HITL)
        approval = LegalApproval(
            id=uuid.uuid4(),
            document_id=document.id,
            reviewer_id=lawyer_user.id,
            status=ApprovalStatus.APPROVED,
            professional_license=reviewer_license or lawyer_user.professional_license,
            reviewer_name=lawyer_user.full_name,
            notes=f"Versión {next_version_num} aprobada formalmente. {version_notes}",
            approved_hash=new_sha256,
            created_at=datetime.now(timezone.utc),
            resolved_at=datetime.now(timezone.utc)
        )
        self.db.add(approval)

        self.db.commit()
        self.db.refresh(doc_version)
        return doc_version, compiled_text
