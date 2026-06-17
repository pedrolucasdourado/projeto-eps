"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/contexts/auth-context";
import { publicPath } from "@/lib/public-path";

export default function LoginPage() {
  const { ready, token, login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!ready) return;
    if (token) router.replace("/dashboard");
  }, [ready, token, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao entrar.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-shell-bg px-4">
      <div className="w-full max-w-md rounded-2xl border border-shell-border bg-shell-surface p-8 shadow-2xl">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <Image
            src={publicPath("/logo.png")}
            alt="Assistente de Apreensão Inteligente"
            width={72}
            height={72}
            className="rounded-lg border border-shell-border bg-shell-sidebar p-2"
            priority
          />
          <div>
            <h1 className="text-xl font-semibold text-shell-text">
              Assistente de Apreensão Inteligente
            </h1>
            <p className="mt-1 text-sm text-shell-muted">
              Acesso restrito ao ambiente operacional
            </p>
          </div>
        </div>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium text-shell-text"
            >
              E-mail
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(ev) => setEmail(ev.target.value)}
              className="w-full rounded-lg border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text shadow-sm outline-none transition focus:border-shell-accent focus:ring-1 focus:ring-shell-accent"
              placeholder="seu@email.com"
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-sm font-medium text-shell-text"
            >
              Senha
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(ev) => setPassword(ev.target.value)}
              className="w-full rounded-lg border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text shadow-sm outline-none transition focus:border-shell-accent focus:ring-1 focus:ring-shell-accent"
              placeholder="••••••••"
            />
          </div>

          {error ? (
            <p className="rounded-md border border-red-700/50 bg-red-950/40 px-3 py-2 text-sm text-red-300">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={submitting || !ready}
            className="mt-2 w-full rounded-lg border border-shell-accent/50 bg-shell-accentBlue py-2.5 text-sm font-semibold text-shell-text shadow-md transition-colors hover:bg-[#2a4f86] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
