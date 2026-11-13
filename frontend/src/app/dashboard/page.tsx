"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { UserProfile, LegalDocument, DocumentPreview, AsyncTask, AIModelInfo, AIAnalysisRecord } from "@/types";
import { 
  Scale, 
  Building, 
  LogOut, 
  FileText, 
  ShieldCheck, 
  FolderLock, 
  BookOpen, 
  History, 
  PlusCircle, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  RefreshCw,
  Cpu,
  Upload,
  Search,
  Eye,
  Download,
  X,
  FileCheck,
  Calendar,
  DollarSign,
  Briefcase,
  Bot,
  Sparkles,
  Zap,
  HelpCircle,
  Lightbulb,
  AlertTriangle,
  ShieldAlert
} from "lucide-react";
import RulesEngineView from "@/components/RulesEngineView";
import AdvancedAnalysisView from "@/components/AdvancedAnalysisView";

const DOC_TYPES = [
  "CONTRATO", "CONVENIO", "DEMANDA", "CONTESTACION", 
  "ESCRITO_JUDICIAL", "PODER_NOTARIAL", "ACTA_ASAMBLEA", 
  "DOCUMENTO_CORPORATIVO", "ANEXO", "IDENTIFICACION", "OTRO"
];

const AI_AGENTS = [
  { id: "FULL_SUITE", name: "Suite Completa (Clasificación + Riesgos + Verificación)" },
  { id: "CLASSIFIER", name: "Agente Clasificador Documental" },
  { id: "EXTRACTOR", name: "Agente Extractor de Entidades & Hechos" },
  { id: "CLAUSE_ANALYST", name: "Agente Analista de Cláusulas & Omisiones" },
  { id: "RISK_DETECTOR", name: "Agente Detector de Riesgos Contractuales" },
  { id: "RESEARCHER", name: "Agente Investigador Normativo (Leyes MX)" },
  { id: "DRAFTER", name: "Agente Redactor de Cláusulas Equilibradas" },
  { id: "VERIFIER", name: "Agente Verificador de Calidad & Episteme" },
];

export default function DashboardPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [user, setUser] = useState<UserProfile | null>(null);
  const [activeTab, setActiveTab] = useState<"documents" | "advanced" | "rules" | "ai" | "tasks">("documents");

  // Documentos
  const [documents, setDocuments] = useState<LegalDocument[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDocType, setSelectedDocType] = useState<string>("");
  
  // Carga de documento
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadType, setUploadType] = useState("CONTRATO");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Modal de Vista Previa
  const [previewDoc, setPreviewDoc] = useState<DocumentPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  // Módulo de IA (Ollama Local)
  const [aiModels, setAiModels] = useState<AIModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [selectedAgent, setSelectedAgent] = useState<string>("FULL_SUITE");
  const [selectedDocForAI, setSelectedDocForAI] = useState<string>("");
  const [customPrompt, setCustomPrompt] = useState<string>("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AIAnalysisRecord | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  // Tareas asíncronas
  const [tasks, setTasks] = useState<AsyncTask[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);

  useEffect(() => {
    const currentUser = api.getCurrentUser();
    if (!currentUser) {
      router.push("/login");
      return;
    }
    setUser(currentUser);
    loadDocuments();
    loadTasks();
    loadAIModels();
  }, [router]);

  const loadDocuments = async () => {
    setLoadingDocs(true);
    try {
      const res = await api.searchDocuments(searchQuery, selectedDocType || undefined);
      setDocuments(res.items);
      if (res.items.length > 0 && !selectedDocForAI) {
        setSelectedDocForAI(res.items[0].id);
      }
    } catch (err: any) {
      console.error("Error al cargar documentos:", err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const loadTasks = async () => {
    setLoadingTasks(true);
    try {
      const data = await api.listTasks();
      setTasks(data);
    } catch (err) {
      console.error("Error al cargar tareas:", err);
    } finally {
      setLoadingTasks(false);
    }
  };

  const loadAIModels = async () => {
    try {
      const models = await api.listAIModels();
      setAiModels(models);
      if (models.length > 0) {
        // Seleccionar por defecto qwen3.5 o qwen2.5 si existe
        const defaultM = models.find(m => m.name.includes("qwen3.5") || m.name.includes("qwen2.5-coder:7b")) || models[0];
        setSelectedModel(defaultM.name);
      }
    } catch (err) {
      console.error("Error al cargar modelos de Ollama:", err);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadSuccess(null);
    setUploadError(null);

    const formData = new FormData();
    formData.append("file", uploadFile);
    if (uploadTitle) formData.append("title", uploadTitle);
    formData.append("doc_type", uploadType);

    try {
      const newDoc = await api.uploadDocument(formData);
      setUploadSuccess(`Documento "${newDoc.title}" cargado e indexado en bóveda inmutable.`);
      setUploadFile(null);
      setUploadTitle("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      await loadDocuments();
      setSelectedDocForAI(newDoc.id);
    } catch (err: any) {
      setUploadError(err?.message || "Error al cargar documento");
    } finally {
      setUploading(false);
    }
  };

  const handleRunAIAnalysis = async () => {
    if (!selectedDocForAI) return;
    setAnalyzing(true);
    setAiError(null);
    setAnalysisResult(null);

    try {
      const result = await api.analyzeDocument(
        selectedDocForAI,
        selectedAgent,
        selectedModel || undefined,
        customPrompt || undefined
      );
      setAnalysisResult(result);
    } catch (err: any) {
      setAiError(err?.message || "Error durante la inferencia en Ollama");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleOpenPreview = async (docId: string) => {
    setLoadingPreview(true);
    try {
      const data = await api.previewDocument(docId);
      setPreviewDoc(data);
    } catch (err: any) {
      alert(`Error al generar vista previa: ${err?.message}`);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDownload = async (docId: string, filename: string) => {
    try {
      const url = api.getDownloadUrl(docId);
      const res = await fetch(url, {
        headers: { ...api.getAuthHeader() }
      });
      if (!res.ok) throw new Error("Error en descarga autorizada");
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`Error al descargar: ${err?.message}`);
    }
  };

  const handleLogout = () => {
    api.logout();
    router.push("/login");
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Topbar */}
      <nav className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-amber-400 text-slate-900 p-2 rounded-lg font-bold">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight">LegalAI México</span>
              <span className="text-xs text-slate-400 block font-mono">Motor de IA Local & Bóveda Inmutable</span>
            </div>
          </div>

          <div className="flex items-center space-x-6">
            <div className="hidden md:flex items-center space-x-2 text-xs text-slate-300">
              <Building className="h-4 w-4 text-amber-400" />
              <span className="font-semibold text-white">{user.tenant_name}</span>
            </div>

            <div className="flex items-center space-x-3 border-l border-slate-800 pl-6">
              <div className="text-right">
                <span className="text-xs font-semibold block text-white">{user.full_name}</span>
                <span className="text-[10px] text-amber-400 font-mono block">{user.role}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Cerrar Sesión"
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 mb-6 space-x-8">
          <button
            onClick={() => setActiveTab("documents")}
            className={`pb-3 text-sm font-semibold flex items-center space-x-2 border-b-2 transition-all ${
              activeTab === "documents"
                ? "border-slate-900 text-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <FolderLock className="h-4 w-4" />
            <span>Bóveda Documental (WORM)</span>
            <span className="px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700">{documents.length}</span>
          </button>

          <button
            onClick={() => setActiveTab("advanced")}
            className={`pb-3 text-sm font-semibold flex items-center space-x-2 border-b-2 transition-all ${
              activeTab === "advanced"
                ? "border-slate-900 text-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <ShieldAlert className="h-4 w-4 text-rose-600" />
            <span>Análisis Jurídico Avanzado</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-rose-50 text-rose-700 font-bold border border-rose-200">
              Auditoría Integral
            </span>
          </button>

          <button
            onClick={() => setActiveTab("rules")}
            className={`pb-3 text-sm font-semibold flex items-center space-x-2 border-b-2 transition-all ${
              activeTab === "rules"
                ? "border-slate-900 text-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Scale className="h-4 w-4 text-emerald-600" />
            <span>Motor de Reglas Deterministas</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">
              Criterio Objetivo
            </span>
          </button>

          <button
            onClick={() => setActiveTab("ai")}
            className={`pb-3 text-sm font-semibold flex items-center space-x-2 border-b-2 transition-all ${
              activeTab === "ai"
                ? "border-slate-900 text-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Bot className="h-4 w-4 text-indigo-600" />
            <span>Agentes de IA (Ollama Local)</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">
              GPU NVIDIA 6GB
            </span>
          </button>

          <button
            onClick={() => setActiveTab("tasks")}
            className={`pb-3 text-sm font-semibold flex items-center space-x-2 border-b-2 transition-all ${
              activeTab === "tasks"
                ? "border-slate-900 text-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Cpu className="h-4 w-4" />
            <span>Cola Asíncrona</span>
            <span className="px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700">{tasks.length}</span>
          </button>
        </div>

        {activeTab === "documents" ? (
          <div>
            {/* Upload Section */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-8">
              <h2 className="text-base font-bold text-slate-900 mb-1 flex items-center space-x-2">
                <Upload className="h-4 w-4 text-amber-500" />
                <span>Cargar Documento Jurídico a la Bóveda</span>
              </h2>
              <p className="text-xs text-slate-500 mb-4">
                Formatos: PDF, DOCX, TXT e imágenes. Se aplica hashing SHA-256 inmutable, sanitización contra Prompt Injection y extracción automática de metadatos.
              </p>

              {uploadSuccess && (
                <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              {uploadError && (
                <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              <form onSubmit={handleUploadSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Título del Documento</label>
                  <input
                    type="text"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    placeholder="Ej. Contrato Arrendamiento 2026"
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Clasificación Jurídica</label>
                  <select
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value)}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                  >
                    {DOC_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Archivo (Máx. 50 MB)</label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    required
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="w-full text-xs p-1.5 border border-slate-300 rounded-lg file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
                  />
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={uploading || !uploadFile}
                    className="w-full py-2.5 px-4 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800 transition-all shadow-sm flex items-center justify-center space-x-1.5 disabled:opacity-50"
                  >
                    <Upload className="h-4 w-4" />
                    <span>{uploading ? "Procesando..." : "Subir e Indexar"}</span>
                  </button>
                </div>
              </form>
            </div>

            {/* Search & Filter Bar */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm mb-6 flex flex-col sm:flex-row gap-4 justify-between items-center">
              <div className="relative w-full sm:w-96">
                <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && loadDocuments()}
                  placeholder="Buscar por texto contenido, título o número..."
                  className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="flex items-center space-x-3 w-full sm:w-auto">
                <select
                  value={selectedDocType}
                  onChange={(e) => {
                    setSelectedDocType(e.target.value);
                  }}
                  className="text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                >
                  <option value="">Todos los tipos jurídicos</option>
                  {DOC_TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>

                <button
                  onClick={loadDocuments}
                  className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-medium transition-colors flex items-center space-x-1"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${loadingDocs ? "animate-spin text-amber-600" : ""}`} />
                  <span>Filtrar</span>
                </button>
              </div>
            </div>

            {/* Documents Table */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              {documents.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <FileText className="h-10 w-10 mx-auto mb-2 opacity-40" />
                  <p className="text-sm font-medium">No se encontraron documentos en la bóveda.</p>
                  <p className="text-xs text-slate-400 mt-1">Carga tu primer contrato, demanda o acuerdo judicial arriba.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200 text-xs">
                    <thead>
                      <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                        <th className="py-3 px-4">Título / Archivo</th>
                        <th className="py-3 px-4">Clasificación</th>
                        <th className="py-3 px-4">Hash SHA-256</th>
                        <th className="py-3 px-4">Páginas</th>
                        <th className="py-3 px-4">Fecha</th>
                        <th className="py-3 px-4 text-right">Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {documents.map((d) => (
                        <tr key={d.id} className="hover:bg-slate-50 transition-colors">
                          <td className="py-3 px-4">
                            <span className="font-bold text-slate-900 block">{d.title}</span>
                            <span className="text-[11px] text-slate-500 font-mono">{d.filename} • {(d.file_size_bytes / 1024).toFixed(1)} KB</span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                              {d.doc_type}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                            <span title={d.sha256_hash} className="cursor-help">
                              {d.sha256_hash.slice(0, 12)}...
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-700 font-medium">{d.page_count} pág(s)</td>
                          <td className="py-3 px-4 text-slate-500 font-mono">{new Date(d.created_at).toLocaleDateString()}</td>
                          <td className="py-3 px-4 text-right space-x-2">
                            <button
                              onClick={() => handleOpenPreview(d.id)}
                              className="px-2.5 py-1 text-slate-700 bg-slate-100 hover:bg-slate-200 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                            >
                              <Eye className="h-3.5 w-3.5 text-slate-600" />
                              <span>Vista Previa</span>
                            </button>
                            <button
                              onClick={() => {
                                setSelectedDocForAI(d.id);
                                setActiveTab("rules");
                              }}
                              className="px-2.5 py-1 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                            >
                              <Scale className="h-3.5 w-3.5 text-emerald-600" />
                              <span>Reglas</span>
                            </button>
                            <button
                              onClick={() => {
                                setSelectedDocForAI(d.id);
                                setActiveTab("advanced");
                              }}
                              className="px-2.5 py-1 text-rose-800 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                            >
                              <ShieldAlert className="h-3.5 w-3.5 text-rose-600" />
                              <span>Análisis Avanzado</span>
                            </button>
                            <button
                              onClick={() => {
                                setSelectedDocForAI(d.id);
                                setActiveTab("ai");
                              }}
                              className="px-2.5 py-1 text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                            >
                              <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                              <span>Analizar con IA</span>
                            </button>
                            <button
                              onClick={() => handleDownload(d.id, d.filename)}
                              className="px-2.5 py-1 text-slate-900 bg-amber-400 hover:bg-amber-300 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                            >
                              <Download className="h-3.5 w-3.5" />
                              <span>Descargar</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : activeTab === "advanced" ? (
          <AdvancedAnalysisView
            documents={documents}
            initialSelectedDocId={selectedDocForAI || documents[0]?.id}
            userRole={user?.role}
          />
        ) : activeTab === "rules" ? (
          <RulesEngineView
            documents={documents}
            initialSelectedDocId={selectedDocForAI || documents[0]?.id}
            userRole={user?.role}
          />
        ) : activeTab === "ai" ? (
          /* Pestaña de Agentes de IA */
          <div>
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 mb-6 gap-4">
                <div>
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 mb-1">
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Inferencia Soberana 100% Local • Zero Data Exfiltration</span>
                  </span>
                  <h2 className="text-xl font-bold text-slate-900">Agentes de IA Especializados (Ollama)</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Análisis contractual, detección de riesgos y auditoría epistémica ejecutada en tu GPU local.
                  </p>
                </div>

                <div className="flex items-center space-x-2 text-xs text-slate-500">
                  <Cpu className="h-4 w-4 text-emerald-600" />
                  <span>Modelos en GPU: <strong>{aiModels.length} detectados</strong></span>
                </div>
              </div>

              {aiError && (
                <div className="mb-6 p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2">
                  <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Error durante el análisis:</span>
                    <p className="mt-0.5">{aiError}</p>
                  </div>
                </div>
              )}

              {/* Controles de Configuración del Agente */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Documento a Analizar</label>
                  <select
                    value={selectedDocForAI}
                    onChange={(e) => setSelectedDocForAI(e.target.value)}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600 bg-white"
                  >
                    {documents.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.title} ({d.doc_type})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Agente Especializado</label>
                  <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600 bg-white font-medium"
                  >
                    {AI_AGENTS.map((a) => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Modelo Ollama Local</label>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600 bg-white font-mono"
                  >
                    {aiModels.map((m) => (
                      <option key={m.name} value={m.name}>
                        {m.name} ({m.parameter_size || (m.size_bytes / (1024*1024*1024)).toFixed(1) + " GB"})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Instrucción Adicional u Objetivo Específico (Opcional)
                </label>
                <input
                  type="text"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Ej. Enfatizar revisión de cláusulas de pena convencional y vigencia de poderes..."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleRunAIAnalysis}
                  disabled={analyzing || !selectedDocForAI}
                  className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold shadow-md transition-all flex items-center space-x-2 disabled:opacity-50"
                >
                  <Sparkles className={`h-4 w-4 ${analyzing ? "animate-spin" : ""}`} />
                  <span>{analyzing ? "Inferencia en progreso (Ollama GPU)..." : "Ejecutar Análisis Jurídico"}</span>
                </button>
              </div>
            </div>

            {/* Resultados del Análisis con Distinción Epistémica */}
            {analysisResult && (
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 mb-6 gap-2">
                  <div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-900 text-amber-400 font-mono uppercase mr-2">
                      {analysisResult.agent_type}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      Modelo: <strong>{analysisResult.model_used}</strong>
                    </span>
                  </div>

                  <div className="flex items-center space-x-4 text-xs font-mono text-slate-600">
                    <span className="flex items-center space-x-1">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      <span>{analysisResult.latency_ms} ms</span>
                    </span>
                    <span>Tokens In: {analysisResult.tokens_prompt}</span>
                    <span>Tokens Out: {analysisResult.tokens_completion}</span>
                  </div>
                </div>

                {/* Grid Epistémico */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Hechos Extraídos (Facts) */}
                  <div className="border border-emerald-200 rounded-xl p-4 bg-emerald-50/40">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center space-x-1.5 mb-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      <span>Hechos Verificables 1:1 en el Documento (Facts)</span>
                    </h3>
                    <ul className="text-xs text-slate-800 space-y-1.5 list-disc pl-4">
                      {analysisResult.structured_output.facts && analysisResult.structured_output.facts.length > 0 ? (
                        analysisResult.structured_output.facts.map((f: string, i: number) => (
                          <li key={i}>{f}</li>
                        ))
                      ) : (
                        <li className="text-slate-500 italic">No se declararon hechos aislados.</li>
                      )}
                    </ul>
                  </div>

                  {/* Inferencias Lógicas */}
                  <div className="border border-blue-200 rounded-xl p-4 bg-blue-50/40">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-blue-800 flex items-center space-x-1.5 mb-2">
                      <Lightbulb className="h-4 w-4 text-blue-600" />
                      <span>Inferencias Jurídicas Razonadas</span>
                    </h3>
                    <ul className="text-xs text-slate-800 space-y-1.5 list-disc pl-4">
                      {analysisResult.structured_output.inferences && analysisResult.structured_output.inferences.length > 0 ? (
                        analysisResult.structured_output.inferences.map((inf: string, i: number) => (
                          <li key={i}>{inf}</li>
                        ))
                      ) : (
                        <li className="text-slate-500 italic">No se emitieron inferencias.</li>
                      )}
                    </ul>
                  </div>

                  {/* Hipótesis Procesales */}
                  <div className="border border-amber-200 rounded-xl p-4 bg-amber-50/40">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center space-x-1.5 mb-2">
                      <HelpCircle className="h-4 w-4 text-amber-600" />
                      <span>Hipótesis & Escenarios de Controversia</span>
                    </h3>
                    <ul className="text-xs text-slate-800 space-y-1.5 list-disc pl-4">
                      {analysisResult.structured_output.hypotheses && analysisResult.structured_output.hypotheses.length > 0 ? (
                        analysisResult.structured_output.hypotheses.map((h: string, i: number) => (
                          <li key={i}>{h}</li>
                        ))
                      ) : (
                        <li className="text-slate-500 italic">Sin hipótesis contingentes.</li>
                      )}
                    </ul>
                  </div>

                  {/* Recomendaciones */}
                  <div className="border border-purple-200 rounded-xl p-4 bg-purple-50/40">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-purple-900 flex items-center space-x-1.5 mb-2">
                      <Sparkles className="h-4 w-4 text-purple-600" />
                      <span>Recomendaciones Estratégicas (No Vinculantes)</span>
                    </h3>
                    <ul className="text-xs text-slate-800 space-y-1.5 list-disc pl-4">
                      {analysisResult.structured_output.recommendations && analysisResult.structured_output.recommendations.length > 0 ? (
                        analysisResult.structured_output.recommendations.map((r: string, i: number) => (
                          <li key={i}>{r}</li>
                        ))
                      ) : (
                        <li className="text-slate-500 italic">Sin recomendaciones adicionales.</li>
                      )}
                    </ul>
                  </div>
                </div>

                {/* Bloque de Salida Estructurada Completa en JSON */}
                <div className="mt-6 pt-4 border-t border-slate-200">
                  <span className="text-xs font-bold text-slate-700 block mb-2">JSON Estructurado Validado:</span>
                  <pre className="bg-slate-900 text-slate-100 p-4 rounded-xl text-xs font-mono overflow-x-auto max-h-60 leading-relaxed">
                    {JSON.stringify(analysisResult.structured_output, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Tasks View */
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Historial de Procesamiento Asíncrono</h2>
                <p className="text-xs text-slate-500">Trazabilidad de colas de OCR y extracción documental.</p>
              </div>
              <button onClick={loadTasks} className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50">
                <RefreshCw className={`h-4 w-4 ${loadingTasks ? "animate-spin text-amber-600" : ""}`} />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                    <th className="py-2.5 px-3">ID Tarea</th>
                    <th className="py-2.5 px-3">Tipo</th>
                    <th className="py-2.5 px-3">Estado</th>
                    <th className="py-2.5 px-3">Creación</th>
                    <th className="py-2.5 px-3">Detalle</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {tasks.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-700">{t.id.slice(0, 8)}...</td>
                      <td className="py-2.5 px-3 font-semibold text-slate-900">{t.task_type}</td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          t.status === "COMPLETED" ? "bg-emerald-100 text-emerald-800" :
                          t.status === "PROCESSING" ? "bg-amber-100 text-amber-800 animate-pulse" :
                          "bg-slate-100 text-slate-700"
                        }`}>
                          {t.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-500 font-mono">{new Date(t.created_at).toLocaleTimeString()}</td>
                      <td className="py-2.5 px-3 text-slate-600 font-mono text-[11px]">
                        {t.result ? JSON.stringify(t.result).slice(0, 50) + "..." : (t.error_message || "En cola")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal de Vista Previa y Metadatos Jurídicos */}
        {previewDoc && (
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-slate-200">
              {/* Modal Header */}
              <div className="p-5 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 uppercase tracking-wider mb-1 inline-block">
                    {previewDoc.doc_type}
                  </span>
                  <h3 className="text-lg font-bold text-slate-900">{previewDoc.title}</h3>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">SHA-256: {previewDoc.sha256_hash}</p>
                </div>
                <button
                  onClick={() => setPreviewDoc(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6 overflow-y-auto flex-1 grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Metadatos Jurídicos Extraídos */}
                <div className="md:col-span-1 space-y-4 border-r border-slate-100 pr-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
                    <FileCheck className="h-4 w-4 text-emerald-600" />
                    <span>Metadatos Extraídos</span>
                  </h4>

                  {previewDoc.metadata?.doc_date && (
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                      <span className="text-[10px] font-semibold text-slate-500 uppercase flex items-center space-x-1">
                        <Calendar className="h-3 w-3" />
                        <span>Fecha del Instrumento</span>
                      </span>
                      <p className="text-xs font-medium text-slate-900 mt-0.5">{previewDoc.metadata.doc_date}</p>
                    </div>
                  )}

                  {previewDoc.metadata?.amounts && previewDoc.metadata.amounts.length > 0 && (
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                      <span className="text-[10px] font-semibold text-slate-500 uppercase flex items-center space-x-1">
                        <DollarSign className="h-3 w-3 text-emerald-600" />
                        <span>Montos Económicos</span>
                      </span>
                      <ul className="text-xs font-mono text-emerald-700 mt-1 space-y-0.5">
                        {previewDoc.metadata.amounts.map((a, i) => (
                          <li key={i}>• {a}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {previewDoc.metadata?.parties && previewDoc.metadata.parties.length > 0 && (
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                      <span className="text-[10px] font-semibold text-slate-500 uppercase flex items-center space-x-1">
                        <Briefcase className="h-3 w-3" />
                        <span>Partes Identificadas</span>
                      </span>
                      <div className="text-xs text-slate-800 mt-1 space-y-1">
                        {previewDoc.metadata.parties.map((p, i) => (
                          <div key={i}>
                            <span className="font-semibold text-slate-700">{p.role}:</span> {p.name}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {previewDoc.metadata?.jurisdiction && (
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                      <span className="text-[10px] font-semibold text-slate-500 uppercase">Jurisdicción Pactada</span>
                      <p className="text-xs text-slate-800 mt-0.5">{previewDoc.metadata.jurisdiction}</p>
                    </div>
                  )}

                  <div className="text-[11px] text-slate-400">
                    Procesado en {previewDoc.metadata?.processing_time_ms || 0} ms • Páginas: {previewDoc.page_count}
                  </div>
                </div>

                {/* Texto Extraído Normalizado */}
                <div className="md:col-span-2 flex flex-col">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Texto Extraído Sanitizado
                    </h4>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200">
                      Blindaje Anti-Prompt Injection Activo
                    </span>
                  </div>
                  <div className="bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-xs whitespace-pre-wrap flex-1 overflow-y-auto max-h-[50vh] leading-relaxed">
                    {previewDoc.raw_text}
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="p-4 border-t border-slate-200 flex justify-end space-x-3 bg-slate-50 rounded-b-2xl">
                <button
                  onClick={() => setPreviewDoc(null)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-white"
                >
                  Cerrar
                </button>
                <button
                  onClick={() => handleDownload(previewDoc.id, previewDoc.filename)}
                  className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800 flex items-center space-x-1.5"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Descargar Archivo Original</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
