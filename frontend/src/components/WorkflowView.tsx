"use client";

import React, { useState, useEffect } from "react";
import {
  LegalDocument,
  DocumentWorkflow,
  WorkflowState,
  AllowedTransitionOption,
  WorkflowComment,
  CorrectionRequest,
  WorkflowApprovalRecord,
  WorkflowTransition
} from "@/types";
import { api } from "@/lib/api";
import {
  GitMerge,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  UserCheck,
  UserPlus,
  MessageSquare,
  FileEdit,
  ShieldAlert,
  Scale,
  RefreshCw,
  Send,
  Calendar,
  Lock,
  Archive,
  ArrowRight,
  Info,
  Check,
  Building,
  Briefcase,
  AlertCircle
} from "lucide-react";

interface WorkflowViewProps {
  documents: LegalDocument[];
  initialSelectedDocId?: string;
  userRole?: string;
}

const STATE_CONFIG: Record<
  WorkflowState,
  { label: string; bg: string; text: string; border: string; stepIndex: number }
> = {
  RECEIVED: { label: "Recibido", bg: "bg-slate-100", text: "text-slate-800", border: "border-slate-300", stepIndex: 0 },
  PENDING_PROCESSING: { label: "Pend. Procesamiento", bg: "bg-slate-100", text: "text-slate-800", border: "border-slate-300", stepIndex: 1 },
  PROCESSING: { label: "En Procesamiento", bg: "bg-blue-50", text: "text-blue-800", border: "border-blue-300", stepIndex: 2 },
  ANALYSIS_COMPLETED: { label: "Análisis Completado", bg: "bg-indigo-50", text: "text-indigo-800", border: "border-indigo-300", stepIndex: 3 },
  WITH_OBSERVATIONS: { label: "Con Observaciones", bg: "bg-amber-50", text: "text-amber-800", border: "border-amber-300", stepIndex: 4 },
  PENDING_REVIEW: { label: "Pend. Revisión", bg: "bg-amber-50", text: "text-amber-800", border: "border-amber-300", stepIndex: 5 },
  IN_CORRECTION: { label: "En Corrección", bg: "bg-rose-50", text: "text-rose-800", border: "border-rose-300", stepIndex: 6 },
  PENDING_APPROVAL: { label: "Pend. Aprobación", bg: "bg-purple-50", text: "text-purple-800", border: "border-purple-300", stepIndex: 7 },
  APPROVED: { label: "Aprobado", bg: "bg-emerald-50", text: "text-emerald-800", border: "border-emerald-300", stepIndex: 8 },
  REJECTED: { label: "Rechazado", bg: "bg-red-100", text: "text-red-800", border: "border-red-300", stepIndex: 9 },
  ARCHIVED: { label: "Archivado", bg: "bg-gray-100", text: "text-gray-800", border: "border-gray-300", stepIndex: 10 },
};

const ORDERED_STEPS: WorkflowState[] = [
  "RECEIVED",
  "PROCESSING",
  "ANALYSIS_COMPLETED",
  "PENDING_REVIEW",
  "IN_CORRECTION",
  "PENDING_APPROVAL",
  "APPROVED"
];

export default function WorkflowView({
  documents,
  initialSelectedDocId,
  userRole
}: WorkflowViewProps) {
  const [selectedDocId, setSelectedDocId] = useState<string>(
    initialSelectedDocId || (documents[0]?.id || "")
  );

  const [workflow, setWorkflow] = useState<DocumentWorkflow | null>(null);
  const [allowedTransitions, setAllowedTransitions] = useState<AllowedTransitionOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"approvals" | "corrections" | "comments" | "transitions">("approvals");

  // Feedback states
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Transition modal
  const [transitionTarget, setTransitionTarget] = useState<AllowedTransitionOption | null>(null);
  const [transitionReason, setTransitionReason] = useState("");
  const [executingTransition, setExecutingTransition] = useState(false);

  // Approval modal
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [approvalScope, setApprovalScope] = useState("DEFINITIVE_APPROVAL");
  const [reviewerLicense, setReviewerLicense] = useState("");
  const [approvalNotes, setApprovalNotes] = useState("");
  const [submittingApproval, setSubmittingApproval] = useState(false);

  // Correction request modal
  const [showCorrectionModal, setShowCorrectionModal] = useState(false);
  const [correctionTitle, setCorrectionTitle] = useState("");
  const [correctionDesc, setCorrectionDesc] = useState("");
  const [correctionClause, setCorrectionClause] = useState("");
  const [submittingCorrection, setSubmittingCorrection] = useState(false);

  // Resolve correction modal
  const [resolvingCorrectionId, setResolvingCorrectionId] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [submittingResolution, setSubmittingResolution] = useState(false);

  // Comments
  const [newComment, setNewComment] = useState("");
  const [commentClause, setCommentClause] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);

  // Team assignment modal
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignDeadline, setAssignDeadline] = useState("");
  const [assignPriority, setAssignPriority] = useState<"LOW" | "MEDIUM" | "HIGH" | "URGENT">("MEDIUM");
  const [assignAllowAssistant, setAssignAllowAssistant] = useState(false);
  const [savingAssignment, setSavingAssignment] = useState(false);

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  useEffect(() => {
    if (!selectedDocId) return;
    loadWorkflow(selectedDocId);
  }, [selectedDocId]);

  const loadWorkflow = async (docId: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await api.getDocumentWorkflow(docId);
      setWorkflow(data);
      const trans = await api.getAllowedTransitions(data.id);
      setAllowedTransitions(trans);
      if (data.deadline_at) {
        setAssignDeadline(data.deadline_at.split("T")[0]);
      }
      setAssignPriority(data.priority);
      setAssignAllowAssistant(data.allow_assistant_approval);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al cargar el flujo del documento");
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteTransition = async () => {
    if (!workflow || !transitionTarget) return;
    setExecutingTransition(true);
    setErrorMsg(null);
    try {
      await api.executeWorkflowTransition(
        workflow.id,
        transitionTarget.target_state,
        transitionReason || undefined
      );
      setSuccessMsg(`Estado cambiado exitosamente a: ${STATE_CONFIG[transitionTarget.target_state]?.label || transitionTarget.target_state}`);
      setTransitionTarget(null);
      setTransitionReason("");
      await loadWorkflow(selectedDocId);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al ejecutar la transición");
    } finally {
      setExecutingTransition(false);
    }
  };

  const handleSubmitApproval = async () => {
    if (!workflow) return;
    setSubmittingApproval(true);
    setErrorMsg(null);
    try {
      const approval = await api.submitWorkflowApproval(
        workflow.id,
        approvalScope,
        reviewerLicense || undefined,
        approvalNotes || undefined
      );
      setSuccessMsg(`Aprobación formal registrada (${approval.scope}) por ${approval.user_name}.`);
      setShowApprovalModal(false);
      setReviewerLicense("");
      setApprovalNotes("");
      await loadWorkflow(selectedDocId);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al emitir la aprobación jurídica");
    } finally {
      setSubmittingApproval(false);
    }
  };

  const handleCreateCorrection = async () => {
    if (!workflow) return;
    if (!correctionTitle.trim() || !correctionDesc.trim()) {
      setErrorMsg("Debe ingresar título y descripción de la corrección.");
      return;
    }
    setSubmittingCorrection(true);
    setErrorMsg(null);
    try {
      await api.requestWorkflowCorrection(
        workflow.id,
        correctionTitle.trim(),
        correctionDesc.trim(),
        correctionClause.trim() || undefined
      );
      setSuccessMsg("Solicitud de corrección registrada y notificada al equipo.");
      setShowCorrectionModal(false);
      setCorrectionTitle("");
      setCorrectionDesc("");
      setCorrectionClause("");
      await loadWorkflow(selectedDocId);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al solicitar corrección");
    } finally {
      setSubmittingCorrection(false);
    }
  };

  const handleResolveCorrection = async (corrId: string) => {
    if (!resolutionNotes.trim()) {
      setErrorMsg("Ingrese notas explicando cómo se resolvió la corrección.");
      return;
    }
    setSubmittingResolution(true);
    setErrorMsg(null);
    try {
      await api.resolveWorkflowCorrection(corrId, resolutionNotes.trim());
      setSuccessMsg("Corrección marcada como solventada.");
      setResolvingCorrectionId(null);
      setResolutionNotes("");
      await loadWorkflow(selectedDocId);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al solventar corrección");
    } finally {
      setSubmittingResolution(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workflow || !newComment.trim()) return;
    setSubmittingComment(true);
    setErrorMsg(null);
    try {
      await api.addWorkflowComment(
        workflow.id,
        newComment.trim(),
        commentClause.trim() || undefined,
        true
      );
      setNewComment("");
      setCommentClause("");
      await loadWorkflow(selectedDocId);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al agregar comentario");
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleSaveAssignment = async () => {
    if (!workflow) return;
    setSavingAssignment(true);
    setErrorMsg(null);
    try {
      const deadlineIso = assignDeadline ? new Date(assignDeadline).toISOString() : undefined;
      await api.assignWorkflowTeam(workflow.id, {
        priority: assignPriority,
        deadline_at: deadlineIso,
        allow_assistant_approval: assignAllowAssistant,
      });
      setSuccessMsg("Gobernanza, fecha límite y políticas actualizadas.");
      setShowAssignModal(false);
      await loadWorkflow(selectedDocId);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al actualizar asignación");
    } finally {
      setSavingAssignment(false);
    }
  };

  const currentStateInfo = workflow ? STATE_CONFIG[workflow.current_state] : null;

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-800 border border-blue-200">
                <GitMerge className="h-3.5 w-3.5 text-blue-600" />
                <span>Automatización de Flujos de Trabajo Jurídicos</span>
              </span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <Scale className="h-3 w-3" />
                <span>Gobernanza & Aprobación HITL</span>
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 mt-1">
              Ciclo de Vida del Expediente Documental
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Gestión del recorrido de cada documento desde su recepción hasta su aprobación definitiva por el abogado facultado.
            </p>
          </div>

          {/* Quick Actions Header */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAssignModal(true)}
              disabled={loading || !workflow}
              className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold rounded-lg text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 transition-colors"
            >
              <UserPlus className="h-3.5 w-3.5 text-slate-700" />
              <span>Gobernanza & Plazos</span>
            </button>

            <button
              onClick={() => setShowCorrectionModal(true)}
              disabled={loading || !workflow}
              className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold rounded-lg text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors"
            >
              <FileEdit className="h-3.5 w-3.5" />
              <span>Solicitar Corrección</span>
            </button>

            <button
              onClick={() => setShowApprovalModal(true)}
              disabled={loading || !workflow}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg text-white bg-emerald-700 hover:bg-emerald-800 shadow-sm transition-colors"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Emitir Aprobación</span>
            </button>
          </div>
        </div>

        {/* Alerts */}
        {errorMsg && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2">
            <AlertTriangle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Error en Workflow:</span> {errorMsg}
            </div>
          </div>
        )}

        {successMsg && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-start space-x-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Operación exitosa:</span> {successMsg}
            </div>
          </div>
        )}

        {/* Document Selector */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Documento del Expediente
            </label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title} ({d.doc_type}) — Versión {d.versions?.length || 1}
                </option>
              ))}
            </select>
          </div>

          {/* Current State & SLA Badge */}
          {workflow && (
            <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Estado Actual</span>
                <span className={`inline-block font-bold text-xs px-2.5 py-0.5 rounded-full border mt-0.5 ${currentStateInfo?.bg} ${currentStateInfo?.text} ${currentStateInfo?.border}`}>
                  {currentStateInfo?.label || workflow.current_state}
                </span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Prioridad</span>
                <span className={`inline-block font-bold text-[11px] px-2 py-0.5 rounded mt-0.5 ${
                  workflow.priority === "URGENT" ? "bg-red-100 text-red-800" :
                  workflow.priority === "HIGH" ? "bg-amber-100 text-amber-800" : "bg-slate-200 text-slate-800"
                }`}>
                  {workflow.priority}
                </span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Fecha Límite Fatal</span>
                {workflow.deadline_at ? (
                  <span className={`inline-flex items-center space-x-1 font-mono text-xs font-semibold mt-0.5 ${
                    workflow.is_overdue ? "text-rose-700 font-bold" : "text-slate-700"
                  }`}>
                    {workflow.is_overdue && <AlertTriangle className="h-3.5 w-3.5 text-rose-600" />}
                    <span>{new Date(workflow.deadline_at).toLocaleDateString("es-MX")}</span>
                    {workflow.is_overdue && <span className="text-[10px] bg-rose-100 px-1 rounded text-rose-800">Vencido</span>}
                  </span>
                ) : (
                  <span className="text-xs text-slate-400 mt-0.5 block">Sin fecha fijada</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Stepper Progression Visualizer */}
        {workflow && (
          <div className="mt-6 pt-4 border-t border-slate-100">
            <span className="text-xs font-semibold text-slate-700 block mb-2">Progreso del Flujo Jurídico:</span>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-1.5">
              {ORDERED_STEPS.map((step, idx) => {
                const stepConf = STATE_CONFIG[step];
                const isCurrent = workflow.current_state === step;
                const isPassed = (STATE_CONFIG[workflow.current_state]?.stepIndex || 0) > idx;

                return (
                  <div
                    key={step}
                    className={`p-2 rounded-lg border text-center transition-all ${
                      isCurrent
                        ? "border-slate-900 bg-slate-900 text-white shadow-sm"
                        : isPassed
                        ? "border-emerald-200 bg-emerald-50/50 text-emerald-800"
                        : "border-slate-200 bg-slate-50 text-slate-400"
                    }`}
                  >
                    <div className="text-[10px] font-mono font-bold">Paso {idx + 1}</div>
                    <div className="text-[11px] font-semibold truncate mt-0.5">{stepConf.label}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Dynamic Allowed Transitions Engine Bar */}
        {workflow && (
          <div className="mt-4 p-3 bg-blue-50/50 border border-blue-200 rounded-lg flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center space-x-2 text-xs text-blue-900 font-semibold">
              <ArrowRight className="h-4 w-4 text-blue-600" />
              <span>Transiciones de Estado Disponibles:</span>
            </div>

            <div className="flex flex-wrap items-center gap-1.5">
              {allowedTransitions.map((t) => (
                <button
                  key={t.target_state}
                  onClick={() => setTransitionTarget(t)}
                  disabled={!t.can_execute}
                  title={t.block_reason || "Ejecutar transición"}
                  className={`px-3 py-1 text-xs font-semibold rounded-md border transition-colors flex items-center space-x-1 ${
                    t.can_execute
                      ? "bg-white hover:bg-slate-100 text-slate-800 border-slate-300 shadow-xs"
                      : "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
                  }`}
                >
                  <span>Mover a: {STATE_CONFIG[t.target_state]?.label || t.target_state}</span>
                  {!t.can_execute && <Lock className="h-3 w-3 text-slate-400" />}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Tabs Container */}
      {workflow && (
        <div className="space-y-4">
          {/* Inner Navigation Tabs */}
          <div className="flex border-b border-slate-200 bg-white px-4 pt-3 rounded-t-xl shadow-xs space-x-6 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("approvals")}
              className={`pb-3 flex items-center space-x-1.5 border-b-2 transition-all ${
                activeTab === "approvals"
                  ? "border-emerald-600 text-emerald-800"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Aprobaciones & Validez Jurídica</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-100 text-slate-700">
                {workflow.approvals.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab("corrections")}
              className={`pb-3 flex items-center space-x-1.5 border-b-2 transition-all ${
                activeTab === "corrections"
                  ? "border-rose-600 text-rose-800"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <FileEdit className="h-4 w-4 text-rose-600" />
              <span>Solicitudes de Corrección</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-rose-50 text-rose-700 font-bold border border-rose-200">
                {workflow.corrections.filter((c) => c.status === "OPEN").length} abiertas
              </span>
            </button>

            <button
              onClick={() => setActiveTab("comments")}
              className={`pb-3 flex items-center space-x-1.5 border-b-2 transition-all ${
                activeTab === "comments"
                  ? "border-blue-600 text-blue-800"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <MessageSquare className="h-4 w-4 text-blue-600" />
              <span>Comentarios Internos</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-100 text-slate-700">
                {workflow.comments.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab("transitions")}
              className={`pb-3 flex items-center space-x-1.5 border-b-2 transition-all ${
                activeTab === "transitions"
                  ? "border-slate-900 text-slate-900"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Clock className="h-4 w-4 text-slate-600" />
              <span>Historial de Transiciones</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-100 text-slate-700">
                {workflow.transitions.length}
              </span>
            </button>
          </div>

          {/* TAB 1: Aprobaciones y Validez Jurídica */}
          {activeTab === "approvals" && (
            <div className="bg-white rounded-b-xl border border-t-0 border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Registro Formal de Aprobaciones Jurídicas</h3>
                  <p className="text-xs text-slate-500">
                    Regla de oro: Cualquier modificación posterior invalida automáticamente aprobaciones previas si afectan el contenido.
                  </p>
                </div>
                <button
                  onClick={() => setShowApprovalModal(true)}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg text-white bg-emerald-700 hover:bg-emerald-800 shadow-sm"
                >
                  <Scale className="h-3.5 w-3.5" />
                  <span>Emitir Aprobación (HITL)</span>
                </button>
              </div>

              {workflow.approvals.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400">
                  <Scale className="h-8 w-8 mx-auto mb-2 opacity-40 text-slate-400" />
                  <p className="font-medium">No se han emitido aprobaciones jurídicas para este documento.</p>
                  <p className="text-[11px] mt-0.5">El abogado responsable debe evaluar el contenido y aprobar con cédula profesional.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {workflow.approvals.map((app) => (
                    <div
                      key={app.id}
                      className={`p-4 rounded-xl border transition-all ${
                        app.status === "VALID"
                          ? "border-emerald-200 bg-emerald-50/20"
                          : "border-rose-200 bg-rose-50/30"
                      }`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-100">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`text-[11px] font-bold px-2 py-0.5 rounded border ${
                              app.status === "VALID"
                                ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                                : "bg-rose-100 text-rose-800 border-rose-300"
                            }`}
                          >
                            {app.status === "VALID" ? "✓ APROBACIÓN VIGENTE" : "✕ INVALIDADA POR CAMBIO DE CONTENIDO"}
                          </span>
                          <span className="text-xs font-bold text-slate-800">
                            Versión {app.version_number} — {app.scope}
                          </span>
                        </div>

                        <div className="text-xs text-slate-500 font-mono">
                          {new Date(app.approved_at).toLocaleString("es-MX")}
                        </div>
                      </div>

                      <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-semibold block">Abogado Autorizador</span>
                          <span className="font-bold text-slate-900">{app.user_name}</span>
                          <span className="text-[11px] text-slate-500 block font-mono">
                            {app.user_role} {app.reviewer_license && `• Cédula: ${app.reviewer_license}`}
                          </span>
                        </div>

                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-semibold block">Hash SHA-256 Aprobado</span>
                          <span className="font-mono text-[11px] text-slate-700 truncate block" title={app.document_hash}>
                            {app.document_hash.slice(0, 16)}...
                          </span>
                        </div>

                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-semibold block">Dictamen / Notas</span>
                          <span className="text-slate-700 italic">
                            {app.approval_notes ? `"${app.approval_notes}"` : "Sin notas adicionales."}
                          </span>
                        </div>
                      </div>

                      {app.status !== "VALID" && (
                        <div className="mt-3 p-2 bg-rose-100/70 border border-rose-200 rounded text-xs text-rose-900">
                          <strong>Causa de Invalidación:</strong> {app.invalidation_reason || "Se generó una versión posterior que afectó el texto aprobado."}
                          {app.invalidated_by_version && ` (Superada por Versión ${app.invalidated_by_version})`}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Solicitudes de Corrección */}
          {activeTab === "corrections" && (
            <div className="bg-white rounded-b-xl border border-t-0 border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Correcciones y Ajustes Solicitados</h3>
                  <p className="text-xs text-slate-500">
                    Al solicitar una corrección, el expediente pasa automáticamente a &apos;En corrección&apos; hasta que se solvente.
                  </p>
                </div>
                <button
                  onClick={() => setShowCorrectionModal(true)}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg text-white bg-rose-700 hover:bg-rose-800 shadow-sm"
                >
                  <FileEdit className="h-3.5 w-3.5" />
                  <span>Nueva Solicitud de Corrección</span>
                </button>
              </div>

              {workflow.corrections.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400">
                  <CheckCircle2 className="h-8 w-8 mx-auto mb-2 opacity-40 text-emerald-500" />
                  <p className="font-medium">No hay solicitudes de corrección activas.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {workflow.corrections.map((corr) => (
                    <div
                      key={corr.id}
                      className={`p-4 rounded-xl border ${
                        corr.status === "OPEN" ? "border-amber-200 bg-amber-50/20" : "border-slate-200 bg-slate-50/40"
                      }`}
                    >
                      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                              corr.status === "OPEN" ? "bg-amber-100 text-amber-800 border border-amber-300" : "bg-emerald-100 text-emerald-800"
                            }`}
                          >
                            {corr.status === "OPEN" ? "ABIERTA" : "SOLVENTADA"}
                          </span>
                          <h4 className="text-xs font-bold text-slate-900">{corr.title}</h4>
                          {corr.target_clause && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-200 text-slate-800 font-mono">
                              {corr.target_clause}
                            </span>
                          )}
                        </div>

                        <div className="text-[11px] text-slate-400">
                          {new Date(corr.created_at).toLocaleString("es-MX")}
                        </div>
                      </div>

                      <p className="text-xs text-slate-700 mt-2 leading-relaxed">{corr.description}</p>

                      {corr.status === "RESOLVED" && corr.resolution_notes && (
                        <div className="mt-2 p-2 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-900">
                          <strong>Solución Aplicada:</strong> {corr.resolution_notes}
                        </div>
                      )}

                      {corr.status === "OPEN" && (
                        <div className="mt-3 flex items-center justify-end">
                          {resolvingCorrectionId === corr.id ? (
                            <div className="w-full space-y-2 p-3 bg-white border border-slate-300 rounded-lg">
                              <label className="block text-xs font-semibold text-slate-700">Notas de Solución:</label>
                              <input
                                type="text"
                                value={resolutionNotes}
                                onChange={(e) => setResolutionNotes(e.target.value)}
                                placeholder="Ej: Se reformuló la cláusula reduciendo el plazo a 15 días..."
                                className="w-full text-xs p-2 border border-slate-300 rounded focus:ring-1 focus:ring-emerald-600"
                              />
                              <div className="flex justify-end space-x-2">
                                <button
                                  onClick={() => setResolvingCorrectionId(null)}
                                  className="px-2 py-1 text-xs text-slate-600 border border-slate-300 rounded"
                                >
                                  Cancelar
                                </button>
                                <button
                                  onClick={() => handleResolveCorrection(corr.id)}
                                  disabled={submittingResolution}
                                  className="px-3 py-1 text-xs font-semibold text-white bg-emerald-700 hover:bg-emerald-800 rounded"
                                >
                                  {submittingResolution ? "Guardando..." : "Confirmar Solución"}
                                </button>
                              </div>
                            </div>
                          ) : (
                            <button
                              onClick={() => {
                                setResolvingCorrectionId(corr.id);
                                setResolutionNotes("");
                              }}
                              className="px-3 py-1 text-xs font-semibold rounded text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300"
                            >
                              Marcar como Solventada
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Comentarios Internos */}
          {activeTab === "comments" && (
            <div className="bg-white rounded-b-xl border border-t-0 border-slate-200 p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
                Notas y Comunicación Interna del Equipo Jurídico
              </h3>

              {/* Comments Thread */}
              <div className="space-y-3 max-h-80 overflow-y-auto p-1">
                {workflow.comments.length === 0 ? (
                  <p className="text-center py-6 text-xs text-slate-400">No hay comentarios en este expediente.</p>
                ) : (
                  workflow.comments.map((comm) => (
                    <div key={comm.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                      <div className="flex items-center justify-between text-slate-500 text-[10px]">
                        <span className="font-bold text-slate-800">
                          {comm.author_name} ({comm.author_role})
                        </span>
                        <span>{new Date(comm.created_at).toLocaleString("es-MX")}</span>
                      </div>
                      {comm.clause_reference && (
                        <span className="inline-block text-[10px] font-mono font-semibold px-1.5 py-0.2 bg-blue-100 text-blue-800 rounded">
                          {comm.clause_reference}
                        </span>
                      )}
                      <p className="text-slate-800 text-xs leading-relaxed">{comm.comment_text}</p>
                    </div>
                  ))
                )}
              </div>

              {/* New Comment Form */}
              <form onSubmit={handleAddComment} className="pt-3 border-t border-slate-100 space-y-2">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                  <div className="md:col-span-3">
                    <input
                      type="text"
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      placeholder="Escriba una nota o comentario interno para el equipo..."
                      className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                    />
                  </div>
                  <div>
                    <input
                      type="text"
                      value={commentClause}
                      onChange={(e) => setCommentClause(e.target.value)}
                      placeholder="Cláusula (Opcional)"
                      className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono"
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={submittingComment || !newComment.trim()}
                    className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg text-white bg-slate-900 hover:bg-slate-800 disabled:opacity-40"
                  >
                    <Send className="h-3 w-3" />
                    <span>{submittingComment ? "Enviando..." : "Publicar Comentario"}</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* TAB 4: Historial de Transiciones (Auditoría) */}
          {activeTab === "transitions" && (
            <div className="bg-white rounded-b-xl border border-t-0 border-slate-200 p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
                Línea de Tiempo de Transiciones (Auditoría Inmutable)
              </h3>

              <div className="space-y-3">
                {workflow.transitions.map((trans) => (
                  <div key={trans.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs flex items-start space-x-3">
                    <div className="p-2 rounded-full bg-slate-200 text-slate-700 flex-shrink-0 mt-0.5">
                      <Clock className="h-3.5 w-3.5" />
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900">
                          {trans.from_state} <ArrowRight className="inline h-3 w-3 mx-1 text-slate-400" /> {trans.to_state}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {new Date(trans.created_at).toLocaleString("es-MX")}
                        </span>
                      </div>
                      <p className="text-slate-600 text-[11px]">
                        <strong>Motivo:</strong> {trans.reason || "Sin justificación registrada."}
                      </p>
                      <div className="text-[10px] text-slate-400">
                        Tipo de evento: <code>{trans.trigger_type}</code>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modal: Ejecutar Transición de Estado */}
      {transitionTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center space-x-2">
              <ArrowRight className="h-4 w-4 text-blue-600" />
              <span>Confirmar Transición de Estado</span>
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Cambiar estado del documento a: <strong>{STATE_CONFIG[transitionTarget.target_state]?.label || transitionTarget.target_state}</strong>.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Justificación de la Transición {transitionTarget.requires_reason && "* (Obligatorio)"}
                </label>
                <textarea
                  rows={3}
                  value={transitionReason}
                  onChange={(e) => setTransitionReason(e.target.value)}
                  placeholder="Explique las razones jurídicas o procesales del cambio de estado..."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 mt-6">
              <button
                type="button"
                onClick={() => setTransitionTarget(null)}
                className="px-3.5 py-2 text-xs font-semibold text-slate-600 border border-slate-300 rounded-lg"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleExecuteTransition}
                disabled={executingTransition || (transitionTarget.requires_reason && transitionReason.trim().length < 3)}
                className="px-4 py-2 text-xs font-semibold rounded-lg text-white bg-slate-900 hover:bg-slate-800 disabled:opacity-40"
              >
                {executingTransition ? "Ejecutando..." : "Confirmar Cambio"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Emitir Aprobación Formal (HITL) */}
      {showApprovalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Emitir Aprobación Jurídica Formal (HITL)</span>
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              La aprobación definitiva asienta firma jurídica y fecha, promoviendo el expediente al estado &apos;Aprobado&apos;.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Alcance de la Aprobación</label>
                <select
                  value={approvalScope}
                  onChange={(e) => setApprovalScope(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                >
                  <option value="DEFINITIVE_APPROVAL">Aprobación Definitiva (Plenos Efectos)</option>
                  <option value="LEGAL_CONTENT_APPROVAL">Aprobación de Contenido Legal y Cláusulas</option>
                  <option value="PRELIMINARY_APPROVAL">Aprobación Preliminar / Formato</option>
                  <option value="TERMS_AND_CONDITIONS">Aprobación de Condiciones Comerciales</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Cédula Profesional del Abogado Autorizador *
                </label>
                <input
                  type="text"
                  value={reviewerLicense}
                  onChange={(e) => setReviewerLicense(e.target.value)}
                  placeholder="Ej: CED-PROF-12345678"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg font-mono focus:ring-1 focus:ring-emerald-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Dictamen / Observaciones</label>
                <textarea
                  rows={2}
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                  placeholder="Ej: Aprobado conforme a las disposiciones del Código de Comercio..."
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-[11px] text-emerald-900">
                <strong>Garantía de Integridad:</strong> Si con posterioridad se crea una nueva versión que altere el documento, esta aprobación será invalidada de forma automática.
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 mt-6">
              <button
                type="button"
                onClick={() => setShowApprovalModal(false)}
                className="px-3.5 py-2 text-xs font-semibold text-slate-600 border border-slate-300 rounded-lg"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSubmitApproval}
                disabled={submittingApproval || (approvalScope === "DEFINITIVE_APPROVAL" && reviewerLicense.trim().length < 4)}
                className="px-4 py-2 text-xs font-semibold rounded-lg text-white bg-emerald-700 hover:bg-emerald-800 disabled:opacity-40"
              >
                {submittingApproval ? "Aprobando..." : "Confirmar y Aprobar"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Solicitar Corrección */}
      {showCorrectionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center space-x-2">
              <FileEdit className="h-4 w-4 text-rose-600" />
              <span>Solicitar Corrección Jurídica</span>
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              El documento pasará automáticamente a estado &apos;En corrección&apos;.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Título del Ajuste Requerido *</label>
                <input
                  type="text"
                  value={correctionTitle}
                  onChange={(e) => setCorrectionTitle(e.target.value)}
                  placeholder="Ej: Corregir penalidad moratoria diaria"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Cláusula o Sección Afectada</label>
                <input
                  type="text"
                  value={correctionClause}
                  onChange={(e) => setCorrectionClause(e.target.value)}
                  placeholder="Ej: Cláusula Quinta (Penalizaciones)"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Descripción Detallada *</label>
                <textarea
                  rows={3}
                  value={correctionDesc}
                  onChange={(e) => setCorrectionDesc(e.target.value)}
                  placeholder="Indique con precisión qué subsanar..."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 mt-6">
              <button
                type="button"
                onClick={() => setShowCorrectionModal(false)}
                className="px-3.5 py-2 text-xs font-semibold text-slate-600 border border-slate-300 rounded-lg"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleCreateCorrection}
                disabled={submittingCorrection || !correctionTitle.trim() || !correctionDesc.trim()}
                className="px-4 py-2 text-xs font-semibold rounded-lg text-white bg-rose-700 hover:bg-rose-800 disabled:opacity-40"
              >
                {submittingCorrection ? "Solicitando..." : "Ingresar Solicitud"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Gobernanza, Asignaciones y Plazos */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center space-x-2">
              <UserPlus className="h-4 w-4 text-slate-700" />
              <span>Gobernanza, Plazos y Asignaciones</span>
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Configure la fecha límite procesal, nivel de prioridad y políticas de delegación.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Fecha Límite Fatal (SLA)</label>
                <input
                  type="date"
                  value={assignDeadline}
                  onChange={(e) => setAssignDeadline(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Nivel de Prioridad</label>
                <select
                  value={assignPriority}
                  onChange={(e) => setAssignPriority(e.target.value as any)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                >
                  <option value="LOW">Baja</option>
                  <option value="MEDIUM">Media</option>
                  <option value="HIGH">Alta</option>
                  <option value="URGENT">Urgente</option>
                </select>
              </div>

              <div className="pt-2">
                <label className="flex items-center space-x-2 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={assignAllowAssistant}
                    onChange={(e) => setAssignAllowAssistant(e.target.checked)}
                    className="rounded text-slate-900 focus:ring-slate-900"
                  />
                  <span>Permitir aprobación jurídica a asistentes delegados</span>
                </label>
                <p className="text-[10px] text-slate-400 mt-0.5 ml-5">
                  Por defecto, los asistentes no pueden aprobar de manera definitiva sin esta política.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 mt-6">
              <button
                type="button"
                onClick={() => setShowAssignModal(false)}
                className="px-3.5 py-2 text-xs font-semibold text-slate-600 border border-slate-300 rounded-lg"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSaveAssignment}
                disabled={savingAssignment}
                className="px-4 py-2 text-xs font-semibold rounded-lg text-white bg-slate-900 hover:bg-slate-800 disabled:opacity-40"
              >
                {savingAssignment ? "Guardando..." : "Guardar Configuración"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
