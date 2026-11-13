"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { WorkflowNotification } from "@/types";
import { 
  Bell, 
  CheckCheck, 
  Clock, 
  AlertCircle, 
  CheckCircle2, 
  RefreshCw, 
  MailOpen, 
  Mail,
  Filter
} from "lucide-react";

export default function NotificationsView() {
  const [notifications, setNotifications] = useState<WorkflowNotification[]>([]);
  const [loading, setLoading] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [markingAll, setMarkingAll] = useState(false);

  useEffect(() => {
    loadNotifications();
  }, [unreadOnly]);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await api.listNotifications(unreadOnly);
      setNotifications(data);
    } catch (err) {
      console.error("Error al cargar notificaciones:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error("Error al marcar como leída:", err);
    }
  };

  const handleMarkAll = async () => {
    setMarkingAll(true);
    try {
      await api.markAllNotificationsRead();
      await loadNotifications();
    } catch (err) {
      console.error("Error al marcar todas leídas:", err);
    } finally {
      setMarkingAll(false);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-900 text-amber-400 font-mono mb-1">
            <Bell className="h-3.5 w-3.5" />
            <span>Centro de Alertas & Vencimientos</span>
          </span>
          <h2 className="text-xl font-bold text-slate-900">Buzón de Notificaciones Jurídicas</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Avisos de transiciones de workflow, asignaciones de expedientes, solicitudes de corrección y plazos fatales.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleMarkAll}
            disabled={markingAll || unreadCount === 0}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5 disabled:opacity-50"
          >
            <CheckCheck className="h-4 w-4 text-emerald-600" />
            <span>Marcar todas leídas</span>
          </button>

          <button
            onClick={loadNotifications}
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
            <span>Actualizar</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setUnreadOnly(false)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              !unreadOnly 
                ? "bg-slate-900 text-white" 
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            Todas ({notifications.length})
          </button>
          <button
            onClick={() => setUnreadOnly(true)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              unreadOnly 
                ? "bg-slate-900 text-white" 
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            Solo no leídas
          </button>
        </div>

        <span className="text-xs text-slate-500 font-mono">
          {unreadCount} pendiente(s) de atención
        </span>
      </div>

      {/* Notification List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
        {notifications.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <MailOpen className="h-10 w-10 mx-auto mb-2 opacity-30 text-slate-500" />
            <p className="text-sm font-semibold text-slate-700">No hay notificaciones en la bandeja.</p>
            <p className="text-xs text-slate-400 mt-1">Las alertas procesales y solicitudes de revisión aparecerán aquí.</p>
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => !n.is_read && handleMarkAsRead(n.id)}
              className={`p-4 flex items-start justify-between gap-4 transition-colors cursor-pointer ${
                !n.is_read ? "bg-amber-50/40 hover:bg-amber-50/60" : "hover:bg-slate-50 text-slate-600"
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className={`p-2 rounded-lg mt-0.5 ${
                  !n.is_read ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-500"
                }`}>
                  {!n.is_read ? <Mail className="h-4 w-4" /> : <MailOpen className="h-4 w-4" />}
                </div>

                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className={`text-xs ${!n.is_read ? "font-bold text-slate-900" : "font-semibold text-slate-700"}`}>
                      {n.title}
                    </h4>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 uppercase">
                      {n.notification_type}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 mt-1 leading-relaxed max-w-2xl">
                    {n.message}
                  </p>
                </div>
              </div>

              <div className="text-right flex-shrink-0">
                <span className="text-[10px] font-mono text-slate-400 block">
                  {new Date(n.created_at).toLocaleString("es-MX", {
                    dateStyle: "short",
                    timeStyle: "short"
                  })}
                </span>
                {!n.is_read && (
                  <span className="inline-block mt-1 h-2 w-2 rounded-full bg-amber-500" title="No leída"></span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
