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
from app.models.rule import (
    LegalRule, RuleVersion, RuleAuditLog, RuleEvaluation, RuleEvaluationDetail,
    RuleCategory, RuleSeverity, RuleOperator, RuleEvaluationStatus
)
from app.models.advanced_analysis import (
    AdvancedAnalysisSession, LegalFinding, ClauseDecomposition, VersionComparison,
    FindingIssueType, FindingSeverity, FindingReviewStatus
)
from app.models.modification import (
    ModificationProposalBatch, LegalModificationProposal,
    ProposalBatchStatus, ProposalItemStatus
)
from app.models.workflow import (
    DocumentWorkflow, WorkflowTransition, WorkflowComment,
    CorrectionRequest, WorkflowApprovalRecord, WorkflowReminder,
    WorkflowNotification, WorkflowIntegrationConfig,
    WorkflowState, ApprovalScope
)

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
    "AIAgentType",
    "LegalRule",
    "RuleVersion",
    "RuleAuditLog",
    "RuleEvaluation",
    "RuleEvaluationDetail",
    "RuleCategory",
    "RuleSeverity",
    "RuleOperator",
    "RuleEvaluationStatus",
    "AdvancedAnalysisSession",
    "LegalFinding",
    "ClauseDecomposition",
    "VersionComparison",
    "FindingIssueType",
    "FindingSeverity",
    "FindingReviewStatus",
    "ModificationProposalBatch",
    "LegalModificationProposal",
    "ProposalBatchStatus",
    "ProposalItemStatus",
    "DocumentWorkflow",
    "WorkflowTransition",
    "WorkflowComment",
    "CorrectionRequest",
    "WorkflowApprovalRecord",
    "WorkflowReminder",
    "WorkflowNotification",
    "WorkflowIntegrationConfig",
    "WorkflowState",
    "ApprovalScope"
]
