/** Headers de segurança HTTP — CSP com nonce por request (sem unsafe-inline/eval em produção). */

export function apiConnectSrc(): string[] {
  const apiOrigin = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    .trim()
    .replace(/\/$/, "");
  const sources = ["'self'", apiOrigin];
  if (apiOrigin.includes("localhost")) {
    sources.push("http://127.0.0.1:8000");
  }
  return sources;
}

/** CSP estrita com nonce — Next.js injeta o nonce nos scripts de hidratação. */
export function buildCspHeader(nonce: string): string {
  const isDev = process.env.NODE_ENV !== "production";
  const connectSrc = apiConnectSrc().join(" ");

  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ""}`,
    `style-src 'self' 'nonce-${nonce}'${isDev ? " 'unsafe-inline'" : ""}`,
    "img-src 'self' data: blob:",
    "font-src 'self'",
    `connect-src ${connectSrc}`,
    "frame-ancestors 'none'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ]
    .join("; ")
    .replace(/\s{2,}/g, " ")
    .trim();
}

/** Headers fixos (sem CSP — definida por request no middleware). */
export const baseSecurityHeaders: { key: string; value: string }[] = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-XSS-Protection", value: "1; mode=block" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), browsing-topics=()",
  },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  { key: "Cross-Origin-Embedder-Policy", value: "credentialless" },
  { key: "Cross-Origin-Resource-Policy", value: "same-origin" },
  {
    key: "Cache-Control",
    value: "private, no-cache, no-store, must-revalidate",
  },
];

/** Headers para chunks estáticos (sem CSP — política aplica-se ao documento HTML). */
export const staticAssetHeaders: { key: string; value: string }[] = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Cross-Origin-Resource-Policy", value: "same-origin" },
  {
    key: "Cache-Control",
    value: "public, max-age=31536000, immutable",
  },
];
