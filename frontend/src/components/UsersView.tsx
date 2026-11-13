"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { UserProfile } from "@/types";
import { 
  Users, 
  UserPlus, 
  ShieldCheck, 
  Search, 
  Mail, 
  Key, 
  RefreshCw, 
  Scale, 
  CheckCircle2, 
  AlertCircle,
  X,
  Building
} from "lucide-react";

export default function UsersView({ userRole }: { userRole?: string }) {
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRole, setSelectedRole] = useState("");

  // Modal Alta de Usuario
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "ASSOCIATE_LAWYER",
    bar_license_number: ""
  });

  const canManageUsers = userRole === "SUPER_ADMIN" || userRole === "MANAGING_PARTNER";

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await api.listUsers();
      setUsers(data);
    } catch (err) {
      console.error("Error al cargar equipo:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setFormError(null);
    setFormSuccess(null);

    try {
      const newUser = await api.createUser({
        email: formData.email.trim(),
        password: formData.password,
        full_name: formData.full_name.trim(),
        role: formData.role,
        bar_license_number: formData.bar_license_number.trim() || undefined
      });

      setFormSuccess(`Usuario "${newUser.full_name}" creado con rol ${newUser.role}.`);
      await loadUsers();
      setTimeout(() => {
        setShowModal(false);
        setFormSuccess(null);
        setFormData({
          email: "",
          password: "",
          full_name: "",
          role: "ASSOCIATE_LAWYER",
          bar_license_number: ""
        });
      }, 1200);
    } catch (err: any) {
      setFormError(err?.message || "Error al crear el usuario.");
    } finally {
      setCreating(false);
    }
  };

  const filteredUsers = users.filter(u => {
    const q = searchQuery.toLowerCase();
    const matchesSearch = 
      u.full_name.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      (u.bar_license_number && u.bar_license_number.toLowerCase().includes(q));
    const matchesRole = selectedRole ? u.role === selectedRole : true;
    return matchesSearch && matchesRole;
  });

  const getRoleBadge = (role: string) => {
    switch (role) {
      case "MANAGING_PARTNER":
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">Socio Director</span>;
      case "SENIOR_LAWYER":
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-900 border border-purple-300">Abogado Senior</span>;
      case "ASSOCIATE_LAWYER":
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-900 border border-blue-300">Abogado Asociado</span>;
      case "LEGAL_ASSISTANT":
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-300">Asistente Jurídico</span>;
      case "SUPER_ADMIN":
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-900 border border-rose-300">Super Admin</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800">{role}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-900 text-amber-400 font-mono mb-1">
            <Users className="h-3.5 w-3.5" />
            <span>Gestión del Despacho & RBAC</span>
          </span>
          <h2 className="text-xl font-bold text-slate-900">Equipo Jurídico y Usuarios</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Administración de credenciales, roles deontológicos, cédulas profesionales y permisos de aprobación.
          </p>
        </div>

        {canManageUsers && (
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm flex items-center space-x-1.5 flex-shrink-0"
          >
            <UserPlus className="h-4 w-4 text-amber-400" />
            <span>Nuevo Integrante</span>
          </button>
        )}
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="relative w-full sm:w-96">
          <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por nombre, correo o cédula profesional..."
            className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
          >
            <option value="">Todos los roles</option>
            <option value="MANAGING_PARTNER">Socio Director</option>
            <option value="SENIOR_LAWYER">Abogado Senior</option>
            <option value="ASSOCIATE_LAWYER">Abogado Asociado</option>
            <option value="LEGAL_ASSISTANT">Asistente Jurídico</option>
          </select>

          <button
            onClick={loadUsers}
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
            <span>Actualizar</span>
          </button>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-600 font-semibold text-left">
                <th className="py-3 px-4">Nombre / Correo</th>
                <th className="py-3 px-4">Rol en Despacho</th>
                <th className="py-3 px-4">Cédula Profesional</th>
                <th className="py-3 px-4">Estado</th>
                <th className="py-3 px-4">Fecha de Alta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredUsers.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4">
                    <span className="font-bold text-slate-900 block">{u.full_name}</span>
                    <span className="text-[11px] text-slate-500 font-mono flex items-center space-x-1 mt-0.5">
                      <Mail className="h-3 w-3 text-slate-400" />
                      <span>{u.email}</span>
                    </span>
                  </td>

                  <td className="py-3 px-4">
                    {getRoleBadge(u.role)}
                  </td>

                  <td className="py-3 px-4 font-mono">
                    {u.bar_license_number || u.professional_license ? (
                      <span className="font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        {u.bar_license_number || u.professional_license}
                      </span>
                    ) : (
                      <span className="text-slate-400 italic">No registrada</span>
                    )}
                  </td>

                  <td className="py-3 px-4">
                    <span className="inline-flex items-center space-x-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-bold text-[10px] border border-emerald-200">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-600"></span>
                      <span>Activo</span>
                    </span>
                  </td>

                  <td className="py-3 px-4 text-slate-500 font-mono">
                    {new Date(u.created_at || Date.now()).toLocaleDateString("es-MX")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Alta de Usuario */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
              <div className="flex items-center space-x-2">
                <UserPlus className="h-5 w-5 text-amber-400" />
                <h3 className="text-sm font-bold">Registrar Integrante del Despacho</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="p-6 space-y-4">
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
                  Nombre Completo <span className="text-rose-600">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="Ej. Lic. Fernando Martínez Rivas"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Correo Electrónico Institucional <span className="text-rose-600">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="fmartinez@despacho.com"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Contraseña Inicial <span className="text-rose-600">*</span>
                </label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Mínimo 8 caracteres"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Rol Asignado
                  </label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                  >
                    <option value="MANAGING_PARTNER">Socio Director</option>
                    <option value="SENIOR_LAWYER">Abogado Senior</option>
                    <option value="ASSOCIATE_LAWYER">Abogado Asociado</option>
                    <option value="LEGAL_ASSISTANT">Asistente Jurídico</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Cédula Profesional
                  </label>
                  <input
                    type="text"
                    value={formData.bar_license_number}
                    onChange={(e) => setFormData({ ...formData, bar_license_number: e.target.value })}
                    placeholder="Ej. 12948210"
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono"
                  />
                </div>
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
                  {creating ? "Registrando..." : "Crear Usuario"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
