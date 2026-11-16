"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { AuditLogEntry } from "@/types";
import { 
  History, 
  Search, 
  RefreshCw, 
  Filter, 
  ShieldCheck, 
  Terminal, 
  User, 
  Clock, 
  FileText, 
  X,
  Code
} from "lucide-react";

const ACTIONS = [
  "DOCUMENT_UPLOAD",
  "DOCUMENT_DOWNLOAD",
  "WORKFLOW_TRANSITION",
  "TEAM_ASSIGNED",
  "APPROVAL_SUBMITTED",
  "RULE_EVALUATED",
  "RULE_CREATED",
  "MODIFICATION_GENERATED",
  "MODIFICATION_REVIEWED",
  "LOGIN_SUCCESS"
];

export default function AuditView({ userRole }: { userRole?: string }) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAction, setSelectedAction] = useState("");
  const [selectedResource, setSelectedResource] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  // Modal Inspección JSON
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  useEffect(() => {
    loadLogs();
  }, [selectedAction, selectedResource]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedAction, selectedResource]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await api.listAuditLogs(
        selectedAction || undefined,
        selectedResource || undefined
      );
      setLogs(data);
    } catch (err) {
      console.error("Error al cargar bitácora de auditoría:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(l => {
    const q = searchQuery.toLowerCase();
    return (
      l.action.toLowerCase().includes(q) ||
      (l.user_name && l.user_name.toLowerCase().includes(q)) ||
      (l.resource_type && l.resource_type.toLowerCase().includes(q)) ||
      (l.resource_id && l.resource_id.toLowerCase().includes(q))
    );
  });

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage) || 1;
  const paginatedLogs = filteredLogs.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-900 text-amber-400 font-mono mb-1">
            <History className="h-3.5 w-3.5" />
            <span>Trazabilidad Forense Inmutable</span>
          </span>
          <h2 className="text-xl font-bold text-slate-900">Bitácora de Auditoría Legal</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Registro append-only de cada consulta, descarga, transición de estado, dictamen de IA y aprobación definitiva.
          </p>
        </div>

        <button
          onClick={loadLogs}
          className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1 flex-shrink-0"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
          <span>Actualizar Bitácora</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="relative w-full sm:w-96">
          <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por usuario, acción, recurso o ID..."
            className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <select
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value)}
            className="text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
          >
            <option value="">Todas las acciones</option>
            {ACTIONS.map((act) => (
              <option key={act} value={act}>{act}</option>
            ))}
          </select>

          <select
            value={selectedResource}
            onChange={(e) => setSelectedResource(e.target.value)}
            className="text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
          >
            <option value="">Todos los recursos</option>
            <option value="DOCUMENT">Documentos</option>
            <option value="WORKFLOW">Workflows</option>
            <option value="APPROVAL">Aprobaciones</option>
            <option value="RULE">Reglas</option>
            <option value="FINDING">Hallazgos</option>
            <option value="PROPOSAL">Propuestas</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {filteredLogs.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <ShieldCheck className="h-10 w-10 mx-auto mb-2 opacity-30 text-slate-500" />
            <p className="text-sm font-semibold text-slate-700">No se encontraron eventos forenses registrados.</p>
            <p className="text-xs text-slate-400 mt-1">Cualquier operación realizada en la plataforma se registrará en este panel.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                  <th className="py-3 px-4">Acción Ejecutada</th>
                  <th className="py-3 px-4">Usuario Responsable</th>
                  <th className="py-3 px-4">Recurso Afectado</th>
                  <th className="py-3 px-4">Dirección IP</th>
                  <th className="py-3 px-4">Timestamp UTC</th>
                  <th className="py-3 px-4 text-right">Detalle Forense</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4">
                      <span className="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 text-[11px]">
                        {log.action}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <span className="font-semibold text-slate-800 block">
                        {log.user_name || "Sistema / Inferencia IA"}
                      </span>
                      {log.user_id && (
                        <span className="text-[10px] text-slate-400 font-mono">ID: {log.user_id.slice(0, 8)}...</span>
                      )}
                    </td>

                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                        {log.resource_type || "SISTEMA"}
                      </span>
                      {log.resource_id && (
                        <span className="text-[10px] text-slate-400 font-mono block mt-0.5">
                          ID: {log.resource_id.slice(0, 10)}...
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                      {!log.ip_address || log.ip_address === "testclient" || log.ip_address === "localhost" ? "127.0.0.1" : log.ip_address}
                    </td>

                    <td className="py-3 px-4 text-slate-500 font-mono">
                      {new Date(log.created_at).toLocaleString("es-MX", {
                        dateStyle: "short",
                        timeStyle: "medium"
                      })}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="px-2.5 py-1 text-slate-700 bg-slate-100 hover:bg-slate-200 rounded font-semibold text-[11px] inline-flex items-center space-x-1"
                      >
                        <Terminal className="h-3.5 w-3.5 text-slate-500" />
                        <span>Ver JSON</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {filteredLogs.length > 0 && (
          <div className="p-4 border-t border-slate-200 bg-slate-50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
            <div>
              Mostrando <span className="font-semibold font-mono text-slate-900">{(currentPage - 1) * itemsPerPage + 1}</span> a <span className="font-semibold font-mono text-slate-900">{Math.min(currentPage * itemsPerPage, filteredLogs.length)}</span> de <span className="font-semibold font-mono text-slate-900">{filteredLogs.length}</span> registros
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed font-medium shadow-2xs"
              >
                Anterior
              </button>
              <span className="font-mono px-2 font-semibold text-slate-900">
                Página {currentPage} de {Math.ceil(filteredLogs.length / itemsPerPage) || 1}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(Math.ceil(filteredLogs.length / itemsPerPage) || 1, p + 1))}
                disabled={currentPage === (Math.ceil(filteredLogs.length / itemsPerPage) || 1)}
                className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed font-medium shadow-2xs"
              >
                Siguiente
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal Inspector JSON */}
      {selectedLog && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
              <div className="flex items-center space-x-2">
                <Code className="h-4 w-4 text-amber-400" />
                <h3 className="text-xs font-bold font-mono">
                  Evidencia Forense • {selectedLog.action} (ID: {selectedLog.id})
                </h3>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto flex-1 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-xs bg-slate-50 p-3 rounded-lg border border-slate-200">
                <div>
                  <span className="font-semibold text-slate-500 block">Usuario:</span>
                  <span className="font-bold text-slate-900">{selectedLog.user_name || "Sistema"}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-500 block">IP Origen:</span>
                  <span className="font-mono text-slate-900">{selectedLog.ip_address || "127.0.0.1"}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-500 block">Recurso:</span>
                  <span className="font-mono text-slate-900">{selectedLog.resource_type} / {selectedLog.resource_id}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-500 block">Fecha y Hora:</span>
                  <span className="font-mono text-slate-900">{selectedLog.created_at}</span>
                </div>
              </div>

              <div>
                <span className="text-xs font-bold text-slate-700 block mb-1">
                  Metadata del Evento (Payload JSON):
                </span>
                <pre className="p-4 bg-slate-900 text-amber-300 rounded-xl text-xs font-mono overflow-x-auto max-h-80 leading-relaxed">
                  {JSON.stringify(selectedLog.details || {}, null, 2)}
                </pre>
              </div>
            </div>

            <div className="p-3 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
