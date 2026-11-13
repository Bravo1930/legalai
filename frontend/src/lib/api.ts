import {
  AuthTokens, SystemHealth, UserProfile, AsyncTask, LegalDocument, DocumentVersion,
  DocumentPreview, Case, Client, AIModelInfo, AIAnalysisRecord,
  LegalRule, RuleEvaluation, RuleEvaluationDetail,
  AdvancedAnalysisSession, LegalFinding, VersionComparisonResult,
  LegalModificationProposal, ModificationProposalBatch
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

class ApiClient {
  public getAuthHeader(): Record<string, string> {
    if (typeof window === "undefined") return {};
    const token = localStorage.getItem("legal_ai_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${API_BASE_URL}/health`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`Error al consultar salud del backend: ${res.statusText}`);
    }
    return res.json();
  }

  async login(email: string, password: string, tenantSlug?: string): Promise<AuthTokens> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        tenant_slug: tenantSlug || undefined,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      const msg = data?.error?.message || "Error al iniciar sesión";
      throw new Error(msg);
    }

    if (typeof window !== "undefined") {
      localStorage.setItem("legal_ai_token", data.access_token);
      localStorage.setItem("legal_ai_user", JSON.stringify(data.user));
    }

    return data;
  }

  async getMe(): Promise<UserProfile> {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { ...this.getAuthHeader() },
    });

    if (!res.ok) {
      throw new Error("Sesión inválida o expirada");
    }
    return res.json();
  }

  logout(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("legal_ai_token");
      localStorage.removeItem("legal_ai_user");
    }
  }

  getCurrentUser(): UserProfile | null {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem("legal_ai_user");
    return raw ? JSON.parse(raw) : null;
  }

  // Tareas asíncronas
  async listTasks(): Promise<AsyncTask[]> {
    const res = await fetch(`${API_BASE_URL}/tasks`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al consultar tareas asíncronas");
    return res.json();
  }

  async enqueueTask(taskType: string, payload?: Record<string, any>): Promise<AsyncTask> {
    const res = await fetch(`${API_BASE_URL}/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify({ task_type: taskType, payload }),
    });

    if (!res.ok) throw new Error("Error al encolar tarea");
    return res.json();
  }

  // Gestión Documental
  async searchDocuments(query?: string, docType?: string, caseId?: string): Promise<{ items: LegalDocument[]; total: number }> {
    const params = new URLSearchParams();
    if (query) params.append("query", query);
    if (docType) params.append("doc_type", docType);
    if (caseId) params.append("case_id", caseId);

    const res = await fetch(`${API_BASE_URL}/documents?${params.toString()}`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al consultar documentos");
    return res.json();
  }

  async uploadDocument(formData: FormData): Promise<LegalDocument> {
    const res = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: "POST",
      headers: { ...this.getAuthHeader() },
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || "Error al cargar documento");
    }
    return data;
  }

  async previewDocument(documentId: string): Promise<DocumentPreview> {
    const res = await fetch(`${API_BASE_URL}/documents/${documentId}/preview`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al generar vista previa");
    return res.json();
  }

  getDownloadUrl(documentId: string, versionId?: string): string {
    const token = typeof window !== "undefined" ? localStorage.getItem("legal_ai_token") : "";
    const verParam = versionId ? `?version_id=${versionId}` : "";
    return `${API_BASE_URL}/documents/${documentId}/download${verParam}`;
  }

  // Casos & Clientes
  async listCases(): Promise<Case[]> {
    const res = await fetch(`${API_BASE_URL}/cases`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al listar expedientes");
    return res.json();
  }

  async listClients(): Promise<Client[]> {
    const res = await fetch(`${API_BASE_URL}/clients`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al listar clientes");
    return res.json();
  }

  // Agentes de Inteligencia Artificial (Ollama Local)
  async listAIModels(): Promise<AIModelInfo[]> {
    const res = await fetch(`${API_BASE_URL}/ai/models`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al consultar modelos de Ollama");
    return res.json();
  }

  async analyzeDocument(documentId: string, agentType: string, model?: string, userPrompt?: string): Promise<AIAnalysisRecord> {
    const res = await fetch(`${API_BASE_URL}/ai/analyze/${documentId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify({
        agent_type: agentType,
        model: model || undefined,
        user_prompt: userPrompt || undefined
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || "Error al ejecutar agente de IA");
    }
    return data;
  }

  async listDocumentAnalyses(documentId: string): Promise<AIAnalysisRecord[]> {
    const res = await fetch(`${API_BASE_URL}/ai/analyses/${documentId}`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al consultar historial de análisis de IA");
    return res.json();
  }

  // Motor de Reglas Deterministas
  async listRules(category?: string, severity?: string, isActive?: boolean): Promise<LegalRule[]> {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (severity) params.append("severity", severity);
    if (isActive !== undefined) params.append("is_active", String(isActive));

    const res = await fetch(`${API_BASE_URL}/rules?${params.toString()}`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al listar catálogo de reglas deterministas");
    return res.json();
  }

  async createRule(data: any): Promise<LegalRule> {
    const res = await fetch(`${API_BASE_URL}/rules`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al crear regla determinista");
    return resData;
  }

  async updateRule(ruleId: string, data: any): Promise<LegalRule> {
    const res = await fetch(`${API_BASE_URL}/rules/${ruleId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al actualizar regla");
    return resData;
  }

  async toggleRuleStatus(ruleId: string, isActive: boolean, reason?: string): Promise<LegalRule> {
    const res = await fetch(`${API_BASE_URL}/rules/${ruleId}/status`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify({ is_active: isActive, reason }),
    });
    if (!res.ok) throw new Error("Error al modificar estado de la regla");
    return res.json();
  }

  async evaluateDocumentRules(documentId: string, ruleIds?: string[]): Promise<RuleEvaluation> {
    const res = await fetch(`${API_BASE_URL}/rules/evaluate/${documentId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify(ruleIds || null),
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al evaluar reglas deterministas");
    return resData;
  }

  async listDocumentEvaluations(documentId: string): Promise<RuleEvaluation[]> {
    const res = await fetch(`${API_BASE_URL}/rules/evaluations/${documentId}`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al obtener historial de evaluaciones deterministas");
    return res.json();
  }

  async verifyEvaluationDetail(detailId: string, status: string, notes: string): Promise<RuleEvaluationDetail> {
    const res = await fetch(`${API_BASE_URL}/rules/evaluations/detail/${detailId}/verify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify({ status, notes }),
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al validar observación");
    return resData;
  }

  // Motor Avanzado de Análisis Jurídico Documental
  async runAdvancedAnalysis(documentId: string, versionId?: string): Promise<AdvancedAnalysisSession> {
    const url = versionId
      ? `${API_BASE_URL}/advanced-analysis/analyze/${documentId}?version_id=${versionId}`
      : `${API_BASE_URL}/advanced-analysis/analyze/${documentId}`;
    
    const res = await fetch(url, {
      method: "POST",
      headers: { ...this.getAuthHeader() },
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al ejecutar análisis jurídico avanzado");
    return resData;
  }

  async getLatestDocumentAnalysis(documentId: string): Promise<AdvancedAnalysisSession | null> {
    const res = await fetch(`${API_BASE_URL}/advanced-analysis/document/${documentId}`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al consultar sesión de análisis");
    return res.json();
  }

  async reviewFinding(findingId: string, reviewStatus: string, notes: string, license?: string): Promise<LegalFinding> {
    const res = await fetch(`${API_BASE_URL}/advanced-analysis/findings/${findingId}/review`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify({
        review_status: reviewStatus,
        reviewer_license: license || undefined,
        reviewer_notes: notes,
      }),
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al revisar hallazgo");
    return resData;
  }

  async compareVersions(documentId: string, baseText: string, compareText: string, baseLabel?: string, compareLabel?: string): Promise<VersionComparisonResult> {
    const res = await fetch(`${API_BASE_URL}/advanced-analysis/compare/${documentId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify({
        base_text: baseText,
        compare_text: compareText,
        base_label: baseLabel || "Versión Base (Original)",
        compare_label: compareLabel || "Versión Comparada (Revisada)",
      }),
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al comparar versiones");
    return resData;
  }

  // Módulo de Propuestas de Modificación y Redacción
  async generateModificationProposals(
    documentId: string,
    title?: string,
    objective: string = "BALANCED",
    findingIds?: string[]
  ): Promise<ModificationProposalBatch> {
    const res = await fetch(`${API_BASE_URL}/modifications/generate/${documentId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify({
        title: title || undefined,
        objective,
        finding_ids: findingIds || undefined,
      }),
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al generar propuestas de modificación");
    return resData;
  }

  async listModificationBatches(documentId: string): Promise<ModificationProposalBatch[]> {
    const res = await fetch(`${API_BASE_URL}/modifications/batches/${documentId}`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al consultar lotes de propuestas");
    return res.json();
  }

  async getModificationBatch(batchId: string): Promise<ModificationProposalBatch> {
    const res = await fetch(`${API_BASE_URL}/modifications/batch/${batchId}`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error("Error al consultar detalle del lote de propuestas");
    return res.json();
  }

  async reviewModificationProposal(
    proposalId: string,
    data: {
      status: "ACCEPTED" | "REJECTED" | "MODIFIED_BY_LAWYER";
      lawyer_final_text?: string;
      lawyer_notes?: string;
      reviewer_license?: string;
    }
  ): Promise<LegalModificationProposal> {
    const res = await fetch(`${API_BASE_URL}/modifications/proposals/${proposalId}/review`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al revisar propuesta");
    return resData;
  }

  async applyBatchToNewVersion(
    batchId: string,
    versionNotes: string,
    reviewerLicense?: string
  ): Promise<DocumentVersion> {
    const res = await fetch(`${API_BASE_URL}/modifications/batch/${batchId}/apply-version`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify({
        version_notes: versionNotes,
        reviewer_license: reviewerLicense || undefined,
      }),
    });
    const resData = await res.json();
    if (!res.ok) throw new Error(resData?.error?.message || resData?.detail || "Error al aplicar versión compilada");
    return resData;
  }

  async downloadExport(documentId: string, format: "docx" | "pdf", version?: number): Promise<void> {
    const url = new URL(`${API_BASE_URL}/modifications/export/${format}/${documentId}`);
    if (version !== undefined && version !== null) {
      url.searchParams.append("version", String(version));
    }

    const res = await fetch(url.toString(), {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) throw new Error(`Error al exportar documento en formato ${format.toUpperCase()}`);

    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    // Extract filename from disposition if present
    const disposition = res.headers.get("Content-Disposition");
    let filename = `documento.${format}`;
    if (disposition && disposition.includes("filename=")) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) filename = match[1];
    }
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    document.body.removeChild(a);
  }
}

export const api = new ApiClient();
