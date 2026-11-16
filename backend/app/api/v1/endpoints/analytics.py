from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.user import User
from app.models.document import Document, DocumentVersion
from app.models.workflow import DocumentWorkflow, WorkflowState, WorkflowTransition, WorkflowApprovalRecord
from app.models.advanced_analysis import LegalFinding, FindingSeverity
from app.models.case import Case
from app.models.client import Client
from app.models.audit_log import AuditLog
from app.services.auth_service import get_current_user
from app.core.errors import ForbiddenException

router = APIRouter()


@router.get("/dashboard", summary="Métricas reales y consolidadas del despacho jurídico")
def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calcula y retorna estadísticas 100% reales basadas en los datos del despacho:
    - Documentos recibidos, procesados, revisiones pendientes, riesgos críticos, aprobados, rechazados.
    - Carga de trabajo por abogado asignado.
    - Tiempos promedio de revisión.
    - Actividad reciente verificable.
    """
    if current_user.role == "SUPER_ADMIN":
        # Métricas a nivel plataforma para SUPER_ADMIN
        total_tenants = db.query(User.tenant_id).distinct().count()
        total_docs = db.query(Document).count()
        return {
            "is_global_admin": True,
            "total_tenants": total_tenants,
            "total_documents": total_docs,
            "message": "Panel administrativo global de plataforma."
        }

    tenant_id = current_user.tenant_id

    # 1. Documentos recibidos y procesados
    total_docs = db.query(Document).filter(Document.tenant_id == tenant_id).count()
    
    # Documentos por estado en workflow
    workflows = db.query(DocumentWorkflow).filter(DocumentWorkflow.tenant_id == tenant_id).all()
    wf_by_state = {}
    for wf in workflows:
        wf_by_state[wf.current_state] = wf_by_state.get(wf.current_state, 0) + 1

    received_count = wf_by_state.get(WorkflowState.RECEIVED, 0)
    processing_count = wf_by_state.get(WorkflowState.PROCESSING, 0)
    processed_count = total_docs - received_count  # Todos los que han avanzado del estado inicial
    if processed_count < 0:
        processed_count = 0

    pending_reviews_count = (
        wf_by_state.get(WorkflowState.PENDING_REVIEW, 0) +
        wf_by_state.get(WorkflowState.PENDING_APPROVAL, 0) +
        wf_by_state.get(WorkflowState.WITH_OBSERVATIONS, 0)
    )

    approved_count = wf_by_state.get(WorkflowState.APPROVED, 0)
    rejected_count = wf_by_state.get(WorkflowState.REJECTED, 0)
    in_correction_count = wf_by_state.get(WorkflowState.IN_CORRECTION, 0)

    # 2. Riesgos detectados en documentos del despacho (consistente con matriz de riesgos)
    critical_risks_count = db.query(LegalFinding).filter(
        LegalFinding.tenant_id == tenant_id,
        LegalFinding.severity == FindingSeverity.CRITICAL
    ).count()

    high_risks_count = db.query(LegalFinding).filter(
        LegalFinding.tenant_id == tenant_id,
        LegalFinding.severity == FindingSeverity.HIGH
    ).count()

    # 3. Expedientes y Clientes
    total_cases = db.query(Case).filter(Case.tenant_id == tenant_id).count()
    total_clients = db.query(Client).filter(Client.tenant_id == tenant_id).count()

    # 4. Carga de trabajo por abogado
    lawyers = db.query(User).filter(
        User.tenant_id == tenant_id,
        User.is_active == True
    ).all()

    workload = []
    for law in lawyers:
        assigned_wf = [w for w in workflows if w.assigned_lawyer_id == law.id]
        active_docs = len(assigned_wf)
        pending_law_reviews = len([w for w in assigned_wf if w.current_state in [WorkflowState.PENDING_REVIEW, WorkflowState.PENDING_APPROVAL]])
        approved_law_docs = len([w for w in assigned_wf if w.current_state == WorkflowState.APPROVED])

        workload.append({
            "lawyer_id": str(law.id),
            "lawyer_name": law.full_name,
            "role": law.role,
            "license": law.professional_license,
            "active_documents": active_docs,
            "pending_reviews": pending_law_reviews,
            "approved_documents": approved_law_docs
        })

    # 5. Cálculo real de tiempo promedio de revisión / aprobación (en horas)
    approvals = db.query(WorkflowApprovalRecord).filter(
        WorkflowApprovalRecord.status == "VALID"
    ).all()

    review_times_hours = []
    for app in approvals:
        wf = next((w for w in workflows if w.id == app.workflow_id), None)
        if wf and app.approved_at and wf.created_at:
            delta_h = (app.approved_at - wf.created_at).total_seconds() / 3600.0
            if delta_h >= 0:
                review_times_hours.append(delta_h)

    avg_review_hours = round(sum(review_times_hours) / len(review_times_hours), 1) if review_times_hours else 0.0

    # 6. Actividad reciente verificable (últimas transiciones y auditoría)
    recent_transitions = db.query(WorkflowTransition).join(
        DocumentWorkflow, WorkflowTransition.workflow_id == DocumentWorkflow.id
    ).filter(
        DocumentWorkflow.tenant_id == tenant_id
    ).order_by(WorkflowTransition.created_at.desc()).limit(8).all()

    recent_activity = []
    for t in recent_transitions:
        actor_name = t.triggered_by.full_name if t.triggered_by else "Sistema Automático"
        recent_activity.append({
            "id": str(t.id),
            "event_type": "TRANSITION",
            "actor": actor_name,
            "description": f"Transición de '{t.from_state}' a '{t.to_state}'.",
            "reason": t.reason,
            "timestamp": t.created_at.isoformat()
        })

    # Si hay logs de auditoría adicionales, complementar
    audit_events = db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id
    ).order_by(AuditLog.created_at.desc()).limit(5).all()

    for a in audit_events:
        user_name = a.user.full_name if a.user else "Sistema"
        recent_activity.append({
            "id": str(a.id),
            "event_type": "AUDIT",
            "actor": user_name,
            "description": f"Operación {a.action} sobre {a.resource_type}",
            "reason": None,
            "timestamp": a.created_at.isoformat()
        })

    # Ordenar combinados por fecha descendente
    recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "is_global_admin": False,
        "tenant_id": str(tenant_id),
        "total_documents": total_docs,
        "received_documents": received_count,
        "processing_documents": processing_count,
        "processed_documents": processed_count,
        "pending_reviews": pending_reviews_count,
        "approved_documents": approved_count,
        "rejected_documents": rejected_count,
        "in_correction_documents": in_correction_count,
        "critical_risks": critical_risks_count,
        "high_risks": high_risks_count,
        "total_cases": total_cases,
        "total_clients": total_clients,
        "avg_review_time_hours": avg_review_hours,
        "workload_by_lawyer": workload,
        "recent_activity": recent_activity[:10]
    }
