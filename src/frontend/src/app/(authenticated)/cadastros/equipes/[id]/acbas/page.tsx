"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { apiRequest } from "@/lib/api";
import type { EquipeAcbaItem, EquipeOperacional } from "@/types/acba";

export default function EquipeAcbasPage() {
  const params = useParams<{ id: string }>();
  const equipeId = Number(params.id);

  const [equipe, setEquipe] = useState<EquipeOperacional | null>(null);
  const [items, setItems] = useState<EquipeAcbaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [eq, acbas] = await Promise.all([
        apiRequest<EquipeOperacional>(`/api/cadastros/equipes/${equipeId}`),
        apiRequest<EquipeAcbaItem[]>(
          `/api/cadastros/equipes/${equipeId}/acbas`,
        ),
      ]);
      setEquipe(eq);
      setItems(acbas);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar.");
    } finally {
      setLoading(false);
    }
  }, [equipeId]);

  useEffect(() => {
    if (!Number.isFinite(equipeId)) return;
    void load();
  }, [equipeId, load]);

  if (!Number.isFinite(equipeId)) {
    return <p className="text-red-300">ID inválido.</p>;
  }

  return (
    <div className="space-y-4">
      <div>
        <Link
          href="/cadastros/equipes"
          className="text-xs text-shell-muted hover:underline"
        >
          ← Voltar para equipes
        </Link>
        <h2 className="text-xl font-semibold text-shell-text">
          {equipe ? (
            <>
              ACBAs da equipe{" "}
              <span className="font-mono">{equipe.numero}</span>
              {equipe.nome ? ` — ${equipe.nome}` : ""}
            </>
          ) : (
            "ACBAs da equipe"
          )}
        </h2>
      </div>

      {error ? (
        <p className="rounded border border-red-700/60 bg-red-950/30 p-3 text-sm text-red-300">
          {error}
        </p>
      ) : null}

      <div className="overflow-hidden rounded-xl border border-shell-border bg-shell-surface">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#0f141c] text-shell-muted">
            <tr>
              <th className="px-4 py-3">Número</th>
              <th className="px-4 py-3">Data</th>
              <th className="px-4 py-3">Alvo</th>
              <th className="px-4 py-3">Delegacia</th>
              <th className="px-4 py-3">Delegado</th>
              <th className="px-4 py-3">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-shell-muted">
                  Carregando...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-shell-muted">
                  Nenhum ACBA vinculado a esta equipe.
                </td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.id} className="border-t border-shell-border/70">
                  <td className="px-4 py-3 text-shell-text">{row.numero_auto}</td>
                  <td className="px-4 py-3 text-shell-text">
                    {new Date(row.data_lavratura).toLocaleDateString("pt-BR")}
                  </td>
                  <td className="px-4 py-3 text-shell-text">{row.alvo_busca}</td>
                  <td className="px-4 py-3 text-shell-text">
                    {row.delegacia_nome ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-shell-text">
                    {row.delegado_nome ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/acba/${row.id}`}
                      className="text-shell-accent hover:underline"
                    >
                      Visualizar
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
