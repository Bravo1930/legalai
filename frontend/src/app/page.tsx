"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { SystemHealth } from "@/types";
import { 
  ShieldCheck, 
  Cpu, 
  Database, 
  Zap, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Scale, 
  Lock, 
  FileCheck,
  RefreshCw
} from "lucide-react";

export default function HomePage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (err: any) {
      setError(err?.message || "No se pudo conectar con el servidor backend");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen flex flex-col justify-between bg-slate-50">
      {/* Top Navigation */}
      <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-slate-900 text-amber-400 p-2 rounded-xl shadow-xs">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-slate-900">LegalAI</span>
              <span className="text-xs ml-1.5 font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200/80">México</span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <a 
              href="http://127.0.0.1:8000/api/v1/docs" 
              target="_blank" 
              rel="noreferrer" 
              className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
            >
              Documentación API
            </a>
            <Link
              href="/login"
              className="apple-interactive inline-flex items-center space-x-1.5 px-4 py-2 text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-xl shadow-xs"
            >
              <span>Acceder al Despacho</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-1">
        <div className="max-w-3xl mb-12">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-50/80 border border-amber-200/80 text-amber-900 text-xs font-semibold mb-4 backdrop-blur-xs">
            <ShieldCheck className="h-4 w-4 text-amber-600" />
            <span>Supervisión letrada obligatoria • Inferencia local con Ollama • Aislamiento por despacho</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-[-0.03em] leading-[1.12] font-serif-legal">
            Inteligencia Artificial para la Práctica Jurídica en México
          </h1>
          <p className="mt-4 text-lg text-slate-600 leading-relaxed font-sans">
            Plataforma profesional para revisión de contratos, análisis de acuerdos judiciales y extracción documental con sustento en legislación federal, estatal, CDMX y jurisprudencia de la SCJN.
          </p>
          <div className="mt-6 flex flex-wrap gap-4">
            <Link
              href="/login"
              className="apple-interactive px-6 py-3 text-base font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-xl shadow-xs flex items-center space-x-2"
            >
              <span>Iniciar Sesión en el Portal</span>
              <ArrowRight className="h-5 w-5" />
            </Link>
            <button
              onClick={fetchHealth}
              className="apple-interactive px-4 py-3 text-base font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-xl shadow-xs flex items-center space-x-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-amber-600" : ""}`} />
              <span>Verificar Infraestructura</span>
            </button>
          </div>
        </div>

        {/* Live System Diagnostics Grid */}
        <section className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
              <Zap className="h-5 w-5 text-amber-500" />
              <span>Diagnóstico de Infraestructura en Tiempo Real</span>
            </h2>
            <span className="text-xs text-slate-500 font-mono">
              Ambiente: {health?.environment || "Conectando..."}
            </span>
          </div>

          {error && (
            <div className="p-4 mb-6 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-start space-x-3">
              <XCircle className="h-5 w-5 text-rose-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-sm">Error de conexión con Backend</p>
                <p className="text-xs mt-0.5">{error}</p>
                <p className="text-xs mt-2 text-slate-600">Asegúrate de que el backend FastAPI esté en ejecución en <code>http://127.0.0.1:8000</code>.</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Database Card */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-[0_4px_20px_-2px_rgba(15,23,42,0.03)] hover:shadow-[0_8px_30px_-4px_rgba(15,23,42,0.08)] transition-all duration-300 ease-apple-spring hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Database className="h-5 w-5 text-indigo-600" />
                  <h3 className="font-bold text-slate-900">PostgreSQL</h3>
                </div>
                {health?.database.status === "healthy" ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> En línea
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                    <XCircle className="h-3.5 w-3.5 mr-1" /> Offline
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-600 font-mono break-all line-clamp-2">
                {health?.database.version || "Consultando motor relacional..."}
              </p>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span>Extensión pgvector:</span>
                <span className={`font-semibold ${health?.database.pgvector_enabled ? "text-emerald-600" : "text-amber-600"}`}>
                  {health?.database.pgvector_enabled ? "Activa (HNSW)" : "Soporte Híbrido Activo"}
                </span>
              </div>
            </div>

            {/* Redis / Queue Card */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-[0_4px_20px_-2px_rgba(15,23,42,0.03)] hover:shadow-[0_8px_30px_-4px_rgba(15,23,42,0.08)] transition-all duration-300 ease-apple-spring hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Zap className="h-5 w-5 text-rose-600" />
                  <h3 className="font-bold text-slate-900">Redis & Tareas</h3>
                </div>
                {health?.redis.connected ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> En línea
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                    <AlertTriangle className="h-3.5 w-3.5 mr-1" /> Fallback DB
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-600">
                {health?.redis.details || "Broker de procesamiento asíncrono para OCR y embeddings."}
              </p>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span>Mecanismo de Cola:</span>
                <span className="font-semibold text-slate-700">
                  {health?.redis.connected ? "Redis Distributed Broker" : "PostgreSQL Task Queue"}
                </span>
              </div>
            </div>

            {/* Ollama Local AI Card */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-[0_4px_20px_-2px_rgba(15,23,42,0.03)] hover:shadow-[0_8px_30px_-4px_rgba(15,23,42,0.08)] transition-all duration-300 ease-apple-spring hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Cpu className="h-5 w-5 text-emerald-600" />
                  <h3 className="font-bold text-slate-900">Ollama Local</h3>
                </div>
                {health?.ollama.status === "healthy" ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> GPU Activa
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                    <XCircle className="h-3.5 w-3.5 mr-1" /> Inaccesible
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-600 font-mono">
                {health?.ollama.base_url || "http://127.0.0.1:11434"}
              </p>
              <div className="mt-4 pt-3 border-t border-slate-100">
                <span className="text-xs text-slate-500 block mb-1.5">Modelos detectados:</span>
                <div className="flex flex-wrap gap-1">
                  {health?.ollama.models_available.slice(0, 3).map((m) => (
                    <span key={m} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md text-[10px] font-mono">
                      {m}
                    </span>
                  ))}
                  {(health?.ollama.models_available.length || 0) > 3 && (
                    <span className="text-[10px] text-slate-400 self-center">
                      +{health!.ollama.models_available.length - 3} más
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Guarantees Grid */}
        <section className="mt-16 border-t border-slate-200 pt-12">
          <h2 className="text-lg font-bold text-slate-900 mb-6">Principios Obligatorios de la Plataforma</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-start space-x-3">
              <FileCheck className="h-5 w-5 text-slate-700 mt-1 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-bold text-slate-900">Validación Humana Obligatoria</h3>
                <p className="text-xs text-slate-600 mt-1">Ninguna conclusión o redacción de IA surte efecto sin aprobación y cédula profesional de un abogado facultado.</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <Lock className="h-5 w-5 text-slate-700 mt-1 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-bold text-slate-900">Inmutabilidad Criptográfica</h3>
                <p className="text-xs text-slate-600 mt-1">El documento primigenio se almacena bajo SHA-256 en modo WORM. Cada análisis es una versión hija auditable.</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <ShieldCheck className="h-5 w-5 text-slate-700 mt-1 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-bold text-slate-900">Aislamiento por Despacho</h3>
                <p className="text-xs text-slate-600 mt-1">Segregación estricta de base de datos. Ningún usuario o despacho puede acceder a expedientes ni documentos de otras firmas.</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500">
          <p>© 2026 LegalAI México. Sistema de Inteligencia Artificial para Despachos y Firmas Jurídicas. Diseñado para estricto apego al secreto profesional y normativa mexicana.</p>
        </div>
      </footer>
    </div>
  );
}
