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
