"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Client } from "@/types";
import { 
  Building, 
  User, 
  Search, 
  Plus, 
  Mail, 
  Phone, 
  MapPin, 
  AlertCircle, 
  CheckCircle2, 
  RefreshCw,
  X,
  CreditCard
} from "lucide-react";

export default function ClientsView({ userRole }: { userRole?: string }) {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<string>("");

  // Modal Nuevo Cliente
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: "",
    rfc: "",
    curp: "",
    client_type: "PERSONA_MORAL",
    contact_email: "",
    contact_phone: "",
    address: ""
  });

  useEffect(() => {
    loadClients();
  }, []);

  const loadClients = async () => {
    setLoading(true);
    try {
      const data = await api.listClients();
      setClients(data);
    } catch (err) {
      console.error("Error al cargar clientes:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setFormError(null);
    setFormSuccess(null);

    try {
      const newClient = await api.createClient(formData);
      setFormSuccess(`Cliente "${newClient.name}" registrado en el despacho.`);
      await loadClients();
      setTimeout(() => {
        setShowModal(false);
        setFormSuccess(null);
        setFormData({
          name: "",
          rfc: "",
          curp: "",
          client_type: "PERSONA_MORAL",
          contact_email: "",
          contact_phone: "",
          address: ""
        });
      }, 1200);
    } catch (err: any) {
      setFormError(err?.message || "Error al registrar cliente.");
    } finally {
      setCreating(false);
    }
  };

  const filteredClients = clients.filter(c => {
    const matchesSearch = 
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.rfc && c.rfc.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (c.contact_email && c.contact_email.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = selectedType ? c.client_type === selectedType : true;
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-900 text-amber-400 font-mono mb-1">
            <Building className="h-3.5 w-3.5" />
            <span>Directorio de Clientes del Despacho</span>
          </span>
          <h2 className="text-xl font-bold text-slate-900">Padrón de Clientes</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Registro de personas físicas y morales con validación de RFC/CURP e histórico de instrumentos.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm flex items-center space-x-1.5 flex-shrink-0"
        >
          <Plus className="h-4 w-4 text-amber-400" />
          <span>Registrar Cliente</span>
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
            placeholder="Buscar por razón social, nombre, RFC o correo..."
            className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
          >
            <option value="">Todos los tipos</option>
            <option value="PERSONA_MORAL">Persona Moral (Empresa)</option>
            <option value="PERSONA_FISICA">Persona Física</option>
          </select>

          <button
            onClick={loadClients}
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-medium transition-colors flex items-center space-x-1"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
            <span>Actualizar</span>
          </button>
        </div>
      </div>

      {/* Clients Cards Grid */}
      {filteredClients.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400 shadow-sm">
          <Building className="h-10 w-10 mx-auto mb-2 opacity-30" />
          <p className="text-sm font-semibold text-slate-700">No se encontraron clientes registrados.</p>
          <p className="text-xs text-slate-400 mt-1">Haga clic en &quot;Registrar Cliente&quot; para añadir la primera entidad.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredClients.map((client) => (
            <div
              key={client.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 hover:shadow-sm transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    client.client_type === "PERSONA_MORAL"
                      ? "bg-slate-900 text-amber-400"
                      : "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  }`}>
                    {client.client_type === "PERSONA_MORAL" ? "Persona Moral" : "Persona Física"}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(client.created_at).toLocaleDateString("es-MX")}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-900 mb-1">{client.name}</h3>

                <div className="space-y-1.5 my-3 text-xs text-slate-600">
                  {client.rfc && (
                    <div className="flex items-center space-x-2 font-mono">
                      <CreditCard className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                      <span className="font-semibold text-slate-800">RFC: {client.rfc}</span>
                    </div>
                  )}

                  {client.curp && (
                    <div className="flex items-center space-x-2 font-mono">
                      <CreditCard className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                      <span>CURP: {client.curp}</span>
                    </div>
                  )}

                  {client.contact_email && (
                    <div className="flex items-center space-x-2 truncate">
                      <Mail className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                      <a href={`mailto:${client.contact_email}`} className="text-indigo-600 hover:underline truncate">
                        {client.contact_email}
                      </a>
                    </div>
                  )}

                  {client.contact_phone && (
                    <div className="flex items-center space-x-2">
                      <Phone className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                      <span>{client.contact_phone}</span>
                    </div>
                  )}

                  {client.address && (
                    <div className="flex items-start space-x-2 text-[11px] text-slate-500 pt-1">
                      <MapPin className="h-3.5 w-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
                      <span className="line-clamp-2">{client.address}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px]">
                <span className="text-emerald-700 font-medium flex items-center space-x-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-600"></span>
                  <span>Activo en despacho</span>
                </span>
                <span className="text-slate-400 font-mono text-[10px]">ID: {client.id.slice(0, 8)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Alta de Cliente */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
              <div className="flex items-center space-x-2">
                <Building className="h-5 w-5 text-amber-400" />
                <h3 className="text-sm font-bold">Registrar Nuevo Cliente</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateClient} className="p-6 space-y-4">
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

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Tipo de Persona <span className="text-rose-600">*</span>
                  </label>
                  <select
                    value={formData.client_type}
                    onChange={(e) => setFormData({ ...formData, client_type: e.target.value })}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                  >
                    <option value="PERSONA_MORAL">Persona Moral (Sociedad)</option>
                    <option value="PERSONA_FISICA">Persona Física</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    RFC Mexicano
                  </label>
                  <input
                    type="text"
                    value={formData.rfc}
                    onChange={(e) => setFormData({ ...formData, rfc: e.target.value.toUpperCase() })}
                    placeholder="Ej. ABC010203XYZ"
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono uppercase"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Razón Social o Nombre Completo <span className="text-rose-600">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ej. Inmobiliaria del Centro S.A. de C.V."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Correo Electrónico de Contacto
                  </label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                    placeholder="contacto@empresa.com"
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Teléfono
                  </label>
                  <input
                    type="tel"
                    value={formData.contact_phone}
                    onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                    placeholder="Ej. +52 55 1234 5678"
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Domicilio Fiscal o Convencional
                </label>
                <textarea
                  rows={2}
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Calle, número, colonia, alcaldía/municipio, C.P., estado..."
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
                  {creating ? "Registrando..." : "Guardar Cliente"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
