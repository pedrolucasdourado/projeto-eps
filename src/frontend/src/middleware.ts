import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { securityHeaders } from "@/lib/security-headers";

export function middleware(_request: NextRequest) {
  const response = NextResponse.next();
  for (const { key, value } of securityHeaders) {
    response.headers.set(key, value);
  }
  return response;
}

/** Páginas e rotas dinâmicas; assets estáticos usam headers() no next.config. */
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)"],
};
