"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/contexts/auth-context";

export default function HomePage() {
  const { ready, token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!ready) return;
    router.replace(token ? "/dashboard" : "/login");
  }, [ready, token, router]);

  return (
    <div className="flex min-h-screen items-center justify-center text-slate-500">
      Carregando…
    </div>
  );
}
