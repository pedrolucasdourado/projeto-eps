"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiRequest, getApiBaseUrl } from "@/lib/api";
import type { AcbaDetail } from "@/types/acba";

export default function AcbaDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [record, setRecord] = useState<AcbaDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setLoadError(null);
      try {
        const data = await apiRequest<AcbaDetail>(`/api/acba/${params.id}`);
        setRecord(data);
      } catch (err) {
        setLoadError(err instanceof Error ? err.message : "Erro ao carregar.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [params.id]);

  async function deleteRecord() {
    if (!confirm("Confirma a exclusão deste auto?")) return;
    setRemoving(true);
    try {
      await apiRequest<void>(`/api/acba/${params.id}`, { method: "DELETE" });
      router.push("/acba");
    } finally {
      setRemoving(false);
    }
  }

  async function downloadPdf() {
    const token = localStorage.getItem("aai_access_token");
    if (!token) return;
    setPdfError(null);
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/acba/${params.id}/pdf`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const j = await res.json().catch(() => null);
        const msg =
          typeof j?.detail === "string"
            ? j.detail
            : Array.isArray(j?.detail)
              ? j.detail.map((x: { msg?: string }) => x?.msg).filter(Boolean).join(" ")
              : "Falha ao gerar PDF.";
        throw new Error(msg);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `acba_${record?.numero_auto ?? params.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setPdfError(err instanceof Error ? err.message : "Erro no PDF");
    }
  }

  if (loading) return <p className="text-shell-muted">Carregando...</p>;
  if (loadError || !record) {
    return (
      <p className="text-red-300">
        {loadError ?? "Registro não encontrado."}
      </p>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-shell-text">
          ACBA {record.numero_auto}
        </h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void downloadPdf()}
            className="rounded border border-shell-border bg-shell-surface px-3 py-2 text-sm text-shell-text"
          >
            Gerar PDF
          </button>
          <Link
            href={`/acba/${record.id}/edit`}
            className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-2 text-sm text-shell-text"
          >
            Editar
          </Link>
          <button
            type="button"
            disabled={removing}
            onClick={deleteRecord}
            className="rounded border border-red-700/60 bg-red-950/30 px-3 py-2 text-sm text-red-300 disabled:opacity-60"
          >
            Excluir
          </button>
        </div>
      </div>

      {pdfError ? (
        <p className="rounded border border-red-700/60 bg-red-950/30 p-3 text-sm text-red-300">
          {pdfError}
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5">
          <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
            Órgão e vínculos
          </p>
          <p className="mt-2 text-shell-text">{record.unidade_nome}</p>
          <p className="text-shell-text">{record.delegacia_nome}</p>
          <p className="text-shell-muted">
            {record.cidade_nome} — {record.uf_sigla} ({record.uf_nome})
          </p>
          <p className="mt-2 text-sm text-shell-muted">
            Procedimento: {record.tipo_procedimento_nome} —{" "}
            {record.procedimento_numero}
          </p>
        </div>
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5">
          <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
            Data / autoridade
          </p>
          <p className="mt-2 text-shell-text">
            {new Date(record.data_lavratura).toLocaleDateString("pt-BR")}{" "}
            {record.hora_lavratura?.slice(0, 5) ?? ""}
          </p>
          <p className="mt-2 text-shell-text">
            Delegado: {record.delegado_nome}
            {record.delegado_matricula ? ` (${record.delegado_matricula})` : ""}
          </p>
          <p className="text-shell-muted">Escrivão: {record.escrivao_nome}</p>
        </div>
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5 md:col-span-2">
          <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">Local</p>
          <p className="mt-2 text-shell-text">{record.alvo_busca}</p>
          <p className="mt-2 whitespace-pre-wrap text-shell-muted">
            {record.endereco_busca}
          </p>
        </div>
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5 md:col-span-2">
          <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
            Fundamentação
          </p>
          <p className="mt-2 whitespace-pre-wrap text-shell-text">
            {record.fundamento_legal}
          </p>
        </div>
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5 md:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
              Equipe operacional —{" "}
              <span className="font-mono normal-case tracking-normal text-shell-text">
                {record.equipe_numero}
              </span>
              {record.equipe_nome ? (
                <span className="normal-case tracking-normal text-shell-text">
                  {" "}
                  ({record.equipe_nome})
                </span>
              ) : null}
            </p>
            <Link
              href={`/cadastros/equipes/${record.equipe_id}/agentes`}
              className="rounded border border-shell-border px-2 py-1 text-xs text-shell-text hover:border-shell-accent hover:text-shell-accent"
            >
              Gerenciar equipe
            </Link>
          </div>
          {record.agentes_equipe && record.agentes_equipe.length > 0 ? (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-shell-text">
              {record.agentes_equipe.map((m) => (
                <li key={m.id}>
                  {m.nome} — {m.matricula}
                  {m.funcao_padrao ? ` — ${m.funcao_padrao}` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-shell-muted">
              Nenhum agente vinculado a esta equipe.
            </p>
          )}
        </div>
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5 md:col-span-2">
          <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
            Observações e assinatura
          </p>
          <p className="mt-2 whitespace-pre-wrap text-shell-text">
            {record.observacoes || "—"}
          </p>
          <p className="mt-4 text-sm text-shell-muted">
            Responsável (assinatura): {record.assinatura_responsavel}
          </p>
        </div>
      </div>
    </div>
  );
}
