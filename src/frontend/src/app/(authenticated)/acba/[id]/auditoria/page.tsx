"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { apiRequest } from "@/lib/api";
import type { AcbaAuditEntry, AcbaDetail } from "@/types/acba";

const ACAO_LABEL: Record<AcbaAuditEntry["acao"], string> = {
  criado: "Criação",
  editado: "Edição",
  excluido: "Exclusão",
  pdf_gerado: "PDF gerado",
};

const ROLE_LABEL: Record<AcbaAuditEntry["user_role"], string> = {
  administrador: "Administrador",
  delegado: "Delegado",
  escrivao: "Escrivão",
  agente: "Agente",
};

function fmtDate(value: string): string {
  try {
    return new Date(value).toLocaleString("pt-BR");
  } catch {
    return value;
  }
}

function fmtValue(v: unknown): string {
  if (v == null) return "—";
  if (typeof v === "object") {
    try {
      return JSON.stringify(v);
    } catch {
      return String(v);
    }
  }
  return String(v);
}

export default function AcbaAuditPage() {
  const params = useParams<{ id: string }>();
  const [acba, setAcba] = useState<AcbaDetail | null>(null);
  const [entries, setEntries] = useState<AcbaAuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AcbaAuditEntry | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [acbaData, auditData] = await Promise.all([
          apiRequest<AcbaDetail>(`/api/acba/${params.id}`),
          apiRequest<AcbaAuditEntry[]>(`/api/acba/${params.id}/auditoria`),
        ]);
        setAcba(acbaData);
        setEntries(auditData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [params.id]);

  async function openEntry(entry: AcbaAuditEntry) {
    setSelected(entry);
    setLoadingDetail(true);
    try {
      const full = await apiRequest<AcbaAuditEntry>(
        `/api/acba/${params.id}/auditoria/${entry.id}`,
      );
      setSelected(full);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar entrada.");
    } finally {
      setLoadingDetail(false);
    }
  }

  const changesKeys = useMemo<string[]>(() => {
    if (!selected?.changes) return [];
    return Object.keys(selected.changes).sort();
  }, [selected]);

  if (loading) return <p className="text-shell-muted">Carregando auditoria...</p>;
  if (error) return <p className="text-red-300">{error}</p>;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.12em] text-shell-muted">
            Auditoria
          </p>
          <h2 className="text-xl font-semibold text-shell-text">
            ACBA — Prot.{" "}
            <span className="font-mono">
              {acba?.protocolo_numero ?? params.id}
            </span>
          </h2>
        </div>
        <Link
          href={`/acba/${params.id}`}
          className="rounded border border-shell-border bg-shell-surface px-3 py-2 text-sm text-shell-text hover:border-shell-accent hover:text-shell-accent"
        >
          ← Voltar ao ACBA
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="overflow-hidden rounded-xl border border-shell-border bg-shell-surface">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#0f141c] text-shell-muted">
              <tr>
                <th className="px-3 py-2">Quando</th>
                <th className="px-3 py-2">Quem</th>
                <th className="px-3 py-2">Ação</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 ? (
                <tr>
                  <td className="px-3 py-4 text-shell-muted" colSpan={3}>
                    Nenhuma alteração registrada.
                  </td>
                </tr>
              ) : (
                entries.map((e) => {
                  const ativo = selected?.id === e.id;
                  return (
                    <tr
                      key={e.id}
                      onClick={() => void openEntry(e)}
                      className={`cursor-pointer border-t border-shell-border/70 ${
                        ativo
                          ? "bg-shell-accent/10 text-shell-accent"
                          : "hover:bg-shell-sidebarHover"
                      }`}
                    >
                      <td className="px-3 py-2 text-shell-text">
                        {fmtDate(e.changed_at)}
                      </td>
                      <td className="px-3 py-2 text-shell-text">
                        <div className="flex flex-col">
                          <span>{e.user_full_name ?? e.user_email}</span>
                          <span className="text-[10px] uppercase tracking-[0.12em] text-shell-muted">
                            {ROLE_LABEL[e.user_role]}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-shell-text">
                        {ACAO_LABEL[e.acao]}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="rounded-xl border border-shell-border bg-shell-surface p-4">
          {!selected ? (
            <p className="text-shell-muted">
              Selecione uma alteração na lista para inspecionar o diff e a
              versão completa do documento naquele momento.
            </p>
          ) : (
            <div className="space-y-4 text-sm text-shell-text">
              <div>
                <p className="text-xs uppercase tracking-[0.12em] text-shell-muted">
                  Detalhes
                </p>
                <p className="mt-1">
                  <strong>{ACAO_LABEL[selected.acao]}</strong> por{" "}
                  {selected.user_full_name ?? selected.user_email}
                  {" "}
                  <span className="text-shell-muted">
                    ({ROLE_LABEL[selected.user_role]})
                  </span>
                </p>
                <p className="text-shell-muted">
                  {fmtDate(selected.changed_at)}
                  {selected.ip ? ` — IP ${selected.ip}` : ""}
                </p>
                {selected.user_agent ? (
                  <p className="break-all text-xs text-shell-muted">
                    UA: {selected.user_agent}
                  </p>
                ) : null}
              </div>

              {loadingDetail ? (
                <p className="text-shell-muted">Carregando detalhes...</p>
              ) : null}

              {selected.changes && changesKeys.length > 0 ? (
                <div>
                  <p className="text-xs uppercase tracking-[0.12em] text-shell-muted">
                    Campos alterados ({changesKeys.length})
                  </p>
                  <div className="mt-2 overflow-hidden rounded border border-shell-border">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#0f141c] text-shell-muted">
                        <tr>
                          <th className="px-2 py-1">Campo</th>
                          <th className="px-2 py-1">De</th>
                          <th className="px-2 py-1">Para</th>
                        </tr>
                      </thead>
                      <tbody>
                        {changesKeys.map((k) => {
                          const c = selected.changes![k];
                          return (
                            <tr
                              key={k}
                              className="border-t border-shell-border/60"
                            >
                              <td className="px-2 py-1 font-mono text-shell-text">
                                {k}
                              </td>
                              <td className="px-2 py-1 align-top text-red-200">
                                {fmtValue(c.de)}
                              </td>
                              <td className="px-2 py-1 align-top text-green-200">
                                {fmtValue(c.para)}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : null}

              {selected.snapshot_before ? (
                <details className="rounded border border-shell-border bg-shell-bg">
                  <summary className="cursor-pointer px-3 py-2 text-xs uppercase tracking-[0.12em] text-shell-muted">
                    Documento ANTES da alteração
                  </summary>
                  <pre className="max-h-[400px] overflow-auto whitespace-pre-wrap break-words px-3 py-2 text-[11px] text-shell-text">
                    {JSON.stringify(selected.snapshot_before, null, 2)}
                  </pre>
                </details>
              ) : null}

              {selected.snapshot_after ? (
                <details className="rounded border border-shell-border bg-shell-bg">
                  <summary className="cursor-pointer px-3 py-2 text-xs uppercase tracking-[0.12em] text-shell-muted">
                    Documento DEPOIS da alteração
                  </summary>
                  <pre className="max-h-[400px] overflow-auto whitespace-pre-wrap break-words px-3 py-2 text-[11px] text-shell-text">
                    {JSON.stringify(selected.snapshot_after, null, 2)}
                  </pre>
                </details>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
