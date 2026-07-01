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

const permissionsPolicy =
  "camera=(), microphone=(), geolocation=(), browsing-topics=()";

/** Headers comuns a respostas que não são documentos HTML. */
export const resourceSecurityHeaders: { key: string; value: string }[] = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  {
    key: "Permissions-Policy",
    value: permissionsPolicy,
  },
  { key: "Cross-Origin-Resource-Policy", value: "same-origin" },
];

/** Headers fixos para páginas HTML (sem CSP — definida por request no middleware). */
export const baseSecurityHeaders: { key: string; value: string }[] = [
  ...resourceSecurityHeaders,
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-XSS-Protection", value: "1; mode=block" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  { key: "Cross-Origin-Embedder-Policy", value: "credentialless" },
  {
    key: "Cache-Control",
    value: "private, no-cache, must-revalidate",
  },
];

/** Chunks e assets versionados (_next/static, fontes, imagens públicas). */
export const staticAssetHeaders: { key: string; value: string }[] = [
  ...resourceSecurityHeaders,
  {
    key: "Cache-Control",
    value: "public, max-age=31536000, immutable",
  },
];

/** robots.txt, sitemap.xml — públicos e cacheáveis. */
export const publicTextHeaders: { key: string; value: string }[] = [
  ...resourceSecurityHeaders,
  {
    key: "Cache-Control",
    value: "public, max-age=86400",
  },
];

export function isPublicTextPath(pathname: string): boolean {
  return pathname === "/robots.txt" || pathname === "/sitemap.xml";
}

export function isStaticResourcePath(pathname: string): boolean {
  if (pathname.startsWith("/_next/static")) {
    return true;
  }
  return /\.(?:png|jpe?g|gif|webp|ico|svg|woff2|js|css|txt|xml)$/i.test(pathname);
}
