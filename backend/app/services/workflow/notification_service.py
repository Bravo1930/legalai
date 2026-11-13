import hmac
import hashlib
import json
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.workflow import (
    WorkflowNotification, WorkflowIntegrationConfig, DocumentWorkflow
)
from app.models.user import User
from app.models.document import Document
from app.core.logging import logger


class NotificationType:
    NEW_DOCUMENT_RECEIVED = "NEW_DOCUMENT_RECEIVED"
    ANALYSIS_FINISHED = "ANALYSIS_FINISHED"
    CRITICAL_RISK_DETECTED = "CRITICAL_RISK_DETECTED"
    PENDING_REVIEW_ALERT = "PENDING_REVIEW_ALERT"
    CORRECTION_REQUESTED = "CORRECTION_REQUESTED"
    PENDING_APPROVAL_ALERT = "PENDING_APPROVAL_ALERT"
    DEADLINE_EXPIRING_SOON = "DEADLINE_EXPIRING_SOON"
    APPROVAL_COMPLETED = "APPROVAL_COMPLETED"
    APPROVAL_INVALIDATED = "APPROVAL_INVALIDATED"


class NotificationService:
    """Gestiona el centro de notificaciones in-app y el envío hacia integraciones externas."""

    def __init__(self, db: Session):
        self.db = db

    def emit_notification(
        self,
        tenant_id: UUID,
        recipient_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        document_id: Optional[UUID] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> WorkflowNotification:
        """Crea una notificación dentro de la aplicación y la almacena en base de datos."""
        notif = WorkflowNotification(
            tenant_id=tenant_id,
            recipient_id=recipient_id,
            document_id=document_id,
            notification_type=notification_type,
            title=title,
            message=message,
            payload=payload or {},
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(notif)
        self.db.flush()

        # Disparar integración externa configurable en segundo plano
        self._dispatch_external_integration(tenant_id, notif)

        return notif

    def notify_team(
        self,
        workflow: DocumentWorkflow,
        notification_type: str,
        title: str,
        message: str,
        exclude_user_id: Optional[UUID] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> List[WorkflowNotification]:
        """Notifica a todos los miembros asignados al expediente (abogado, revisor, asistente)."""
        recipients = set()
        if workflow.assigned_lawyer_id:
            recipients.add(workflow.assigned_lawyer_id)
        if workflow.reviewer_id:
            recipients.add(workflow.reviewer_id)
        if workflow.assistant_id:
            recipients.add(workflow.assistant_id)

        if exclude_user_id and exclude_user_id in recipients:
            recipients.remove(exclude_user_id)

        created_notifs = []
        for uid in recipients:
            n = self.emit_notification(
                tenant_id=workflow.tenant_id,
                recipient_id=uid,
                notification_type=notification_type,
                title=title,
                message=message,
                document_id=workflow.document_id,
                payload=payload
            )
            created_notifs.append(n)

        return created_notifs

    def list_user_notifications(
        self,
        tenant_id: UUID,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[WorkflowNotification]:
        """Consulta el buzón de notificaciones del usuario."""
        q = self.db.query(WorkflowNotification).filter(
            WorkflowNotification.tenant_id == tenant_id,
            WorkflowNotification.recipient_id == user_id
        )
        if unread_only:
            q = q.filter(WorkflowNotification.is_read == False)

        return q.order_by(WorkflowNotification.created_at.desc()).limit(limit).all()

    def get_unread_count(self, tenant_id: UUID, user_id: UUID) -> int:
        """Devuelve el contador de notificaciones no leídas."""
        return self.db.query(WorkflowNotification).filter(
            WorkflowNotification.tenant_id == tenant_id,
            WorkflowNotification.recipient_id == user_id,
            WorkflowNotification.is_read == False
        ).count()

    def mark_as_read(self, tenant_id: UUID, user_id: UUID, notification_id: UUID) -> WorkflowNotification:
        """Marca una notificación específica como leída."""
        notif = self.db.query(WorkflowNotification).filter(
            WorkflowNotification.id == notification_id,
            WorkflowNotification.tenant_id == tenant_id,
            WorkflowNotification.recipient_id == user_id
        ).first()

        if notif:
            notif.is_read = True
            notif.read_at = datetime.now(timezone.utc)
            self.db.flush()

        return notif

    def mark_all_as_read(self, tenant_id: UUID, user_id: UUID) -> int:
        """Marca todas las notificaciones pendientes del usuario como leídas."""
        now = datetime.now(timezone.utc)
        count = self.db.query(WorkflowNotification).filter(
            WorkflowNotification.tenant_id == tenant_id,
            WorkflowNotification.recipient_id == user_id,
            WorkflowNotification.is_read == False
        ).update({"is_read": True, "read_at": now})
        self.db.flush()
        return count

    def check_deadlines_and_alert(self, tenant_id: UUID) -> int:
        """
        Escanea expedientes con fecha límite próxima a vencer (< 48 hrs) o vencidos
        y emite recordatorios automáticos.
        """
        now = datetime.now(timezone.utc)
        workflows = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.tenant_id == tenant_id,
            DocumentWorkflow.deadline_at != None,
            DocumentWorkflow.current_state.notin_(["APPROVED", "REJECTED", "ARCHIVED"])
        ).all()

        alerted = 0
        for wf in workflows:
            diff_hours = (wf.deadline_at - now).total_seconds() / 3600.0
            if diff_hours <= 0 and not wf.is_overdue:
                wf.is_overdue = True
                self.notify_team(
                    workflow=wf,
                    notification_type=NotificationType.DEADLINE_EXPIRING_SOON,
                    title="⚠️ Plazo Legal Vencido",
                    message=f"El plazo límite para el documento ha vencido el {wf.deadline_at.strftime('%d/%m/%Y %H:%M')}.",
                    payload={"deadline": wf.deadline_at.isoformat(), "is_overdue": True}
                )
                alerted += 1
            elif 0 < diff_hours <= 48:
                self.notify_team(
                    workflow=wf,
                    notification_type=NotificationType.DEADLINE_EXPIRING_SOON,
                    title="⏰ Plazo Próximo a Vencer",
                    message=f"El plazo límite vence en {int(diff_hours)} horas.",
                    payload={"deadline": wf.deadline_at.isoformat(), "hours_remaining": int(diff_hours)}
                )
                alerted += 1

        self.db.flush()
        return alerted

    def _dispatch_external_integration(self, tenant_id: UUID, notif: WorkflowNotification):
        """Despacho hacia webhooks o canales externos configurables."""
        config = self.db.query(WorkflowIntegrationConfig).filter(
            WorkflowIntegrationConfig.tenant_id == tenant_id,
            WorkflowIntegrationConfig.is_active == True
        ).first()

        if not config:
            return

        payload = {
            "event": notif.notification_type,
            "title": notif.title,
            "message": notif.message,
            "document_id": str(notif.document_id) if notif.document_id else None,
            "timestamp": notif.created_at.isoformat(),
            "extra": notif.payload
        }

        # Envío a Webhook Genérico con firma HMAC
        if config.webhook_url:
            self._send_http_webhook(config.webhook_url, config.webhook_secret, payload)

        # Envío a Slack si está configurado
        if config.slack_webhook_url:
            slack_msg = {"text": f"*{notif.title}*\n{notif.message}"}
            self._send_http_webhook(config.slack_webhook_url, None, slack_msg)

        # Envío a Teams si está configurado
        if config.teams_webhook_url:
            teams_msg = {"title": notif.title, "text": notif.message}
            self._send_http_webhook(config.teams_webhook_url, None, teams_msg)

    def _send_http_webhook(self, url: str, secret: Optional[str], payload: Dict[str, Any]):
        """Envío HTTP seguro con timeout corto."""
        body_bytes = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if secret:
            sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
            headers["X-LegalAI-Signature"] = f"sha256={sig}"

        try:
            with httpx.Client(timeout=3.0) as client:
                client.post(url, content=body_bytes, headers=headers)
        except Exception as e:
            logger.warning(f"[NotificationService] Falla al despachar webhook hacia {url}: {e}")
