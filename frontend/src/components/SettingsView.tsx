"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Tenant, UserProfile } from "@/types";
import { 
  Settings, 
  Building, 
  ShieldCheck, 
  Webhook, 
  Key, 
  Save, 
  CheckCircle2, 
  AlertCircle, 
  Cpu, 
  Scale, 
  Lock,
  RefreshCw
} from "lucide-react";

interface SettingsViewProps {
  user: UserProfile;
}

export default function SettingsView({ user }: SettingsViewProps) {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form profile
  const [name, setName] = useState("");
  const [rfc, setRfc] = useState("");
  const [contactEmail, setContactEmail] = useState("");

  // Assistant Delegation Policy
  const [allowAssistantDrafts, setAllowAssistantDrafts] = useState(false);

  // Webhooks
  const [webhookUrl, setWebhookUrl] = useState("https://api.despacho.com.mx/webhooks/legal-ai");
  const [webhookSecret, setWebhookSecret] = useState("sec_hmac_948fbc204812ae93108df");

  const canEdit = user.role === "SUPER_ADMIN" || user.role === "MANAGING_PARTNER";

  useEffect(() => {
    loadTenantData();
  }, []);

  const loadTenantData = async () => {
    setLoading(true);
    try {
      const data = await api.getCurrentTenant();
      setTenant(data);
      setName(data.name);
      setRfc(data.rfc || "");
      setContactEmail(data.contact_email);
    } catch (err) {
      console.error("Error al cargar datos del despacho:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const updated = await api.updateCurrentTenant({
        name: name.trim(),
        rfc: rfc.trim().toUpperCase() || undefined,
        contact_email: contactEmail.trim()
      });
      setTenant(updated);
      setSuccessMsg("Información corporativa del despacho actualizada correctamente.");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setErrorMsg(err?.message || "Error al actualizar la configuración.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-900 text-amber-400 font-mono mb-1">
          <Settings className="h-3.5 w-3.5" />
          <span>Gobernanza & Parámetros Operativos</span>
        </span>
        <h2 className="text-xl font-bold text-slate-900">Configuración del Despacho</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Parámetros de identidad legal, políticas de delegación, integración de webhooks y seguridad de la firma.
        </p>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center space-x-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Grid Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Panel 1: Perfil de la Firma */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 pb-3 border-b border-slate-100 mb-4">
              <Building className="h-4 w-4 text-amber-600" />
              <h3 className="text-sm font-bold text-slate-900">Identidad Corporativa & Fiscal</h3>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Nombre o Razón Social del Despacho
                </label>
                <input
                  type="text"
                  required
                  disabled={!canEdit}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 disabled:bg-slate-50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  RFC de la Firma (México)
                </label>
                <input
                  type="text"
                  disabled={!canEdit}
                  value={rfc}
                  onChange={(e) => setRfc(e.target.value.toUpperCase())}
                  placeholder="Ej. BGA050810XYZ"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono uppercase disabled:bg-slate-50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Correo Electrónico Institucional
                </label>
                <input
                  type="email"
                  required
                  disabled={!canEdit}
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 disabled:bg-slate-50"
                />
              </div>

              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-[11px] text-slate-600 font-mono space-y-1">
                <div>Tenant ID: {tenant?.id || "N/D"}</div>
                <div>Slug de Acceso: {tenant?.slug || "N/D"}</div>
                <div>Aislamiento Lógico: PostgreSQL Schema Partitioning</div>
              </div>

              {canEdit && (
                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm flex items-center space-x-1.5 disabled:opacity-50"
                  >
                    <Save className="h-4 w-4 text-amber-400" />
                    <span>{saving ? "Guardando..." : "Actualizar Perfil"}</span>
                  </button>
                </div>
              )}
            </form>
          </div>
        </div>

        {/* Panel 2: Políticas de Delegación y Gobernanza */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
              <Scale className="h-4 w-4 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Políticas de Delegación & Firma</h3>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-900">Delegación a Asistentes Jurídicos</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Permite que los pasantes y asistentes autorizados emitan vistos buenos intermedios de formato sin alcance definitivo.
                  </p>
                </div>
                <input
                  type="checkbox"
                  disabled={!canEdit}
                  checked={allowAssistantDrafts}
                  onChange={(e) => setAllowAssistantDrafts(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-900 mt-1 cursor-pointer"
                />
              </div>

              <div className="text-[10px] text-slate-500 bg-white p-2 rounded border border-slate-200 font-mono">
                Regla RBAC: Toda aprobación definitiva a clientes siempre requerirá cédula profesional de Abogado Senior o Socio.
              </div>
            </div>

            {/* Webhooks & API Integration */}
            <div className="pt-2">
              <div className="flex items-center space-x-2 mb-2">
                <Webhook className="h-4 w-4 text-emerald-600" />
                <h4 className="text-xs font-bold text-slate-900">Webhooks Salientes (HMAC SHA-256)</h4>
              </div>

              <div className="space-y-2">
                <div>
                  <label className="block text-[10px] font-semibold text-slate-600 mb-0.5">
                    Endpoint de Notificaciones (Eventos de Workflow & Aprobaciones)
                  </label>
                  <input
                    type="url"
                    disabled={!canEdit}
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono disabled:bg-slate-50"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-semibold text-slate-600 mb-0.5">
                    Firma Criptográfica Secreta
                  </label>
                  <div className="relative">
                    <input
                      type="password"
                      disabled
                      value={webhookSecret}
                      className="w-full text-xs p-2 border border-slate-300 rounded-lg font-mono bg-slate-50 text-slate-500"
                    />
                    <Key className="h-3.5 w-3.5 absolute right-3 top-2.5 text-slate-400" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>Motor: Ollama Local In-House</span>
            <span>Seguridad: Cifrado en Reposo & Tránsito</span>
          </div>
        </div>
      </div>
    </div>
  );
}
