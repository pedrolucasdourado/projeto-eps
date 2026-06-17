import type { NextConfig } from "next";

/** No Docker, use INTERNAL_API_URL=http://backend:8000 para o proxy de /api e evitar CORS. */
const internalApi = process.env.INTERNAL_API_URL?.trim();
const basePath = (process.env.NEXT_PUBLIC_BASE_PATH ?? "")
  .trim()
  .replace(/\/$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  ...(basePath ? { basePath } : {}),
  eslint: {
    ignoreDuringBuilds: true,
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
