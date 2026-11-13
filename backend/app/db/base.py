# Consolidación de modelos ORM para Alembic y SQLAlchemy
from app.db.session import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.task import Task
from app.models.client import Client
from app.models.case import Case, LegalMatter, CaseStatus
from app.models.document import Document, DocumentVersion, DocumentMetadata, DocumentClassification
from app.models.approval import LegalApproval, ApprovalStatus
from app.models.ai import AIAnalysis, AIAgentType

__all__ = [
    "Base",
    "Tenant",
    "User",
    "AuditLog",
    "Task",
    "Client",
    "Case",
    "LegalMatter",
    "CaseStatus",
    "Document",
    "DocumentVersion",
    "DocumentMetadata",
    "DocumentClassification",
    "LegalApproval",
    "ApprovalStatus",
    "AIAnalysis",
    "AIAgentType"
]
