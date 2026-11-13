"use client";

import React, { useState, useEffect } from "react";
import {
  LegalDocument,
  AdvancedAnalysisSession,
  LegalFinding,
  ClauseDecomposition,
  VersionComparisonResult
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
  GitCompare,
  BookOpen,
  UserCheck,
  Calendar,
  DollarSign,
  Briefcase,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileText,
  HelpCircle,
  Info
} from "lucide-react";

interface AdvancedAnalysisViewProps {
  documents: LegalDocument[];
  initialSelectedDocId?: string;
  userRole?: string;
}

export default function AdvancedAnalysisView({
  documents,
  initialSelectedDocId,
  userRole
}: AdvancedAnalysisViewProps) {
  const [selectedDocId, setSelectedDocId] = useState<string>(
    initialSelectedDocId || (documents[0]?.id || "")
  );
  const [activeSubTab, setActiveSubTab] = useState<"findings" | "clauses" | "comparison">("findings");

  // Sesión de análisis
  const [session, setSession] = useState<AdvancedAnalysisSession | null>(null);
  const [loadingSession, setLoadingSession] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filtros de Hallazgos
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");

  // Cláusulas
  const [expandedClauseId, setExpandedClauseId] = useState<string | null>(null);

  // HITL Review Modal / Inline
  const [reviewingFindingId, setReviewingFindingId] = useState<string | null>(null);
  const [reviewStatus, setReviewStatus] = useState<string>("VALIDATED");
  const [reviewNotes, setReviewNotes] = useState<string>("");
  const [reviewerLicense, setReviewerLicense] = useState<string>("");
  const [submittingReview, setSubmittingReview] = useState(false);

  // Comparativa de Versiones
  const [baseText, setBaseText] = useState<string>("");
  const [compareText, setCompareText] = useState<string>("");
  const [baseLabel, setBaseLabel] = useState<string>("Versión 1 (Original)");
  const [compareLabel, setCompareLabel] = useState<string>("Versión 2 (Revisada)");
  const [comparing, setComparing] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<VersionComparisonResult | null>(null);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  // Cargar última sesión cuando cambia el documento seleccionado
  useEffect(() => {
    if (!selectedDocId) return;
    setLoadingSession(true);
    setErrorMsg(null);
    api.getLatestDocumentAnalysis(selectedDocId)
      .then((res) => {
        setSession(res);
      })
      .catch((err) => {
        console.error("Error al obtener sesión de análisis:", err);
      })
      .finally(() => {
        setLoadingSession(false);
      });
  }, [selectedDocId]);

  const handleRunAnalysis = async () => {
    if (!selectedDocId) return;
    setAnalyzing(true);
    setErrorMsg(null);
    try {
      const res = await api.runAdvancedAnalysis(selectedDocId);
      setSession(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al ejecutar el análisis avanzado");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReviewFinding = async (findingId: string) => {
    if (!reviewNotes.trim()) {
      alert("Por favor ingrese el dictamen u observaciones del abogado revisor.");
      return;
    }
    setSubmittingReview(true);
    try {
      const updated = await api.reviewFinding(findingId, reviewStatus, reviewNotes, reviewerLicense);
      if (session) {
        setSession({
          ...session,
          findings: session.findings.map(f => f.id === findingId ? updated : f)
        });
      }
      setReviewingFindingId(null);
      setReviewNotes("");
    } catch (err: any) {
      alert(err.message || "Error al registrar validación humana");
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleCompareVersions = async () => {
    if (!baseText.trim() || !compareText.trim()) {
      setComparisonError("Debe ingresar el texto de ambas versiones para realizar la comparativa.");
      return;
    }
    setComparing(true);
    setComparisonError(null);
    try {
      const res = await api.compareVersions(selectedDocId, baseText, compareText, baseLabel, compareLabel);
      setComparisonResult(res);
    } catch (err: any) {
      setComparisonError(err.message || "Error al ejecutar la comparativa entre versiones");
    } finally {
      setComparing(false);
    }
  };

  const filteredFindings = session?.findings.filter((f) => {
    if (severityFilter === "ALL") return true;
    return f.severity === severityFilter;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Alerta Constitucional / HITL */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start space-x-3 text-xs text-amber-900 shadow-sm">
        <Scale className="h-5 w-5 text-amber-700 flex-shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-extrabold block text-amber-950 mb-0.5">
            Principio Human-in-the-Loop & Priorización Epistémica (México)
          </span>
          La puntuación de riesgo y las observaciones generadas por el sistema constituyen una{" "}
          <strong>herramienta de priorización</strong> y no una conclusión jurídica definitiva.
          Ninguna determinación tiene carácter vinculante sin la validación y firma de un abogado con cédula profesional registrada ante la Dirección General de Profesiones.
        </div>
      </div>

      {/* Barra de Control y Selector de Documento */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex-1 max-w-md">
          <label className="text-xs font-bold text-slate-800 block mb-1">
            Expediente / Documento en Revisión:
          </label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-900 focus:ring-2 focus:ring-slate-900 focus:outline-none"
          >
            {documents.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.title} ({doc.doc_type})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleRunAnalysis}
            disabled={analyzing || !selectedDocId}
            className="px-4 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold flex items-center space-x-2 transition-all disabled:opacity-50 shadow"
          >
            <RefreshCw className={`h-4 w-4 ${analyzing ? "animate-spin text-amber-400" : ""}`} />
            <span>{analyzing ? "Ejecutando Análisis..." : "⚡ Ejecutar Análisis Jurídico Avanzado"}</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Pestañas de la Vista Avanzada */}
      <div className="flex border-b border-slate-200 space-x-4">
        <button
          onClick={() => setActiveSubTab("findings")}
          className={`pb-3 text-xs font-bold flex items-center space-x-2 border-b-2 transition-all ${
            activeSubTab === "findings"
              ? "border-slate-900 text-slate-900"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <ShieldAlert className="h-4 w-4 text-rose-600" />
          <span>Matriz de Riesgos & Hallazgos</span>
          {session && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-rose-100 text-rose-800 font-extrabold">
              {session.findings_count}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveSubTab("clauses")}
          className={`pb-3 text-xs font-bold flex items-center space-x-2 border-b-2 transition-all ${
            activeSubTab === "clauses"
              ? "border-slate-900 text-slate-900"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <FileText className="h-4 w-4 text-indigo-600" />
          <span>Desglose de Cláusulas</span>
          {session && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-indigo-100 text-indigo-800 font-extrabold">
              {session.clauses.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveSubTab("comparison")}
          className={`pb-3 text-xs font-bold flex items-center space-x-2 border-b-2 transition-all ${
            activeSubTab === "comparison"
              ? "border-slate-900 text-slate-900"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <GitCompare className="h-4 w-4 text-emerald-600" />
          <span>Comparativa entre Versiones (Redline)</span>
        </button>
      </div>

      {/* SubTab 1: Matriz de Riesgos y Hallazgos */}
      {activeSubTab === "findings" && (
        <div className="space-y-6">
          {session && (
            <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
              <div className="md:col-span-2 bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col justify-between">
                <div>
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                    Puntuación de Riesgo Ponderado
                  </span>
                  <div className="flex items-baseline space-x-2 mt-1">
                    <span className={`text-3xl font-extrabold ${
                      session.overall_risk_score > 60 ? "text-rose-600" :
                      session.overall_risk_score > 30 ? "text-amber-600" : "text-emerald-600"
                    }`}>
                      {session.overall_risk_score.toFixed(0)}
                    </span>
                    <span className="text-xs text-slate-400 font-semibold">/ 100</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                      session.overall_severity === "CRITICAL" ? "bg-rose-100 text-rose-800" :
                      session.overall_severity === "HIGH" ? "bg-amber-100 text-amber-800" :
                      session.overall_severity === "MEDIUM" ? "bg-yellow-100 text-yellow-800" :
                      "bg-slate-100 text-slate-700"
                    }`}>
                      {session.overall_severity}
                    </span>
                  </div>
                </div>
                <span className="text-[10px] text-slate-400 mt-2 block">
                  Procesado en {session.execution_time_ms}ms • Priorización objetiva
                </span>
              </div>

              <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 text-rose-900 flex flex-col justify-between">
                <span className="text-[11px] font-bold">Críticos</span>
                <span className="text-2xl font-black">{session.critical_count}</span>
                <span className="text-[10px] text-rose-700">Atención urgente</span>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-amber-900 flex flex-col justify-between">
                <span className="text-[11px] font-bold">Altos</span>
                <span className="text-2xl font-black">{session.high_count}</span>
                <span className="text-[10px] text-amber-700">Riesgo contractual</span>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-3 text-yellow-900 flex flex-col justify-between">
                <span className="text-[11px] font-bold">Medios / Bajos</span>
                <span className="text-2xl font-black">{session.medium_count + session.low_count}</span>
                <span className="text-[10px] text-yellow-700">Observaciones</span>
              </div>

              <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-3 text-indigo-900 flex flex-col justify-between">
                <span className="text-[11px] font-bold">Validación HITL</span>
                <span className="text-2xl font-black">{session.pending_review_count}</span>
                <span className="text-[10px] text-indigo-700">Criterio humano</span>
              </div>
            </div>
          )}

          {/* Filtros de Severidad */}
          <div className="flex items-center space-x-2 text-xs">
            <span className="font-bold text-slate-600">Filtrar:</span>
            {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW", "REQUIRES_HUMAN_VALIDATION"].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1 rounded-lg font-bold text-[11px] transition-colors ${
                  severityFilter === sev
                    ? "bg-slate-900 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {sev === "ALL" ? "Todos los Hallazgos" : sev}
              </button>
            ))}
          </div>

          {/* Lista de Hallazgos */}
          {!session ? (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
              No hay una sesión de análisis reciente para este documento. Haga clic en "Ejecutar Análisis Jurídico Avanzado".
            </div>
          ) : (
            <div className="space-y-4">
              {filteredFindings.map((finding) => (
                <div
                  key={finding.id}
                  className={`bg-white rounded-xl border p-5 shadow-sm space-y-3 transition-all ${
                    finding.severity === "CRITICAL" ? "border-rose-300" :
                    finding.severity === "HIGH" ? "border-amber-300" :
                    finding.severity === "REQUIRES_HUMAN_VALIDATION" ? "border-indigo-300" :
                    "border-slate-200"
                  }`}
                >
                  {/* Encabezado del Hallazgo */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
                        {finding.finding_code}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold ${
                        finding.severity === "CRITICAL" ? "bg-rose-100 text-rose-800" :
                        finding.severity === "HIGH" ? "bg-amber-100 text-amber-800" :
                        finding.severity === "MEDIUM" ? "bg-yellow-100 text-yellow-800" :
                        finding.severity === "REQUIRES_HUMAN_VALIDATION" ? "bg-indigo-100 text-indigo-800" :
                        "bg-slate-100 text-slate-700"
                      }`}>
                        {finding.severity}
                      </span>
                      <span className="text-[11px] font-bold text-slate-500 uppercase">
                        [{finding.issue_type}]
                      </span>
                      <h4 className="font-bold text-xs text-slate-900">{finding.title}</h4>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        finding.review_status === "VALIDATED" ? "bg-emerald-100 text-emerald-800" :
                        finding.review_status === "REJECTED" ? "bg-slate-100 text-slate-600 line-through" :
                        "bg-amber-100 text-amber-800"
                      }`}>
                        {finding.review_status === "VALIDATED" ? "Validado por Abogado ✓" :
                         finding.review_status === "REJECTED" ? "Descartado ✗" :
                         "Pendiente de Dictamen ⚠️"}
                      </span>
                    </div>
                  </div>

                  {/* Descripción */}
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {finding.description}
                  </p>

                  {/* Fragmento Original */}
                  {finding.original_fragment && (
                    <div className="bg-slate-50 border-l-4 border-slate-400 p-3 rounded-r-lg text-xs font-mono text-slate-800">
                      <span className="text-[10px] font-bold text-slate-500 block uppercase mb-1">
                        Fragmento Original ({finding.clause_ref || finding.location}):
                      </span>
                      "{finding.original_fragment}"
                    </div>
                  )}

                  {/* Fundamentación Normativa Verificada en México */}
                  {finding.legal_foundation && (
                    <div className={`p-3 rounded-lg text-xs border ${
                      finding.legal_foundation.is_verified
                        ? "bg-emerald-50/60 border-emerald-200 text-emerald-950"
                        : "bg-amber-50/60 border-amber-200 text-amber-950"
                    }`}>
                      <div className="flex items-center space-x-2 font-bold mb-1">
                        {finding.legal_foundation.is_verified ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0" />
                        )}
                        <span>
                          {finding.legal_foundation.is_verified
                            ? `Fundamento Normativo Verificado (DOF / ${finding.legal_foundation.jurisdiction})`
                            : "Fundamento Requiere Investigación Jurídica"}
                        </span>
                      </div>
                      <div className="space-y-0.5 text-[11px] leading-relaxed">
                        <p><strong>Disposición:</strong> {finding.legal_foundation.disposition_name} {finding.legal_foundation.article ? `(Art. ${finding.legal_foundation.article})` : ""}</p>
                        <p><strong>Fuente Oficial:</strong> {finding.legal_foundation.official_source}</p>
                        <p><strong>Vigencia y Reformas:</strong> {finding.legal_foundation.publication_reform_date}</p>
                        {finding.legal_foundation.verification_note && (
                          <p className="text-slate-600 italic mt-1">"{finding.legal_foundation.verification_note}"</p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Explicación del Riesgo y Recomendación */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                    <div className="bg-rose-50/40 border border-rose-100 p-3 rounded-lg text-rose-950">
                      <span className="font-bold block text-rose-900 mb-1">Explicación del Riesgo Jurídico:</span>
                      <p className="text-[11px] leading-relaxed">{finding.risk_explanation}</p>
                    </div>

                    <div className="bg-indigo-50/40 border border-indigo-100 p-3 rounded-lg text-indigo-950">
                      <span className="font-bold block text-indigo-900 mb-1">Recomendación de Redacción:</span>
                      <p className="text-[11px] leading-relaxed">{finding.recommendation}</p>
                    </div>
                  </div>

                  {/* Notas de Validación Humana Previas */}
                  {finding.reviewer_notes && (
                    <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg text-xs space-y-1">
                      <span className="font-bold text-slate-800 flex items-center space-x-1.5">
                        <UserCheck className="h-3.5 w-3.5 text-emerald-600" />
                        <span>Dictamen del Abogado Revisor:</span>
                      </span>
                      <p className="italic text-slate-700 text-[11px]">"{finding.reviewer_notes}"</p>
                      {finding.reviewer_license && (
                        <span className="text-[10px] text-slate-500 font-mono block">
                          Cédula Profesional: {finding.reviewer_license}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Botón de Acción HITL */}
                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => setReviewingFindingId(reviewingFindingId === finding.id ? null : finding.id)}
                      className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold flex items-center space-x-1.5 transition-colors"
                    >
                      <UserCheck className="h-3.5 w-3.5" />
                      <span>{reviewingFindingId === finding.id ? "Cerrar Validación" : "Revisar Hallazgo (HITL)"}</span>
                    </button>
                  </div>

                  {/* Formulario HITL */}
                  {reviewingFindingId === finding.id && (
                    <div className="mt-3 p-4 bg-slate-50 rounded-xl border border-slate-300 space-y-3 text-xs">
                      <span className="font-bold text-slate-900 block">
                        Validación Humana por Abogado Autorizado:
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <label className="font-semibold text-slate-700 block mb-1">Determinación:</label>
                          <select
                            value={reviewStatus}
                            onChange={(e) => setReviewStatus(e.target.value)}
                            className="w-full rounded border border-slate-300 p-1.5 bg-white text-slate-900"
                          >
                            <option value="VALIDATED">Validar Hallazgo (Confirmado)</option>
                            <option value="REJECTED">Descartar (Falso Positivo / No Aplicable)</option>
                            <option value="MODIFIED">Modificar Observación</option>
                          </select>
                        </div>

                        <div>
                          <label className="font-semibold text-slate-700 block mb-1">Cédula Profesional:</label>
                          <input
                            type="text"
                            placeholder="Número de Cédula..."
                            value={reviewerLicense}
                            onChange={(e) => setReviewerLicense(e.target.value)}
                            className="w-full rounded border border-slate-300 p-1.5 bg-white"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Dictamen / Observaciones:</label>
                        <textarea
                          rows={2}
                          placeholder="Fundamento u observaciones jurídicas que respaldan la determinación..."
                          value={reviewNotes}
                          onChange={(e) => setReviewNotes(e.target.value)}
                          className="w-full rounded border border-slate-300 p-2 bg-white"
                        />
                      </div>

                      <div className="flex justify-end space-x-2 pt-1">
                        <button
                          type="button"
                          onClick={() => setReviewingFindingId(null)}
                          className="px-3 py-1.5 rounded text-xs text-slate-600 hover:bg-slate-200"
                        >
                          Cancelar
                        </button>
                        <button
                          type="button"
                          onClick={() => handleReviewFinding(finding.id)}
                          disabled={submittingReview}
                          className="px-4 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs disabled:opacity-50"
                        >
                          {submittingReview ? "Guardando..." : "Registrar Dictamen"}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SubTab 2: Desglose de Cláusulas */}
      {activeSubTab === "clauses" && (
        <div className="space-y-4">
          {!session || session.clauses.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
              No hay cláusulas descompuestas en esta sesión. Ejecute el análisis avanzado para segmentar el documento.
            </div>
          ) : (
            <div className="space-y-3">
              {session.clauses.map((clause) => {
                const isExpanded = expandedClauseId === clause.id;
                return (
                  <div
                    key={clause.id}
                    className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3"
                  >
                    <div
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setExpandedClauseId(isExpanded ? null : clause.id)}
                    >
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                          #{clause.clause_number}
                        </span>
                        <h4 className="font-bold text-xs text-slate-900">{clause.title}</h4>
                      </div>
                      <div className="flex items-center space-x-2 text-slate-400">
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </div>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      <strong>Resumen:</strong> {clause.summary}
                    </p>

                    {/* Etiquetas de Obligaciones, Derechos, Plazos y Penas */}
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {clause.obligations.map((ob, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-800 border border-blue-200">
                          Obligación: {ob}
                        </span>
                      ))}
                      {clause.rights.map((rt, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          Derecho: {rt}
                        </span>
                      ))}
                      {clause.deadlines.map((dl, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-50 text-purple-800 border border-purple-200 flex items-center space-x-1">
                          <Calendar className="h-3 w-3" />
                          <span>Plazo: {dl}</span>
                        </span>
                      ))}
                      {clause.penalties.map((pn, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-800 border border-rose-200 flex items-center space-x-1">
                          <AlertTriangle className="h-3 w-3" />
                          <span>Penalización: {pn}</span>
                        </span>
                      ))}
                    </div>

                    {/* Texto Íntegro Plegable */}
                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t border-slate-100 bg-slate-50 p-3 rounded-lg text-xs font-mono text-slate-800 whitespace-pre-wrap leading-relaxed">
                        {clause.raw_text}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* SubTab 3: Comparativa entre Versiones (Redline & Risk Delta) */}
      {activeSubTab === "comparison" && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Comparativa Redline & Delta de Riesgos</h3>
              <p className="text-xs text-slate-500">
                Compare dos versiones de un contrato para detectar supresiones, adiciones y si los riesgos fueron efectivamente remediados.
              </p>
            </div>

            {comparisonError && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {comparisonError}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="font-bold text-slate-800">Versión Base (Original / V1):</label>
                  <input
                    type="text"
                    value={baseLabel}
                    onChange={(e) => setBaseLabel(e.target.value)}
                    className="text-[11px] border border-slate-300 rounded px-2 py-0.5 text-slate-700"
                  />
                </div>
                <textarea
                  rows={8}
                  placeholder="Pegue aquí el texto íntegro de la versión original..."
                  value={baseText}
                  onChange={(e) => setBaseText(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2.5 font-mono text-xs bg-slate-50/50"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="font-bold text-slate-800">Versión Comparada (Revisada / V2):</label>
                  <input
                    type="text"
                    value={compareLabel}
                    onChange={(e) => setCompareLabel(e.target.value)}
                    className="text-[11px] border border-slate-300 rounded px-2 py-0.5 text-slate-700"
                  />
                </div>
                <textarea
                  rows={8}
                  placeholder="Pegue aquí el texto de la versión con modificaciones o adendas..."
                  value={compareText}
                  onChange={(e) => setCompareText(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2.5 font-mono text-xs bg-slate-50/50"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleCompareVersions}
                disabled={comparing}
                className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center space-x-2 transition-all shadow"
              >
                <GitCompare className={`h-4 w-4 ${comparing ? "animate-spin" : ""}`} />
                <span>{comparing ? "Comparando Versiones..." : "Ejecutar Comparativa de Versiones"}</span>
              </button>
            </div>
          </div>

          {/* Resultados de Comparativa */}
          {comparisonResult && (
            <div className="space-y-4">
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-xs text-emerald-950">
                <span className="font-bold block mb-1">Dictamen Ejecutivo de la Comparativa:</span>
                <p className="leading-relaxed">{comparisonResult.summary}</p>
              </div>

              {/* Delta de Riesgos */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 space-y-2">
                  <span className="text-xs font-bold text-emerald-900 block flex items-center space-x-1.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <span>Riesgos Mitigados / Resueltos ({comparisonResult.risk_delta.mitigated_risks?.length || 0})</span>
                  </span>
                  <ul className="text-xs space-y-1.5 text-emerald-800">
                    {comparisonResult.risk_delta.mitigated_risks?.map((r, i) => (
                      <li key={i} className="p-2 rounded bg-white/70 border border-emerald-100">
                        <strong>✓ {r.title}</strong>
                        {r.description && <p className="text-[11px] text-emerald-700 mt-0.5">{r.description}</p>}
                      </li>
                    ))}
                    {(!comparisonResult.risk_delta.mitigated_risks || comparisonResult.risk_delta.mitigated_risks.length === 0) && (
                      <li className="text-[11px] text-slate-500 italic">No se detectaron riesgos mitigados.</li>
                    )}
                  </ul>
                </div>

                <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 space-y-2">
                  <span className="text-xs font-bold text-rose-900 block flex items-center space-x-1.5">
                    <AlertTriangle className="h-4 w-4 text-rose-600" />
                    <span>Nuevos Riesgos Introducidos ({comparisonResult.risk_delta.introduced_risks?.length || 0})</span>
                  </span>
                  <ul className="text-xs space-y-1.5 text-rose-800">
                    {comparisonResult.risk_delta.introduced_risks?.map((r, i) => (
                      <li key={i} className="p-2 rounded bg-white/70 border border-rose-100">
                        <strong>⚠️ {r.title}</strong>
                        {r.description && <p className="text-[11px] text-rose-700 mt-0.5">{r.description}</p>}
                      </li>
                    ))}
                    {(!comparisonResult.risk_delta.introduced_risks || comparisonResult.risk_delta.introduced_risks.length === 0) && (
                      <li className="text-[11px] text-emerald-700 italic">No se introdujeron nuevos riesgos.</li>
                    )}
                  </ul>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
                  <span className="text-xs font-bold text-slate-900 block flex items-center space-x-1.5">
                    <Info className="h-4 w-4 text-slate-600" />
                    <span>Riesgos Persistentes ({comparisonResult.risk_delta.persistent_risks?.length || 0})</span>
                  </span>
                  <ul className="text-xs space-y-1.5 text-slate-700">
                    {comparisonResult.risk_delta.persistent_risks?.map((r, i) => (
                      <li key={i} className="p-2 rounded bg-white border border-slate-200">
                        <strong>• {r.title}</strong> ({r.severity})
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Cláusulas Añadidas, Suprimidas y Modificadas */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-2 shadow-sm">
                  <span className="font-bold text-slate-900 block">
                    Cláusulas Agregadas ({comparisonResult.added_clauses.length}):
                  </span>
                  <ul className="space-y-1.5">
                    {comparisonResult.added_clauses.map((c, i) => (
                      <li key={i} className="p-2 rounded bg-emerald-50/60 border border-emerald-100 text-emerald-950">
                        <strong>+ {c.title}</strong>
                        <p className="text-[11px] text-slate-600 mt-0.5">{c.summary}</p>
                      </li>
                    ))}
                    {comparisonResult.added_clauses.length === 0 && (
                      <li className="text-slate-400 italic">Sin cláusulas añadidas.</li>
                    )}
                  </ul>
                </div>

                <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-2 shadow-sm">
                  <span className="font-bold text-slate-900 block">
                    Cláusulas Suprimidas ({comparisonResult.removed_clauses.length}):
                  </span>
                  <ul className="space-y-1.5">
                    {comparisonResult.removed_clauses.map((c, i) => (
                      <li key={i} className="p-2 rounded bg-rose-50/60 border border-rose-100 text-rose-950">
                        <strong>- {c.title}</strong>
                        <p className="text-[11px] text-slate-600 mt-0.5">{c.summary}</p>
                      </li>
                    ))}
                    {comparisonResult.removed_clauses.length === 0 && (
                      <li className="text-slate-400 italic">Sin cláusulas eliminadas.</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
