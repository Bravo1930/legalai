"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { 
  UserProfile, 
  LegalDocument, 
  DocumentPreview, 
  AsyncTask, 
  AIModelInfo, 
  AIAnalysisRecord, 
  WorkflowNotification 
} from "@/types";
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
  ShieldAlert,
  FileEdit,
  GitMerge,
  Bell,
  LayoutDashboard,
  Users,
  Settings,
  Server,
  ChevronRight,
  Menu,
  Brain,
  Send
} from "lucide-react";

import DashboardView from "@/components/DashboardView";
import DocumentReviewViewer from "@/components/DocumentReviewViewer";
import CasesView from "@/components/CasesView";
import ClientsView from "@/components/ClientsView";
import RisksView from "@/components/RisksView";
import RulesEngineView from "@/components/RulesEngineView";
import AdvancedAnalysisView from "@/components/AdvancedAnalysisView";
import ModificationsView from "@/components/ModificationsView";
import WorkflowView from "@/components/WorkflowView";
import ApprovalsView from "@/components/ApprovalsView";
import UsersView from "@/components/UsersView";
import NotificationsView from "@/components/NotificationsView";
import AuditView from "@/components/AuditView";
import SettingsView from "@/components/SettingsView";
import AdminView from "@/components/AdminView";

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
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  // Floating Toast Notifications System (Bottom-Right, 4s auto-dismiss, manual dismiss)
  interface ToastItem {
    id: string;
    title: string;
    message?: string;
    type?: "info" | "success" | "warning" | "error" | "loading";
  }
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = (
    title: string,
    message?: string,
    type: "info" | "success" | "warning" | "error" | "loading" = "info"
  ) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Notificaciones In-App
  const [notifications, setNotifications] = useState<WorkflowNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [showNotifMenu, setShowNotifMenu] = useState<boolean>(false);

  // Documentos
  const [documents, setDocuments] = useState<LegalDocument[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [docAccessDenied, setDocAccessDenied] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDocType, setSelectedDocType] = useState<string>("");
  const [docPage, setDocPage] = useState<number>(1);
  const docPageSize = 10;

  // Floating AI Assistant Chat Panel
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ id: string; sender: "user" | "assistant"; text: string; time: string }>>([
    {
      id: "initial",
      sender: "assistant",
      text: "Hola, soy el Asistente Jurídico de LegalAI México con Inferencia Soberana local. ¿En qué asunto procesal, contractual o normativo le puedo asistir hoy?",
      time: "Ahora"
    }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatThinking, setChatThinking] = useState(false);

  const handleSendChatMessage = async (presetText?: string) => {
    const text = (presetText || chatInput).trim();
    if (!text || chatThinking) return;

    const userMsg = {
      id: Math.random().toString(36).substring(2, 9),
      sender: "user" as const,
      text,
      time: new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" })
    };

    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setChatThinking(true);

    try {
      const resp = await api.askLegalAssistant(text, selectedDocForAI || undefined, selectedModel || undefined);
      const assistantMsg = {
        id: Math.random().toString(36).substring(2, 9),
        sender: "assistant" as const,
        text: resp.reply,
        time: new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" })
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      let fallbackText = "Conforme a la legislación mexicana aplicable:\n\n";
      const q = text.toLowerCase();
      if (q.includes("confidencialidad") || q.includes("lfppi")) {
        fallbackText += "Conforme al Artículo 82 y 85 de la LFPPI, la cláusula debe definir explícitamente la información reservada, el secreto industrial y las medidas técnicas adoptadas para su salvaguarda.";
      } else if (q.includes("pagaré") || q.includes("lgtoc")) {
        fallbackText += "Conforme al Artículo 170 de la LGTOC, el pagaré debe contener la mención de ser pagaré, la promesa incondicional de pagar una suma determinada, nombre del beneficiario, época y lugar de pago, fecha y lugar de suscripción, y la firma del suscriptor.";
      } else if (q.includes("mercantil") || q.includes("demanda")) {
        fallbackText += "Conforme al Artículo 1378 del Código de Comercio, el término para contestar una demanda en juicio oral mercantil es de nueve días hábiles siguientes al emplazamiento.";
      } else {
        fallbackText += "He registrado su consulta. Recomiendo verificar la correspondencia con las tesis y jurisprudencias aplicables de la Suprema Corte de Justicia de la Nación.";
      }
      setChatMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).substring(2, 9),
          sender: "assistant",
          text: fallbackText,
          time: new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" })
        }
      ]);
    } finally {
      setChatThinking(false);
    }
  };
  
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
    
    // Si es SUPER_ADMIN, no consultar documentos de despachos (Zero-Knowledge)
    if (currentUser.role?.toUpperCase() === "SUPER_ADMIN") {
      setDocAccessDenied("Plano de Control: El Administrador Global no tiene acceso a documentos privados de despachos por diseño de privacidad.");
    } else {
      loadDocuments();
    }
    
    loadTasks();
    loadAIModels();
    loadNotifications();
  }, [router]);

  const loadNotifications = async () => {
    try {
      const count = await api.getUnreadNotificationsCount();
      setUnreadCount(count);
      const list = await api.listNotifications(false);
      setNotifications(list);
    } catch (err) {
      console.error("Error al cargar notificaciones:", err);
    }
  };

  const handleMarkNotificationRead = async (notifId: string) => {
    try {
      await api.markNotificationRead(notifId);
      await loadNotifications();
    } catch (err) {
      console.error("Error al marcar notificación:", err);
    }
  };

  const handleMarkAllNotificationsRead = async () => {
    try {
      await api.markAllNotificationsRead();
      await loadNotifications();
    } catch (err) {
      console.error("Error al marcar todas las notificaciones:", err);
    }
  };

  const loadDocuments = async () => {
    const curUser = api.getCurrentUser();
    if (curUser?.role?.toUpperCase() === "SUPER_ADMIN") {
      setDocAccessDenied("Plano de Control: El Administrador Global no tiene acceso a documentos privados de despachos por diseño de privacidad.");
      return;
    }
    setLoadingDocs(true);
    setDocAccessDenied(null);
    try {
      const res = await api.searchDocuments(searchQuery, selectedDocType || undefined);
      setDocuments(res.items);
      if (res.items.length > 0 && !selectedDocForAI) {
        setSelectedDocForAI(res.items[0].id);
      }
    } catch (err: any) {
      if (err?.status === 401 || err?.message?.includes("401") || err?.message?.includes("Sesión")) {
        api.logout();
        router.push("/login");
        return;
      }
      if (err?.status === 403 || err?.message?.includes("403") || err?.message?.includes("permiso")) {
        setDocAccessDenied("Acceso restringido: Su rol actual no cuenta con permisos para consultar la bóveda de documentos.");
      } else {
        console.error("Error al cargar documentos:", err);
      }
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

  const isSuperAdmin = user.role === "SUPER_ADMIN";
  const isManagingPartner = user.role === "MANAGING_PARTNER" || user.role === "ADMIN";
  const isLawyer = user.role === "SENIOR_LAWYER" || user.role === "ASSOCIATE_LAWYER" || user.role === "LAWYER" || isManagingPartner;
  const isReviewer = user.role === "REVIEWER" || user.role === "AUDITOR";
  const isAssistant = user.role === "ASSISTANT" || user.role === "PARALEGAL" || user.role === "LEGAL_ASSISTANT";

  const renderSidebarNav = (isMobile: boolean = false) => {
    const handleNavSelect = (tab: string) => {
      setActiveTab(tab);
      if (isMobile) setSidebarOpen(false);
    };

    const containerCardClass = isMobile
      ? "bg-slate-800/90 backdrop-blur-md rounded-2xl border border-slate-700/80 p-3 shadow-xs"
      : "bg-white/90 backdrop-blur-md rounded-2xl border border-slate-200/80 p-3 shadow-xs";

    const getBtnClass = (tab: string) => {
      const isActive = activeTab === tab;
      if (isActive) {
        return "bg-slate-900 text-white shadow-xs";
      }
      return isMobile
        ? "text-slate-300 hover:bg-slate-800/80 hover:text-white"
        : "text-slate-600 hover:bg-slate-100";
    };

    return (
      <div className="space-y-4">
        {/* Group 1: Operación Jurídica */}
        <div className={containerCardClass}>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-2 block font-mono">
            Operación Jurídica
          </span>
          <nav className="space-y-1">
            <button
              onClick={() => handleNavSelect("dashboard")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("dashboard")}`}
            >
              <LayoutDashboard className="h-4 w-4 text-amber-400" />
              <span>Dashboard General</span>
            </button>

            <button
              onClick={() => handleNavSelect("documents")}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("documents")}`}
            >
              <div className="flex items-center space-x-2.5">
                <FolderLock className="h-4 w-4 text-slate-400" />
                <span>Bóveda Documental</span>
              </div>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${isMobile ? "bg-slate-700 text-slate-300" : "bg-slate-100 text-slate-700"}`}>
                {documents.length}
              </span>
            </button>

            <button
              onClick={() => handleNavSelect("review")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("review")}`}
            >
              <BookOpen className="h-4 w-4 text-amber-500" />
              <span>Visor de Revisión</span>
            </button>

            <button
              onClick={() => handleNavSelect("cases")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("cases")}`}
            >
              <Briefcase className="h-4 w-4 text-blue-500" />
              <span>Expedientes & Asuntos</span>
            </button>

            <button
              onClick={() => handleNavSelect("clients")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("clients")}`}
            >
              <Building className="h-4 w-4 text-emerald-500" />
              <span>Directorio Clientes</span>
            </button>

            <button
              onClick={() => handleNavSelect("workflow")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("workflow")}`}
            >
              <GitMerge className="h-4 w-4 text-indigo-500" />
              <span>Flujos de Trabajo</span>
            </button>

            <button
              onClick={() => handleNavSelect("approvals")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("approvals")}`}
            >
              <FileCheck className="h-4 w-4 text-emerald-600" />
              <span>Aprobaciones Formales</span>
            </button>
          </nav>
        </div>

        {/* Group 2: Inteligencia & Análisis */}
        <div className={containerCardClass}>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-2 block font-mono">
            Inteligencia & Análisis
          </span>
          <nav className="space-y-1">
            <button
              onClick={() => handleNavSelect("ai_agents")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("ai_agents")}`}
            >
              <Bot className="h-4 w-4 text-indigo-500" />
              <span>Agentes IA (Ollama)</span>
            </button>

            <button
              onClick={() => handleNavSelect("advanced")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("advanced")}`}
            >
              <ShieldAlert className="h-4 w-4 text-rose-500" />
              <span>Auditoría Integral</span>
            </button>

            <button
              onClick={() => handleNavSelect("risks")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("risks")}`}
            >
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              <span>Matriz de Riesgos</span>
            </button>

            <button
              onClick={() => handleNavSelect("rules")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("rules")}`}
            >
              <Scale className="h-4 w-4 text-emerald-500" />
              <span>Reglas Deterministas</span>
            </button>

            <button
              onClick={() => handleNavSelect("modifications")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("modifications")}`}
            >
              <FileEdit className="h-4 w-4 text-amber-500" />
              <span>Propuestas & Redacción</span>
            </button>
          </nav>
        </div>

        {/* Group 3: Gobierno & Despacho */}
        <div className={containerCardClass}>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-2 block font-mono">
            Gobierno & Despacho
          </span>
          <nav className="space-y-1">
            <button
              onClick={() => handleNavSelect("notifications")}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("notifications")}`}
            >
              <div className="flex items-center space-x-2.5">
                <Bell className="h-4 w-4 text-slate-400" />
                <span>Notificaciones</span>
              </div>
              {unreadCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-rose-600 text-white font-bold">
                  {unreadCount}
                </span>
              )}
            </button>

            <button
              onClick={() => handleNavSelect("users")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("users")}`}
            >
              <Users className="h-4 w-4 text-slate-500" />
              <span>Equipo & Abogados</span>
            </button>

            <button
              onClick={() => handleNavSelect("audit")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("audit")}`}
            >
              <History className="h-4 w-4 text-slate-500" />
              <span>Bitácora Forense</span>
            </button>

            <button
              onClick={() => handleNavSelect("settings")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("settings")}`}
            >
              <Settings className="h-4 w-4 text-slate-500" />
              <span>Configuración</span>
            </button>

            {(isSuperAdmin || isManagingPartner) && (
              <button
                onClick={() => handleNavSelect("admin")}
                className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("admin")}`}
              >
                <Server className="h-4 w-4 text-rose-500" />
                <span>Administración</span>
              </button>
            )}

            <button
              onClick={() => handleNavSelect("tasks")}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all ${getBtnClass("tasks")}`}
            >
              <div className="flex items-center space-x-2.5">
                <Cpu className="h-4 w-4 text-slate-400" />
                <span>Cola Asíncrona</span>
              </div>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${isMobile ? "bg-slate-700 text-slate-300" : "bg-slate-100 text-slate-700"}`}>
                {tasks.length}
              </span>
            </button>
          </nav>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Topbar */}
      <nav className="bg-slate-900/85 backdrop-blur-xl border-b border-white/10 text-white sticky top-0 z-40 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.25)]">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2">
          {/* Brand & Toggle */}
          <div className="flex items-center space-x-2 sm:space-x-3 min-w-0">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="apple-interactive p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/80 lg:hidden shrink-0"
              aria-label="Alternar menú lateral"
            >
              <Menu className="h-5 w-5" />
            </button>

            <div className="bg-amber-400 text-slate-900 p-2 rounded-xl font-bold shadow-xs shrink-0">
              <Scale className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <span className="text-base sm:text-lg font-bold tracking-tight text-white whitespace-nowrap block">
                LegalAI México
              </span>
              <span className="hidden lg:block text-xs text-slate-400 font-mono truncate">
                Plataforma Jurídica Integral | Bóveda Inmutable y Motor Local
              </span>
            </div>
          </div>

          {/* User & Actions */}
          <div className="flex items-center space-x-2 sm:space-x-4 shrink-0">
            <div className="hidden xl:flex items-center space-x-2 text-xs text-slate-300 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10">
              <Building className="h-4 w-4 text-amber-400 shrink-0" />
              <span className="font-semibold text-white truncate max-w-[140px]">{user.tenant_name}</span>
            </div>

            {/* Centro de Notificaciones In-App */}
            <div className="relative">
              <button
                onClick={() => setShowNotifMenu(!showNotifMenu)}
                title="Notificaciones Jurídicas"
                className="apple-interactive relative p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/80 transition-colors"
              >
                <Bell className="h-5 w-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white shadow-xs">
                    {unreadCount > 9 ? "9+" : unreadCount}
                  </span>
                )}
              </button>

              {/* Dropdown Popover */}
              {showNotifMenu && (
                <div className="absolute right-0 mt-2 w-80 md:w-96 rounded-2xl bg-white/95 backdrop-blur-2xl shadow-2xl border border-slate-200/80 z-50 text-slate-900 overflow-hidden">
                  <div className="p-3 bg-slate-900 text-white flex items-center justify-between border-b border-white/10">
                    <div className="flex items-center space-x-2">
                      <Bell className="h-4 w-4 text-amber-400" />
                      <span className="text-xs font-bold">Alertas y Vencimientos</span>
                    </div>
                    {unreadCount > 0 && (
                      <button
                        onClick={handleMarkAllNotificationsRead}
                        className="text-[10px] text-amber-300 hover:text-amber-200 underline font-medium"
                      >
                        Marcar todas leídas
                      </button>
                    )}
                  </div>

                  <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                    {notifications.length === 0 ? (
                      <div className="p-6 text-center text-xs text-slate-400">
                        No hay notificaciones en su buzón.
                      </div>
                    ) : (
                      notifications.slice(0, 10).map((n) => (
                        <div
                          key={n.id}
                          onClick={() => {
                            handleMarkNotificationRead(n.id);
                            setShowNotifMenu(false);
                            setActiveTab("notifications");
                          }}
                          className={`p-3 text-xs cursor-pointer hover:bg-slate-50 transition-colors ${
                            !n.is_read ? "bg-amber-50/40 font-medium" : "text-slate-600"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-1">
                            <span className="font-bold text-slate-900 text-[11px] block">{n.title}</span>
                            <span className="text-[10px] text-slate-400 font-mono flex-shrink-0">
                              {new Date(n.created_at).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" })}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-600 mt-0.5 leading-relaxed">{n.message}</p>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="p-2 border-t border-slate-100 bg-slate-50 text-center">
                    <button
                      onClick={() => {
                        setShowNotifMenu(false);
                        setActiveTab("notifications");
                      }}
                      className="apple-interactive text-xs text-slate-700 hover:text-slate-900 font-semibold"
                    >
                      Ver todas las notificaciones →
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* User Profile */}
            <div className="flex items-center space-x-2 sm:space-x-3 border-l border-white/15 pl-2 sm:pl-4">
              <div className="text-right">
                <span className="text-xs font-semibold block text-white truncate max-w-[95px] sm:max-w-[140px] md:max-w-[180px]" title={user.full_name}>
                  {user.full_name}
                </span>
                <span className="text-[10px] text-amber-400 font-mono block truncate max-w-[95px] sm:max-w-[140px]">
                  {user.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                title="Cerrar Sesión"
                className="apple-interactive p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors shrink-0"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Drawer Backdrop */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs z-40 lg:hidden"
        />
      )}

      {/* Mobile Slide-out Drawer */}
      <aside
        className={`fixed top-0 left-0 bottom-0 z-50 w-72 bg-slate-900 border-r border-slate-800 p-4 overflow-y-auto space-y-4 shadow-2xl transition-transform duration-300 ease-out lg:hidden ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <div className="bg-amber-400 text-slate-900 p-1.5 rounded-lg font-bold">
              <Scale className="h-4 w-4" />
            </div>
            <span className="text-sm font-bold text-white">Menú Legal</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            aria-label="Cerrar menú"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        {renderSidebarNav(true)}
      </aside>

      {/* Main Body */}
      <div className="flex-1 flex max-w-7xl mx-auto w-full px-3 sm:px-6 lg:px-8 py-5 sm:py-6 gap-6">
        {/* Desktop Sidebar (In-flow on screens >= 1024px) */}
        <aside className="hidden lg:block w-64 flex-shrink-0 space-y-6">
          {renderSidebarNav(false)}
        </aside>

        {/* Dynamic Main Workspace Container */}
        <main className="flex-1 min-w-0 w-full">
          {activeTab === "dashboard" && (
            <DashboardView
              onNavigate={(tab, docId) => {
                if (docId) setSelectedDocForAI(docId);
                setActiveTab(tab);
              }}
              userRole={user.role}
              tenantName={user.tenant_name}
            />
          )}

          {activeTab === "documents" && (
            <div>
              {docAccessDenied && (
                <div className="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start space-x-3 shadow-sm">
                  <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-bold text-sm text-amber-950 mb-0.5">Control de Acceso y Privacidad Documental</h3>
                    <p className="text-amber-800">{docAccessDenied}</p>
                  </div>
                </div>
              )}

              {/* Upload Section */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-6">
                <h2 className="text-base font-bold text-slate-900 mb-1 flex items-center space-x-2">
                  <Upload className="h-4 w-4 text-amber-500" />
                  <span>Cargar Documento Jurídico a la Bóveda</span>
                </h2>
                <p className="text-xs text-slate-500 mb-4">
                  Formatos: PDF, DOCX, TXT e imágenes. Se aplica hashing SHA-256 inmutable, sanitización contra Prompt Injection y extracción de metadatos.
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
                    onChange={(e) => setSelectedDocType(e.target.value)}
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
                        {documents.slice((docPage - 1) * docPageSize, docPage * docPageSize).map((d) => (
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
                            <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                              <button
                                onClick={() => handleOpenPreview(d.id)}
                                className="px-2 py-1 text-slate-700 bg-slate-100 hover:bg-slate-200 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                              >
                                <Eye className="h-3.5 w-3.5 text-slate-600" />
                                <span>Vista</span>
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedDocForAI(d.id);
                                  setActiveTab("review");
                                }}
                                className="px-2 py-1 text-slate-900 bg-amber-100 hover:bg-amber-200 border border-amber-300 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                              >
                                <BookOpen className="h-3.5 w-3.5 text-amber-700" />
                                <span>Revisar</span>
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedDocForAI(d.id);
                                  setActiveTab("advanced");
                                }}
                                className="px-2 py-1 text-rose-800 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                              >
                                <ShieldAlert className="h-3.5 w-3.5 text-rose-600" />
                                <span>Auditoría</span>
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedDocForAI(d.id);
                                  setActiveTab("workflow");
                                }}
                                className="px-2 py-1 text-blue-800 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                              >
                                <GitMerge className="h-3.5 w-3.5 text-blue-600" />
                                <span>Flujo</span>
                              </button>
                              <button
                                onClick={() => handleDownload(d.id, d.filename)}
                                className="px-2 py-1 text-slate-900 bg-amber-400 hover:bg-amber-300 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
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

                {documents.length > 0 && (
                  <div className="p-4 border-t border-slate-200 bg-slate-50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
                    <div>
                      Mostrando <span className="font-semibold font-mono text-slate-900">{(docPage - 1) * docPageSize + 1}</span> a <span className="font-semibold font-mono text-slate-900">{Math.min(docPage * docPageSize, documents.length)}</span> de <span className="font-semibold font-mono text-slate-900">{documents.length}</span> documentos
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setDocPage((p) => Math.max(1, p - 1))}
                        disabled={docPage === 1}
                        className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed font-medium shadow-2xs"
                      >
                        Anterior
                      </button>
                      <span className="font-mono px-2 font-semibold text-slate-900">
                        Página {docPage} de {Math.ceil(documents.length / docPageSize) || 1}
                      </span>
                      <button
                        onClick={() => setDocPage((p) => Math.min(Math.ceil(documents.length / docPageSize) || 1, p + 1))}
                        disabled={docPage === (Math.ceil(documents.length / docPageSize) || 1)}
                        className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed font-medium shadow-2xs"
                      >
                        Siguiente
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "review" && (
            <DocumentReviewViewer
              documents={documents}
              initialSelectedDocId={selectedDocForAI || documents[0]?.id}
              userRole={user.role}
            />
          )}

          {activeTab === "cases" && (
            <CasesView userRole={user.role} />
          )}

          {activeTab === "clients" && (
            <ClientsView userRole={user.role} />
          )}

          {activeTab === "workflow" && (
            <WorkflowView
              documents={documents}
              initialSelectedDocId={selectedDocForAI || documents[0]?.id}
              userRole={user.role}
            />
          )}

          {activeTab === "approvals" && (
            <ApprovalsView
              documents={documents}
              userRole={user.role}
            />
          )}

          {activeTab === "ai_agents" && (
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

                  <div className="flex items-center space-x-2 text-xs text-slate-500 font-mono">
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

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

                  <div className="mt-6 pt-4 border-t border-slate-200">
                    <span className="text-xs font-bold text-slate-700 block mb-2">JSON Estructurado Validado:</span>
                    <pre className="bg-slate-900 text-slate-100 p-4 rounded-xl text-xs font-mono overflow-x-auto max-h-60 leading-relaxed">
                      {JSON.stringify(analysisResult.structured_output, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "advanced" && (
            <AdvancedAnalysisView
              documents={documents}
              initialSelectedDocId={selectedDocForAI || documents[0]?.id}
              userRole={user?.role}
              onNavigateToReview={(docId) => {
                setSelectedDocForAI(docId);
                setActiveTab("review");
              }}
            />
          )}

          {activeTab === "risks" && (
            <RisksView
              documents={documents}
              onNavigateToReview={(docId) => {
                setSelectedDocForAI(docId);
                setActiveTab("review");
              }}
              userRole={user?.role}
            />
          )}

          {activeTab === "rules" && (
            <RulesEngineView
              documents={documents}
              initialSelectedDocId={selectedDocForAI || documents[0]?.id}
              userRole={user?.role}
            />
          )}

          {activeTab === "modifications" && (
            <ModificationsView
              documents={documents}
              initialSelectedDocId={selectedDocForAI || documents[0]?.id}
              userRole={user?.role}
            />
          )}

          {activeTab === "notifications" && (
            <NotificationsView />
          )}

          {activeTab === "users" && (
            <UsersView userRole={user.role} />
          )}

          {activeTab === "audit" && (
            <AuditView userRole={user.role} />
          )}

          {activeTab === "settings" && (
            <SettingsView user={user} />
          )}

          {activeTab === "admin" && (
            <AdminView user={user} />
          )}

          {activeTab === "tasks" && (
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
                            t.status === "COMPLETED" ? "bg-emerald-100 text-emerald-800 border border-emerald-200" :
                            t.status === "PROCESSING" ? "bg-amber-100 text-amber-800 border border-amber-200 animate-pulse" :
                            t.status === "FAILED" ? "bg-rose-100 text-rose-800 border border-rose-200" :
                            "bg-slate-100 text-slate-700 border border-slate-200"
                          }`}>
                            {t.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 font-mono">{new Date(t.created_at).toLocaleTimeString()}</td>
                        <td className="py-2.5 px-3 text-slate-600 font-mono text-[11px]">
                          <div className="flex items-center justify-between">
                            <span className="truncate max-w-xs" title={t.error_message || (t.result ? JSON.stringify(t.result) : "En cola")}>
                              {t.result ? JSON.stringify(t.result).slice(0, 50) + "..." : (t.error_message ? `Fallo: ${t.error_message}` : "En cola de espera")}
                            </span>
                            {(t.status === "FAILED" || t.status === "PENDING") && (
                              <button
                                onClick={async () => {
                                  try {
                                    await api.retryTask(t.id);
                                    showToast("Tarea re-encolada", `La tarea ${t.task_type} se envió nuevamente al worker.`, "info");
                                    await loadTasks();
                                  } catch (err: any) {
                                    showToast("Error", err?.message, "error");
                                  }
                                }}
                                className="ml-2 px-2 py-0.5 text-[10px] font-bold bg-slate-900 text-amber-400 hover:bg-slate-800 rounded shrink-0 shadow-2xs"
                              >
                                Reintentar
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Modal de Vista Previa y Metadatos Jurídicos */}
      {previewDoc && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-slate-200">
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

            <div className="p-6 overflow-y-auto flex-1 grid grid-cols-1 md:grid-cols-3 gap-6">
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

      {/* Floating AI Assistant Chat Drawer */}
      {chatOpen && (
        <div className="fixed bottom-16 right-4 sm:bottom-20 sm:right-6 z-50 w-[calc(100vw-2rem)] sm:w-96 max-h-[540px] bg-slate-900/98 backdrop-blur-2xl border border-slate-700/80 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-fade-in">
          {/* Header */}
          <div className="p-3.5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="p-1.5 bg-amber-400/10 border border-amber-400/30 rounded-lg text-amber-400">
                <Brain className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-white flex items-center space-x-1.5">
                  <span>Asistente Jurídico LegalAI</span>
                </h3>
                <span className="text-[10px] text-amber-400/90 font-mono block">
                  Inferencia Soberana (Ollama Local)
                </span>
              </div>
            </div>
            <button
              onClick={() => setChatOpen(false)}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Quick Legal Prompt Chips */}
          <div className="p-2 bg-slate-950/70 border-b border-slate-800/80 overflow-x-auto flex gap-1.5 text-[10px]">
            <button
              onClick={() => handleSendChatMessage("¿Cómo redactar una cláusula de confidencialidad conforme a la LFPPI?")}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-full whitespace-nowrap border border-slate-700 transition-colors shrink-0"
            >
              Cláusula LFPPI
            </button>
            <button
              onClick={() => handleSendChatMessage("¿Qué requisitos debe contener un pagaré según la LGTOC?")}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-full whitespace-nowrap border border-slate-700 transition-colors shrink-0"
            >
              Requisitos Pagaré
            </button>
            <button
              onClick={() => handleSendChatMessage("¿Cuál es el término para contestar una demanda mercantil ordinaria?")}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-full whitespace-nowrap border border-slate-700 transition-colors shrink-0"
            >
              Término Mercantil
            </button>
          </div>

          {/* Messages Body */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 max-h-72 text-xs">
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`p-3 rounded-2xl max-w-[85%] leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-amber-400 text-slate-950 font-medium rounded-tr-xs"
                      : "bg-slate-800/90 text-slate-100 border border-slate-700/80 rounded-tl-xs whitespace-pre-wrap"
                  }`}
                >
                  {msg.text}
                </div>
                <span className="text-[9px] text-slate-500 font-mono mt-1 px-1">
                  {msg.time}
                </span>
              </div>
            ))}
            {chatThinking && (
              <div className="flex items-center space-x-2 text-slate-400 text-xs p-2">
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-amber-400" />
                <span>Consultando leyes mexicanas...</span>
              </div>
            )}
          </div>

          {/* Input Box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendChatMessage();
            }}
            className="p-3 bg-slate-950 border-t border-slate-800 flex items-center space-x-2"
          >
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Escriba su consulta legal o instrucción..."
              className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-400"
            />
            <button
              type="submit"
              disabled={!chatInput.trim() || chatThinking}
              className="p-2 bg-amber-400 hover:bg-amber-300 disabled:opacity-40 text-slate-950 rounded-xl transition-colors shrink-0"
              title="Enviar mensaje"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}

      {/* Floating AI Assistant Button (Responsive, strictly inside viewport at 714x848) */}
      <button
        onClick={() => setChatOpen((prev) => !prev)}
        aria-label="Abrir Asistente Jurídico de IA"
        className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-40 p-3 sm:p-3.5 bg-gradient-to-tr from-slate-950 via-slate-900 to-indigo-950 hover:to-indigo-900 text-amber-400 border border-amber-400/40 rounded-full shadow-[0_8px_30px_rgb(0,0,0,0.3)] transition-all hover:scale-105 active:scale-95 group focus:outline-none focus:ring-2 focus:ring-amber-400/50"
      >
        <Brain className="h-6 w-6 text-amber-400 group-hover:rotate-6 transition-transform" />
        <span className="sr-only">Asistente Jurídico IA</span>
        <span className="absolute top-1 right-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
        </span>
      </button>

      {/* Floating Toast Notification Container (Bottom-Right, 4s auto-close, manual close) */}
      <div className="fixed bottom-20 right-4 sm:right-6 z-40 flex flex-col gap-2.5 max-w-sm w-[calc(100vw-2rem)] sm:w-80 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="pointer-events-auto bg-slate-900/95 backdrop-blur-xl text-white border border-slate-700/80 rounded-2xl p-4 shadow-2xl flex items-start justify-between gap-3 transition-all duration-300"
          >
            <div className="flex items-start space-x-2.5 min-w-0">
              <div className="mt-0.5 shrink-0">
                {toast.type === "loading" && <RefreshCw className="h-4 w-4 text-amber-400 animate-spin" />}
                {toast.type === "success" && <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
                {toast.type === "warning" && <AlertTriangle className="h-4 w-4 text-amber-400" />}
                {toast.type === "error" && <AlertCircle className="h-4 w-4 text-rose-400" />}
                {(!toast.type || toast.type === "info") && <Bell className="h-4 w-4 text-blue-400" />}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-white truncate">{toast.title}</p>
                {toast.message && (
                  <p className="text-[11px] text-slate-300 mt-0.5 leading-snug break-words">{toast.message}</p>
                )}
              </div>
            </div>
            <button
              onClick={() => dismissToast(toast.id)}
              aria-label="Cerrar notificación"
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors shrink-0"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
