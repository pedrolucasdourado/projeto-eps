"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { apiRequest } from "@/lib/api";
import type { AgenteEquipeVinculo, AgenteListing } from "@/types/acba";

function formatDateBR(value: string | null | undefined): string {
  if (!value) return "—";
  const isoDate = /^\d{4}-\d{2}-\d{2}$/.exec(value);
  if (isoDate) {
    const [y, m, d] = value.split("-");
    return `${d}/${m}/${y}`;
  }
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleDateString("pt-BR");
}

function diffInDays(inicio: string, fim: string | null | undefined): number {
  const start = new Date(inicio).getTime();
  const end = fim ? new Date(fim).getTime() : Date.now();
  const diff = Math.max(0, end - start);
  return Math.round(diff / 86_400_000);
}

export default function AgenteHistoricoEquipesPage() {
  const params = useParams<{ id: string }>();
  const agenteId = Number(params.id);

  const [agente, setAgente] = useState<AgenteListing | null>(null);
  const [vinculos, setVinculos] = useState<AgenteEquipeVinculo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [a, hist] = await Promise.all([
        apiRequest<AgenteListing>(`/api/cadastros/agentes/${agenteId}`),
        apiRequest<AgenteEquipeVinculo[]>(
          `/api/cadastros/agentes/${agenteId}/equipes/historico`,
        ),
      ]);
      setAgente(a);
      setVinculos(hist);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar.");
    } finally {
      setLoading(false);
    }
  }, [agenteId]);

  useEffect(() => {
    if (!Number.isFinite(agenteId)) return;
    void load();
  }, [agenteId, load]);

  const ativos = useMemo(
    () => vinculos.filter((v) => v.ativo),
    [vinculos],
  );
  const encerrados = useMemo(
    () => vinculos.filter((v) => !v.ativo),
    [vinculos],
  );

  if (!Number.isFinite(agenteId)) {
    return <p className="text-red-300">ID inválido.</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/cadastros/agentes"
          className="text-xs text-shell-muted hover:underline"
        >
          ← Voltar para agentes
        </Link>
        <h2 className="text-xl font-semibold text-shell-text">
          {agente ? (
            <>
              Histórico de equipes — {agente.nome}{" "}
              <span className="text-shell-muted text-base font-normal">
                ({agente.matricula})
              </span>
            </>
          ) : (
            "Histórico de equipes"
          )}
        </h2>
        {agente?.funcao_padrao ? (
          <p className="text-xs text-shell-muted">
            Função padrão: {agente.funcao_padrao}
          </p>
        ) : null}
      </div>

      {error ? (
        <p className="rounded border border-red-700/60 bg-red-950/30 p-3 text-sm text-red-300">
          {error}
        </p>
      ) : null}

      <section className="space-y-2">
        <h3 className="text-sm font-semibold text-shell-text">
          Vínculos ativos
        </h3>
        <div className="overflow-hidden rounded-xl border border-shell-border bg-shell-surface">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#0f141c] text-shell-muted">
              <tr>
                <th className="px-4 py-3">Equipe</th>
                <th className="px-4 py-3">Nome</th>
                <th className="px-4 py-3">Data de ingresso</th>
                <th className="px-4 py-3">Tempo na equipe</th>
                <th className="px-4 py-3">Ações</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-shell-muted">
                    Carregando...
                  </td>
                </tr>
              ) : ativos.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-shell-muted">
                    Este agente não está vinculado a nenhuma equipe no momento.
                  </td>
                </tr>
              ) : (
                ativos.map((v) => (
                  <tr key={v.id} className="border-t border-shell-border/70">
                    <td className="px-4 py-3 text-shell-text font-mono">
                      {v.equipe_numero}
                    </td>
                    <td className="px-4 py-3 text-shell-text">
                      {v.equipe_nome ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-shell-text">
                      {formatDateBR(v.data_inicio)}
                    </td>
                    <td className="px-4 py-3 text-shell-text">
                      {diffInDays(v.data_inicio, null)} dia(s)
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/cadastros/equipes/${v.equipe_id}/agentes`}
                        className="text-shell-accent hover:underline"
                      >
                        Abrir equipe
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-2">
        <h3 className="text-sm font-semibold text-shell-text">
          Passagens encerradas
        </h3>
        <div className="overflow-hidden rounded-xl border border-shell-border bg-shell-surface">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#0f141c] text-shell-muted">
              <tr>
                <th className="px-4 py-3">Equipe</th>
                <th className="px-4 py-3">Nome</th>
                <th className="px-4 py-3">Período</th>
                <th className="px-4 py-3">Duração</th>
                <th className="px-4 py-3">Motivo da saída</th>
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
              ) : encerrados.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-shell-muted">
                    Nenhuma passagem anterior registrada.
                  </td>
                </tr>
              ) : (
                encerrados.map((v) => (
                  <tr key={v.id} className="border-t border-shell-border/70">
                    <td className="px-4 py-3 text-shell-text font-mono">
                      {v.equipe_numero}
                    </td>
                    <td className="px-4 py-3 text-shell-text">
                      {v.equipe_nome ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-shell-text">
                      {formatDateBR(v.data_inicio)} —{" "}
                      {formatDateBR(v.data_fim)}
                    </td>
                    <td className="px-4 py-3 text-shell-text">
                      {diffInDays(v.data_inicio, v.data_fim)} dia(s)
                    </td>
                    <td className="px-4 py-3 text-shell-text">
                      {v.motivo_saida ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/cadastros/equipes/${v.equipe_id}/agentes`}
                        className="text-shell-accent hover:underline"
                      >
                        Abrir equipe
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
