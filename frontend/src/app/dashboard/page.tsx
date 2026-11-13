"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { UserProfile, AsyncTask } from "@/types";
import { 
  Scale, 
  Building, 
  User as UserIcon, 
  LogOut, 
  FileText, 
  ShieldCheck, 
  FolderLock, 
  BookOpen, 
  History, 
  PlusCircle, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  RefreshCw,
  Cpu
} from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [tasks, setTasks] = useState<AsyncTask[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [enqueueing, setEnqueueing] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    const currentUser = api.getCurrentUser();
    if (!currentUser) {
      router.push("/login");
      return;
    }
    setUser(currentUser);
    loadTasks();
  }, [router]);

  const loadTasks = async () => {
    setLoadingTasks(true);
    try {
      const data = await api.listTasks();
      setTasks(data);
    } catch (err) {
      console.error("Error al cargar tareas:", err);
    } finally {
      setLoadingTasks(false);
    }
  };

  const handleEnqueueTest = async (type: string) => {
    setEnqueueing(true);
    setActionMessage(null);
    try {
      const newTask = await api.enqueueTask(type, {
        document_id: "demo-doc-001",
        pages: 12,
        notes: "Prueba de procesamiento asíncrono desde frontend"
      });
      setActionMessage(`Tarea de tipo ${type} encolada exitosamente (ID: ${newTask.id})`);
      await loadTasks();
    } catch (err: any) {
      setActionMessage(`Error al encolar: ${err?.message || "Fallo de conexión"}`);
    } finally {
      setEnqueueing(false);
    }
  };

  const handleLogout = () => {
    api.logout();
    router.push("/login");
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">Cargando sesión del despacho...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Dashboard Topbar */}
      <nav className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-amber-400 text-slate-900 p-2 rounded-lg font-bold">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight">LegalAI México</span>
              <span className="text-xs text-slate-400 block font-mono">Consola del Despacho</span>
            </div>
          </div>

          <div className="flex items-center space-x-6">
            <div className="hidden md:flex items-center space-x-2 text-xs text-slate-300">
              <Building className="h-4 w-4 text-amber-400" />
              <span className="font-semibold text-white">{user.tenant_name}</span>
              <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400 font-mono">
                {user.tenant_slug}
              </span>
            </div>

            <div className="flex items-center space-x-3 border-l border-slate-800 pl-6">
              <div className="text-right">
                <span className="text-xs font-semibold block text-white">{user.full_name}</span>
                <span className="text-[10px] text-amber-400 font-mono block">{user.role}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Cerrar Sesión"
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Banner */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 mb-2">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              <span>Aislamiento Activo para Despacho: {user.tenant_name}</span>
            </span>
            <h1 className="text-2xl font-bold text-slate-900">
              Bienvenido, {user.full_name}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Cédula Profesional: {user.professional_license || "No registrada"} • Rol en Firma: {user.role}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-500">Sesión autenticada con JWT</span>
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
        </div>

        {/* Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-slate-400 transition-all cursor-pointer">
            <div className="p-2 bg-slate-100 rounded-lg w-fit text-slate-800 mb-3">
              <FolderLock className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Bóveda Inmutable (WORM)</h3>
            <p className="text-xs text-slate-500 mt-1">Expedientes y contratos con hash SHA-256 no sobreescribibles.</p>
            <span className="text-[10px] font-semibold text-amber-700 mt-3 block uppercase tracking-wider">Fase 2 (Próxima)</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-slate-400 transition-all cursor-pointer">
            <div className="p-2 bg-slate-100 rounded-lg w-fit text-slate-800 mb-3">
              <BookOpen className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">RAG Normativo México</h3>
            <p className="text-xs text-slate-500 mt-1">Leyes Federales, Estatales, CDMX y Tesis SCJN.</p>
            <span className="text-[10px] font-semibold text-amber-700 mt-3 block uppercase tracking-wider">Fase 4 (Próxima)</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-slate-400 transition-all cursor-pointer">
            <div className="p-2 bg-slate-100 rounded-lg w-fit text-slate-800 mb-3">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Aprobación HITL</h3>
            <p className="text-xs text-slate-500 mt-1">Firma y validación obligatoria por abogado senior.</p>
            <span className="text-[10px] font-semibold text-amber-700 mt-3 block uppercase tracking-wider">Fase 6 (Próxima)</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-slate-400 transition-all cursor-pointer">
            <div className="p-2 bg-slate-100 rounded-lg w-fit text-slate-800 mb-3">
              <History className="h-5 w-5 text-slate-700" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Auditoría Forense</h3>
            <p className="text-xs text-slate-500 mt-1">Trazabilidad inmutable de accesos, descargas y consultas.</p>
            <span className="text-[10px] font-semibold text-emerald-700 mt-3 block uppercase tracking-wider">Activa (Append-Only)</span>
          </div>
        </div>

        {/* Live Asynchronous Tasks Section */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-4 mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <Cpu className="h-5 w-5 text-slate-700" />
                <span>Cola de Procesamiento Asíncrono (Workers)</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Prueba en vivo de encolado y persistencia en base de datos PostgreSQL y Redis.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleEnqueueTest("OCR_EXTRACTION")}
                disabled={enqueueing}
                className="px-3 py-1.5 text-xs font-semibold text-slate-900 bg-amber-400 hover:bg-amber-300 rounded-lg shadow-sm transition-all flex items-center space-x-1.5 disabled:opacity-50"
              >
                <PlusCircle className="h-4 w-4" />
                <span>Simular Tarea OCR</span>
              </button>

              <button
                onClick={() => handleEnqueueTest("CONTRACT_ANALYSIS")}
                disabled={enqueueing}
                className="px-3 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-sm transition-all flex items-center space-x-1.5 disabled:opacity-50"
              >
                <PlusCircle className="h-4 w-4" />
                <span>Simular Análisis IA</span>
              </button>

              <button
                onClick={loadTasks}
                className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
                title="Refrescar lista"
              >
                <RefreshCw className={`h-4 w-4 ${loadingTasks ? "animate-spin text-amber-600" : ""}`} />
              </button>
            </div>
          </div>

          {actionMessage && (
            <div className="p-3 mb-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
              <span>{actionMessage}</span>
            </div>
          )}

          {tasks.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-xs">No hay tareas asíncronas registradas para este despacho.</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Haz clic en "Simular Tarea OCR" para probar el encolado.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                    <th className="py-2.5 px-3">ID Tarea</th>
                    <th className="py-2.5 px-3">Tipo</th>
                    <th className="py-2.5 px-3">Estado</th>
                    <th className="py-2.5 px-3">Fecha de Creación</th>
                    <th className="py-2.5 px-3">Resultado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {tasks.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-700">{t.id.slice(0, 8)}...</td>
                      <td className="py-2.5 px-3 font-semibold text-slate-900">{t.task_type}</td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          t.status === "COMPLETED" ? "bg-emerald-100 text-emerald-800" :
                          t.status === "PROCESSING" ? "bg-amber-100 text-amber-800 animate-pulse" :
                          t.status === "FAILED" ? "bg-rose-100 text-rose-800" :
                          "bg-slate-100 text-slate-700"
                        }`}>
                          {t.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-500 font-mono">{new Date(t.created_at).toLocaleTimeString()}</td>
                      <td className="py-2.5 px-3 text-slate-600 font-mono text-[11px]">
                        {t.result ? JSON.stringify(t.result).slice(0, 45) + "..." : (t.error_message || "En cola de espera...")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
