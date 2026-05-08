"use client";

/**
 * Base da API para o navegador.
 * - Com `NEXT_PUBLIC_API_URL` definido (ex.: http://localhost:8000): chamada direta → exige CORS alinhado à origem (localhost vs 127.0.0.1).
 * - Vazio: mesmo host que o Next (`/api/...`) → no Docker o Next faz proxy para o backend e não há CORS.
 */
export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!raw) {
    return "";
  }
  return raw.replace(/\/$/, "");
}

function formatValidationDetail(detail: unknown): string | null {
  if (!Array.isArray(detail) || detail.length === 0) return null;
  const parts = detail.map((item) => {
    if (item && typeof item === "object" && "msg" in item) {
      const loc = Array.isArray((item as { loc?: unknown }).loc)
        ? (item as { loc: unknown[] }).loc.join(".")
        : "";
      const msg = String((item as { msg: string }).msg);
      return loc ? `${loc}: ${msg}` : msg;
    }
    return JSON.stringify(item);
  });
  return parts.join("; ");
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("aai_access_token");
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${getApiBaseUrl()}${path}`, {
    ...options,
    headers,
  });
  if (!res.ok) {
    let message = "Erro de comunicação com a API.";
    const payload = await res.json().catch(() => null);
    if (payload?.detail && typeof payload.detail === "string") {
      message = payload.detail;
    } else if (payload?.detail) {
      const formatted = formatValidationDetail(payload.detail);
      if (formatted) message = formatted;
    }
    throw new Error(message);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}
