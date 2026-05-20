"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getApiBaseUrl } from "@/lib/api";

export type UserRole = "administrador" | "delegado" | "escrivao" | "agente";

export type AuthUser = {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  ativo: boolean;
  delegado_id: number | null;
  escrivao_id: number | null;
  agente_id: number | null;
};

type AuthContextValue = {
  token: string | null;
  user: AuthUser | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "aai_access_token";
const USER_KEY = "aai_user";

function parseApiErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  return "Não foi possível entrar. Verifique suas credenciais.";
}

/**
 * Aceita o payload retornado pelo backend ou guardado em localStorage
 * (que pode estar em formato antigo, sem `role`). Aplica defaults seguros.
 */
function normalizeAuthUser(raw: unknown): AuthUser {
  const obj = (raw ?? {}) as Record<string, unknown>;
  return {
    id: Number(obj.id),
    email: String(obj.email ?? ""),
    full_name: typeof obj.full_name === "string" ? obj.full_name : null,
    role:
      (obj.role as UserRole | undefined) === "delegado" ||
      obj.role === "escrivao" ||
      obj.role === "agente" ||
      obj.role === "administrador"
        ? (obj.role as UserRole)
        : "administrador",
    ativo: obj.ativo !== false,
    delegado_id:
      typeof obj.delegado_id === "number" ? obj.delegado_id : null,
    escrivao_id:
      typeof obj.escrivao_id === "number" ? obj.escrivao_id : null,
    agente_id: typeof obj.agente_id === "number" ? obj.agente_id : null,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);
    if (storedToken && storedUser) {
      try {
        const parsed = normalizeAuthUser(JSON.parse(storedUser));
        setToken(storedToken);
        setUser(parsed);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      }
    }
    setReady(true);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const url = `${getApiBaseUrl()}/api/auth/login`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(parseApiErrorDetail(data.detail));
    }
    const normalized = normalizeAuthUser(data.user);
    setToken(data.access_token);
    setUser(normalized);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(normalized));
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      ready,
      login,
      logout,
    }),
    [token, user, ready, login, logout],
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider.");
  }
  return ctx;
}
