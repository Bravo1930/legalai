import os
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from app.models.document import Document, DocumentVersion
from app.models.user import User
from app.models.advanced_analysis import LegalFinding
from app.models.modification import (
    ModificationProposalBatch, LegalModificationProposal,
    ProposalBatchStatus, ProposalItemStatus
)
from app.core.security import LegalRoles
from app.services.modifications.proposal_generator import ProposalGenerator
from app.services.modifications.version_compiler import VersionCompiler
from app.services.modifications.document_exporter import DocumentExporter
from app.services.analysis.defect_detector import DefectDetector
from app.services.analysis.clause_decomposer import ClauseDecomposer


class ModificationService:
    """Servicio orquestador del módulo de propuestas de modificación y exportación jurídica."""

    def __init__(self, db: Session):
        self.db = db
        self.version_compiler = VersionCompiler(db)

    def generate_proposals_batch(
        self,
        tenant_id: uuid.UUID,
        user: User,
        document_id: uuid.UUID,
        title: Optional[str] = None,
        objective: str = "BALANCED",
        finding_ids: Optional[List[uuid.UUID]] = None
    ) -> ModificationProposalBatch:
        # 1. Seguridad
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso restringido por diseño: El administrador global no puede generar propuestas sobre documentos de clientes."
            )

        # 2. Obtener documento
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")

        # 3. Obtener texto seguro
        raw_text = ""
        if document.metadata_record and document.metadata_record.raw_text:
            raw_text = document.metadata_record.raw_text
        elif document.storage_path and os.path.exists(document.storage_path):
            with open(document.storage_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()

        if not raw_text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El documento no tiene texto para generar propuestas.")

        # 4. Obtener o calcular los hallazgos a subsanar
        findings = []
        if finding_ids:
            findings = self.db.query(LegalFinding).filter(
                LegalFinding.id.in_(finding_ids),
                LegalFinding.tenant_id == tenant_id
            ).all()
        else:
            # Obtener los hallazgos existentes en BD
            findings = self.db.query(LegalFinding).filter(
                LegalFinding.document_id == document_id,
                LegalFinding.tenant_id == tenant_id
            ).all()

            # Si no hay hallazgos en BD, detectarlos directamente
            if not findings:
                clauses = ClauseDecomposer.decompose(raw_text)
                detected_raw = DefectDetector.detect_all(raw_text, clauses, document.doc_type or "CONTRATO")
                for d in detected_raw:
                    findings.append(LegalFinding(
                        id=uuid.uuid4(),
                        session_id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        document_id=document_id,
                        finding_code="TEMP-FINDING",
                        issue_type=d["issue_type"],
                        title=d["title"],
                        description=d["description"],
                        severity=d["severity"],
                        original_fragment=d.get("original_fragment"),
                        location=d.get("location"),
                        clause_ref=d.get("clause_ref"),
                        legal_foundation=d.get("legal_foundation"),
                        risk_explanation=d["risk_explanation"],
                        recommendation=d["recommendation"],
                        confidence_score=d.get("confidence_score", 0.9),
                        confidence_level="HIGH",
                        review_status="PENDING_REVIEW"
                    ))

        # 5. Generar propuestas con estricta adherencia a reglas sin alucinación
        generated_data = ProposalGenerator.generate_proposals_from_findings(raw_text, findings)

        # 6. Guardar lote en Base de Datos
        batch_id = uuid.uuid4()
        batch_title = title or f"Lote de Propuestas de Redacción ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')})"
        
        batch = ModificationProposalBatch(
            id=batch_id,
            tenant_id=tenant_id,
            document_id=document_id,
            created_by_id=user.id,
            title=batch_title,
            objective=objective,
            status=ProposalBatchStatus.PENDING_REVIEW,
            total_proposals=len(generated_data),
            accepted_count=0,
            rejected_count=0,
            pending_count=len(generated_data),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.db.add(batch)
        self.db.flush()

        for item in generated_data:
            f_id = item.get("finding_id")
            if f_id:
                exists = self.db.query(LegalFinding.id).filter(LegalFinding.id == f_id).first()
                if not exists:
                    f_id = None

            prop = LegalModificationProposal(
                id=uuid.uuid4(),
                batch_id=batch_id,
                tenant_id=tenant_id,
                document_id=document_id,
                finding_id=f_id,
                clause_title=item["clause_title"],
                problem_explanation=item["problem_explanation"],
                original_text=item["original_text"],
                proposed_text=item["proposed_text"],
                alternative_options=item.get("alternative_options", []),
                missing_data_placeholders=item.get("missing_data_placeholders", []),
                legal_foundation=item.get("legal_foundation"),
                diff_summary=item.get("diff_summary"),
                status=ProposalItemStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(prop)

        self.db.commit()
        self.db.refresh(batch)
        return batch

    def list_batches_for_document(self, tenant_id: uuid.UUID, user: User, document_id: uuid.UUID) -> List[ModificationProposalBatch]:
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido para SUPER_ADMIN.")

        return self.db.query(ModificationProposalBatch).filter(
            ModificationProposalBatch.tenant_id == tenant_id,
            ModificationProposalBatch.document_id == document_id
        ).order_by(desc(ModificationProposalBatch.created_at)).all()

    def get_batch(self, tenant_id: uuid.UUID, user: User, batch_id: uuid.UUID) -> ModificationProposalBatch:
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido para SUPER_ADMIN.")

        batch = self.db.query(ModificationProposalBatch).filter(
            ModificationProposalBatch.id == batch_id,
            ModificationProposalBatch.tenant_id == tenant_id
        ).first()
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote de propuestas no encontrado.")
        return batch

    def review_proposal_item(
        self,
        tenant_id: uuid.UUID,
        lawyer_user: User,
        proposal_id: uuid.UUID,
        status_val: str,
        lawyer_final_text: Optional[str] = None,
        lawyer_notes: Optional[str] = None,
        reviewer_license: Optional[str] = None
    ) -> LegalModificationProposal:
        """Permite que el abogado acepte, rechace o modifique la redacción propuesta (HITL)."""
        if lawyer_user.role not in [LegalRoles.SENIOR_LAWYER, LegalRoles.MANAGING_PARTNER, LegalRoles.ASSOCIATE_LAWYER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un abogado facultado puede autorizar modificaciones de cláusulas."
            )

        prop = self.db.query(LegalModificationProposal).filter(
            LegalModificationProposal.id == proposal_id,
            LegalModificationProposal.tenant_id == tenant_id
        ).first()
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Propuesta no encontrada.")

        prop.status = status_val
        if lawyer_final_text is not None:
            prop.lawyer_final_text = lawyer_final_text
        if lawyer_notes is not None:
            prop.lawyer_notes = lawyer_notes
        prop.reviewed_by_id = lawyer_user.id
        prop.reviewer_license = reviewer_license or lawyer_user.professional_license
        prop.reviewed_at = datetime.now(timezone.utc)

        # Recalcular contadores del lote
        batch = prop.batch
        all_items = batch.items
        accepted = sum(1 for it in all_items if it.status in [ProposalItemStatus.ACCEPTED, ProposalItemStatus.MODIFIED_BY_LAWYER])
        rejected = sum(1 for it in all_items if it.status == ProposalItemStatus.REJECTED)
        pending = sum(1 for it in all_items if it.status == ProposalItemStatus.PENDING)

        batch.accepted_count = accepted
        batch.rejected_count = rejected
        batch.pending_count = pending
        
        if pending == 0 and accepted > 0 and rejected == 0:
            batch.status = ProposalBatchStatus.FULLY_ACCEPTED
        elif accepted > 0:
            batch.status = ProposalBatchStatus.PARTIALLY_ACCEPTED
        elif pending == 0 and rejected > 0 and accepted == 0:
            batch.status = ProposalBatchStatus.REJECTED

        batch.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(prop)
        return prop

    def compile_new_version(
        self,
        tenant_id: uuid.UUID,
        lawyer_user: User,
        batch_id: uuid.UUID,
        version_notes: str,
        reviewer_license: Optional[str] = None
    ) -> DocumentVersion:
        """Aplica los cambios aceptados y crea una nueva versión oficial del documento."""
        doc_version, _ = self.version_compiler.compile_new_version_from_batch(
            tenant_id=tenant_id,
            lawyer_user=lawyer_user,
            batch_id=batch_id,
            version_notes=version_notes,
            reviewer_license=reviewer_license or lawyer_user.professional_license or "12345678"
        )
        return doc_version

    def export_document_file(
        self,
        tenant_id: uuid.UUID,
        user: User,
        document_id: uuid.UUID,
        export_format: str,
        version_number: Optional[int] = None
    ) -> Tuple[bytes, str, str]:
        """Exporta el documento a DOCX o PDF retornando (bytes, filename, media_type)."""
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido para SUPER_ADMIN.")

        doc = self.db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")

        text_to_export = ""
        version_label = "Versión Original"
        sha_hash = doc.sha256_hash

        if version_number and version_number > 1:
            ver = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == version_number
            ).first()
            if ver and ver.storage_path and os.path.exists(ver.storage_path):
                with open(ver.storage_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_to_export = f.read()
                version_label = f"Versión {ver.version_number} (Revisada)"
                sha_hash = ver.sha256_hash

        if not text_to_export:
            if doc.metadata_record and doc.metadata_record.raw_text:
                text_to_export = doc.metadata_record.raw_text
            elif doc.storage_path and os.path.exists(doc.storage_path):
                with open(doc.storage_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_to_export = f.read()

        clean_title = doc.title or "Documento Jurídico"
        base_filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', clean_title).strip('_')

        if export_format.lower() == "docx":
            file_bytes = DocumentExporter.export_to_docx(
                title=clean_title,
                content_text=text_to_export,
                sha256_hash=sha_hash,
                version_label=version_label
            )
            return file_bytes, f"{base_filename}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif export_format.lower() == "pdf":
            file_bytes = DocumentExporter.export_to_pdf(
                title=clean_title,
                content_text=text_to_export,
                sha256_hash=sha_hash,
                version_label=version_label
            )
            return file_bytes, f"{base_filename}.pdf", "application/pdf"
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato no soportado. Elija 'docx' o 'pdf'.")
