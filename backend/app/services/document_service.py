from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from fastapi import UploadFile
from app.core.logging import logger
from app.core.errors import NotFoundException, ForbiddenException, ConflictException, ValidationException
from app.models.document import Document, DocumentVersion, DocumentMetadata, DocumentClassification
from app.models.case import Case
from app.models.client import Client
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.workflow import DocumentWorkflow
from app.services.storage_service import StorageService
from app.services.extraction_service import ExtractionService


class DocumentService:
    @staticmethod
    async def upload_document(
        db: Session,
        tenant_id: UUID,
        upload_file: UploadFile,
        title: Optional[str] = None,
        doc_type: str = DocumentClassification.CONTRATO,
        case_id: Optional[UUID] = None,
        client_id: Optional[UUID] = None,
        uploaded_by_id: Optional[UUID] = None,
        is_confidential: bool = False
    ) -> Document:
        """Carga, valida, almacena y procesa un documento jurídico de forma inmutable."""
        
        # Validar pertenencia de caso y cliente al despacho (Protección Horizontal)
        if case_id:
            case = db.query(Case).filter(Case.id == case_id, Case.tenant_id == tenant_id).first()
            if not case:
                raise NotFoundException("El expediente judicial especificado no pertenece a este despacho")
            if not client_id and case.client_id:
                client_id = case.client_id

        if client_id:
            client = db.query(Client).filter(Client.id == client_id, Client.tenant_id == tenant_id).first()
            if not client:
                raise NotFoundException("El cliente especificado no pertenece a este despacho")

        # 1. Almacenamiento seguro inmutable (WORM)
        storage_path, sha256_hash, file_size, mime_type, safe_filename = await StorageService.save_uploaded_file(
            upload_file=upload_file,
            tenant_id=str(tenant_id)
        )

        doc_title = title.strip() if title else safe_filename

        # 2. Extracción de texto y metadatos jurídicos
        extraction_result = ExtractionService.process_document_pipeline(storage_path, mime_type)

        # 3. Persistencia de la entidad Document (Original inmutable)
        doc = Document(
            tenant_id=tenant_id,
            case_id=case_id,
            client_id=client_id,
            uploaded_by_id=uploaded_by_id,
            title=doc_title,
            filename=safe_filename,
            file_size_bytes=file_size,
            mime_type=mime_type,
            sha256_hash=sha256_hash,
            storage_path=storage_path,
            doc_type=doc_type,
            is_original=True,
            is_confidential=is_confidential,
            page_count=extraction_result["page_count"]
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 4. Persistencia de Metadatos y Texto Extraído
        meta_data = extraction_result["metadata"]
        doc_meta = DocumentMetadata(
            document_id=doc.id,
            parties=meta_data.get("parties"),
            doc_date=meta_data.get("doc_date"),
            subject_matter=meta_data.get("subject_matter"),
            obligations=meta_data.get("obligations"),
            amounts=meta_data.get("amounts"),
            terms_deadlines=meta_data.get("terms_deadlines"),
            signers=meta_data.get("signers"),
            jurisdiction=meta_data.get("jurisdiction"),
            court_authority=meta_data.get("court_authority"),
            procedure_type=meta_data.get("procedure_type"),
            references=meta_data.get("references"),
            raw_text=extraction_result["safe_text"],
            ocr_applied=extraction_result["ocr_applied"],
            processing_time_ms=extraction_result["processing_time_ms"]
        )
        db.add(doc_meta)

        # 5. Auditoría
        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=uploaded_by_id,
            action="DOCUMENT_UPLOAD",
            resource_type="DOCUMENT",
            resource_id=str(doc.id),
            details={
                "title": doc.title,
                "filename": doc.filename,
                "sha256": sha256_hash,
                "size_bytes": file_size,
                "doc_type": doc_type
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(doc)

        return doc

    @staticmethod
    def get_document(
        db: Session,
        document_id: UUID,
        tenant_id: Optional[UUID],
        user_role: str,
        user_id: Optional[UUID] = None
    ) -> Document:
        """Obtiene un documento validando que pertenezca al despacho del solicitante y permisos RBAC."""
        norm_role = (user_role or "").upper()
        if norm_role == "SUPER_ADMIN":
            raise ForbiddenException("Aislamiento de Confidencialidad: El administrador global no tiene acceso a los documentos confidenciales del despacho.")

        if not tenant_id:
            raise ForbiddenException("El usuario no tiene un despacho asignado.")

        allowed_roles = [
            "ADMIN", "MANAGING_PARTNER",
            "LAWYER", "SENIOR_LAWYER", "ASSOCIATE_LAWYER",
            "REVIEWER", "AUDITOR",
            "ASSISTANT", "PARALEGAL", "LEGAL_ASSISTANT"
        ]
        if norm_role not in allowed_roles:
            raise ForbiddenException(f"El rol '{user_role}' no tiene autorización para acceder a documentos.")

        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()

        if not doc:
            raise NotFoundException("Documento no encontrado o no pertenece a este despacho")

        return doc

    @staticmethod
    def search_documents(
        db: Session,
        tenant_id: Optional[UUID],
        user_role: str,
        user_id: Optional[UUID] = None,
        query: Optional[str] = None,
        case_id: Optional[UUID] = None,
        client_id: Optional[UUID] = None,
        doc_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Document], int]:
        """Búsqueda avanzada con aislamiento multi-tenant y verificación de permisos RBAC."""
        norm_role = (user_role or "").upper()
        if norm_role == "SUPER_ADMIN":
            raise ForbiddenException("El administrador global de la plataforma no puede consultar documentos de despachos.")

        if not tenant_id:
            raise ForbiddenException("El usuario no tiene un despacho asignado para consultar documentos.")

        allowed_roles = [
            "ADMIN", "MANAGING_PARTNER",
            "LAWYER", "SENIOR_LAWYER", "ASSOCIATE_LAWYER",
            "REVIEWER", "AUDITOR",
            "ASSISTANT", "PARALEGAL", "LEGAL_ASSISTANT"
        ]
        if norm_role not in allowed_roles:
            raise ForbiddenException(f"El rol '{user_role}' no tiene autorización para consultar documentos.")

        q = db.query(Document).filter(Document.tenant_id == tenant_id)

        # Validación estricta por expediente (Case-Level Access Control)
        if case_id:
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case or case.tenant_id != tenant_id:
                raise NotFoundException("Expediente no encontrado o no pertenece a este despacho")

            # Si el usuario no es Admin / Managing Partner, verificar asignación en el expediente
            if norm_role not in ["ADMIN", "MANAGING_PARTNER"]:
                has_permission = False
                if case.lead_lawyer_id is None or case.lead_lawyer_id == user_id:
                    has_permission = True
                else:
                    # Verificar si el usuario está asignado al flujo de algún documento del caso
                    assignment = db.query(DocumentWorkflow).join(Document).filter(
                        Document.case_id == case_id,
                        Document.tenant_id == tenant_id,
                        or_(
                            DocumentWorkflow.assigned_lawyer_id == user_id,
                            DocumentWorkflow.reviewer_id == user_id,
                            DocumentWorkflow.assistant_id == user_id
                        )
                    ).first()
                    if assignment:
                        has_permission = True

                if not has_permission:
                    raise ForbiddenException("No cuenta con permisos asignados para consultar documentos de este expediente.")

            q = q.filter(Document.case_id == case_id)

        if client_id:
            client = db.query(Client).filter(Client.id == client_id, Client.tenant_id == tenant_id).first()
            if not client:
                raise NotFoundException("Cliente no encontrado o no pertenece a este despacho")
            q = q.filter(Document.client_id == client_id)

        if doc_type:
            q = q.filter(Document.doc_type == doc_type)

        if query:
            clean_q = f"%{query.strip()}%"
            # Búsqueda en título, nombre de archivo o en texto extraído (vía join con metadata)
            q = q.outerjoin(DocumentMetadata).filter(
                or_(
                    Document.title.ilike(clean_q),
                    Document.filename.ilike(clean_q),
                    DocumentMetadata.raw_text.ilike(clean_q)
                )
            )

        total = q.count()
        docs = q.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
        return docs, total

    @staticmethod
    async def create_document_version(
        db: Session,
        document_id: UUID,
        tenant_id: UUID,
        upload_file: UploadFile,
        created_by_id: UUID,
        change_summary: str
    ) -> DocumentVersion:
        """Crea una versión subsecuente de un documento sin modificar el original."""
        doc = db.query(Document).filter(Document.id == document_id, Document.tenant_id == tenant_id).first()
        if not doc:
            raise NotFoundException("Documento no encontrado")

        storage_path, sha256_hash, file_size, mime_type, safe_filename = await StorageService.save_uploaded_file(
            upload_file=upload_file,
            tenant_id=str(tenant_id)
        )

        # Determinar número de versión siguiente (v1 es el original inmutable, primera derivada es v2)
        latest_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == doc.id
        ).order_by(desc(DocumentVersion.version_number)).first()
        current_max_ver = (latest_version.version_number + 1) if latest_version else 2

        version = DocumentVersion(
            document_id=doc.id,
            created_by_id=created_by_id,
            version_number=current_max_ver,
            storage_path=storage_path,
            sha256_hash=sha256_hash,
            file_size_bytes=file_size,
            change_summary=change_summary
        )
        db.add(version)
        db.commit()
        db.refresh(version)

        # Audit
        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=created_by_id,
            action="DOCUMENT_NEW_VERSION",
            resource_type="DOCUMENT_VERSION",
            resource_id=str(version.id),
            details={"document_id": str(doc.id), "version": current_max_ver, "sha256": sha256_hash}
        )
        db.add(audit)
        db.commit()

        # Invalidación automática de aprobaciones previas al modificarse el contenido del documento
        try:
            from app.services.workflow.approval_service import ApprovalService
            approval_svc = ApprovalService(db)
            approval_svc.invalidate_approvals_on_change(
                document_id=doc.id,
                new_version_number=current_max_ver,
                reason=f"Nueva versión {current_max_ver} generada: {change_summary}"
            )
            db.commit()
        except Exception as e:
            logger.warning(f"No se pudo invalidar aprobaciones previas para Doc:{doc.id}: {e}")

        return version
