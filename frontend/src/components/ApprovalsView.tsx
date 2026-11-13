"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { WorkflowApprovalRecord, LegalDocument, DocumentWorkflow } from "@/types";
import { 
  FileCheck, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  Search, 
  RefreshCw, 
  Clock, 
  XCircle, 
  Plus, 
  Scale, 
  UserCheck,
  X
} from "lucide-react";

interface ApprovalsViewProps {
  documents: LegalDocument[];
  userRole?: string;
}

export default function ApprovalsView({ documents, userRole }: ApprovalsViewProps) {
  const [approvals, setApprovals] = useState<WorkflowApprovalRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedScope, setSelectedScope] = useState("");

  // Modal Firmar Aprobación Formal
  const [showModal, setShowModal] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState(documents[0]?.id || "");
  const [approvalScope, setApprovalScope] = useState("DEFINITIVE_APPROVAL");
  const [reviewerLicense, setReviewerLicense] = useState("");
  const [approvalNotes, setApprovalNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const data = await api.listApprovals();
      setApprovals(data);
    } catch (err) {
      console.error("Error al cargar historial de aprobaciones:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApproval = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDocId) return;

    setSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(null);

    try {
      // Get document workflow first
      const wf = await api.getDocumentWorkflow(selectedDocId);
      
      const record = await api.submitWorkflowApproval(
        wf.id,
        approvalScope,
        reviewerLicense || undefined,
        approvalNotes || undefined
      );

      setSubmitSuccess(`Aprobación formal registrada exitosamente para el documento.`);
      await loadApprovals();
      setTimeout(() => {
        setShowModal(false);
        setSubmitSuccess(null);
        setApprovalNotes("");
      }, 1500);
    } catch (err: any) {
      setSubmitError(err?.message || "Error al emitir la aprobación jurídica.");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredApprovals = approvals.filter(a => {
    const matchesSearch = 
      (a.reviewer_license && a.reviewer_license.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (a.approval_notes && a.approval_notes.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (a.user_name && a.user_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      a.scope.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesScope = selectedScope ? a.scope === selectedScope : true;
    return matchesSearch && matchesScope;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono mb-1">
            <FileCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>Gobernanza HITL & Fe Pública Jurídica</span>
          </span>
          <h2 className="text-xl font-bold text-slate-900">Registro Formal de Aprobaciones</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Bitácora legal de vistos buenos y firmas definitivas emitidas por abogados titulados con número de cédula profesional.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm flex items-center space-x-1.5 flex-shrink-0"
          >
            <UserCheck className="h-4 w-4 text-amber-400" />
            <span>Emitir Aprobación</span>
          </button>
        </div>
      </div>

      {/* Info Card on Legal Rules */}
      <div className="bg-amber-50/50 border border-amber-200 rounded-xl p-4 flex items-start space-x-3 text-xs text-amber-950">
        <Scale className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-amber-900 block">Reglas Deontológicas de Aprobación Documental:</span>
          <p className="mt-0.5 leading-relaxed text-amber-800">
            • Los modelos de IA no tienen personalidad jurídica y no pueden aprobar documentos.
            <br />• Toda aprobación definitiva exige la cédula profesional del abogado responsable del asunto.
            <br />• Si un documento aprobado es editado o versionado con posterioridad, su visto bueno previo queda automáticamente invalidado.
          </p>
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
            placeholder="Buscar por cédula profesional, notas o alcance..."
            className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <select
            value={selectedScope}
            onChange={(e) => setSelectedScope(e.target.value)}
            className="text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
          >
            <option value="">Todos los alcances</option>
            <option value="DEFINITIVE_APPROVAL">Aprobación Definitiva</option>
            <option value="INTERMEDIATE_REVIEW">Revisión Intermedia</option>
            <option value="CONDITIONAL_APPROVAL">Aprobación Condicionada</option>
          </select>

          <button
            onClick={loadApprovals}
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
            <span>Actualizar</span>
          </button>
        </div>
      </div>

      {/* Approvals Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {filteredApprovals.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <ShieldCheck className="h-10 w-10 mx-auto mb-2 opacity-30 text-slate-500" />
            <p className="text-sm font-semibold text-slate-700">No hay registros de aprobación emitidos.</p>
            <p className="text-xs text-slate-400 mt-1">Utilice el botón &quot;Emitir Aprobación&quot; para registrar el primer visto bueno formal.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                  <th className="py-3 px-4">Alcance / Tipo</th>
                  <th className="py-3 px-4">Abogado / Cédula</th>
                  <th className="py-3 px-4">Estado de Vigencia</th>
                  <th className="py-3 px-4">Notas & Fundamentación</th>
                  <th className="py-3 px-4">Fecha de Emisión</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredApprovals.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        a.scope === "DEFINITIVE_APPROVAL"
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                          : a.scope === "CONDITIONAL_APPROVAL"
                          ? "bg-amber-100 text-amber-800 border border-amber-200"
                          : "bg-blue-100 text-blue-800 border border-blue-200"
                      }`}>
                        {a.scope}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono block mt-0.5">ID: {a.id.slice(0, 8)}</span>
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-1.5 font-mono text-slate-900">
                        <Scale className="h-3.5 w-3.5 text-slate-400" />
                        <span className="font-bold">Cédula: {a.reviewer_license || "No requerida"}</span>
                      </div>
                      <span className="text-[10px] text-slate-700 font-semibold block mt-0.5">
                        {a.user_name} ({a.user_role})
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono block">
                        Versión: v{a.version_number}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      {a.status === "VALID" ? (
                        <span className="inline-flex items-center space-x-1 text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-[10px]">
                          <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                          <span>Vigente & Válida</span>
                        </span>
                      ) : (
                        <div>
                          <span className="inline-flex items-center space-x-1 text-rose-700 font-bold bg-rose-50 px-2 py-0.5 rounded border border-rose-200 text-[10px]">
                            <XCircle className="h-3 w-3 text-rose-600" />
                            <span>Invalidada</span>
                          </span>
                          {a.invalidation_reason && (
                            <p className="text-[10px] text-slate-500 mt-1 max-w-xs">{a.invalidation_reason}</p>
                          )}
                        </div>
                      )}
                    </td>

                    <td className="py-3 px-4 max-w-xs">
                      <p className="text-slate-700 text-xs leading-relaxed">{a.approval_notes || "Sin observaciones adicionales."}</p>
                    </td>

                    <td className="py-3 px-4 text-slate-500 font-mono">
                      {new Date(a.approved_at || a.created_at || Date.now()).toLocaleString("es-MX", {
                        dateStyle: "short",
                        timeStyle: "short"
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Emitir Aprobación */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                <h3 className="text-sm font-bold">Emitir Aprobación Jurídica Formal (HITL)</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateApproval} className="p-6 space-y-4">
              {submitSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                  <span>{submitSuccess}</span>
                </div>
              )}

              {submitError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-rose-600 flex-shrink-0" />
                  <span>{submitError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Documento a Dictaminar <span className="text-rose-600">*</span>
                </label>
                <select
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                >
                  {documents.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.title} ({d.doc_type})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Alcance de Aprobación
                  </label>
                  <select
                    value={approvalScope}
                    onChange={(e) => setApprovalScope(e.target.value)}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                  >
                    <option value="DEFINITIVE_APPROVAL">Aprobación Definitiva</option>
                    <option value="INTERMEDIATE_REVIEW">Revisión Intermedia</option>
                    <option value="CONDITIONAL_APPROVAL">Aprobación Condicionada</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Cédula Profesional {approvalScope === "DEFINITIVE_APPROVAL" && <span className="text-rose-600">*</span>}
                  </label>
                  <input
                    type="text"
                    required={approvalScope === "DEFINITIVE_APPROVAL"}
                    value={reviewerLicense}
                    onChange={(e) => setReviewerLicense(e.target.value)}
                    placeholder="Ej. 10485920"
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Notas Técnicas y Dictamen Jurídico
                </label>
                <textarea
                  rows={3}
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                  placeholder="Fundamente el sentido del visto bueno, excepciones o condicionantes..."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm disabled:opacity-50"
                >
                  {submitting ? "Firmando..." : "Registrar Aprobación"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
