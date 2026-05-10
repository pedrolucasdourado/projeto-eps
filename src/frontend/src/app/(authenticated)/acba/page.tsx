"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiRequest } from "@/lib/api";
import { AcbaListItem, TipoMaterial } from "@/types/acba";

export default function AcbaListPage() {
  const [items, setItems] = useState<AcbaListItem[]>([]);
  const [tipos, setTipos] = useState<TipoMaterial[]>([]);
  const [tipoFiltro, setTipoFiltro] = useState<number | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = tipoFiltro ? `?tipo_material_id=${tipoFiltro}` : "";
      const data = await apiRequest<AcbaListItem[]>(`/api/acba/${qs}`);
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar.");
    } finally {
      setLoading(false);
    }
  }, [tipoFiltro]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    void apiRequest<TipoMaterial[]>("/api/cadastros/tipos-material")
      .then(setTipos)
      .catch(() => setTipos([]));
  }, []);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-shell-text">
          Autos Circunstanciados de Busca e Arrecadação
        </h2>
        <Link
          href="/acba/new"
          className="rounded-lg border border-shell-accent/50 bg-shell-accentBlue px-4 py-2 text-sm font-semibold text-shell-text"
        >
          Novo ACBA
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <label className="text-sm text-shell-muted">
          Filtrar por tipo de material:
        </label>
        <select
          className="rounded border border-shell-border bg-shell-bg px-3 py-1 text-sm text-shell-text"
          value={tipoFiltro}
          onChange={(e) =>
            setTipoFiltro(e.target.value ? Number(e.target.value) : "")
          }
        >
          <option value="">— todos —</option>
          {tipos
            .filter((t) => t.ativo)
            .map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome}
              </option>
            ))}
        </select>
        {tipoFiltro ? (
          <button
            type="button"
            onClick={() => setTipoFiltro("")}
            className="rounded border border-shell-border px-2 py-1 text-xs text-shell-text"
          >
            limpar
          </button>
        ) : null}
      </div>

      <div className="overflow-hidden rounded-xl border border-shell-border bg-shell-surface">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#0f141c] text-shell-muted">
            <tr>
              <th className="px-4 py-3">Processo</th>
              <th className="px-4 py-3">Protocolo</th>
              <th className="px-4 py-3">Delegacia</th>
              <th className="px-4 py-3">Data</th>
              <th className="px-4 py-3">Alvo</th>
              <th className="px-4 py-3">Delegado</th>
              <th className="px-4 py-3">Equipe</th>
              <th className="px-4 py-3">Revisão</th>
              <th className="px-4 py-3">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td className="px-4 py-6 text-shell-muted" colSpan={9}>
                  Carregando registros...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-shell-muted" colSpan={9}>
                  Nenhum registro encontrado.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-t border-shell-border/70">
                  <td className="px-4 py-3 text-shell-text font-mono">
                    {item.processo_numero}
                  </td>
                  <td className="px-4 py-3 text-shell-text font-mono">
                    {item.protocolo_numero}
                  </td>
                  <td className="px-4 py-3 text-shell-text">
                    {item.delegacia_nome}
                  </td>
                  <td className="px-4 py-3 text-shell-text">
                    {new Date(item.data_lavratura).toLocaleDateString("pt-BR")}
                  </td>
                  <td className="px-4 py-3 text-shell-text">{item.alvo_busca}</td>
                  <td className="px-4 py-3 text-shell-text">
                    {item.delegado_nome}
                  </td>
                  <td className="px-4 py-3 text-shell-text">
                    <span className="font-mono">{item.equipe_numero}</span>
                    {item.equipe_nome ? ` — ${item.equipe_nome}` : ""}
                  </td>
                  <td className="px-4 py-3 text-xs">
                    {item.materiais_pendentes_revisao > 0 ? (
                      <span className="rounded bg-amber-900/40 px-2 py-1 text-amber-200">
                        {item.materiais_pendentes_revisao} pendente(s)
                      </span>
                    ) : (
                      <span className="rounded bg-green-900/40 px-2 py-1 text-green-200">
                        OK
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/acba/${item.id}`}
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

      {error ? (
        <p className="rounded border border-red-700/60 bg-red-950/30 p-3 text-sm text-red-300">
          {error}
        </p>
      ) : null}
    </div>
  );
}
