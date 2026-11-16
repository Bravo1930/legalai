"use client";

import React, { useState, useEffect } from "react";
import { DashboardAnalytics, LegalDocument } from "@/types";
import { api } from "@/lib/api";
import {
  FileText,
  Clock,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  FileCheck,
  TrendingUp,
  UserCheck,
  Building,
  RefreshCw,
  Scale,
  Calendar,
  AlertTriangle,
  ArrowUpRight,
  Briefcase,
  Users
} from "lucide-react";

interface DashboardViewProps {
  onNavigate: (tab: string, docId?: string) => void;
  userRole?: string;
  tenantName?: string;
}

export default function DashboardView({ onNavigate, userRole, tenantName }: DashboardViewProps) {
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);
  const [showSyncSuccess, setShowSyncSuccess] = useState<boolean>(false);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await api.getDashboardAnalytics();
      setAnalytics(data);
      const timeStr = new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      setLastSyncTime(timeStr);
      setShowSyncSuccess(true);
      setTimeout(() => setShowSyncSuccess(false), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || "Error al cargar analítica de la plataforma");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-900 rounded-2xl p-4 sm:p-6 text-white shadow-[0_8px_30px_-4px_rgba(15,23,42,0.15)] border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-400 text-slate-900 shadow-xs">
              Despacho Jurídico
            </span>
            <span className="text-xs text-slate-300 font-medium">{tenantName || "Bufete de Abogados"}</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">Tablero de Control Jurídico</h1>
          <p className="text-xs text-slate-300 mt-1">
            Supervisión ejecutiva de expedientes, revisión documental con IA soberana y gobernanza procesal.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
          {showSyncSuccess && lastSyncTime && (
            <div className="flex items-center space-x-1.5 bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 px-3 py-1.5 rounded-xl text-[11px] font-mono animate-fade-in shadow-xs">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              <span>Sincronizado a las {lastSyncTime}</span>
            </div>
          )}
          {!showSyncSuccess && lastSyncTime && (
            <span className="text-[10px] text-slate-400 font-mono hidden md:inline-block">
              Última sincronización: {lastSyncTime}
            </span>
          )}
          <button
            onClick={loadAnalytics}
            disabled={loading}
            className="apple-interactive px-3.5 py-2 bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-xs shrink-0"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-amber-400" : ""}`} />
            <span>{loading ? "Sincronizando..." : "Actualizar Métricas"}</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2">
          <AlertTriangle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {/* Documentos Recibidos */}
        <div
          onClick={() => onNavigate("documents")}
          className="apple-interactive bg-white/95 backdrop-blur-sm p-4 rounded-2xl border border-slate-200/80 shadow-[0_2px_10px_-2px_rgba(15,23,42,0.03)] hover:shadow-[0_8px_24px_-4px_rgba(15,23,42,0.08)] cursor-pointer transition-all hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-semibold">Recibidos</span>
            <FileText className="h-4 w-4 text-slate-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">
            {loading ? "..." : analytics?.received_documents ?? 0}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-medium">En bóveda documental</div>
        </div>

        {/* Documentos Procesados */}
        <div
          onClick={() => onNavigate("documents")}
          className="apple-interactive bg-white/95 backdrop-blur-sm p-4 rounded-2xl border border-slate-200/80 shadow-[0_2px_10px_-2px_rgba(15,23,42,0.03)] hover:shadow-[0_8px_24px_-4px_rgba(15,23,42,0.08)] cursor-pointer transition-all hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-semibold">Procesados</span>
            <FileCheck className="h-4 w-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">
            {loading ? "..." : analytics?.processed_documents ?? 0}
          </div>
          <div className="text-[10px] text-blue-600 mt-1 font-medium">OCR & Extracción listos</div>
        </div>

        {/* Revisiones Pendientes */}
        <div
          onClick={() => onNavigate("workflow")}
          className="apple-interactive bg-white/95 backdrop-blur-sm p-4 rounded-2xl border border-slate-200/80 shadow-[0_2px_10px_-2px_rgba(15,23,42,0.03)] hover:shadow-[0_8px_24px_-4px_rgba(15,23,42,0.08)] cursor-pointer transition-all hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-semibold">Pend. Revisión</span>
            <Clock className="h-4 w-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-700">
            {loading ? "..." : analytics?.pending_reviews ?? 0}
          </div>
          <div className="text-[10px] text-amber-600 mt-1 font-medium">Esperan dictamen</div>
        </div>

        {/* Riesgos Críticos */}
        <div
          onClick={() => onNavigate("risks")}
          className="apple-interactive bg-white/95 backdrop-blur-sm p-4 rounded-2xl border border-rose-200/80 shadow-[0_2px_10px_-2px_rgba(15,23,42,0.03)] hover:shadow-[0_8px_24px_-4px_rgba(15,23,42,0.08)] bg-rose-50/20 cursor-pointer transition-all hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between text-rose-700 mb-2">
            <span className="text-[11px] font-bold">Riesgos Críticos</span>
            <ShieldAlert className="h-4 w-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-700">
            {loading ? "..." : analytics?.critical_risks ?? 0}
          </div>
          <div className="text-[10px] text-rose-600 mt-1 font-medium">Atención inmediata</div>
        </div>

        {/* Aprobados */}
        <div
          onClick={() => onNavigate("approvals")}
          className="apple-interactive bg-white/95 backdrop-blur-sm p-4 rounded-2xl border border-emerald-200/80 shadow-[0_2px_10px_-2px_rgba(15,23,42,0.03)] hover:shadow-[0_8px_24px_-4px_rgba(15,23,42,0.08)] bg-emerald-50/20 cursor-pointer transition-all hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between text-emerald-700 mb-2">
            <span className="text-[11px] font-bold">Aprobados</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-700">
            {loading ? "..." : analytics?.approved_documents ?? 0}
          </div>
          <div className="text-[10px] text-emerald-600 mt-1 font-medium">Firma legal asentada</div>
        </div>

        {/* Rechazados */}
        <div
          onClick={() => onNavigate("workflow")}
          className="apple-interactive bg-white/95 backdrop-blur-sm p-4 rounded-2xl border border-slate-200/80 shadow-[0_2px_10px_-2px_rgba(15,23,42,0.03)] hover:shadow-[0_8px_24px_-4px_rgba(15,23,42,0.08)] cursor-pointer transition-all hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-semibold">Rechazados</span>
            <XCircle className="h-4 w-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-slate-700">
            {loading ? "..." : analytics?.rejected_documents ?? 0}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-medium">Concluidos / Descartados</div>
        </div>
      </div>

      {/* Second Row: Performance Metrics & Operational Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Carga de Trabajo por Abogado */}
        <div className="lg:col-span-2 bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/80 p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <div className="flex items-center space-x-2">
              <UserCheck className="h-4 w-4 text-amber-500" />
              <h3 className="text-sm font-bold text-slate-900">Carga de Trabajo por Abogado</h3>
            </div>
            <button
              onClick={() => onNavigate("users")}
              className="text-xs text-slate-500 hover:text-slate-800 underline font-medium"
            >
              Gestionar Equipo
            </button>
          </div>

          {!analytics?.workload_by_lawyer || analytics.workload_by_lawyer.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400">
              No hay abogados asignados a expedientes activos.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs divide-y divide-slate-100">
                <thead>
                  <tr className="text-slate-500 text-left font-semibold">
                    <th className="py-2 px-3">Abogado</th>
                    <th className="py-2 px-3">Rol</th>
                    <th className="py-2 px-3">Cédula</th>
                    <th className="py-2 px-3 text-center">Docs Asignados</th>
                    <th className="py-2 px-3 text-center">Pendientes</th>
                    <th className="py-2 px-3 text-center">Aprobados</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {analytics.workload_by_lawyer.map((law) => (
                    <tr key={law.lawyer_id} className="hover:bg-slate-50/50">
                      <td className="py-2.5 px-3 font-bold text-slate-900">{law.lawyer_name}</td>
                      <td className="py-2.5 px-3 text-slate-500 text-[11px] font-mono">{law.role}</td>
                      <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">{law.license || "N/A"}</td>
                      <td className="py-2.5 px-3 text-center font-bold text-slate-800">{law.active_documents}</td>
                      <td className="py-2.5 px-3 text-center font-bold text-amber-700">{law.pending_reviews}</td>
                      <td className="py-2.5 px-3 text-center font-bold text-emerald-700">{law.approved_documents}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* SLA & Estadísticas de Despacho */}
        <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-4">
          <div className="pb-3 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
              <TrendingUp className="h-4 w-4 text-emerald-600" />
              <span>Eficiencia & Gobernanza</span>
            </h3>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
              SLA Operativo
            </span>
          </div>

          <div className="space-y-3">
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Tiempo Promedio de Dictamen</span>
              <div className="flex items-baseline space-x-2 mt-1">
                <span className="text-2xl font-bold text-slate-900 font-mono">
                  {analytics?.avg_review_time_hours ?? 0}
                </span>
                <span className="text-xs text-slate-500">horas por expediente</span>
              </div>
              <p className="text-[10px] text-slate-400 mt-1">
                Calculado con base en aprobaciones formales de versiones emitidas por el equipo.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div
                onClick={() => onNavigate("cases")}
                className="p-3 bg-slate-50 border border-slate-100 rounded-lg hover:border-slate-300 cursor-pointer transition-colors"
              >
                <div className="flex items-center space-x-1 text-slate-500 mb-1">
                  <Briefcase className="h-3.5 w-3.5 text-blue-600" />
                  <span className="font-semibold text-[11px]">Expedientes</span>
                </div>
                <div className="text-xl font-bold text-slate-900">{analytics?.total_cases ?? 0}</div>
              </div>

              <div
                onClick={() => onNavigate("clients")}
                className="p-3 bg-slate-50 border border-slate-100 rounded-lg hover:border-slate-300 cursor-pointer transition-colors"
              >
                <div className="flex items-center space-x-1 text-slate-500 mb-1">
                  <Users className="h-3.5 w-3.5 text-indigo-600" />
                  <span className="font-semibold text-[11px]">Clientes</span>
                </div>
                <div className="text-xl font-bold text-slate-900">{analytics?.total_clients ?? 0}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Third Row: Recent Activity Feed */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-slate-700" />
            <h3 className="text-sm font-bold text-slate-900">Actividad y Operaciones Recientes</h3>
          </div>
          <button
            onClick={() => onNavigate("audit")}
            className="text-xs text-slate-500 hover:text-slate-800 underline font-medium"
          >
            Ver Bitácora de Auditoría Completa
          </button>
        </div>

        {!analytics?.recent_activity || analytics.recent_activity.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-400">
            No hay operaciones recientes registradas en la bitácora.
          </div>
        ) : (
          <div className="space-y-2.5">
            {analytics.recent_activity.map((act) => (
              <div
                key={act.id}
                className="p-3 bg-slate-50/70 border border-slate-100 rounded-lg text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-3"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-full bg-slate-200 text-slate-700 flex-shrink-0">
                    <Scale className="h-3.5 w-3.5" />
                  </div>
                  <div>
                    <span className="font-bold text-slate-900">{act.actor}</span>
                    <span className="text-slate-600 mx-1">•</span>
                    <span className="text-slate-700">{act.description}</span>
                    {act.reason && <span className="text-[11px] text-slate-500 block italic">&quot;{act.reason}&quot;</span>}
                  </div>
                </div>

                <div className="text-[10px] text-slate-400 font-mono flex-shrink-0">
                  {new Date(act.timestamp).toLocaleString("es-MX")}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
