"use client";

import React, { useState, useEffect } from "react";
import {
  LegalDocument,
  AdvancedAnalysisSession,
  LegalFinding,
  ClauseDecomposition,
} from "@/types";
import { api } from "@/lib/api";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileSearch,
  Scale,
  RefreshCw,
  BookOpen,
  UserCheck,
  Calendar,
  Clock,
  ChevronRight,
  FileText,
  X,
  ExternalLink,
  ShieldCheck,
  Search,
  Check,
  Layers,
  Award
} from "lucide-react";

interface AdvancedAnalysisViewProps {
  documents: LegalDocument[];
  initialSelectedDocId?: string;
  userRole?: string;
  onNavigateToReview?: (docId: string, findingId?: string) => void;
}

export default function AdvancedAnalysisView({
  documents,
  initialSelectedDocId,
  userRole,
  onNavigateToReview
}: AdvancedAnalysisViewProps) {
  const [sessions, setSessions] = useState<AdvancedAnalysisSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");

  // Selected session for detailed drill-down inspection
  const [inspectSession, setInspectSession] = useState<AdvancedAnalysisSession | null>(null);

  // New analysis execution modal
  const [showNewAuditModal, setShowNewAuditModal] = useState(false);
  const [newAuditDocId, setNewAuditDocId] = useState<string>(
    initialSelectedDocId || (documents[0]?.id || "")
  );
  const [executingAudit, setExecutingAudit] = useState(false);
  const [auditNotice, setAuditNotice] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await api.listAnalysisSessions();
      setSessions(data);
    } catch (err: any) {
      console.error("Error al cargar sesiones de auditoría:", err);
      setErrorMsg(err?.message || "Error al cargar sesiones de auditoría");
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteNewAudit = async () => {
    if (!newAuditDocId) return;
    setExecutingAudit(true);
    setAuditNotice(null);
    try {
      const newSession = await api.runAdvancedAnalysis(newAuditDocId);
      setAuditNotice(`Auditoría ejecutada con éxito. ${newSession.findings_count} hallazgos detectados.`);
      setShowNewAuditModal(false);
      await loadSessions();
      setInspectSession(newSession);
      setTimeout(() => setAuditNotice(null), 4000);
    } catch (err: any) {
      alert(`Error al ejecutar auditoría: ${err?.message || "Fallo en motor de análisis"}`);
    } finally {
      setExecutingAudit(false);
    }
  };

  const getDoc = (docId: string): LegalDocument | undefined => {
    return documents.find((d) => d.id === docId);
  };

  // Executive KPI Calculations
  const totalSessions = sessions.length;
  const uniqueAuditedDocs = new Set(sessions.map((s) => s.document_id)).size;
  const avgRiskScore = totalSessions > 0
    ? sessions.reduce((acc, s) => acc + (s.overall_risk_score || 0), 0) / totalSessions
    : 0;
  const avgComplianceRate = Math.max(0, 100 - avgRiskScore);
  const totalCriticalFindings = sessions.reduce((acc, s) => acc + (s.critical_count || 0), 0);
  const totalHighFindings = sessions.reduce((acc, s) => acc + (s.high_count || 0), 0);

  // Filtered Sessions
  const filteredSessions = sessions.filter((s) => {
    const doc = getDoc(s.document_id);
    const docTitle = doc?.title?.toLowerCase() || "";
    const docType = doc?.doc_type?.toLowerCase() || "";
    const q = searchQuery.toLowerCase();
    const matchesQuery = !q || docTitle.includes(q) || docType.includes(q) || (s.summary && s.summary.toLowerCase().includes(q));
    const matchesSeverity = selectedSeverity === "ALL" || s.overall_severity === selectedSeverity;
    return matchesQuery && matchesSeverity;
  });

  return (
    <div className="space-y-6">
      {/* Executive Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono mb-1">
            <Scale className="h-3.5 w-3.5 text-indigo-600" />
            <span>Auditoría Jurídica Integral & Supervisión Ejecutiva</span>
          </span>
          <h2 className="text-xl font-bold text-slate-900">Reporte Ejecutivo de Auditoría Documental</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Supervisión integral de sesiones ejecutadas, tasas de cumplimiento normativo y control de hallazgos críticos del despacho.
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={() => setShowNewAuditModal(true)}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-xs"
          >
            <FileSearch className="h-4 w-4 text-amber-400" />
            <span>Ejecutar Nueva Auditoría</span>
          </button>
          <button
            onClick={loadSessions}
            disabled={loading}
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors border border-slate-200"
            title="Actualizar sesiones"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-amber-600" : ""}`} />
          </button>
        </div>
      </div>

      {auditNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center space-x-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{auditNotice}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Executive KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
        {/* Total Sessions */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-[11px] font-semibold">Sesiones Ejecutadas</span>
            <Layers className="h-4 w-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalSessions}</div>
          <div className="text-[10px] text-slate-400 mt-1">Análisis completos</div>
        </div>

        {/* Audited Docs */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-[11px] font-semibold">Docs. Auditados</span>
            <FileText className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{uniqueAuditedDocs}</div>
          <div className="text-[10px] text-slate-400 mt-1">De {documents.length} en bóveda</div>
        </div>

        {/* Compliance Rate */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-[11px] font-semibold">Cumplimiento Global</span>
            <Award className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-700">
            {avgComplianceRate.toFixed(1)}%
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Índice de riesgo: {avgRiskScore.toFixed(1)} / 100
          </div>
        </div>

        {/* Critical Risks */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-[11px] font-semibold">Riesgos Críticos</span>
            <ShieldAlert className="h-4 w-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-700">{totalCriticalFindings}</div>
          <div className="text-[10px] text-slate-400 mt-1">Contingencias graves</div>
        </div>

        {/* High Risks */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-[11px] font-semibold">Riesgos Altos</span>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600">{totalHighFindings}</div>
          <div className="text-[10px] text-slate-400 mt-1">Requieren atención</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col sm:flex-row gap-3 justify-between items-center">
        <div className="relative w-full sm:w-96">
          <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por documento o resumen de auditoría..."
            className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <span className="text-xs text-slate-500 font-medium">Severidad:</span>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
          >
            <option value="ALL">Todas las severidades</option>
            <option value="CRITICAL">Crítica</option>
            <option value="HIGH">Alta</option>
            <option value="MEDIUM">Media</option>
            <option value="LOW">Baja</option>
          </select>
        </div>
      </div>

      {/* Sessions Audit Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-1.5">
            <FileSearch className="h-4 w-4 text-slate-700" />
            <span>Historial Consolidado de Sesiones de Auditoría ({filteredSessions.length})</span>
          </h3>
          <span className="text-[11px] text-slate-500">
            Detección automática de cláusulas, omisiones y riesgos conforme a la legislación mexicana.
          </span>
        </div>

        {filteredSessions.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <ShieldCheck className="h-10 w-10 mx-auto mb-2 opacity-40 text-slate-400" />
            <p className="text-sm font-medium">No se encontraron sesiones de auditoría registradas.</p>
            <p className="text-xs text-slate-400 mt-1">Haga clic en &quot;Ejecutar Nueva Auditoría&quot; para auditar un contrato o documento.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                  <th className="py-3 px-4">Documento Auditado</th>
                  <th className="py-3 px-4">Fecha & Duración</th>
                  <th className="py-3 px-4">Severidad Global</th>
                  <th className="py-3 px-4">Índice de Riesgo</th>
                  <th className="py-3 px-4">Hallazgos</th>
                  <th className="py-3 px-4">Validación HITL</th>
                  <th className="py-3 px-4 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredSessions.map((s) => {
                  const doc = getDoc(s.document_id);
                  const isCritical = s.overall_severity === "CRITICAL";
                  const isHigh = s.overall_severity === "HIGH";
                  const isMedium = s.overall_severity === "MEDIUM";
                  const complianceScore = Math.max(0, 100 - (s.overall_risk_score || 0));

                  return (
                    <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-bold text-slate-900 block truncate max-w-xs" title={doc?.title || "Documento"}>
                          {doc?.title || "Documento en Bóveda"}
                        </span>
                        <div className="flex items-center space-x-1.5 mt-0.5">
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                            {doc?.doc_type || "LEGAL"}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            ID: {s.document_id.slice(0, 8)}...
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="text-slate-800 font-mono block">
                          {new Date(s.created_at).toLocaleDateString("es-MX", {
                            day: "2-digit",
                            month: "short",
                            year: "numeric"
                          })}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {s.execution_time_ms ? `${(s.execution_time_ms / 1000).toFixed(1)}s` : "< 1s"} • {new Date(s.created_at).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          isCritical ? "bg-rose-50 text-rose-700 border-rose-200" :
                          isHigh ? "bg-amber-50 text-amber-700 border-amber-200" :
                          isMedium ? "bg-blue-50 text-blue-700 border-blue-200" :
                          "bg-emerald-50 text-emerald-700 border-emerald-200"
                        }`}>
                          {s.overall_severity}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-slate-200 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-2 rounded-full ${
                                s.overall_risk_score > 60 ? "bg-rose-500" :
                                s.overall_risk_score > 30 ? "bg-amber-500" : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.min(100, s.overall_risk_score)}%` }}
                            />
                          </div>
                          <span className="font-mono font-bold text-slate-800 text-[11px]">
                            {s.overall_risk_score.toFixed(0)}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono block mt-0.5">
                          Cumplimiento: {complianceScore.toFixed(0)}%
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-1 font-mono text-[11px]">
                          {s.critical_count > 0 && (
                            <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 font-bold" title="Críticos">
                              {s.critical_count}C
                            </span>
                          )}
                          {s.high_count > 0 && (
                            <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-bold" title="Altos">
                              {s.high_count}A
                            </span>
                          )}
                          <span className="text-slate-500 text-[10px]">
                            ({s.findings_count} total)
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        {s.pending_review_count === 0 ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center space-x-1 w-max">
                            <UserCheck className="h-3 w-3 text-emerald-600" />
                            <span>Validado 100%</span>
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 flex items-center space-x-1 w-max">
                            <Clock className="h-3 w-3 text-amber-600" />
                            <span>{s.pending_review_count} Pendientes</span>
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                        <button
                          onClick={() => setInspectSession(s)}
                          className="px-2.5 py-1 text-slate-900 bg-amber-50 hover:bg-amber-100 border border-amber-300 rounded-lg font-semibold text-[11px] inline-flex items-center space-x-1 shadow-2xs"
                        >
                          <FileSearch className="h-3.5 w-3.5 text-amber-700" />
                          <span>Examinar</span>
                        </button>
                        {onNavigateToReview && (
                          <button
                            onClick={() => onNavigateToReview(s.document_id)}
                            className="px-2.5 py-1 text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg font-semibold text-[11px] inline-flex items-center space-x-1 shadow-2xs"
                          >
                            <BookOpen className="h-3.5 w-3.5 text-slate-600" />
                            <span>Visor</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Drill-Down Audit Inspection Drawer / Modal */}
      {inspectSession && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="bg-amber-400 text-slate-900 p-1.5 rounded-lg font-bold shrink-0">
                  <Scale className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-white truncate">
                    Auditoría Ejecutiva: {getDoc(inspectSession.document_id)?.title || "Documento Jurídico"}
                  </h3>
                  <div className="flex items-center space-x-2 text-[10px] text-slate-300 mt-0.5 font-mono">
                    <span>Severidad: {inspectSession.overall_severity}</span>
                    <span>•</span>
                    <span>Riesgo: {inspectSession.overall_risk_score.toFixed(0)} / 100</span>
                    <span>•</span>
                    <span>{new Date(inspectSession.created_at).toLocaleString("es-MX")}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setInspectSession(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors shrink-0"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              {/* Executive Summary */}
              {inspectSession.summary && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1 flex items-center space-x-1.5">
                    <FileText className="h-3.5 w-3.5 text-indigo-600" />
                    <span>Dictamen y Resumen Ejecutivo de Auditoría</span>
                  </h4>
                  <p className="text-xs text-slate-700 leading-relaxed font-sans">
                    {inspectSession.summary}
                  </p>
                </div>
              )}

              {/* Findings Section */}
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center justify-between">
                  <span className="flex items-center space-x-1.5">
                    <ShieldAlert className="h-4 w-4 text-rose-600" />
                    <span>Hallazgos Jurídicos & Fundamento Normativo ({inspectSession.findings?.length || 0})</span>
                  </span>
                  {onNavigateToReview && (
                    <button
                      onClick={() => {
                        const docId = inspectSession.document_id;
                        setInspectSession(null);
                        onNavigateToReview(docId);
                      }}
                      className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 inline-flex items-center space-x-1"
                    >
                      <span>Abrir en Visor de Revisión Táctico</span>
                      <ExternalLink className="h-3 w-3" />
                    </button>
                  )}
                </h4>

                {(!inspectSession.findings || inspectSession.findings.length === 0) ? (
                  <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs">
                    No se detectaron riesgos ni violaciones normativas en esta sesión. Documento cumple con los estándares revisados.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {inspectSession.findings.map((f) => (
                      <div
                        key={f.id}
                        className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-colors space-y-2 shadow-2xs"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              f.severity === "CRITICAL" ? "bg-rose-100 text-rose-800" :
                              f.severity === "HIGH" ? "bg-amber-100 text-amber-800" :
                              "bg-blue-100 text-blue-800"
                            }`}>
                              {f.severity}
                            </span>
                            <span className="font-mono text-xs font-bold text-slate-900">{f.finding_code}</span>
                            <span className="text-xs font-semibold text-slate-800">{f.title}</span>
                          </div>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                            {f.issue_type}
                          </span>
                        </div>

                        <p className="text-xs text-slate-600 leading-relaxed">
                          {f.risk_explanation}
                        </p>

                        {f.legal_foundation && (
                          <div className="p-2 rounded-lg bg-amber-50/70 border border-amber-200/60 text-[11px] text-amber-900 flex items-start space-x-1.5">
                            <Scale className="h-3.5 w-3.5 text-amber-700 shrink-0 mt-0.5" />
                            <div>
                              <strong className="font-semibold">Fundamento Legal:</strong>{" "}
                              {typeof f.legal_foundation === "object"
                                ? `${f.legal_foundation.disposition_name || ""}${f.legal_foundation.article ? ` - ${f.legal_foundation.article}` : ""}${f.legal_foundation.jurisdiction ? ` (${f.legal_foundation.jurisdiction})` : ""}`
                                : String(f.legal_foundation)}
                            </div>
                          </div>
                        )}

                        {f.recommendation && (
                          <div className="p-2 rounded-lg bg-emerald-50/70 border border-emerald-200/60 text-[11px] text-emerald-900">
                            <strong className="font-semibold block mb-0.5">Recomendación Técnica:</strong>
                            <p className="text-[11px] text-emerald-800 leading-relaxed">{f.recommendation}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
              <span className="text-xs text-slate-500 font-mono">
                Sesión: {inspectSession.id.slice(0, 12)}...
              </span>
              <button
                onClick={() => setInspectSession(null)}
                className="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-semibold hover:bg-slate-800 transition-colors"
              >
                Cerrar Reporte
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Nueva Auditoría */}
      {showNewAuditModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <FileSearch className="h-5 w-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">Ejecutar Nueva Auditoría Jurídica</h3>
              </div>
              <button
                onClick={() => setShowNewAuditModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Seleccione el documento de la bóveda para iniciar la descomposición de cláusulas, cálculo de riesgo y auditoría contra leyes mexicanas.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Documento a Auditar
              </label>
              <select
                value={newAuditDocId}
                onChange={(e) => setNewAuditDocId(e.target.value)}
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
              >
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.title} ({d.doc_type})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowNewAuditModal(false)}
                className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={executingAudit || !newAuditDocId}
                onClick={handleExecuteNewAudit}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 disabled:opacity-50"
              >
                {executingAudit && <RefreshCw className="h-3.5 w-3.5 animate-spin text-amber-400" />}
                <span>{executingAudit ? "Analizando Cláusulas..." : "Iniciar Auditoría"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
