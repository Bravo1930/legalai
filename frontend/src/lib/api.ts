import { AuthTokens, SystemHealth, UserProfile, AsyncTask } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

class ApiClient {
  private getAuthHeader(): Record<string, string> {
    if (typeof window === "undefined") return {};
    const token = localStorage.getItem("legal_ai_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${API_BASE_URL}/health`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`Error al consultar salud del backend: ${res.statusText}`);
    }
    return res.json();
  }

  async login(email: string, password: string, tenantSlug?: string): Promise<AuthTokens> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        tenant_slug: tenantSlug || undefined,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      const msg = data?.error?.message || "Error al iniciar sesión";
      throw new Error(msg);
    }

    if (typeof window !== "undefined") {
      localStorage.setItem("legal_ai_token", data.access_token);
      localStorage.setItem("legal_ai_user", JSON.stringify(data.user));
    }

    return data;
  }

  async getMe(): Promise<UserProfile> {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        ...this.getAuthHeader(),
      },
    });

    if (!res.ok) {
      throw new Error("Sesión inválida o expirada");
    }
    return res.json();
  }

  logout(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("legal_ai_token");
      localStorage.removeItem("legal_ai_user");
    }
  }

  getCurrentUser(): UserProfile | null {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem("legal_ai_user");
    return raw ? JSON.parse(raw) : null;
  }

  async listTasks(): Promise<AsyncTask[]> {
    const res = await fetch(`${API_BASE_URL}/tasks`, {
      headers: { ...this.getAuthHeader() },
    });
    if (!res.ok) {
      throw new Error("Error al consultar tareas asíncronas");
    }
    return res.json();
  }

  async enqueueTask(taskType: string, payload?: Record<string, any>): Promise<AsyncTask> {
    const res = await fetch(`${API_BASE_URL}/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
      body: JSON.stringify({ task_type: taskType, payload }),
    });

    if (!res.ok) {
      throw new Error("Error al encolar tarea");
    }
    return res.json();
  }
}

export const api = new ApiClient();
