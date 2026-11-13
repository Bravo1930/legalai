"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { LegalFinding, LegalDocument } from "@/types";
import { 
  ShieldAlert, 
  AlertTriangle, 
  AlertCircle, 
  CheckCircle2, 
  Filter, 
  Search, 
  RefreshCw, 
  Scale, 
  Check, 
  X, 
  BookOpen,
  ArrowRight,
  ShieldCheck
} from "lucide-react";

interface RisksViewProps {
  documents: LegalDocument[];
  onNavigateToReview?: (docId: string, findingId?: string) => void;
  userRole?: string;
}

export default function RisksView({ documents, onNavigateToReview, userRole }: { documents: LegalDocument[]; onNavigateToReview?: (docId: string, findingId?: string) => void; userRole?: string }) {
  const [findings, setFindings] = useState<LegalFinding[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSeverity, setSelectedSeverity] = useState<string>("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadFindings();
  }, [selectedSeverity, selectedStatus]);

  const loadFindings = async () => {
    setLoading(true);
    try {
      const data = await api.listAllFindings(
        selectedSeverity || undefined,
        selectedStatus || undefined
      );
      setFindings(data);
    } catch (err) {
      console.error("Error al cargar riesgos:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewAction = async (findingId: string, status: "VALIDATED" | "REJECTED") => {
    try {
      await api.reviewFinding(
        findingId,
        status,
        status === "VALIDATED" ? "Riesgo confirmado y validado en matriz" : "Riesgo descartado por excepción legal"
      );
      setActionSuccess(`Hallazgo actualizado a "${status}".`);
      await loadFindings();
      setTimeout(() => setActionSuccess(null), 2500);
    } catch (err: any) {
      alert(`Error al actualizar estado del hallazgo: ${err?.message}`);
    }
  };

  const filteredFindings = findings.filter(f => {
    const q = searchQuery.toLowerCase();
    return (
      f.title.toLowerCase().includes(q) ||
      f.finding_code.toLowerCase().includes(q) ||
      f.risk_explanation.toLowerCase().includes(q) ||
      (f.related_rule_code && f.related_rule_code.toLowerCase().includes(q))
    );
  });

  // Severity metrics
  const criticalCount = findings.filter(f => f.severity === "CRITICAL").length;
  const highCount = findings.filter(f => f.severity === "HIGH").length;
  const mediumCount = findings.filter(f => f.severity === "MEDIUM").length;
  const lowCount = findings.filter(f => f.severity === "LOW").length;

  const getDocTitle = (docId: string) => {
    const doc = documents.find(d => d.id === docId);
    return doc ? doc.title : "Documento";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200 font-mono mb-1">
            <ShieldAlert className="h-3.5 w-3.5 text-rose-600" />
            <span>Matriz Consolidada de Riesgos Contractuales</span>
          </span>
          <h2 className="text-xl font-bold text-slate-900">Riesgos y Contingencias Detectadas</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Concentrador de observaciones críticas, violaciones de políticas y fundamentos jurídicos de todo el despacho.
          </p>
        </div>

        <button
          onClick={loadFindings}
          className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1 flex-shrink-0"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
          <span>Actualizar Matriz</span>
        </button>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center space-x-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Severity Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div 
          onClick={() => setSelectedSeverity(selectedSeverity === "CRITICAL" ? "" : "CRITICAL")}
          className={`bg-white rounded-xl border p-4 shadow-xs cursor-pointer transition-all ${
            selectedSeverity === "CRITICAL" ? "border-rose-600 ring-2 ring-rose-600/20 bg-rose-50/20" : "border-slate-200 hover:border-slate-300"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-700 uppercase">Crítico</span>
            <AlertCircle className="h-4 w-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{criticalCount}</div>
          <p className="text-[11px] text-slate-500 mt-1">Invalidez legal o pena lesiva</p>
        </div>

        <div 
          onClick={() => setSelectedSeverity(selectedSeverity === "HIGH" ? "" : "HIGH")}
          className={`bg-white rounded-xl border p-4 shadow-xs cursor-pointer transition-all ${
            selectedSeverity === "HIGH" ? "border-orange-500 ring-2 ring-orange-500/20 bg-orange-50/20" : "border-slate-200 hover:border-slate-300"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-orange-700 uppercase">Alto</span>
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{highCount}</div>
          <p className="text-[11px] text-slate-500 mt-1">Desequilibrio o desprotección</p>
        </div>

        <div 
          onClick={() => setSelectedSeverity(selectedSeverity === "MEDIUM" ? "" : "MEDIUM")}
          className={`bg-white rounded-xl border p-4 shadow-xs cursor-pointer transition-all ${
            selectedSeverity === "MEDIUM" ? "border-amber-500 ring-2 ring-amber-500/20 bg-amber-50/20" : "border-slate-200 hover:border-slate-300"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-amber-700 uppercase">Medio</span>
            <Scale className="h-4 w-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{mediumCount}</div>
          <p className="text-[11px] text-slate-500 mt-1">Ambigüedad o plazo forzoso</p>
        </div>

        <div 
          onClick={() => setSelectedSeverity(selectedSeverity === "LOW" ? "" : "LOW")}
          className={`bg-white rounded-xl border p-4 shadow-xs cursor-pointer transition-all ${
            selectedSeverity === "LOW" ? "border-blue-500 ring-2 ring-blue-500/20 bg-blue-50/20" : "border-slate-200 hover:border-slate-300"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-blue-700 uppercase">Bajo / Estilo</span>
            <ShieldCheck className="h-4 w-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{lowCount}</div>
          <p className="text-[11px] text-slate-500 mt-1">Mejora de técnica jurídica</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="relative w-full sm:w-96">
          <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por código, título, regla o fragmento..."
            className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
          >
            <option value="">Todos los estados HITL</option>
            <option value="PENDING_REVIEW">Pendiente de revisión</option>
            <option value="VALIDATED">Validados por abogado</option>
            <option value="REJECTED">Descartados</option>
          </select>

          {selectedSeverity && (
            <button
              onClick={() => setSelectedSeverity("")}
              className="px-2.5 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium flex items-center space-x-1"
            >
              <span>Filtro {selectedSeverity}</span>
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Risks Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {filteredFindings.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <CheckCircle2 className="h-10 w-10 mx-auto mb-2 text-emerald-500 opacity-60" />
            <p className="text-sm font-semibold text-slate-800">No se encontraron riesgos bajo los filtros actuales.</p>
            <p className="text-xs text-slate-400 mt-1">Ejecute un análisis jurídico en la bóveda o seleccione otra categoría.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                  <th className="py-3 px-4">Severidad / Código</th>
                  <th className="py-3 px-4">Riesgo & Análisis Jurídico</th>
                  <th className="py-3 px-4">Fundamento Legal (Leyes MX)</th>
                  <th className="py-3 px-4">Recomendación</th>
                  <th className="py-3 px-4">Estado HITL</th>
                  <th className="py-3 px-4 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredFindings.map((f) => (
                  <tr key={f.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 align-top">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase mb-1 ${
                          f.severity === "CRITICAL"
                            ? "bg-rose-100 text-rose-800 border border-rose-200"
                            : f.severity === "HIGH"
                            ? "bg-orange-100 text-orange-800 border border-orange-200"
                            : f.severity === "MEDIUM"
                            ? "bg-amber-100 text-amber-800 border border-amber-200"
                            : "bg-blue-100 text-blue-800 border border-blue-200"
                        }`}
                      >
                        {f.severity}
                      </span>
                      <span className="font-mono text-[11px] font-bold text-slate-900 block">{f.finding_code}</span>
                      <span className="text-[10px] text-slate-400 font-mono block">Cláusula {f.clause_ref || "Gral."}</span>
                    </td>

                    <td className="py-3 px-4 align-top max-w-xs">
                      <span className="font-bold text-slate-900 block">{f.title}</span>
                      <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">{f.risk_explanation}</p>
                      {f.original_fragment && (
                        <div className="mt-1.5 p-1.5 rounded bg-slate-50 border border-slate-200 font-mono text-[10px] text-slate-700 italic line-clamp-2">
                          &quot;{f.original_fragment}&quot;
                        </div>
                      )}
                    </td>

                    <td className="py-3 px-4 align-top max-w-xs">
                      {f.legal_foundation ? (
                        <div className="bg-emerald-50/50 p-2 rounded border border-emerald-200 text-[11px]">
                          <span className="font-bold text-emerald-950 block">{f.legal_foundation.disposition_name}</span>
                          {f.legal_foundation.article && (
                            <span className="text-emerald-800 font-mono text-[10px] block mt-0.5">{f.legal_foundation.article}</span>
                          )}
                          <span className="text-[9px] text-emerald-700 font-mono block mt-1">
                            Fuente: {f.legal_foundation.official_source}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">No especificado</span>
                      )}
                    </td>

                    <td className="py-3 px-4 align-top max-w-xs">
                      <p className="text-[11px] text-purple-900 bg-purple-50/50 p-2 rounded border border-purple-200 leading-relaxed">
                        {f.recommendation}
                      </p>
                    </td>

                    <td className="py-3 px-4 align-top">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        f.review_status === "VALIDATED"
                          ? "bg-emerald-100 text-emerald-800"
                          : f.review_status === "REJECTED"
                          ? "bg-slate-200 text-slate-700 line-through"
                          : "bg-amber-100 text-amber-800 animate-pulse"
                      }`}>
                        {f.review_status}
                      </span>
                      {f.reviewer_license && (
                        <span className="text-[9px] text-slate-400 font-mono block mt-1">
                          Cédula: {f.reviewer_license}
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-4 align-top text-right space-y-1">
                      {onNavigateToReview && (
                        <button
                          onClick={() => onNavigateToReview(f.document_id || documents[0]?.id, f.id)}
                          className="w-full px-2 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded font-semibold text-[10px] flex items-center justify-center space-x-1 transition-all"
                        >
                          <BookOpen className="h-3 w-3 text-amber-400" />
                          <span>Ir al Visor</span>
                        </button>
                      )}

                      {f.review_status !== "VALIDATED" && (
                        <button
                          onClick={() => handleReviewAction(f.id, "VALIDATED")}
                          className="w-full px-2 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 rounded font-semibold text-[10px] flex items-center justify-center space-x-1 transition-all"
                        >
                          <Check className="h-3 w-3 text-emerald-600" />
                          <span>Validar</span>
                        </button>
                      )}

                      {f.review_status !== "REJECTED" && (
                        <button
                          onClick={() => handleReviewAction(f.id, "REJECTED")}
                          className="w-full px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded font-semibold text-[10px] flex items-center justify-center space-x-1 transition-all"
                        >
                          <X className="h-3 w-3 text-slate-500" />
                          <span>Descartar</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
