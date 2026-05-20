"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/contexts/auth-context";
import { apiRequest, getApiBaseUrl } from "@/lib/api";
import type { AcbaDetail } from "@/types/acba";

export default function AcbaDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
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
      const slug = (record?.protocolo_numero ?? params.id)
        .toString()
        .replace(/\//g, "_")
        .replace(/\s+/g, "_");
      link.download = `acba_${slug}.pdf`;
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

  const role = user?.role ?? "agente";
  // Delegado edita sempre; escrivão só enquanto o PDF não foi gerado;
  // agente nunca edita. Espelha a regra do backend (authz.assert_can_update_acba).
  const podeEditar =
    role === "delegado" ||
    (role === "escrivao" && !record.pdf_gerado_at);
  const podeExcluir = role === "delegado";
  const motivoBloqueioEdicao =
    role === "escrivao" && record.pdf_gerado_at
      ? "Este ACBA já teve o PDF gerado e está bloqueado para o escrivão. Acione o delegado responsável para qualquer ajuste posterior."
      : role === "agente"
        ? "Agentes têm acesso somente para consulta deste ACBA."
        : null;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.12em] text-shell-muted">
            Processo{" "}
            <span className="font-mono normal-case tracking-normal text-shell-text">
              {record.processo_numero}
            </span>
          </p>
          <h2 className="text-xl font-semibold text-shell-text">
            ACBA — Prot.{" "}
            <span className="font-mono">{record.protocolo_numero}</span>
          </h2>
          {record.processo_descricao ? (
            <p className="text-sm text-shell-muted">
              {record.processo_descricao}
            </p>
          ) : null}
          {record.pdf_gerado_at ? (
            <p className="mt-2 inline-block rounded bg-shell-accentBlue px-2 py-1 text-xs text-shell-text">
              PDF gerado em{" "}
              {new Date(record.pdf_gerado_at).toLocaleString("pt-BR")}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void downloadPdf()}
            className="rounded border border-shell-border bg-shell-surface px-3 py-2 text-sm text-shell-text"
          >
            Gerar PDF
          </button>
          {podeEditar ? (
            <Link
              href={`/acba/${record.id}/edit`}
              className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-2 text-sm text-shell-text"
            >
              Editar
            </Link>
          ) : null}
          {podeExcluir ? (
            <button
              type="button"
              disabled={removing}
              onClick={deleteRecord}
              className="rounded border border-red-700/60 bg-red-950/30 px-3 py-2 text-sm text-red-300 disabled:opacity-60"
            >
              Excluir
            </button>
          ) : null}
          <Link
            href={`/acba/${record.id}/auditoria`}
            className="rounded border border-shell-border bg-shell-surface px-3 py-2 text-sm text-shell-text hover:border-shell-accent hover:text-shell-accent"
          >
            Auditoria
          </Link>
        </div>
      </div>

      {motivoBloqueioEdicao ? (
        <p className="rounded border border-amber-700/50 bg-amber-950/30 p-3 text-xs text-amber-200">
          {motivoBloqueioEdicao}
        </p>
      ) : null}

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
          {record.nome_vara_criminal || record.nome_juiz ? (
            <div className="mt-3 grid grid-cols-1 gap-2 border-t border-shell-border pt-3 md:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
                  Vara criminal
                </p>
                <p className="text-shell-text">
                  {record.nome_vara_criminal || "—"}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
                  Juiz(a) que expediu o mandado
                </p>
                <p className="text-shell-text">{record.nome_juiz || "—"}</p>
              </div>
            </div>
          ) : null}
        </div>
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5 md:col-span-2">
          <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
            Fundamentação
          </p>
          <p className="mt-2 whitespace-pre-wrap text-shell-text">
            {record.fundamento_legal}
          </p>
        </div>
        {record.arrombamento_245_2 ||
        record.forca_coisas_245_3 ||
        record.morador_ausente_245_4 ? (
          <div className="rounded-xl border border-shell-border bg-shell-surface p-5 md:col-span-2">
            <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
              Ocorrências da diligência (Art. 245 §§ 2º, 3º e 4º do CPP)
            </p>
            <ul className="mt-2 space-y-3 text-sm text-shell-text">
              {record.arrombamento_245_2 ? (
                <li>
                  <p className="font-medium">
                    §2º — Arrombamento de porta / entrada forçada por
                    desobediência do morador.
                  </p>
                  {record.arrombamento_245_2_obs ? (
                    <p className="mt-1 whitespace-pre-wrap text-shell-muted">
                      {record.arrombamento_245_2_obs}
                    </p>
                  ) : null}
                </li>
              ) : null}
              {record.forca_coisas_245_3 ? (
                <li>
                  <p className="font-medium">
                    §3º — Emprego de força contra coisas no interior da casa por
                    recalcitrância do morador.
                  </p>
                  {record.forca_coisas_245_3_obs ? (
                    <p className="mt-1 whitespace-pre-wrap text-shell-muted">
                      {record.forca_coisas_245_3_obs}
                    </p>
                  ) : null}
                </li>
              ) : null}
              {record.morador_ausente_245_4 ? (
                <li>
                  <p className="font-medium">
                    §4º — Morador ausente; arrombamento de porta e emprego de
                    força contra coisas.
                  </p>
                  {record.morador_ausente_245_4_obs ? (
                    <p className="mt-1 whitespace-pre-wrap text-shell-muted">
                      {record.morador_ausente_245_4_obs}
                    </p>
                  ) : null}
                </li>
              ) : null}
            </ul>
          </div>
        ) : null}
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
            Materiais apreendidos{" "}
            {record.materiais_pendentes_revisao > 0 ? (
              <span className="ml-2 rounded bg-amber-900/40 px-2 py-0.5 text-amber-200">
                {record.materiais_pendentes_revisao} pendente(s) de revisão
              </span>
            ) : null}
          </p>
          {record.materiais.length === 0 ? (
            <p className="mt-2 text-sm text-shell-muted">
              Nenhum material registrado.
            </p>
          ) : (
            <ul className="mt-2 space-y-1 text-sm text-shell-text">
              {record.materiais.map((m) => (
                <li key={m.id ?? `${m.categoria_docx}-${m.item_num}`}>
                  <span className="font-mono">
                    [{m.categoria_docx === "informatica" ? "INF" : "GER"} {m.item_num}]
                  </span>{" "}
                  <strong>{m.tipo_nome}</strong> — {m.descricao}
                  {m.revisado ? null : (
                    <span className="ml-2 text-xs text-amber-300">
                      (revisão pendente)
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
        {!record.morador_ausente_245_4 &&
        (record.morador_nome ||
          record.morador_cpf ||
          record.morador_rg ||
          record.morador_filiacao ||
          record.morador_telefone) ? (
          <div className="rounded-xl border border-shell-border bg-shell-surface p-5 md:col-span-2">
            <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
              Morador presente (Art. 245, caput e §1º do CPP)
            </p>
            <div className="mt-2 grid grid-cols-1 gap-1 text-sm text-shell-text md:grid-cols-2">
              <span className="md:col-span-2">
                <strong>{record.morador_nome || "—"}</strong>
              </span>
              <span>CPF: {record.morador_cpf || "—"}</span>
              <span>RG: {record.morador_rg || "—"}</span>
              <span className="md:col-span-2">
                Filiação: {record.morador_filiacao || "—"}
              </span>
              <span>Telefone: {record.morador_telefone || "—"}</span>
            </div>
          </div>
        ) : null}
        {record.testemunhas && record.testemunhas.length > 0 ? (
          <div className="rounded-xl border border-shell-border bg-shell-surface p-5 md:col-span-2">
            <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
              Testemunhas
            </p>
            <ul className="mt-2 space-y-3 text-sm text-shell-text">
              {record.testemunhas.map((t, idx) => (
                <li
                  key={t.id ?? `${t.nome}-${idx}`}
                  className={
                    t.tipo === "arrombamento"
                      ? "rounded border border-shell-accent/40 p-3"
                      : ""
                  }
                >
                  <p>
                    <strong>{t.nome}</strong>
                    {t.tipo === "arrombamento" ? (
                      <span className="ml-2 rounded bg-shell-accentBlue px-2 py-0.5 text-xs text-shell-text">
                        Testemunha de arrombamento (§4º)
                      </span>
                    ) : null}
                  </p>
                  <div className="mt-1 grid grid-cols-1 gap-1 text-xs text-shell-muted md:grid-cols-2">
                    <span>CPF: {t.cpf || "—"}</span>
                    <span>RG: {t.rg || "—"}</span>
                    <span className="md:col-span-2">
                      Filiação: {t.filiacao || "—"}
                    </span>
                    <span className="md:col-span-2">
                      Endereço: {t.endereco || "—"}
                    </span>
                    {t.tipo === "geral" ? (
                      <>
                        <span>Cidade: {t.cidade || "—"}</span>
                        <span>Telefone: {t.telefone || "—"}</span>
                      </>
                    ) : null}
                    {t.tipo === "arrombamento" && t.arrombamento?.observacoes ? (
                      <span className="md:col-span-2 whitespace-pre-wrap">
                        Obs.: {t.arrombamento.observacoes}
                      </span>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
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
