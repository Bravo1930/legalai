from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, tenants, users, tasks, clients, cases, documents, ai, rules, advanced_analysis

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Salud & Diagnóstico"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación & Sesión"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Despachos Jurídicos (Tenants)"])
api_router.include_router(users.router, prefix="/users", tags=["Usuarios & Abogados"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tareas Asíncronas"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clientes del Despacho"])
api_router.include_router(cases.router, prefix="/cases", tags=["Expedientes & Asuntos Jurídicos"])
api_router.include_router(documents.router, prefix="/documents", tags=["Gestor Documental Inmutable (WORM)"])
api_router.include_router(ai.router, prefix="/ai", tags=["Agentes de Inteligencia Artificial (Ollama Local)"])
api_router.include_router(rules.router, prefix="/rules", tags=["Motor de Reglas Deterministas"])
api_router.include_router(advanced_analysis.router, prefix="/advanced-analysis", tags=["Motor Avanzado de Análisis Jurídico"])
