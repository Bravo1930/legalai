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
