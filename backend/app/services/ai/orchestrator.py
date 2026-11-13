from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.core.errors import NotFoundException, ValidationException
from app.models.document import Document
from app.models.ai import AIAnalysis, AIAgentType
from app.models.audit_log import AuditLog
from app.services.ai.agents.classifier_agent import DocumentClassifierAgent
from app.services.ai.agents.extractor_agent import InformationExtractorAgent
from app.services.ai.agents.clause_analyst_agent import ClauseAnalystAgent
from app.services.ai.agents.risk_detector_agent import RiskDetectorAgent
from app.services.ai.agents.researcher_agent import LegalResearcherAgent
from app.services.ai.agents.drafter_agent import LegalDraftingAgent
from app.services.ai.agents.verifier_agent import ResultVerifierAgent

AGENTS_MAP = {
    AIAgentType.CLASSIFIER: DocumentClassifierAgent,
    AIAgentType.EXTRACTOR: InformationExtractorAgent,
    AIAgentType.CLAUSE_ANALYST: ClauseAnalystAgent,
    AIAgentType.RISK_DETECTOR: RiskDetectorAgent,
    AIAgentType.RESEARCHER: LegalResearcherAgent,
    AIAgentType.DRAFTER: LegalDraftingAgent,
    AIAgentType.VERIFIER: ResultVerifierAgent,
}


class AIOrchestrator:
    @staticmethod
    async def analyze_document(
        db: Session,
        tenant_id: UUID,
        document_id: UUID,
        agent_type: str = AIAgentType.CLASSIFIER,
        model: Optional[str] = None,
        user_prompt: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> AIAnalysis:
        """Ejecuta un agente de IA específico sobre un documento y persiste el análisis."""
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()

        if not doc:
            raise NotFoundException("Documento no encontrado o no pertenece a este despacho")

        # Obtener el texto del documento
        text_content = doc.metadata_record.raw_text if doc.metadata_record else None
        if not text_content or len(text_content.strip()) < 10:
            raise ValidationException("El documento no contiene texto extraído suficiente para análisis.")

        if agent_type == AIAgentType.FULL_SUITE:
            # Ejecutar análisis combinado de Clasificador + Riesgos + Verificador
            return await AIOrchestrator._run_full_suite(
                db=db,
                tenant_id=tenant_id,
                document_id=document_id,
                text_content=text_content,
                model=model,
                user_id=user_id
            )

        agent_cls = AGENTS_MAP.get(agent_type)
        if not agent_cls:
            raise ValidationException(f"Tipo de agente no reconocido: '{agent_type}'. Agentes disponibles: {list(AGENTS_MAP.keys())}")

        logger.info(f"Invocando agente {agent_type} para documento {document_id} con modelo {model or 'óptimo'}")
        
        # Ejecución del agente con Ollama local
        agent_result = await agent_cls.run(
            document_text=text_content,
            user_prompt=user_prompt,
            model=model
        )

        # Persistir registro de análisis inmutable
        analysis = AIAnalysis(
            tenant_id=tenant_id,
            document_id=document_id,
            created_by_id=user_id,
            agent_type=agent_type,
            model_used=agent_result["model_used"],
            prompt_template=agent_result["prompt_template"],
            input_params={"model": model, "user_prompt": user_prompt},
            structured_output=agent_result["structured_output"],
            raw_response=str(agent_result.get("structured_output")),
            tokens_prompt=agent_result["tokens_prompt"],
            tokens_completion=agent_result["tokens_completion"],
            latency_ms=agent_result["latency_ms"]
        )
        db.add(analysis)

        # Registrar en Auditoría
        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="AI_DOCUMENT_ANALYSIS",
            resource_type="DOCUMENT",
            resource_id=str(document_id),
            details={
                "agent_type": agent_type,
                "model": agent_result["model_used"],
                "latency_ms": agent_result["latency_ms"]
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(analysis)

        return analysis

    @staticmethod
    async def _run_full_suite(
        db: Session,
        tenant_id: UUID,
        document_id: UUID,
        text_content: str,
        model: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> AIAnalysis:
        """Ejecuta una corrida coordinada de los agentes principales y sintetiza el dictamen."""
        logger.info(f"Ejecutando FULL_SUITE para doc {document_id}")
        
        # 1. Clasificación
        cls_res = await DocumentClassifierAgent.run(document_text=text_content, model=model)
        # 2. Detección de Riesgos
        risk_res = await RiskDetectorAgent.run(document_text=text_content, model=model)
        # 3. Verificación y Auditoría Epistémica
        ver_res = await ResultVerifierAgent.run(document_text=text_content, model=model)

        total_tokens_prompt = cls_res["tokens_prompt"] + risk_res["tokens_prompt"] + ver_res["tokens_prompt"]
        total_tokens_completion = cls_res["tokens_completion"] + risk_res["tokens_completion"] + ver_res["tokens_completion"]
        total_latency_ms = cls_res["latency_ms"] + risk_res["latency_ms"] + ver_res["latency_ms"]

        combined_output = {
            "classification": cls_res["structured_output"],
            "risk_analysis": risk_res["structured_output"],
            "verification": ver_res["structured_output"],
            "epistemic_summary": ver_res["structured_output"].get("epistemic_breakdown", {})
        }

        analysis = AIAnalysis(
            tenant_id=tenant_id,
            document_id=document_id,
            created_by_id=user_id,
            agent_type=AIAgentType.FULL_SUITE,
            model_used=cls_res["model_used"],
            prompt_template="Coordinación Full Suite (Clasificador + Riesgos + Verificador)",
            input_params={"pipeline": "FULL_SUITE", "model": model},
            structured_output=combined_output,
            raw_response="Full suite execution completed",
            tokens_prompt=total_tokens_prompt,
            tokens_completion=total_tokens_completion,
            latency_ms=total_latency_ms
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def list_analyses_for_document(
        db: Session,
        tenant_id: UUID,
        document_id: UUID
    ) -> List[AIAnalysis]:
        """Consulta el historial de análisis de IA de un documento."""
        return db.query(AIAnalysis).filter(
            AIAnalysis.document_id == document_id,
            AIAnalysis.tenant_id == tenant_id
        ).order_by(AIAnalysis.created_at.desc()).all()
