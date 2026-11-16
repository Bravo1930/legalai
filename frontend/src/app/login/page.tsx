"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Scale, Lock, Mail, Building, ArrowRight, AlertCircle, ArrowLeft, Search, FileText, Shield } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("abogado@bufetemexico.demo");
  const [password, setPassword] = useState("Password1234!");
  const [tenantSlug, setTenantSlug] = useState("despacho-demo");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setPresetUser = (pEmail: string, pPass: string, pSlug: string) => {
    setEmail(pEmail);
    setPassword(pPass);
    setTenantSlug(pSlug);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.login(email, password, tenantSlug);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.message || "Error al autenticar con el servidor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/" className="inline-flex items-center space-x-2 text-xs font-medium text-slate-500 hover:text-slate-800 mb-6 transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Volver al inicio</span>
        </Link>
        <div className="flex justify-center">
          <div className="bg-slate-900 text-amber-400 p-3 rounded-xl shadow-sm">
            <Scale className="h-8 w-8" />
          </div>
        </div>
        <h2 className="mt-4 text-center text-2xl font-bold tracking-tight text-slate-900">
          Acceso al Despacho Jurídico
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500">
          Acceso autenticado por despacho con control de roles (RBAC)
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white/95 backdrop-blur-xl py-8 px-4 shadow-[0_8px_30px_-4px_rgba(15,23,42,0.06)] sm:rounded-2xl sm:px-10 border border-slate-200/80">
          {error && (
            <div className="mb-6 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2">
              <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Identificador del Despacho (Slug)
              </label>
              <div className="relative rounded-md shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Building className="h-4 w-4" />
                </div>
                <input
                  type="text"
                  required
                  value={tenantSlug}
                  onChange={(e) => setTenantSlug(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900/15 focus:border-slate-900 transition-all"
                  placeholder="ej. despacho-demo"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Correo Electrónico
              </label>
              <div className="relative rounded-md shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900/15 focus:border-slate-900 transition-all"
                  placeholder="abogado@despacho.mx"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Contraseña
              </label>
              <div className="relative rounded-md shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900/15 focus:border-slate-900 transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="apple-interactive w-full flex justify-center items-center space-x-2 py-2.5 px-4 rounded-xl shadow-xs text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-all disabled:opacity-50"
              >
                <span>{loading ? "Validando credenciales..." : "Iniciar Sesión"}</span>
                {!loading && <ArrowRight className="h-4 w-4" />}
              </button>
            </div>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-100">
            <p className="text-[11px] font-semibold text-slate-700 mb-2">Acceso rápido por perfil de prueba:</p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPresetUser("abogado@bufetemexico.demo", "Password1234!", "despacho-demo")}
                className="text-left p-2 rounded-lg bg-amber-50 hover:bg-amber-100/80 border border-amber-200 text-amber-900 transition-all flex flex-col gap-0.5"
              >
                <div className="flex items-center space-x-1.5">
                  <Scale className="h-3.5 w-3.5 text-amber-700 flex-shrink-0" />
                  <span className="font-bold text-[11px]">Abogado Titular</span>
                </div>
                <span className="text-[10px] text-slate-600 font-mono truncate">abogado@bufetemexico.demo</span>
              </button>

              <button
                type="button"
                onClick={() => setPresetUser("admin@bufetemexico.demo", "Password1234!", "despacho-demo")}
                className="text-left p-2 rounded-lg bg-blue-50 hover:bg-blue-100/80 border border-blue-200 text-blue-900 transition-all flex flex-col gap-0.5"
              >
                <div className="flex items-center space-x-1.5">
                  <Building className="h-3.5 w-3.5 text-blue-700 flex-shrink-0" />
                  <span className="font-bold text-[11px]">Socio Administrador</span>
                </div>
                <span className="text-[10px] text-slate-600 font-mono truncate">admin@bufetemexico.demo</span>
              </button>

              <button
                type="button"
                onClick={() => setPresetUser("revisor@bufetemexico.demo", "Password1234!", "despacho-demo")}
                className="text-left p-2 rounded-lg bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-200 text-emerald-900 transition-all flex flex-col gap-0.5"
              >
                <div className="flex items-center space-x-1.5">
                  <Search className="h-3.5 w-3.5 text-emerald-700 flex-shrink-0" />
                  <span className="font-bold text-[11px]">Abogado Revisor</span>
                </div>
                <span className="text-[10px] text-slate-600 font-mono truncate">revisor@bufetemexico.demo</span>
              </button>

              <button
                type="button"
                onClick={() => setPresetUser("asistente@bufetemexico.demo", "Password1234!", "despacho-demo")}
                className="text-left p-2 rounded-lg bg-purple-50 hover:bg-purple-100/80 border border-purple-200 text-purple-900 transition-all flex flex-col gap-0.5"
              >
                <div className="flex items-center space-x-1.5">
                  <FileText className="h-3.5 w-3.5 text-purple-700 flex-shrink-0" />
                  <span className="font-bold text-[11px]">Asistente Legal</span>
                </div>
                <span className="text-[10px] text-slate-600 font-mono truncate">asistente@bufetemexico.demo</span>
              </button>
            </div>

            <div className="mt-2.5 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setPresetUser("admin@legalai.mx", "Admin1234!", "despacho-demo")}
                className="w-full text-left p-2 rounded-lg bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-800 transition-all"
              >
                <div className="flex items-center space-x-1.5">
                  <Shield className="h-3.5 w-3.5 text-slate-700 flex-shrink-0" />
                  <span className="font-bold text-[11px]">Superadministrador de Plataforma</span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono block mt-0.5">admin@legalai.mx (Control plane, sin acceso a expedientes privados)</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
