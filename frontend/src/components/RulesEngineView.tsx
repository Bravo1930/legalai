"use client";

import React, { useState, useEffect } from "react";
import { LegalDocument, LegalRule, RuleEvaluation, RuleEvaluationDetail } from "@/types";
import { api } from "@/lib/api";
import {
  Scale,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  PlusCircle,
  RefreshCw,
  Search,
  Filter,
  ShieldAlert,
  FileText,
  UserCheck,
  ChevronRight,
  BookOpen,
  X
} from "lucide-react";

interface RulesEngineViewProps {
  documents: LegalDocument[];
  initialSelectedDocId?: string;
  userRole?: string;
}

const CATEGORIES = [
  { id: "MANDATORY_CLAUSE", label: "Cláusula Obligatoria" },
  { id: "PROHIBITED_CLAUSE", label: "Cláusula Prohibida" },
  { id: "TERM_LIMIT", label: "Límite de Plazos" },
  { id: "AMOUNT_LIMIT", label: "Límites Económicos / Montos" },
  { id: "PENALTY", label: "Penalización / Pena Convencional" },
  { id: "OBLIGATION", label: "Obligaciones Específicas" },
  { id: "CONFIDENTIALITY", label: "Confidencialidad" },
  { id: "DATA_PROTECTION", label: "Protección de Datos Personales" },
  { id: "TERMINATION", label: "Terminación & Rescisión" },
  { id: "JURISDICTION", label: "Jurisdicción & Tribunales" },
  { id: "COMPETENCE", label: "Competencia & Fuero" },
  { id: "SIGNATURES", label: "Requisitos de Firma" },
  { id: "LEGAL_REPRESENTATION", label: "Representación Legal" },
  { id: "POWERS_FACULTIES", label: "Facultades & Atribuciones" },
  { id: "COMMERCIAL_REQUIREMENT", label: "Requisito Comercial de Cliente" },
];

export default function RulesEngineView({ documents, initialSelectedDocId, userRole }: RulesEngineViewProps) {
  const [subTab, setSubTab] = useState<"audit" | "catalog">("audit");
  const [rules, setRules] = useState<LegalRule[]>([]);
  const [loadingRules, setLoadingRules] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string>(initialSelectedDocId || (documents[0]?.id || ""));

  // Evaluación
  const [evaluating, setEvaluating] = useState(false);
  const [evaluation, setEvaluation] = useState<RuleEvaluation | null>(null);
  const [evalHistory, setEvalHistory] = useState<RuleEvaluation[]>([]);
  const [evalError, setEvalError] = useState<string | null>(null);

  // HITL Verification Modal/Inline
  const [verifyingDetailId, setVerifyingDetailId] = useState<string | null>(null);
  const [verificationStatus, setVerificationStatus] = useState<string>("COMPLIANT");
  const [verificationNotes, setVerificationNotes] = useState<string>("");
  const [submittingVerification, setSubmittingVerification] = useState(false);

  // Modal Nueva Regla
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newRuleCode, setNewRuleCode] = useState("");
  const [newRuleName, setNewRuleName] = useState("");
  const [newRuleDesc, setNewRuleDesc] = useState("");
  const [newRuleCategory, setNewRuleCategory] = useState("MANDATORY_CLAUSE");
  const [newRuleSeverity, setNewRuleSeverity] = useState<"CRITICAL" | "HIGH" | "MEDIUM" | "LOW">("CRITICAL");
  const [newRuleOperator, setNewRuleOperator] = useState("CONTAINS_ALL_KEYWORDS");
  const [newRuleKeywords, setNewRuleKeywords] = useState("");
  const [newRuleProhibited, setNewRuleProhibited] = useState("");
  const [newRuleRegex, setNewRuleRegex] = useState("");
  const [newRuleMaxValue, setNewRuleMaxValue] = useState<string>("");
  const [newRuleExpectedOutcome, setNewRuleExpectedOutcome] = useState("");
  const [newRuleFoundation, setNewRuleFoundation] = useState("");
  const [creatingRule, setCreatingRule] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Cargar catálogo de reglas
  const loadRules = async () => {
    try {
      setLoadingRules(true);
      const data = await api.listRules();
      setRules(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoadingRules(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  // Cargar historial de evaluaciones del documento
  useEffect(() => {
    if (!selectedDocId) return;
    api.listDocumentEvaluations(selectedDocId)
      .then((history) => {
        setEvalHistory(history);
        if (history.length > 0) {
          setEvaluation(history[0]);
        } else {
          setEvaluation(null);
        }
      })
      .catch((err) => console.error("Error al cargar historial de evaluaciones:", err));
  }, [selectedDocId]);

  const handleRunEvaluation = async () => {
    if (!selectedDocId) {
      setEvalError("Por favor seleccione un documento de la lista.");
      return;
    }
    setEvaluating(true);
    setEvalError(null);
    try {
      const res = await api.evaluateDocumentRules(selectedDocId);
      setEvaluation(res);
      setEvalHistory([res, ...evalHistory]);
    } catch (err: any) {
      setEvalError(err.message || "Error al ejecutar evaluación determinista");
    } finally {
      setEvaluating(false);
    }
  };

  const handleVerifyDetail = async (detailId: string) => {
    if (!verificationNotes.trim()) {
      alert("Por favor ingrese las observaciones jurídicas del abogado.");
      return;
    }
    setSubmittingVerification(true);
    try {
      const updatedDetail = await api.verifyEvaluationDetail(detailId, verificationStatus, verificationNotes);
      // Actualizar en el estado local
      if (evaluation) {
        const updatedDetails = evaluation.details.map((d) => d.id === detailId ? updatedDetail : d);
        const passed = updatedDetails.filter(d => d.status === "COMPLIANT").length;
        const failed = updatedDetails.filter(d => d.status === "NON_COMPLIANT").length;
        const pending = updatedDetails.filter(d => d.status === "PENDING_HUMAN_REVIEW").length;
        const notApplicable = updatedDetails.filter(d => d.status === "NOT_APPLICABLE").length;
        const applicable = passed + failed + pending;
        const newScore = applicable > 0 ? Math.round((passed / applicable) * 100) : 100;

        setEvaluation({
          ...evaluation,
          passed_count: passed,
          failed_count: failed,
          pending_count: pending,
          not_applicable_count: notApplicable,
          compliance_score: newScore,
          details: updatedDetails,
        });
      }
      setVerifyingDetailId(null);
      setVerificationNotes("");
    } catch (err: any) {
      alert(err.message || "Error al validar observación");
    } finally {
      setSubmittingVerification(false);
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingRule(true);
    setCreateError(null);

    const parameters: Record<string, any> = {};
    if (newRuleOperator === "CONTAINS_ALL_KEYWORDS" || newRuleOperator === "CONTAINS_ANY_KEYWORD") {
      parameters.keywords = newRuleKeywords.split(",").map(s => s.trim()).filter(Boolean);
    } else if (newRuleOperator === "PROHIBITS_KEYWORDS") {
      parameters.prohibited_keywords = newRuleProhibited.split(",").map(s => s.trim()).filter(Boolean);
    } else if (newRuleOperator === "REGEX_MATCH") {
      parameters.regex_pattern = newRuleRegex;
      parameters.expected_match = true;
    } else if (newRuleOperator === "NUMERIC_RANGE") {
      if (newRuleMaxValue) parameters.max_value = parseFloat(newRuleMaxValue);
      parameters.regex_extractor = "(\\d+[\\d,]*)";
    }

    try {
      await api.createRule({
        rule_code: newRuleCode.trim().toUpperCase(),
        name: newRuleName.trim(),
        description: newRuleDesc.trim(),
        category: newRuleCategory,
        severity: newRuleSeverity,
        scope: { doc_types: ["*"] },
        condition_definition: {
          operator: newRuleOperator,
          parameters: parameters
        },
        expected_outcome: newRuleExpectedOutcome.trim(),
        legal_foundation: newRuleFoundation.trim() || undefined
      });
      setShowCreateModal(false);
      // Reset form
      setNewRuleCode("");
      setNewRuleName("");
      setNewRuleDesc("");
      setNewRuleKeywords("");
      setNewRuleProhibited("");
      setNewRuleRegex("");
      setNewRuleMaxValue("");
      setNewRuleExpectedOutcome("");
      setNewRuleFoundation("");
      loadRules();
    } catch (err: any) {
      setCreateError(err.message || "Error al guardar la regla");
    } finally {
      setCreatingRule(false);
    }
  };

  const handleToggleStatus = async (ruleId: string, currentStatus: boolean) => {
    try {
      await api.toggleRuleStatus(ruleId, !currentStatus);
      setRules(rules.map(r => r.id === ruleId ? { ...r, is_active: !currentStatus } : r));
    } catch (err: any) {
      alert("Error al actualizar estado de la regla: " + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Sub-navigation bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSubTab("audit")}
            className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center space-x-2 transition-all ${
              subTab === "audit"
                ? "bg-slate-900 text-white shadow"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            <ShieldAlert className="h-4 w-4 text-emerald-400" />
            <span>Auditoría de Documentos</span>
          </button>

          <button
            onClick={() => setSubTab("catalog")}
            className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center space-x-2 transition-all ${
              subTab === "catalog"
                ? "bg-slate-900 text-white shadow"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            <BookOpen className="h-4 w-4 text-amber-400" />
            <span>Catálogo de Reglas</span>
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">{rules.length}</span>
          </button>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center space-x-1.5 transition-colors shadow-sm"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Nueva Regla Determinista</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Auditoría Determinista de Documentos */}
      {subTab === "audit" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Panel Izquierdo: Selección y Ejecución */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-5">
            <div>
              <label className="text-xs font-bold text-slate-900 block mb-1">
                Documento a Auditar:
              </label>
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-800 focus:ring-2 focus:ring-slate-900 focus:outline-none"
              >
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.title} ({doc.doc_type})
                  </option>
                ))}
              </select>
            </div>

            <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200 text-xs text-slate-600 space-y-1.5">
              <div className="flex items-center text-slate-900 font-bold space-x-1.5">
                <Scale className="h-4 w-4 text-slate-700" />
                <span>Garantía de Determinismo</span>
              </div>
              <p className="text-[11px] leading-relaxed">
                Este motor evalúa condiciones formales sin emplear modelos probabilísticos de IA. Los resultados son 100% reproducibles y con evidencias textuales.
              </p>
            </div>

            <button
              onClick={handleRunEvaluation}
              disabled={evaluating || !selectedDocId}
              className="w-full py-2.5 px-4 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold flex items-center justify-center space-x-2 transition-all disabled:opacity-50 shadow"
            >
              <RefreshCw className={`h-4 w-4 ${evaluating ? "animate-spin text-amber-400" : ""}`} />
              <span>{evaluating ? "Evaluando reglas..." : "Ejecutar auditoría determinista"}</span>
            </button>

            {evalError && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {evalError}
              </div>
            )}

            {/* Score y Métricas */}
            {evaluation && (
              <div className="pt-4 border-t border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-600">Índice de Cumplimiento:</span>
                  <span className={`text-base font-extrabold ${
                    evaluation.compliance_score >= 80 ? "text-emerald-600" :
                    evaluation.compliance_score >= 50 ? "text-amber-600" : "text-rose-600"
                  }`}>
                    {evaluation.compliance_score.toFixed(1)}%
                  </span>
                </div>

                <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      evaluation.compliance_score >= 80 ? "bg-emerald-500" :
                      evaluation.compliance_score >= 50 ? "bg-amber-500" : "bg-rose-500"
                    }`}
                    style={{ width: `${evaluation.compliance_score}%` }}
                  />
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 text-[11px]">
                  <div className="p-2 rounded bg-emerald-50 border border-emerald-100 text-emerald-800">
                    <span className="font-bold block text-sm">{evaluation.passed_count}</span>
                    <span>Reglas conformes</span>
                  </div>
                  <div className="p-2 rounded bg-rose-50 border border-rose-100 text-rose-800">
                    <span className="font-bold block text-sm">{evaluation.failed_count}</span>
                    <span>Incumplimientos</span>
                  </div>
                  <div className="p-2 rounded bg-amber-50 border border-amber-100 text-amber-800">
                    <span className="font-bold block text-sm">{evaluation.pending_count}</span>
                    <span>Revisión letrada requerida</span>
                  </div>
                  <div className="p-2 rounded bg-slate-50 border border-slate-200 text-slate-700">
                    <span className="font-bold block text-sm">{evaluation.not_applicable_count}</span>
                    <span>No aplicables</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Panel Derecho: Detalle de Resultados y Validación HITL */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
                <FileText className="h-4 w-4 text-slate-700" />
                <span>Resultados de la Auditoría</span>
              </h3>
              {evaluation && (
                <span className="text-[10px] text-slate-500 font-mono">
                  {new Date(evaluation.created_at).toLocaleString("es-MX")}
                </span>
              )}
            </div>

            {!evaluation ? (
              <div className="py-16 text-center text-slate-400 text-xs">
                Seleccione un documento y presione "Ejecutar Auditoría Determinista" para auditar contra las reglas activas.
              </div>
            ) : (
              <div className="space-y-3">
                {evaluation.details.map((detail) => (
                  <div
                    key={detail.id}
                    className={`p-3.5 rounded-xl border transition-all ${
                      detail.status === "COMPLIANT" ? "bg-emerald-50/40 border-emerald-200" :
                      detail.status === "NON_COMPLIANT" ? "bg-rose-50/40 border-rose-200" :
                      detail.status === "PENDING_HUMAN_REVIEW" ? "bg-amber-50/50 border-amber-300" :
                      "bg-slate-50 border-slate-200"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-800">
                            {detail.rule_code}
                          </span>
                          <span className="font-bold text-xs text-slate-900">{detail.rule_name}</span>
                          <span className="text-[10px] text-slate-500">({detail.category})</span>
                        </div>

                        {/* Evidencia o Motivo de Fallo */}
                        {detail.matched_evidence && (
                          <div className="mt-1.5 p-2 rounded bg-white/80 border border-slate-200 text-[11px] text-slate-700 font-mono">
                            <span className="font-bold text-slate-900 block mb-0.5">Evidencia hallada:</span>
                            "{detail.matched_evidence}"
                          </div>
                        )}

                        {detail.failure_reason && (
                          <p className="text-[11px] text-rose-700 mt-1 font-semibold flex items-center space-x-1">
                            <AlertTriangle className="h-3 w-3 text-rose-600 flex-shrink-0" />
                            <span>{detail.failure_reason}</span>
                          </p>
                        )}

                        {detail.human_verification_notes && (
                          <div className="mt-1.5 p-2 rounded bg-indigo-50 border border-indigo-200 text-[11px] text-indigo-900">
                            <span className="font-bold flex items-center space-x-1">
                              <UserCheck className="h-3.5 w-3.5 text-indigo-700" />
                              <span>Validación de Abogado (HITL):</span>
                            </span>
                            <p className="mt-0.5 italic">"{detail.human_verification_notes}"</p>
                          </div>
                        )}
                      </div>

                      {/* Status Badge & Actions */}
                      <div className="flex flex-col items-end space-y-2">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold flex items-center space-x-1 ${
                          detail.status === "COMPLIANT" ? "bg-emerald-100 text-emerald-800" :
                          detail.status === "NON_COMPLIANT" ? "bg-rose-100 text-rose-800" :
                          detail.status === "PENDING_HUMAN_REVIEW" ? "bg-amber-100 text-amber-900 border border-amber-300" :
                          "bg-slate-200 text-slate-700"
                        }`}>
                          {detail.status === "COMPLIANT" && <CheckCircle2 className="h-3 w-3 text-emerald-600" />}
                          {detail.status === "NON_COMPLIANT" && <XCircle className="h-3 w-3 text-rose-600" />}
                          {detail.status === "PENDING_HUMAN_REVIEW" && <AlertTriangle className="h-3 w-3 text-amber-600" />}
                          {detail.status === "NOT_APPLICABLE" && <MinusCircle className="h-3 w-3 text-slate-500" />}
                          <span>{detail.status}</span>
                        </span>

                        {detail.status === "PENDING_HUMAN_REVIEW" && (
                          <button
                            onClick={() => setVerifyingDetailId(verifyingDetailId === detail.id ? null : detail.id)}
                            className="text-[11px] font-bold text-amber-700 hover:text-amber-900 underline flex items-center space-x-1"
                          >
                            <span>Validar Hallazgo</span>
                            <ChevronRight className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Formulario de Resolución HITL para Abogado */}
                    {verifyingDetailId === detail.id && (
                      <div className="mt-3 pt-3 border-t border-amber-200 bg-amber-100/50 p-3 rounded-lg space-y-2">
                        <span className="text-xs font-bold text-amber-900 block">
                          Dictamen Humano del Abogado Revisor:
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          <select
                            value={verificationStatus}
                            onChange={(e) => setVerificationStatus(e.target.value)}
                            className="text-xs rounded border border-amber-300 p-1.5 bg-white text-slate-900"
                          >
                            <option value="COMPLIANT">Dictamen: CUMPLE (Aprobado)</option>
                            <option value="NON_COMPLIANT">Dictamen: INCUMPLE (Violación Confirmada)</option>
                          </select>
                          <input
                            type="text"
                            placeholder="Criterio u observaciones jurídicas..."
                            value={verificationNotes}
                            onChange={(e) => setVerificationNotes(e.target.value)}
                            className="text-xs rounded border border-amber-300 p-1.5 bg-white text-slate-900 placeholder:text-slate-400"
                          />
                        </div>
                        <div className="flex justify-end space-x-2 pt-1">
                          <button
                            onClick={() => setVerifyingDetailId(null)}
                            className="px-2.5 py-1 rounded text-xs text-slate-600 hover:bg-amber-200/50"
                          >
                            Cancelar
                          </button>
                          <button
                            onClick={() => handleVerifyDetail(detail.id)}
                            disabled={submittingVerification}
                            className="px-3 py-1 rounded bg-amber-800 text-white text-xs font-bold hover:bg-amber-900 disabled:opacity-50"
                          >
                            {submittingVerification ? "Registrando..." : "Confirmar Validación"}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Catálogo de Reglas del Despacho */}
      {subTab === "catalog" && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Catálogo de Reglas Deterministas</h3>
              <p className="text-xs text-slate-500">
                Reglas jurídicas activas configuradas para la organización.
              </p>
            </div>
            <button onClick={loadRules} className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50">
              <RefreshCw className={`h-4 w-4 ${loadingRules ? "animate-spin text-slate-700" : ""}`} />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                  <th className="py-2.5 px-3">Código</th>
                  <th className="py-2.5 px-3">Nombre & Criterio</th>
                  <th className="py-2.5 px-3">Categoría</th>
                  <th className="py-2.5 px-3">Severidad</th>
                  <th className="py-2.5 px-3">Condición Declarativa</th>
                  <th className="py-2.5 px-3">Versión</th>
                  <th className="py-2.5 px-3">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-900">{rule.rule_code}</td>
                    <td className="py-2.5 px-3">
                      <span className="font-semibold block text-slate-900">{rule.name}</span>
                      <span className="text-[11px] text-slate-500">{rule.description}</span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-700">{rule.category}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        rule.severity === "CRITICAL" ? "bg-rose-100 text-rose-800" :
                        rule.severity === "HIGH" ? "bg-amber-100 text-amber-800" :
                        "bg-slate-100 text-slate-700"
                      }`}>
                        {rule.severity}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-600">
                      {rule.condition_definition?.operator}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-700">v{rule.version}</td>
                    <td className="py-2.5 px-3">
                      <button
                        onClick={() => handleToggleStatus(rule.id, rule.is_active)}
                        className={`px-2.5 py-1 rounded-full text-[10px] font-bold transition-colors ${
                          rule.is_active ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-200" : "bg-slate-200 text-slate-600 hover:bg-slate-300"
                        }`}
                      >
                        {rule.is_active ? "Activa" : "Inactiva"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Crear Nueva Regla Determinista */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-2">
                <Scale className="h-5 w-5 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900">Nueva Regla Jurídica Determinista</h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {createError && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateRule} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-900 block mb-1">Código Único de Regla:</label>
                  <input
                    type="text"
                    required
                    placeholder="Ej. REG-JUR-CDMX"
                    value={newRuleCode}
                    onChange={(e) => setNewRuleCode(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 font-mono uppercase"
                  />
                </div>

                <div>
                  <label className="font-bold text-slate-900 block mb-1">Categoría Jurídica:</label>
                  <select
                    value={newRuleCategory}
                    onChange={(e) => setNewRuleCategory(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 bg-white"
                  >
                    {CATEGORIES.map(c => (
                      <option key={c.id} value={c.id}>{c.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-900 block mb-1">Nombre Descriptivo:</label>
                <input
                  type="text"
                  required
                  placeholder="Ej. Someterse a Tribunales de la Ciudad de México"
                  value={newRuleName}
                  onChange={(e) => setNewRuleName(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2"
                />
              </div>

              <div>
                <label className="font-bold text-slate-900 block mb-1">Descripción del Criterio:</label>
                <textarea
                  required
                  rows={2}
                  placeholder="Explique el criterio y la razón por la que debe comprobarse de forma estricta..."
                  value={newRuleDesc}
                  onChange={(e) => setNewRuleDesc(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-900 block mb-1">Nivel de Severidad:</label>
                  <select
                    value={newRuleSeverity}
                    onChange={(e) => setNewRuleSeverity(e.target.value as any)}
                    className="w-full rounded-lg border border-slate-300 p-2 bg-white"
                  >
                    <option value="CRITICAL">CRITICAL (Incumplimiento Inadmisible)</option>
                    <option value="HIGH">HIGH (Riesgo Alto)</option>
                    <option value="MEDIUM">MEDIUM (Riesgo Moderado)</option>
                    <option value="LOW">LOW (Observación Menor)</option>
                  </select>
                </div>

                <div>
                  <label className="font-bold text-slate-900 block mb-1">Operador Determinista:</label>
                  <select
                    value={newRuleOperator}
                    onChange={(e) => setNewRuleOperator(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 bg-white font-semibold text-slate-800"
                  >
                    <option value="CONTAINS_ALL_KEYWORDS">Debe contener todas las palabras clave</option>
                    <option value="PROHIBITS_KEYWORDS">Prohíbe términos específicos</option>
                    <option value="CONTAINS_ANY_KEYWORD">Debe contener al menos una alternativa</option>
                    <option value="REGEX_MATCH">Expresión Regular (Regex)</option>
                    <option value="NUMERIC_RANGE">Límite Numérico / Monto / Días</option>
                  </select>
                </div>
              </div>

              {/* Parámetros condicionales */}
              {(newRuleOperator === "CONTAINS_ALL_KEYWORDS" || newRuleOperator === "CONTAINS_ANY_KEYWORD") && (
                <div>
                  <label className="font-bold text-slate-900 block mb-1">Palabras Clave (Separadas por comas):</label>
                  <input
                    type="text"
                    required
                    placeholder="ej. tribunales, ciudad de méxico, fuero"
                    value={newRuleKeywords}
                    onChange={(e) => setNewRuleKeywords(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2"
                  />
                </div>
              )}

              {newRuleOperator === "PROHIBITS_KEYWORDS" && (
                <div>
                  <label className="font-bold text-slate-900 block mb-1">Términos Expresamente Prohibidos:</label>
                  <input
                    type="text"
                    required
                    placeholder="ej. renuncia de derechos, sin responsabilidad, arbitraje foráneo"
                    value={newRuleProhibited}
                    onChange={(e) => setNewRuleProhibited(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2"
                  />
                </div>
              )}

              {newRuleOperator === "REGEX_MATCH" && (
                <div>
                  <label className="font-bold text-slate-900 block mb-1">Patrón de Expresión Regular:</label>
                  <input
                    type="text"
                    required
                    placeholder="ej. pena convencional\s*(\d+)%"
                    value={newRuleRegex}
                    onChange={(e) => setNewRuleRegex(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 font-mono"
                  />
                </div>
              )}

              {newRuleOperator === "NUMERIC_RANGE" && (
                <div>
                  <label className="font-bold text-slate-900 block mb-1">Límite Máximo Permitido:</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="ej. 500000"
                    value={newRuleMaxValue}
                    onChange={(e) => setNewRuleMaxValue(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2"
                  />
                </div>
              )}

              <div>
                <label className="font-bold text-slate-900 block mb-1">Resultado Jurídico Esperado:</label>
                <input
                  type="text"
                  required
                  placeholder="ej. El contrato debe estipular fuero competente en la CDMX."
                  value={newRuleExpectedOutcome}
                  onChange={(e) => setNewRuleExpectedOutcome(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2"
                />
              </div>

              <div>
                <label className="font-bold text-slate-900 block mb-1">Fundamento Legal (Opcional):</label>
                <input
                  type="text"
                  placeholder="ej. Art. 1093 del Código de Comercio"
                  value={newRuleFoundation}
                  onChange={(e) => setNewRuleFoundation(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={creatingRule}
                  className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold transition-all shadow"
                >
                  {creatingRule ? "Guardando..." : "Guardar Regla"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
