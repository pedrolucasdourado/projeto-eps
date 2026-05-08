import type { NextConfig } from "next";

/** No Docker, use INTERNAL_API_URL=http://backend:8000 para o proxy de /api e evitar CORS. */
const internalApi = process.env.INTERNAL_API_URL?.trim();

const nextConfig: NextConfig = {
  output: "standalone",
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
