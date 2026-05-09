"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiRequest } from "@/lib/api";
import { AcbaListItem } from "@/types/acba";

export default function AcbaListPage() {
  const [items, setItems] = useState<AcbaListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiRequest<AcbaListItem[]>("/api/acba/");
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
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

      <div className="overflow-hidden rounded-xl border border-shell-border bg-shell-surface">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#0f141c] text-shell-muted">
            <tr>
              <th className="px-4 py-3">Número</th>
              <th className="px-4 py-3">Delegacia</th>
              <th className="px-4 py-3">Data</th>
              <th className="px-4 py-3">Alvo</th>
              <th className="px-4 py-3">Delegado</th>
              <th className="px-4 py-3">Equipe</th>
              <th className="px-4 py-3">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td className="px-4 py-6 text-shell-muted" colSpan={7}>
                  Carregando registros...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-shell-muted" colSpan={7}>
                  Nenhum registro encontrado.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-t border-shell-border/70">
                  <td className="px-4 py-3 text-shell-text">{item.numero_auto}</td>
                  <td className="px-4 py-3 text-shell-text">{item.delegacia_nome}</td>
                  <td className="px-4 py-3 text-shell-text">
                    {new Date(item.data_lavratura).toLocaleDateString("pt-BR")}
                  </td>
                  <td className="px-4 py-3 text-shell-text">{item.alvo_busca}</td>
                  <td className="px-4 py-3 text-shell-text">{item.delegado_nome}</td>
                  <td className="px-4 py-3 text-shell-text">
                    <span className="font-mono">{item.equipe_numero}</span>
                    {item.equipe_nome ? ` — ${item.equipe_nome}` : ""}
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
