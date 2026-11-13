export interface UserProfile {
  id: string;
  tenant_id: string;
  tenant_name: string;
  tenant_slug: string;
  email: string;
  full_name: string;
  role: "SUPER_ADMIN" | "MANAGING_PARTNER" | "SENIOR_LAWYER" | "ASSOCIATE_LAWYER" | "PARALEGAL" | "AUDITOR";
  professional_license?: string;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: UserProfile;
}

export interface SystemHealth {
  status: "healthy" | "degraded" | "unhealthy";
  environment: string;
  version: string;
  timestamp: string;
  database: {
    status: string;
    version?: string;
    pgvector_enabled: boolean;
    error?: string;
  };
  redis: {
    status: string;
    connected: boolean;
    details?: string;
  };
  ollama: {
    status: string;
    base_url: string;
    models_available: string[];
    error?: string;
  };
}

export interface AsyncTask {
  id: string;
  tenant_id: string;
  task_type: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED" | "CANCELLED";
  payload?: Record<string, any>;
  result?: Record<string, any>;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface Client {
  id: string;
  tenant_id: string;
  name: string;
  rfc?: string;
  curp?: string;
  client_type: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  created_at: string;
  updated_at: string;
}

export interface Case {
  id: string;
  tenant_id: string;
  client_id: string;
  lead_lawyer_id?: string;
  case_number: string;
  title: string;
  description?: string;
  matter: string;
  jurisdiction: string;
  state?: string;
  court_authority?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentMetadata {
  parties?: Array<{ role: string; name: string }>;
  doc_date?: string;
  subject_matter?: string;
  obligations?: string[];
  amounts?: string[];
  terms_deadlines?: string[];
  signers?: Array<{ professional_license?: string; name?: string }>;
  jurisdiction?: string;
  court_authority?: string;
  procedure_type?: string;
  references?: string[];
  ocr_applied: boolean;
  processing_time_ms: number;
  extracted_at: string;
}

export interface DocumentVersion {
  id: string;
  version_number: number;
  sha256_hash: string;
  file_size_bytes: number;
  change_summary?: string;
  created_at: string;
}

export interface LegalDocument {
  id: string;
  tenant_id: string;
  case_id?: string;
  client_id?: string;
  title: string;
  filename: string;
  file_size_bytes: number;
  mime_type: string;
  sha256_hash: string;
  doc_type: string;
  is_original: boolean;
  is_confidential: boolean;
  page_count: number;
  created_at: string;
  updated_at: string;
  metadata_record?: DocumentMetadata;
  versions: DocumentVersion[];
}

export interface DocumentPreview {
  id: string;
  title: string;
  filename: string;
  doc_type: string;
  sha256_hash: string;
  page_count: number;
  raw_text: string;
  metadata?: DocumentMetadata;
}

export interface AIModelInfo {
  name: string;
  size_bytes: number;
  parameter_size?: string;
  quantization_level?: string;
  capabilities: string[];
  family?: string;
}

export interface AIAnalysisRecord {
  id: string;
  tenant_id: string;
  document_id: string;
  agent_type: string;
  model_used: string;
  structured_output: Record<string, any>;
  tokens_prompt: number;
  tokens_completion: number;
  latency_ms: number;
  created_at: string;
}

export interface RuleScope {
  doc_types?: string[];
  client_ids?: string[];
  legal_matters?: string[];
  jurisdictions?: string[];
}

export interface RuleCondition {
  operator: string;
  parameters: {
    keywords?: string[];
    prohibited_keywords?: string[];
    regex_pattern?: string;
    expected_match?: boolean;
    min_value?: number;
    max_value?: number;
    target_field?: string;
    regex_extractor?: string;
    case_sensitive?: boolean;
    [key: string]: any;
  };
}

export interface LegalRule {
  id: string;
  tenant_id: string;
  rule_code: string;
  name: string;
  description: string;
  category: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
  is_active: boolean;
  scope: RuleScope;
  condition_definition: RuleCondition;
  expected_outcome: string;
  legal_foundation?: string;
  version: number;
  effective_from: string;
  effective_until?: string;
  created_at: string;
  updated_at: string;
}

export interface RuleEvaluationDetail {
  id: string;
  evaluation_id: string;
  rule_id?: string;
  rule_code: string;
  rule_name: string;
  category: string;
  severity: string;
  status: "COMPLIANT" | "NON_COMPLIANT" | "PENDING_HUMAN_REVIEW" | "NOT_APPLICABLE";
  matched_evidence?: string;
  failure_reason?: string;
  human_verification_notes?: string;
  verified_by_id?: string;
  verified_at?: string;
}

export interface RuleEvaluation {
  id: string;
  tenant_id: string;
  document_id: string;
  document_version_id?: string;
  evaluated_by_id?: string;
  total_rules_evaluated: number;
  passed_count: number;
  failed_count: number;
  pending_count: number;
  not_applicable_count: number;
  compliance_score: number;
  created_at: string;
  details: RuleEvaluationDetail[];
}

export interface LegalFoundation {
  disposition_name: string;
  article?: string;
  jurisdiction: string;
  publication_reform_date: string;
  validity_status: "VIGENTE_VERIFICADA" | "REQUIERE_INVESTIGACION_JURIDICA";
  official_source: string;
  query_date: string;
  is_verified: boolean;
  verification_note?: string;
}

export interface LegalFinding {
  id: string;
  finding_code: string;
  issue_type: string;
  title: string;
  description: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NO_OBSERVATIONS" | "REQUIRES_HUMAN_VALIDATION";
  original_fragment?: string;
  location?: string;
  clause_ref?: string;
  related_rule_code?: string;
  legal_foundation?: LegalFoundation;
  risk_explanation: string;
  recommendation: string;
  confidence_score: number;
  confidence_level: "HIGH" | "MEDIUM" | "LOW";
  review_status: "PENDING_REVIEW" | "VALIDATED" | "REJECTED" | "MODIFIED";
  reviewed_by_id?: string;
  reviewer_license?: string;
  reviewer_notes?: string;
  reviewed_at?: string;
  created_at: string;
}

export interface ClauseDecomposition {
  id: string;
  clause_number: number;
  title: string;
  raw_text: string;
  summary: string;
  obligations: string[];
  rights: string[];
  deadlines: string[];
  penalties: string[];
}

export interface AdvancedAnalysisSession {
  id: string;
  document_id: string;
  overall_risk_score: number;
  overall_severity: string;
  findings_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  pending_review_count: number;
  summary?: string;
  execution_time_ms: number;
  created_at: string;
  findings: LegalFinding[];
  clauses: ClauseDecomposition[];
}

export interface VersionComparisonResult {
  id: string;
  document_id: string;
  base_version_label: string;
  compare_version_label: string;
  added_clauses: Array<{ title: string; clause_number: number; summary: string; raw_text: string }>;
  removed_clauses: Array<{ title: string; clause_number: number; summary: string; raw_text: string }>;
  modified_clauses: Array<{ title: string; clause_number: number; change_summary: string; base_text: string; compare_text: string }>;
  risk_delta: {
    mitigated_risks: Array<{ title: string; severity: string; description?: string }>;
    introduced_risks: Array<{ title: string; severity: string; description?: string }>;
    persistent_risks: Array<{ title: string; severity: string }>;
  };
  summary: string;
  created_at: string;
}
