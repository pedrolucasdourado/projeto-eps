import type { NextConfig } from "next";

import { staticAssetHeaders } from "./src/lib/security-headers";

/** No Docker, use INTERNAL_API_URL=http://backend:8000 para o proxy de /api e evitar CORS. */
const internalApi = process.env.INTERNAL_API_URL?.trim();
const basePath = (process.env.NEXT_PUBLIC_BASE_PATH ?? "")
  .trim()
  .replace(/\/$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  ...(basePath ? { basePath } : {}),
  async headers() {
    return [
      {
        source: "/_next/static/:path*",
        headers: staticAssetHeaders,
      },
    ];
  },
  async rewrites() {
    if (!internalApi) {
      return [];
    }
    const base = internalApi.replace(/\/$/, "");
    return [
      {
        source: "/api/:path*",
        destination: `${base}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
