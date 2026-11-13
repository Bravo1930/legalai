"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Case, Client } from "@/types";
import { 
  Briefcase, 
  Search, 
  Plus, 
  FolderLock, 
  Building, 
  Calendar, 
  AlertCircle, 
  CheckCircle2, 
  RefreshCw,
  Scale,
  X
} from "lucide-react";

const MATTERS = [
  "MERCANTIL",
  "CIVIL",
  "LABORAL",
  "PENAL",
  "CORPORATIVO",
  "FISCAL",
  "ADMINISTRATIVO",
  "AMPARO",
  "OTRO"
];

export default function CasesView({ userRole }: { userRole?: string }) {
  const [cases, setCases] = useState<Case[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMatter, setSelectedMatter] = useState("");

  // Modal Nuevo Expediente
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    client_id: "",
    case_number: "",
    title: "",
    description: "",
    matter: "MERCANTIL",
    jurisdiction: "FEDERAL",
    state: "ACTIVO",
    court_authority: ""
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [casesList, clientsList] = await Promise.all([
        api.listCases().catch(() => []),
        api.listClients().catch(() => [])
      ]);
      setCases(casesList);
      setClients(clientsList);
      if (clientsList.length > 0 && !formData.client_id) {
        setFormData(prev => ({ ...prev, client_id: clientsList[0].id }));
      }
    } catch (err) {
      console.error("Error al cargar expedientes:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.client_id) {
      setFormError("Debe seleccionar un cliente para vincular el expediente.");
      return;
    }
    setCreating(true);
    setFormError(null);
    setFormSuccess(null);

    try {
      const newCase = await api.createCase(formData);
      setFormSuccess(`Expediente "${newCase.case_number}" creado exitosamente.`);
      await loadData();
      setTimeout(() => {
        setShowModal(false);
        setFormSuccess(null);
      }, 1200);
    } catch (err: any) {
      setFormError(err?.message || "Error al crear el expediente judicial.");
    } finally {
      setCreating(false);
    }
  };

  const filteredCases = cases.filter(c => {
    const matchesSearch = 
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.case_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.court_authority && c.court_authority.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesMatter = selectedMatter ? c.matter === selectedMatter : true;
    return matchesSearch && matchesMatter;
  });

  const getClientName = (clientId: string) => {
    const client = clients.find(cl => cl.id === clientId);
    return client ? client.name : "Cliente no asignado";
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-900 text-amber-400 font-mono mb-1">
            <Briefcase className="h-3.5 w-3.5" />
            <span>Control Litigioso & Corporativo</span>
          </span>
          <h2 className="text-xl font-bold text-slate-900">Expedientes y Asuntos Jurídicos</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Gestión centralizada de litigios, arbitrajes, convenios y asuntos societarios con estricto aislamiento por despacho.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm flex items-center space-x-1.5 flex-shrink-0"
        >
          <Plus className="h-4 w-4 text-amber-400" />
          <span>Nuevo Expediente</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="relative w-full sm:w-96">
          <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por número de expediente, título o juzgado..."
            className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <select
            value={selectedMatter}
            onChange={(e) => setSelectedMatter(e.target.value)}
            className="text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
          >
            <option value="">Todas las materias</option>
            {MATTERS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>

          <button
            onClick={loadData}
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-medium transition-colors flex items-center space-x-1"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
            <span>Actualizar</span>
          </button>
        </div>
      </div>

      {/* Cases Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {filteredCases.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <FolderLock className="h-10 w-10 mx-auto mb-2 opacity-30" />
            <p className="text-sm font-semibold text-slate-700">No se encontraron expedientes registrados.</p>
            <p className="text-xs text-slate-400 mt-1">Haga clic en &quot;Nuevo Expediente&quot; para dar de alta el primer asunto judicial.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                  <th className="py-3 px-4">No. Expediente / Título</th>
                  <th className="py-3 px-4">Cliente Vinculado</th>
                  <th className="py-3 px-4">Materia</th>
                  <th className="py-3 px-4">Juzgado / Autoridad</th>
                  <th className="py-3 px-4">Estado</th>
                  <th className="py-3 px-4">Fecha Apertura</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4">
                      <span className="font-mono font-bold text-slate-900 block">{c.case_number}</span>
                      <span className="text-slate-600 font-medium block mt-0.5">{c.title}</span>
                      {c.description && (
                        <span className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{c.description}</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-slate-800 flex items-center space-x-1">
                        <Building className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                        <span>{getClientName(c.client_id)}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                        {c.matter}
                      </span>
                      <span className="text-[10px] text-slate-400 block font-mono mt-0.5">{c.jurisdiction}</span>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-700">
                      {c.court_authority || "No especificado"}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        c.state === "ACTIVO" 
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200" 
                          : "bg-slate-100 text-slate-700"
                      }`}>
                        {c.state}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-500 font-mono">
                      {new Date(c.created_at).toLocaleDateString("es-MX")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Alta de Expediente */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
              <div className="flex items-center space-x-2">
                <Briefcase className="h-5 w-5 text-amber-400" />
                <h3 className="text-sm font-bold">Aperturar Nuevo Expediente</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCase} className="p-6 space-y-4">
              {formSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                  <span>{formSuccess}</span>
                </div>
              )}

              {formError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Cliente Vinculado <span className="text-rose-600">*</span>
                </label>
                {clients.length === 0 ? (
                  <div className="text-xs text-rose-600 bg-rose-50 p-2 rounded border border-rose-200">
                    No hay clientes registrados en el despacho. Por favor dé de alta un cliente primero.
                  </div>
                ) : (
                  <select
                    value={formData.client_id}
                    onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                    required
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                  >
                    {clients.map((cl) => (
                      <option key={cl.id} value={cl.id}>
                        {cl.name} {cl.rfc ? `(${cl.rfc})` : ""}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Número de Expediente <span className="text-rose-600">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.case_number}
                    onChange={(e) => setFormData({ ...formData, case_number: e.target.value })}
                    placeholder="Ej. EXP-2026/842"
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Materia Jurídica
                  </label>
                  <select
                    value={formData.matter}
                    onChange={(e) => setFormData({ ...formData, matter: e.target.value })}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                  >
                    {MATTERS.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Carátula / Título del Asunto <span className="text-rose-600">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Ej. Juicio Oral Mercantil vs Distribuidora del Norte"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Juzgado, Tribunal o Autoridad
                </label>
                <input
                  type="text"
                  value={formData.court_authority}
                  onChange={(e) => setFormData({ ...formData, court_authority: e.target.value })}
                  placeholder="Ej. Juzgado Cuarto de Distrito en Materia Civil en CDMX"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Descripción o Antecedentes (Opcional)
                </label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Resumen del conflicto o negocio jurídico..."
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
                  disabled={creating}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm disabled:opacity-50"
                >
                  {creating ? "Registrando..." : "Guardar Expediente"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
