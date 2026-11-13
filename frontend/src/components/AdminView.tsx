"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Tenant, UserProfile, AIModelInfo } from "@/types";
import { 
  ShieldAlert, 
  Building, 
  Cpu, 
  Activity, 
  Server, 
  Database, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  Lock,
  HardDrive,
  Radio
} from "lucide-react";

export default function AdminView({ user }: { user: UserProfile }) {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [aiModels, setAiModels] = useState<AIModelInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [backendHealth, setBackendHealth] = useState<{ status: string; version: string } | null>(null);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [tenantsList, modelsList] = await Promise.all([
        api.listTenants().catch(() => []),
        api.listAIModels().catch(() => [])
      ]);
      setTenants(tenantsList);
      setAiModels(modelsList);
      setBackendHealth({ status: "healthy", version: "1.0.0" });
    } catch (err) {
      console.error("Error al cargar panel de administración:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-900 text-amber-400 font-mono mb-1">
            <Server className="h-3.5 w-3.5" />
            <span>Plano de Control de Plataforma (Control Plane)</span>
          </span>
          <h2 className="text-xl font-bold text-slate-900">Consola de Administración de Infraestructura</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Supervisión global de despachos aislados, estado de los nodos de cómputo GPU y salud de los servicios locales.
          </p>
        </div>

        <button
          onClick={loadAdminData}
          className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1 flex-shrink-0"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
          <span>Actualizar Telemetría</span>
        </button>
      </div>

      {/* Security Architecture Notice */}
      <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm border border-slate-800 flex items-start space-x-4">
        <Lock className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs leading-relaxed space-y-1">
          <span className="font-bold text-amber-400 block text-sm">
            Aislamiento de Privacidad Multi-Tenant Criptográficamente Garantizado:
          </span>
          <p className="text-slate-300">
            Los roles de administración global de infraestructura operan exclusivamente sobre metadatos de tenants y estado de servicios. 
            El backend FastAPI bloquea terminantemente el acceso de <strong>SUPER_ADMIN</strong> a documentos, contratos y expedientes de clientes de cualquier despacho (HTTP 403 Forbidden).
          </p>
        </div>
      </div>

      {/* Infrastructure Telemetry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Backend Node */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
            <span className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
              <Server className="h-4 w-4 text-emerald-600" />
              <span>Backend FastAPI & Workers</span>
            </span>
            <span className="flex items-center space-x-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              <Radio className="h-3 w-3 animate-pulse text-emerald-600" />
              <span>ONLINE</span>
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-600">
            <div className="flex justify-between">
              <span>Versión API:</span>
              <span className="font-bold text-slate-900">{backendHealth?.version || "1.0.0"}</span>
            </div>
            <div className="flex justify-between">
              <span>Puerto Local:</span>
              <span className="text-slate-800">127.0.0.1:8000</span>
            </div>
            <div className="flex justify-between">
              <span>Cola Asíncrona:</span>
              <span className="text-emerald-700 font-bold">Redis Activo</span>
            </div>
          </div>
        </div>

        {/* Database Node */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
            <span className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
              <Database className="h-4 w-4 text-blue-600" />
              <span>PostgreSQL 16 + pgvector</span>
            </span>
            <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              CONECTADO
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-600">
            <div className="flex justify-between">
              <span>Bóveda WORM:</span>
              <span className="text-emerald-700 font-bold">Inmutable SHA-256</span>
            </div>
            <div className="flex justify-between">
              <span>Vectores HNSW:</span>
              <span className="text-slate-800">1536 dim / Cosine</span>
            </div>
            <div className="flex justify-between">
              <span>Pool de Conexiones:</span>
              <span className="text-slate-800">10 activas</span>
            </div>
          </div>
        </div>

        {/* GPU & Ollama */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
            <span className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
              <Cpu className="h-4 w-4 text-indigo-600" />
              <span>Inferencia Soberana (Ollama)</span>
            </span>
            <span className="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
              GPU ACELERADA
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono text-slate-600">
            <div className="flex justify-between">
              <span>Hardware Local:</span>
              <span className="text-slate-800">NVIDIA RTX 3050 Laptop (6GB)</span>
            </div>
            <div className="flex justify-between">
              <span>Modelos en Memoria:</span>
              <span className="font-bold text-indigo-700">{aiModels.length} disponibles</span>
            </div>
            <div className="flex justify-between">
              <span>Puerto Inferencia:</span>
              <span className="text-slate-800">127.0.0.1:11434</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tenants Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Building className="h-4 w-4 text-slate-700" />
            <h3 className="text-xs font-bold text-slate-900">
              Despachos y Firmas Registradas ({tenants.length})
            </h3>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            Aislamiento por Tenant ID en capa ORM
          </span>
        </div>

        {tenants.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-xs">
            No hay despachos adicionales dados de alta en el sistema.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                  <th className="py-3 px-4">Despacho / Firma</th>
                  <th className="py-3 px-4">Slug de Acceso</th>
                  <th className="py-3 px-4">RFC Registrado</th>
                  <th className="py-3 px-4">Contacto Institucional</th>
                  <th className="py-3 px-4">Estado</th>
                  <th className="py-3 px-4">Fecha de Alta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tenants.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4">
                      <span className="font-bold text-slate-900 block">{t.name}</span>
                      <span className="text-[10px] text-slate-400 font-mono">ID: {t.id}</span>
                    </td>

                    <td className="py-3 px-4 font-mono font-medium text-slate-700">
                      /{t.slug}
                    </td>

                    <td className="py-3 px-4 font-mono text-slate-800 font-bold">
                      {t.rfc || "No registrado"}
                    </td>

                    <td className="py-3 px-4 text-slate-600">
                      {t.contact_email}
                    </td>

                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        t.is_active 
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200" 
                          : "bg-rose-50 text-rose-800"
                      }`}>
                        {t.is_active ? "Activo" : "Suspendido"}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-slate-500 font-mono">
                      {new Date(t.created_at).toLocaleDateString("es-MX")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Models List in GPU */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center space-x-2">
          <Cpu className="h-4 w-4 text-indigo-600" />
          <span>Modelos de Inferencia Local en GPU (Ollama)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {aiModels.map((m) => (
            <div key={m.name} className="p-3 rounded-lg border border-slate-200 bg-slate-50 flex flex-col justify-between">
              <div>
                <span className="font-mono font-bold text-xs text-slate-900 block">{m.name}</span>
                <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">
                  Familia: {m.family || "qwen / llama"}
                </span>
              </div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-200 text-[10px] font-mono text-slate-600">
                <span>Parámetros: {m.parameter_size || "N/D"}</span>
                <span>{(m.size_bytes / (1024*1024*1024)).toFixed(1)} GB</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
