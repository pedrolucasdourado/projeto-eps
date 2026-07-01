import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import {
  baseSecurityHeaders,
  buildCspHeader,
  isPublicTextPath,
  isStaticResourcePath,
  publicTextHeaders,
  staticAssetHeaders,
} from "@/lib/security-headers";

function applyHeaders(
  response: NextResponse,
  headers: { key: string; value: string }[],
) {
  response.headers.delete("cache-control");
  response.headers.delete("Cache-Control");
  for (const { key, value } of headers) {
    response.headers.set(key, value);
  }
  return response;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (isPublicTextPath(pathname)) {
    return applyHeaders(NextResponse.next(), publicTextHeaders);
  }

  if (isStaticResourcePath(pathname)) {
    return applyHeaders(NextResponse.next(), staticAssetHeaders);
  }

  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const csp = buildCspHeader(nonce);

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  });

  response.headers.set("Content-Security-Policy", csp);
  applyHeaders(response, baseSecurityHeaders);

  return response;
}

/** _next/image é otimizado pelo Next; demais rotas passam pelo middleware. */
export const config = {
  matcher: ["/((?!_next/image).*)"],
};
