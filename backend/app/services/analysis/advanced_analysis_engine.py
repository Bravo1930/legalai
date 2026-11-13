import os
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from app.models.document import Document, DocumentVersion
from app.models.user import User
from app.models.rule import LegalRule, RuleEvaluationStatus
from app.models.advanced_analysis import (
    AdvancedAnalysisSession, LegalFinding, ClauseDecomposition, VersionComparison,
    FindingSeverity, FindingReviewStatus, FindingIssueType
)
from app.core.security import LegalRoles
from app.services.analysis.clause_decomposer import ClauseDecomposer
from app.services.analysis.defect_detector import DefectDetector
from app.services.analysis.version_comparator import VersionComparator
from app.services.rules.rule_engine import DeterministicRuleEngine


class AdvancedAnalysisEngine:
    """
    Motor Avanzado de Análisis Jurídico Documental para México.
    
    PRINCIPIOS:
    1. Una puntuación de riesgo generada por el sistema es una herramienta de priorización,
       no una conclusión jurídica definitiva (HITL mandatario).
    2. Rigor epistemológico en fundamentación mexicana (DOF, SCJN, Cámara de Diputados).
    3. Cero alucinación normativa: no afirmar vigencia sin verificación en catálogo oficial.
    """

    def __init__(self, db: Session):
        self.db = db
        self.rule_engine = DeterministicRuleEngine()

    def analyze_document(
        self,
        tenant_id: uuid.UUID,
        user: User,
        document_id: uuid.UUID,
        version_id: Optional[uuid.UUID] = None
    ) -> AdvancedAnalysisSession:
        start_time = time.time()

        # 1. Seguridad: El SUPER_ADMIN global no tiene acceso a documentos privados de despachos
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso restringido por diseño: El administrador global no puede inspeccionar expedientes confidenciales de los despachos."
            )

        # 2. Obtener documento y validar pertenencia al despacho
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento no encontrado o no pertenece a su organización."
            )

        # 3. Obtener texto seguro del documento
        raw_text = ""
        if document.metadata_record and document.metadata_record.raw_text:
            raw_text = document.metadata_record.raw_text
        elif document.storage_path and os.path.exists(document.storage_path):
            try:
                with open(document.storage_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
            except Exception:
                pass

        if not raw_text or len(raw_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento no cuenta con texto extraído suficiente para análisis jurídico."
            )

        # 4. Descomposición analítica de cláusulas
        decomposed_clauses = ClauseDecomposer.decompose(raw_text)

        # 5. Detección de defectos, contradicciones, omisiones y citas normativas
        defect_findings = DefectDetector.detect_all(
            text=raw_text,
            clauses=decomposed_clauses,
            doc_type=document.doc_type or "CONTRATO"
        )

        # 6. Correlación contra Reglas Deterministas internas del despacho
        active_rules = self.db.query(LegalRule).filter(
            LegalRule.tenant_id == tenant_id,
            LegalRule.is_active.is_(True)
        ).all()

        rule_findings = []
        if active_rules:
            rule_eval = self.rule_engine.evaluate_document(
                document=document,
                raw_text=raw_text,
                rules=active_rules
            )
            for d in rule_eval.get("details", []):
                if d["status"] == RuleEvaluationStatus.NON_COMPLIANT:
                    rule_findings.append({
                        "issue_type": FindingIssueType.COMPLIANCE_BREACH,
                        "title": f"Incumplimiento de Regla Interna: {d['rule_name']}",
                        "description": d.get("failure_reason") or "Violación a política contractual configurada.",
                        "severity": d.get("severity") or FindingSeverity.HIGH,
                        "original_fragment": d.get("matched_evidence"),
                        "location": "Auditoría de Políticas",
                        "clause_ref": "Regla Determinista del Despacho",
                        "related_rule_code": d.get("rule_code"),
                        "legal_foundation": None,
                        "risk_explanation": f"Incumplimiento confirmado contra la regla de despacho [{d.get('rule_code')}].",
                        "recommendation": "Adecuar la cláusula para ajustarse a los lineamientos internos aprobados.",
                        "confidence_score": 1.0,
                        "confidence_level": "HIGH"
                    })
                elif d["status"] == RuleEvaluationStatus.PENDING_HUMAN_REVIEW:
                    rule_findings.append({
                        "issue_type": FindingIssueType.AMBIGUITY,
                        "title": f"Observación Pendiente de Confirmación: {d['rule_name']}",
                        "description": d.get("failure_reason") or "La condición requiere criterio interpretativo humano.",
                        "severity": FindingSeverity.REQUIRES_HUMAN_VALIDATION,
                        "original_fragment": d.get("matched_evidence"),
                        "location": "Auditoría de Políticas",
                        "clause_ref": "Regla Interna",
                        "related_rule_code": d.get("rule_code"),
                        "legal_foundation": None,
                        "risk_explanation": "Incertidumbre en la verificación automática de la regla. No se marca como violación definitiva.",
                        "recommendation": "Revisión manual y dictamen por el abogado titular.",
                        "confidence_score": 0.85,
                        "confidence_level": "MEDIUM"
                    })

        all_findings_raw = defect_findings + rule_findings

        # 7. Cálculo de Métricas y Puntuación de Riesgo
        critical_c = sum(1 for f in all_findings_raw if f["severity"] == FindingSeverity.CRITICAL)
        high_c = sum(1 for f in all_findings_raw if f["severity"] == FindingSeverity.HIGH)
        medium_c = sum(1 for f in all_findings_raw if f["severity"] == FindingSeverity.MEDIUM)
        low_c = sum(1 for f in all_findings_raw if f["severity"] == FindingSeverity.LOW)
        pending_c = sum(1 for f in all_findings_raw if f["severity"] == FindingSeverity.REQUIRES_HUMAN_VALIDATION)

        overall_score = min(100.0, (critical_c * 35.0) + (high_c * 18.0) + (medium_c * 8.0) + (low_c * 3.0))
        
        if critical_c > 0:
            overall_severity = FindingSeverity.CRITICAL
        elif high_c > 0:
            overall_severity = FindingSeverity.HIGH
        elif medium_c > 0:
            overall_severity = FindingSeverity.MEDIUM
        elif low_c > 0:
            overall_severity = FindingSeverity.LOW
        elif pending_c > 0:
            overall_severity = FindingSeverity.REQUIRES_HUMAN_VALIDATION
        else:
            overall_severity = FindingSeverity.NO_OBSERVATIONS

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 8. Persistencia en Base de Datos
        session_id = uuid.uuid4()
        summary_text = (
            f"Análisis jurídico completado en {elapsed_ms}ms sobre {len(decomposed_clauses)} cláusulas/secciones. "
            f"Se identificaron {len(all_findings_raw)} observaciones ({critical_c} críticas, {high_c} altas, {medium_c} medias, {pending_c} pendientes de validación humana). "
            f"Herramienta de priorización: requiere validación formal por abogado antes de carácter vinculante."
        )

        db_session = AdvancedAnalysisSession(
            id=session_id,
            tenant_id=tenant_id,
            document_id=document_id,
            document_version_id=version_id,
            created_by_id=user.id,
            overall_risk_score=overall_score,
            overall_severity=overall_severity,
            findings_count=len(all_findings_raw),
            critical_count=critical_c,
            high_count=high_c,
            medium_count=medium_c,
            low_count=low_c,
            pending_review_count=pending_c,
            summary=summary_text,
            execution_time_ms=elapsed_ms,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(db_session)
        self.db.flush()

        # Guardar descomposición de cláusulas
        for c in decomposed_clauses:
            db_clause = ClauseDecomposition(
                id=uuid.uuid4(),
                session_id=session_id,
                document_id=document_id,
                clause_number=c["clause_number"],
                title=c["title"],
                raw_text=c["raw_text"],
                summary=c["summary"],
                obligations=c["obligations"],
                rights=c["rights"],
                deadlines=c["deadlines"],
                penalties=c["penalties"]
            )
            self.db.add(db_clause)

        # Guardar hallazgos jurídicos
        for idx, f in enumerate(all_findings_raw, 1):
            finding_code = f"OBS-{datetime.now(timezone.utc).year}-{idx:03d}"
            db_finding = LegalFinding(
                id=uuid.uuid4(),
                session_id=session_id,
                tenant_id=tenant_id,
                document_id=document_id,
                finding_code=finding_code,
                issue_type=f["issue_type"],
                title=f["title"],
                description=f["description"],
                severity=f["severity"],
                original_fragment=f.get("original_fragment"),
                location=f.get("location"),
                clause_ref=f.get("clause_ref"),
                related_rule_code=f.get("related_rule_code"),
                legal_foundation=f.get("legal_foundation"),
                risk_explanation=f["risk_explanation"],
                recommendation=f["recommendation"],
                confidence_score=f.get("confidence_score", 0.9),
                confidence_level=f.get("confidence_level", "HIGH"),
                review_status=FindingReviewStatus.PENDING_REVIEW
            )
            self.db.add(db_finding)

        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_latest_session(self, tenant_id: uuid.UUID, user: User, document_id: uuid.UUID) -> Optional[AdvancedAnalysisSession]:
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido para SUPER_ADMIN.")

        return self.db.query(AdvancedAnalysisSession).filter(
            AdvancedAnalysisSession.tenant_id == tenant_id,
            AdvancedAnalysisSession.document_id == document_id
        ).order_by(desc(AdvancedAnalysisSession.created_at)).first()

    def review_finding(
        self,
        tenant_id: uuid.UUID,
        lawyer_user: User,
        finding_id: uuid.UUID,
        status_val: str,
        reviewer_license: Optional[str] = None,
        reviewer_notes: Optional[str] = None
    ) -> LegalFinding:
        """Permite que un abogado humano valide, modifique o descarte un hallazgo (HITL)."""
        if lawyer_user.role not in [LegalRoles.SENIOR_LAWYER, LegalRoles.MANAGING_PARTNER, LegalRoles.ASSOCIATE_LAWYER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un abogado facultado puede emitir dictamen sobre hallazgos jurídicos."
            )

        finding = self.db.query(LegalFinding).filter(
            LegalFinding.id == finding_id,
            LegalFinding.tenant_id == tenant_id
        ).first()
        if not finding:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hallazgo jurídico no encontrado.")

        finding.review_status = status_val
        finding.reviewed_by_id = lawyer_user.id
        finding.reviewer_license = reviewer_license or lawyer_user.professional_license
        finding.reviewer_notes = reviewer_notes
        finding.reviewed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(finding)
        return finding

    def compare_document_versions(
        self,
        tenant_id: uuid.UUID,
        user: User,
        document_id: uuid.UUID,
        base_text: str,
        compare_text: str,
        base_label: str = "Versión Base",
        compare_label: str = "Versión Comparada"
    ) -> VersionComparison:
        """Ejecuta comparación entre dos versiones de un documento."""
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido para SUPER_ADMIN.")

        comp_result = VersionComparator.compare_documents(
            base_text=base_text,
            compare_text=compare_text,
            base_label=base_label,
            compare_label=compare_label
        )

        db_comp = VersionComparison(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            document_id=document_id,
            base_version_label=comp_result["base_version_label"],
            compare_version_label=comp_result["compare_version_label"],
            added_clauses=comp_result["added_clauses"],
            removed_clauses=comp_result["removed_clauses"],
            modified_clauses=comp_result["modified_clauses"],
            risk_delta=comp_result["risk_delta"],
            summary=comp_result["summary"],
            compared_by_id=user.id,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(db_comp)
        self.db.commit()
        self.db.refresh(db_comp)
        return db_comp
