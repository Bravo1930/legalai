"use client";

import React, { useState, useEffect } from "react";
import {
  LegalDocument,
  ModificationProposalBatch,
  LegalModificationProposal
} from "@/types";
import { api } from "@/lib/api";
import {
  FileEdit,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileDown,
  Sparkles,
  GitCompare,
  Scale,
  RefreshCw,
  Clock,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Info,
  Lock,
  Edit3,
  FileText,
  Bookmark
} from "lucide-react";

interface ModificationsViewProps {
  documents: LegalDocument[];
  initialSelectedDocId?: string;
  userRole?: string;
}

export default function ModificationsView({
  documents,
  initialSelectedDocId,
  userRole
}: ModificationsViewProps) {
  const [selectedDocId, setSelectedDocId] = useState<string>(
    initialSelectedDocId || (documents[0]?.id || "")
  );

  // Batches state
  const [batches, setBatches] = useState<ModificationProposalBatch[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string>("");
  const [currentBatch, setCurrentBatch] = useState<ModificationProposalBatch | null>(null);
  const [loadingBatches, setLoadingBatches] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<"docx" | "pdf" | null>(null);

  // Feedback states
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filters & UI state
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [editingProposalId, setEditingProposalId] = useState<string | null>(null);
  const [customDraftText, setCustomDraftText] = useState<string>("");
  const [lawyerNotes, setLawyerNotes] = useState<string>("");
  const [reviewerLicense, setReviewerLicense] = useState<string>("");
  const [savingReview, setSavingReview] = useState(false);

  // Generate modal
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [genTitle, setGenTitle] = useState("");
  const [genObjective, setGenObjective] = useState<string>("BALANCED");

  // Compile new version modal
  const [showCompileModal, setShowCompileModal] = useState(false);
  const [compileNotes, setCompileNotes] = useState("");
  const [compileLicense, setCompileLicense] = useState("");
  const [compilingVersion, setCompilingVersion] = useState(false);

  // Selected document info
  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  // Load batches when selectedDocId changes
  useEffect(() => {
    if (!selectedDocId) return;
    loadBatches(selectedDocId);
  }, [selectedDocId]);

  const loadBatches = async (docId: string) => {
    setLoadingBatches(true);
    setErrorMsg(null);
    try {
      const data = await api.listModificationBatches(docId);
      setBatches(data);
      if (data.length > 0) {
        setSelectedBatchId(data[0].id);
        setCurrentBatch(data[0]);
      } else {
        setSelectedBatchId("");
        setCurrentBatch(null);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Error al cargar propuestas de modificación");
    } finally {
      setLoadingBatches(false);
    }
  };

  const handleSelectBatch = async (batchId: string) => {
    setSelectedBatchId(batchId);
    setErrorMsg(null);
    try {
      const batchData = await api.getModificationBatch(batchId);
      setCurrentBatch(batchData);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al consultar lote seleccionado");
    }
  };

  const handleGenerateProposals = async () => {
    if (!selectedDocId) return;
    setGenerating(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    setShowGenerateModal(false);

    try {
      const newBatch = await api.generateModificationProposals(
        selectedDocId,
        genTitle || undefined,
        genObjective
      );
      setSuccessMsg(`Lote de ${newBatch.total_proposals} propuestas generado exitosamente.`);
      await loadBatches(selectedDocId);
      setSelectedBatchId(newBatch.id);
      setCurrentBatch(newBatch);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al generar propuestas con IA");
    } finally {
      setGenerating(false);
    }
  };

  const handleReviewProposal = async (
    proposal: LegalModificationProposal,
    newStatus: "ACCEPTED" | "REJECTED" | "MODIFIED_BY_LAWYER"
  ) => {
    setSavingReview(true);
    setErrorMsg(null);

    const finalText = newStatus === "MODIFIED_BY_LAWYER" ? customDraftText : proposal.proposed_text;

    try {
      const updated = await api.reviewModificationProposal(proposal.id, {
        status: newStatus,
        lawyer_final_text: finalText,
        lawyer_notes: lawyerNotes || undefined,
        reviewer_license: reviewerLicense || undefined,
      });

      // Update currentBatch in memory
      if (currentBatch) {
        const updatedItems = currentBatch.items.map((it) => (it.id === updated.id ? updated : it));
        const accepted = updatedItems.filter((it) => it.status === "ACCEPTED" || it.status === "MODIFIED_BY_LAWYER").length;
        const rejected = updatedItems.filter((it) => it.status === "REJECTED").length;
        const pending = updatedItems.filter((it) => it.status === "PENDING").length;

        setCurrentBatch({
          ...currentBatch,
          items: updatedItems,
          accepted_count: accepted,
          rejected_count: rejected,
          pending_count: pending,
          status: pending === 0 ? "COMPLETED" : "PARTIALLY_ACCEPTED",
        });
      }

      setEditingProposalId(null);
      setSuccessMsg(`Propuesta de "${proposal.clause_title}" marcada como ${newStatus}.`);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al guardar revisión de la propuesta");
    } finally {
      setSavingReview(false);
    }
  };

  const startEditProposal = (proposal: LegalModificationProposal) => {
    setEditingProposalId(proposal.id);
    setCustomDraftText(proposal.lawyer_final_text || proposal.proposed_text);
    setLawyerNotes(proposal.lawyer_notes || "");
    setReviewerLicense(proposal.reviewer_license || "");
  };

  const handleApplyAlternative = (text: string) => {
    setCustomDraftText(text);
  };

  const handleCompileNewVersion = async () => {
    if (!currentBatch) return;
    if (!compileNotes.trim() || compileNotes.trim().length < 5) {
      setErrorMsg("Debe ingresar una justificación legal de al menos 5 caracteres para la nueva versión.");
      return;
    }

    setCompilingVersion(true);
    setErrorMsg(null);
    try {
      const newVersion = await api.applyBatchToNewVersion(
        currentBatch.id,
        compileNotes.trim(),
        compileLicense.trim() || undefined
      );

      setSuccessMsg(
        `¡Versión ${newVersion.version_number} creada exitosamente! SHA-256: ${newVersion.sha256_hash?.slice(0, 16) || ""}...`
      );
      setShowCompileModal(false);
      setCompileNotes("");
      setCompileLicense("");

      // Reload batch to get updated status and applied version number
      await loadBatches(selectedDocId);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al compilar nueva versión oficial");
    } finally {
      setCompilingVersion(false);
    }
  };

  const handleExport = async (format: "docx" | "pdf", versionNumber?: number) => {
    if (!selectedDocId) return;
    setExportingFormat(format);
    setErrorMsg(null);
    try {
      await api.downloadExport(selectedDocId, format, versionNumber);
      setSuccessMsg(`Documento exportado en formato ${format.toUpperCase()} con éxito.`);
    } catch (err: any) {
      setErrorMsg(err.message || `Error al exportar en ${format.toUpperCase()}`);
    } finally {
      setExportingFormat(null);
    }
  };

  const filteredItems = currentBatch?.items.filter((item) => {
    if (statusFilter === "ALL") return true;
    if (statusFilter === "PENDING") return item.status === "PENDING";
    if (statusFilter === "ACCEPTED") return item.status === "ACCEPTED" || item.status === "MODIFIED_BY_LAWYER";
    if (statusFilter === "REJECTED") return item.status === "REJECTED";
    return true;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                <FileEdit className="h-3.5 w-3.5 text-amber-600" />
                <span>Propuestas de Redacción Jurídica • Human-In-The-Loop (HITL)</span>
              </span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <ShieldCheck className="h-3 w-3" />
                <span>Bóveda Original Intacta (WORM)</span>
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 mt-1">
              Revisión, Ajuste de Cláusulas y Compilación de Versiones
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              La IA propone redacciones equilibradas y alternativas conforme a las leyes mexicanas. El abogado titular aprueba, rechaza o ajusta cada cambio antes de generar una nueva versión oficial inmutable.
            </p>
          </div>

          {/* Quick Actions Header */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowGenerateModal(true)}
              disabled={generating || !selectedDocId}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg text-white bg-slate-900 hover:bg-slate-800 shadow-sm disabled:opacity-50 transition-colors"
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-400" />
              <span>{generating ? "Generando..." : "Generar Nuevas Propuestas"}</span>
            </button>

            {/* Export Buttons */}
            <div className="flex items-center space-x-1 border-l border-slate-200 pl-2">
              <button
                onClick={() => handleExport("docx", currentBatch?.applied_version_number)}
                disabled={exportingFormat !== null || !selectedDocId}
                title="Descargar documento en Microsoft Word (.docx)"
                className="inline-flex items-center space-x-1 px-2.5 py-2 text-xs font-medium rounded-lg text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 transition-colors"
              >
                <FileDown className="h-3.5 w-3.5 text-blue-600" />
                <span>{exportingFormat === "docx" ? "Generando DOCX..." : "Word (.docx)"}</span>
              </button>

              <button
                onClick={() => handleExport("pdf", currentBatch?.applied_version_number)}
                disabled={exportingFormat !== null || !selectedDocId}
                title="Descargar documento foliado en PDF con firma y hash SHA-256"
                className="inline-flex items-center space-x-1 px-2.5 py-2 text-xs font-medium rounded-lg text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 transition-colors"
              >
                <FileDown className="h-3.5 w-3.5 text-rose-600" />
                <span>{exportingFormat === "pdf" ? "Generando PDF..." : "PDF Legal"}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Alerts */}
        {errorMsg && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2">
            <AlertTriangle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Error:</span> {errorMsg}
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

        {/* Document Selector & Batch Selector */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Documento Seleccionado
            </label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title} ({d.doc_type}), Versión {d.versions?.length ? d.versions[d.versions.length - 1].version_number : 1}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700">
                Lote de Propuestas de Modificación
              </label>
              {batches.length > 0 && (
                <button
                  onClick={() => loadBatches(selectedDocId)}
                  className="text-[11px] text-slate-500 hover:text-slate-800 flex items-center space-x-1"
                >
                  <RefreshCw className="h-3 w-3" />
                  <span>Actualizar</span>
                </button>
              )}
            </div>
            {batches.length === 0 ? (
              <div className="text-xs text-slate-400 p-2.5 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                <span>No hay lotes de propuesta generados para este documento.</span>
                <button
                  onClick={() => setShowGenerateModal(true)}
                  className="text-amber-600 hover:underline font-semibold text-[11px]"
                >
                  Generar Primer Lote
                </button>
              </div>
            ) : (
              <select
                value={selectedBatchId}
                onChange={(e) => handleSelectBatch(e.target.value)}
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white font-medium"
              >
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.title} ({b.objective}), {b.total_proposals} propuestas [{b.status}]
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Batch Status & Metrics Banner */}
        {currentBatch && (
          <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4 bg-slate-50 p-3 rounded-lg">
            <div className="flex items-center space-x-4 text-xs">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Estado del Lote</span>
                <span
                  className={`inline-block font-bold px-2 py-0.5 rounded text-[11px] ${
                    currentBatch.status === "APPLIED_TO_VERSION"
                      ? "bg-purple-100 text-purple-800 border border-purple-300"
                      : currentBatch.status === "COMPLETED"
                      ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                      : "bg-amber-100 text-amber-800 border border-amber-300"
                  }`}
                >
                  {currentBatch.status === "APPLIED_TO_VERSION"
                    ? `APLICADO EN VERSIÓN ${currentBatch.applied_version_number}`
                    : currentBatch.status === "COMPLETED"
                    ? "REVISIÓN COMPLETA"
                    : "EN REVISIÓN"}
                </span>
              </div>

              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Total Cláusulas</span>
                <span className="font-bold text-slate-800">{currentBatch.total_proposals}</span>
              </div>

              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Aceptadas</span>
                <span className="font-bold text-emerald-700">{currentBatch.accepted_count}</span>
              </div>

              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Rechazadas</span>
                <span className="font-bold text-rose-700">{currentBatch.rejected_count}</span>
              </div>

              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Pendientes</span>
                <span className="font-bold text-amber-700">{currentBatch.pending_count}</span>
              </div>
            </div>

            {/* Compile Version Button */}
            <div className="flex items-center space-x-2">
              {currentBatch.status === "APPLIED_TO_VERSION" ? (
                <div className="text-xs text-purple-700 font-semibold flex items-center space-x-1.5 px-3 py-1.5 bg-purple-50 border border-purple-200 rounded-lg">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Promovido a Versión Oficial {currentBatch.applied_version_number}</span>
                </div>
              ) : (
                <button
                  onClick={() => setShowCompileModal(true)}
                  disabled={currentBatch.accepted_count === 0}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg text-white bg-emerald-700 hover:bg-emerald-800 shadow-sm disabled:opacity-40 transition-colors"
                >
                  <Scale className="h-3.5 w-3.5" />
                  <span>Compilar y Crear Nueva Versión Oficial (HITL)</span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Content: Proposals List */}
      {currentBatch && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex items-center justify-between bg-white px-4 py-3 rounded-lg border border-slate-200 shadow-sm text-xs">
            <div className="flex items-center space-x-2">
              <span className="text-slate-500 font-semibold">Filtrar por decisión:</span>
              <button
                onClick={() => setStatusFilter("ALL")}
                className={`px-2.5 py-1 rounded-md font-medium ${
                  statusFilter === "ALL"
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Todas ({currentBatch.items.length})
              </button>
              <button
                onClick={() => setStatusFilter("PENDING")}
                className={`px-2.5 py-1 rounded-md font-medium ${
                  statusFilter === "PENDING"
                    ? "bg-amber-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Pendientes ({currentBatch.pending_count})
              </button>
              <button
                onClick={() => setStatusFilter("ACCEPTED")}
                className={`px-2.5 py-1 rounded-md font-medium ${
                  statusFilter === "ACCEPTED"
                    ? "bg-emerald-700 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Aceptadas ({currentBatch.accepted_count})
              </button>
              <button
                onClick={() => setStatusFilter("REJECTED")}
                className={`px-2.5 py-1 rounded-md font-medium ${
                  statusFilter === "REJECTED"
                    ? "bg-rose-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Rechazadas ({currentBatch.rejected_count})
              </button>
            </div>

            <div className="text-slate-400 text-[11px]">
              Mostrando {filteredItems.length} de {currentBatch.items.length} cláusulas
            </div>
          </div>

          {/* Proposal Cards */}
          {filteredItems.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-xs">
              No hay propuestas que coincidan con el filtro seleccionado.
            </div>
          ) : (
            filteredItems.map((proposal) => {
              const isEditing = editingProposalId === proposal.id;

              return (
                <div
                  key={proposal.id}
                  className={`bg-white rounded-xl border shadow-sm transition-all overflow-hidden ${
                    proposal.status === "ACCEPTED" || proposal.status === "MODIFIED_BY_LAWYER"
                      ? "border-emerald-200 bg-emerald-50/20"
                      : proposal.status === "REJECTED"
                      ? "border-rose-200 bg-rose-50/20"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  {/* Card Header */}
                  <div className="p-4 bg-slate-50/60 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-200 text-slate-800">
                        {proposal.clause_number ? `Cláusula ${proposal.clause_number}` : "Cláusula"}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">{proposal.clause_title}</h3>
                    </div>

                    <div className="flex items-center space-x-2">
                      {/* Status Badge */}
                      <span
                        className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                          proposal.status === "ACCEPTED"
                            ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                            : proposal.status === "MODIFIED_BY_LAWYER"
                            ? "bg-blue-100 text-blue-800 border-blue-300"
                            : proposal.status === "REJECTED"
                            ? "bg-rose-100 text-rose-800 border-rose-300"
                            : "bg-amber-100 text-amber-800 border-amber-300"
                        }`}
                      >
                        {proposal.status === "ACCEPTED"
                          ? "Aprobada"
                          : proposal.status === "MODIFIED_BY_LAWYER"
                          ? "Ajustada por abogado"
                          : proposal.status === "REJECTED"
                          ? "Rechazada"
                          : "Pendiente de revisión"}
                      </span>

                      {/* Quick Action Buttons */}
                      {proposal.status === "PENDING" && !isEditing && (
                        <div className="flex items-center space-x-1">
                          <button
                            onClick={() => handleReviewProposal(proposal, "ACCEPTED")}
                            disabled={savingReview}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-medium rounded text-white bg-emerald-700 hover:bg-emerald-800 transition-colors"
                          >
                            <CheckCircle2 className="h-3 w-3" />
                            <span>Aceptar</span>
                          </button>
                          <button
                            onClick={() => startEditProposal(proposal)}
                            disabled={savingReview}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-medium rounded text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 transition-colors"
                          >
                            <Edit3 className="h-3 w-3 text-blue-600" />
                            <span>Ajustar</span>
                          </button>
                          <button
                            onClick={() => handleReviewProposal(proposal, "REJECTED")}
                            disabled={savingReview}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-medium rounded text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors"
                          >
                            <XCircle className="h-3 w-3" />
                            <span>Rechazar</span>
                          </button>
                        </div>
                      )}

                      {/* Reopen / Edit when already reviewed */}
                      {proposal.status !== "PENDING" && !isEditing && currentBatch.status !== "APPLIED_TO_VERSION" && (
                        <button
                          onClick={() => startEditProposal(proposal)}
                          className="text-xs text-slate-600 hover:text-slate-900 underline flex items-center space-x-1"
                        >
                          <Edit3 className="h-3 w-3" />
                          <span>Modificar Decisión</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="p-5 space-y-4">
                    {/* Problem Description & Legal Ground */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs bg-slate-50 p-3 rounded-lg border border-slate-100">
                      <div className="md:col-span-2">
                        <span className="font-semibold text-slate-700 block text-[11px] mb-0.5">
                          Diagnóstico Jurídico y Motivo del Cambio:
                        </span>
                        <p className="text-slate-600 leading-relaxed">{proposal.problem_explanation}</p>
                      </div>

                      <div>
                        <span className="font-semibold text-slate-700 block text-[11px] mb-0.5">
                          Fundamento Legal Aplicable:
                        </span>
                        <p className="text-slate-600 font-medium">
                          {proposal.legal_foundation || "Principios Generales de Derecho y Equidad Contractual"}
                        </p>
                      </div>
                    </div>

                    {/* Missing Data Placeholders Badge */}
                    {proposal.missing_data_placeholders && proposal.missing_data_placeholders.length > 0 && (
                      <div className="p-3 rounded-lg bg-amber-50/80 border border-amber-200 text-xs">
                        <div className="flex items-center space-x-1.5 text-amber-900 font-bold mb-1">
                          <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0" />
                          <span>Datos Fácticos Requeridos (Principio de No-Alucinación)</span>
                        </div>
                        <p className="text-amber-800 text-[11px] mb-1.5">
                          La IA no inventó montos ni fechas no pactadas. Antes de formalizar, complete los siguientes campos pendientes:
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {proposal.missing_data_placeholders.map((ph, idx) => (
                            <span
                              key={idx}
                              className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-amber-200 text-amber-900 border border-amber-300"
                            >
                              {ph}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Diff & Side-by-Side Comparison */}
                    {!isEditing ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {/* Original Text */}
                        <div className="border border-rose-200 bg-rose-50/30 rounded-lg p-3">
                          <div className="flex items-center justify-between text-rose-800 text-[11px] font-bold pb-2 border-b border-rose-200 mb-2">
                            <span>Texto Original (Cláusula Previa)</span>
                            <span className="text-[10px] text-rose-600">Inmutable en Bóveda</span>
                          </div>
                          <div className="text-xs font-serif text-slate-700 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                            {proposal.original_text}
                          </div>
                        </div>

                        {/* Proposed Text / Lawyer Final Text */}
                        <div className="border border-emerald-200 bg-emerald-50/30 rounded-lg p-3">
                          <div className="flex items-center justify-between text-emerald-800 text-[11px] font-bold pb-2 border-b border-emerald-200 mb-2">
                            <span>
                              {proposal.status === "MODIFIED_BY_LAWYER"
                                ? "Redacción Ajustada por el Abogado"
                                : "Propuesta de Redacción Sugerida"}
                            </span>
                            <span className="text-[10px] text-emerald-600">Revisión Jurídica</span>
                          </div>
                          <div className="text-xs font-serif text-slate-900 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto font-medium">
                            {proposal.lawyer_final_text || proposal.proposed_text}
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* In-Place Editing Form */
                      <div className="border-2 border-blue-400 bg-blue-50/30 rounded-xl p-4 space-y-4">
                        <div className="flex items-center justify-between border-b border-blue-200 pb-2">
                          <span className="text-xs font-bold text-blue-900 flex items-center space-x-1.5">
                            <Edit3 className="h-4 w-4" />
                            <span>Ajustar Redacción Directamente (HITL)</span>
                          </span>
                          <span className="text-[11px] text-blue-700">
                            Edite el texto de la cláusula o elija una redacción alternativa
                          </span>
                        </div>

                        {/* Alternative Formulation Buttons */}
                        {proposal.alternative_options && proposal.alternative_options.length > 0 && (
                          <div>
                            <span className="block text-[11px] font-semibold text-slate-700 mb-1">
                              Opciones de Formulación Alternativa:
                            </span>
                            <div className="flex flex-wrap gap-2">
                              {proposal.alternative_options.map((alt, idx) => (
                                <button
                                  key={idx}
                                  type="button"
                                  onClick={() => handleApplyAlternative(alt.text)}
                                  className="text-xs font-medium px-2.5 py-1 rounded bg-white hover:bg-blue-100 border border-slate-300 text-slate-800 flex items-center space-x-1 transition-colors"
                                >
                                  <Copy className="h-3 w-3 text-blue-600" />
                                  <span>{alt.label}</span>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Textarea for Lawyer Editing */}
                        <div>
                          <label className="block text-xs font-semibold text-slate-800 mb-1">
                            Texto Definitivo de la Cláusula
                          </label>
                          <textarea
                            rows={6}
                            value={customDraftText}
                            onChange={(e) => setCustomDraftText(e.target.value)}
                            className="w-full text-xs font-serif p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
                            placeholder="Redacte o ajuste la cláusula aquí..."
                          />
                        </div>

                        {/* Lawyer Notes and License */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs font-semibold text-slate-700 mb-1">
                              Comentarios / Notas del Abogado
                            </label>
                            <input
                              type="text"
                              value={lawyerNotes}
                              onChange={(e) => setLawyerNotes(e.target.value)}
                              placeholder="Ej: Se ajustó el plazo conforme al requerimiento del cliente"
                              className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
                            />
                          </div>

                          <div>
                            <label className="block text-xs font-semibold text-slate-700 mb-1">
                              Cédula Profesional del Revisor (Opcional)
                            </label>
                            <input
                              type="text"
                              value={reviewerLicense}
                              onChange={(e) => setReviewerLicense(e.target.value)}
                              placeholder="Ej: CED-PROF-12345678"
                              className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white font-mono"
                            />
                          </div>
                        </div>

                        {/* Editing Action Buttons */}
                        <div className="flex items-center justify-end space-x-2 pt-2 border-t border-blue-200">
                          <button
                            type="button"
                            onClick={() => setEditingProposalId(null)}
                            disabled={savingReview}
                            className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 border border-slate-300 rounded-lg bg-white"
                          >
                            Cancelar
                          </button>
                          <button
                            type="button"
                            onClick={() => handleReviewProposal(proposal, "MODIFIED_BY_LAWYER")}
                            disabled={savingReview || !customDraftText.trim()}
                            className="inline-flex items-center space-x-1.5 px-4 py-1.5 text-xs font-semibold rounded-lg text-white bg-blue-700 hover:bg-blue-800 disabled:opacity-50"
                          >
                            <Check className="h-3.5 w-3.5" />
                            <span>{savingReview ? "Guardando..." : "Guardar Redacción Ajustada"}</span>
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Diff Summary / Observations */}
                    {proposal.diff_summary && (
                      <div className="text-[11px] text-slate-500 flex items-center space-x-2 pt-2 border-t border-slate-100">
                        <GitCompare className="h-3.5 w-3.5 text-slate-400" />
                        <span>
                          <strong>Resumen de Cambios:</strong> {proposal.diff_summary}
                        </span>
                      </div>
                    )}

                    {/* Reviewer signature trail */}
                    {proposal.reviewed_at && (
                      <div className="text-[10px] text-slate-400 flex items-center justify-between pt-1">
                        <span>
                          Revisado: {new Date(proposal.reviewed_at).toLocaleString("es-MX")}
                          {proposal.reviewer_license && ` • Cédula: ${proposal.reviewer_license}`}
                        </span>
                        {proposal.lawyer_notes && (
                          <span className="italic">Nota: &quot;{proposal.lawyer_notes}&quot;</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Modal: Generar Nuevo Lote de Propuestas */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center space-x-2 text-slate-900 font-bold text-lg mb-2">
              <Sparkles className="h-5 w-5 text-amber-500" />
              <h3>Generar Propuestas de Redacción</h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              La IA analizará el documento seleccionado y formulará alternativas de cláusulas conforme a la legislación aplicable, sin inventar hechos.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Título del Lote de Propuestas
                </label>
                <input
                  type="text"
                  value={genTitle}
                  onChange={(e) => setGenTitle(e.target.value)}
                  placeholder="Ej: Revisión Integral y Mitigación de Riesgos"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Enfoque / Objetivo de la Redacción
                </label>
                <select
                  value={genObjective}
                  onChange={(e) => setGenObjective(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                >
                  <option value="BALANCED">Equilibrado (Bilateral y justo para ambas partes)</option>
                  <option value="CLIENT_PROTECTIVE">Protector del Cliente (Máxima seguridad jurídica)</option>
                  <option value="STANDARD">Estándar Mercantil / Notarial</option>
                  <option value="CLARITY">Claridad y Corrección de Sintaxis Jurídica</option>
                </select>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-[11px] text-slate-600 space-y-1">
                <span className="font-semibold block text-slate-800">Garantías del Motor Jurídico:</span>
                <p>• Conservación inmutable del original en almacenamiento WORM.</p>
                <p>• Inclusión de etiquetas <code>[PENDIENTE: ...]</code> para datos no verificados.</p>
                <p>• Ninguna modificación surtirá efectos sin la aprobación expresa del abogado.</p>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 mt-6">
              <button
                type="button"
                onClick={() => setShowGenerateModal(false)}
                className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-lg border border-slate-300"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleGenerateProposals}
                disabled={generating}
                className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg text-white bg-slate-900 hover:bg-slate-800 shadow-sm"
              >
                <Sparkles className="h-3.5 w-3.5 text-amber-400" />
                <span>{generating ? "Generando..." : "Comenzar Generación"}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Compilar Nueva Versión Oficial (HITL) */}
      {showCompileModal && currentBatch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center space-x-2 text-slate-900 font-bold text-lg mb-2">
              <Scale className="h-5 w-5 text-emerald-600" />
              <h3>Compilar y Crear Nueva Versión Oficial</h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Esta acción aplicará únicamente las <strong>{currentBatch.accepted_count} cláusulas aceptadas o modificadas</strong> sobre el texto y generará una nueva versión inmutable con cálculo de hash criptográfico SHA-256.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Resumen y Justificación Legal de la Nueva Versión *
                </label>
                <textarea
                  rows={3}
                  value={compileNotes}
                  onChange={(e) => setCompileNotes(e.target.value)}
                  placeholder="Ej: Se aprobaron cláusulas de penalización conforme al Código Civil y se armonizó la jurisdicción a tribunales de la Ciudad de México..."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Cédula Profesional del Abogado Autorizador
                </label>
                <input
                  type="text"
                  value={compileLicense}
                  onChange={(e) => setCompileLicense(e.target.value)}
                  placeholder="Ej: CED-PROF-12345678"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-600 font-mono"
                />
              </div>

              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-[11px] text-emerald-900">
                <span className="font-bold block mb-1">Registro de Aprobación Legal:</span>
                Se asentará firma digital y folio en la tabla <code>legal_approvals</code> asociada a su usuario ({userRole || "ABOGADO"}).
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 mt-6">
              <button
                type="button"
                onClick={() => setShowCompileModal(false)}
                className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-lg border border-slate-300"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleCompileNewVersion}
                disabled={compilingVersion || compileNotes.trim().length < 5}
                className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg text-white bg-emerald-700 hover:bg-emerald-800 shadow-sm disabled:opacity-40"
              >
                <Check className="h-3.5 w-3.5" />
                <span>{compilingVersion ? "Compilando Versión..." : "Confirmar y Compilar Nueva Versión"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
