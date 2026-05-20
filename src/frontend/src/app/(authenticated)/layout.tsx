"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/contexts/auth-context";

/**
 * Decide se o papel atual tem permissão para a rota. Mantemos a lista
 * curta porque a maioria das telas serve a vários papéis; só barramos os
 * casos críticos: administrador no módulo ACBA e operacionais em /usuarios.
 */
function isRouteForbidden(role: string, pathname: string): boolean {
  if (role === "administrador") {
    return pathname.startsWith("/acba");
  }
  if (pathname.startsWith("/usuarios")) {
    return role !== "administrador";
  }
  return false;
}

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { ready, token, user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!ready) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    if (user && isRouteForbidden(user.role, pathname)) {
      router.replace(
        user.role === "administrador" ? "/usuarios" : "/dashboard",
      );
    }
  }, [ready, token, user, pathname, router]);

  if (!ready || !token) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Carregando…
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
