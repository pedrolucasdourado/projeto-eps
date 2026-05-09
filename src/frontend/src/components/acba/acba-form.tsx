"use client";

import Link from "next/link";
import {
  type ReactNode,
  FormEvent,
  KeyboardEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import { apiRequest } from "@/lib/api";
import type {
  AcbaDetail,
  AcbaFormPayload,
  AgenteBrief,
  EquipeOperacional,
  ObjetoItem,
  Processo,
  TestemunhaItem,
} from "@/types/acba";

type Props = {
  submitting: boolean;
  initialDetail?: AcbaDetail | null;
  onSubmit: (payload: AcbaFormPayload) => Promise<void>;
};

function inputClass() {
  return "w-full rounded-lg border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text outline-none focus:border-shell-accent";
}

function readonlyClass() {
  return "w-full rounded-lg border border-shell-border bg-shell-bg/60 px-3 py-2 text-sm text-shell-muted";
}

function emptyPayload(): AcbaFormPayload {
  return {
    processo_numero: "",
    protocolo_numero: "",
    unidade_id: 0,
    delegacia_id: 0,
    cidade_id: 0,
    data_lavratura: "",
    hora_lavratura: "",
    tipo_procedimento_id: 0,
    procedimento_numero: "",
    fundamento_legal: "",
    endereco_busca: "",
    alvo_busca: "",
    assinatura_responsavel: "",
    observacoes: "",
    equipe_id: 0,
    testemunhas: [],
    objetos_arrecadados: [],
  };
}

function detailToPayload(d: AcbaDetail): AcbaFormPayload {
  return {
    processo_numero: d.processo_numero,
    protocolo_numero: d.protocolo_numero,
    unidade_id: d.unidade_id,
    delegacia_id: d.delegacia_id,
    cidade_id: d.cidade_id,
    data_lavratura: d.data_lavratura.slice(0, 10),
    hora_lavratura:
      d.hora_lavratura.length >= 5 ? d.hora_lavratura.slice(0, 5) : d.hora_lavratura,
    tipo_procedimento_id: d.tipo_procedimento_id,
    procedimento_numero: d.procedimento_numero,
    fundamento_legal: d.fundamento_legal,
    endereco_busca: d.endereco_busca,
    alvo_busca: d.alvo_busca,
    assinatura_responsavel: d.assinatura_responsavel,
    observacoes: d.observacoes,
    equipe_id: d.equipe_id,
    testemunhas: (d.testemunhas as TestemunhaItem[]) ?? [],
    objetos_arrecadados: (d.objetos_arrecadados as ObjetoItem[]) ?? [],
  };
}

export function AcbaForm({ submitting, initialDetail, onSubmit }: Props) {
  const [form, setForm] = useState<AcbaFormPayload>(() =>
    initialDetail ? detailToPayload(initialDetail) : emptyPayload(),
  );
  const [error, setError] = useState<string | null>(null);

  const [unidades, setUnidades] = useState<Record<string, unknown>[]>([]);
  const [cidades, setCidades] = useState<Record<string, unknown>[]>([]);
  const [delegacias, setDelegacias] = useState<Record<string, unknown>[]>([]);
  const [tipos, setTipos] = useState<Record<string, unknown>[]>([]);
  const [equipes, setEquipes] = useState<EquipeOperacional[]>([]);
  const [processos, setProcessos] = useState<Processo[]>([]);
  const [agentesPreview, setAgentesPreview] = useState<AgenteBrief[]>(
    initialDetail?.agentes_equipe ?? [],
  );

  const [processoModalOpen, setProcessoModalOpen] = useState(false);
  const [newProcessoNumero, setNewProcessoNumero] = useState("");
  const [newProcessoDescricao, setNewProcessoDescricao] = useState("");
  const [savingProcesso, setSavingProcesso] = useState(false);
  const [processoModalError, setProcessoModalError] = useState<string | null>(
    null,
  );

  useEffect(() => {
    if (initialDetail) {
      setForm(detailToPayload(initialDetail));
      setAgentesPreview(initialDetail.agentes_equipe ?? []);
    }
  }, [initialDetail]);

  useEffect(() => {
    async function load() {
      try {
        const [u, c, d, t, eq, pr] = await Promise.all([
          apiRequest<Record<string, unknown>[]>("/api/cadastros/unidades"),
          apiRequest<Record<string, unknown>[]>("/api/cadastros/cidades"),
          apiRequest<Record<string, unknown>[]>("/api/cadastros/delegacias"),
          apiRequest<Record<string, unknown>[]>(
            "/api/cadastros/tipos-procedimento",
          ),
          apiRequest<EquipeOperacional[]>("/api/cadastros/equipes"),
          apiRequest<Processo[]>("/api/cadastros/processos"),
        ]);
        setUnidades(u);
        setCidades(c);
        setDelegacias(d);
        setTipos(t);
        setEquipes(eq);
        setProcessos(pr);
      } catch {
        setError("Não foi possível carregar cadastros auxiliares.");
      }
    }
    void load();
  }, []);

  useEffect(() => {
    let aborted = false;
    async function loadAgentes() {
      if (!form.equipe_id) {
        setAgentesPreview([]);
        return;
      }
      try {
        const data = await apiRequest<AgenteBrief[]>(
          `/api/cadastros/equipes/${form.equipe_id}/agentes`,
        );
        if (!aborted) setAgentesPreview(data);
      } catch {
        if (!aborted) setAgentesPreview([]);
      }
    }
    void loadAgentes();
    return () => {
      aborted = true;
    };
  }, [form.equipe_id]);

  const delegaciasFiltradas = useMemo(() => {
    return delegacias.filter((row) => {
      const uid = form.unidade_id ? Number(form.unidade_id) : null;
      const cid = form.cidade_id ? Number(form.cidade_id) : null;
      if (uid && row.unidade_id != null && Number(row.unidade_id) !== uid) return false;
      if (cid && row.cidade_id != null && Number(row.cidade_id) !== cid) return false;
      return true;
    });
  }, [delegacias, form.unidade_id, form.cidade_id]);

  const equipesAtivas = useMemo(
    () => equipes.filter((e) => e.ativo),
    [equipes],
  );

  const processosAtivos = useMemo(
    () => processos.filter((p) => p.ativo),
    [processos],
  );

  const equipeSelecionada = useMemo(
    () => equipes.find((e) => e.id === form.equipe_id) ?? null,
    [equipes, form.equipe_id],
  );

  function updateTestemunha(i: number, p: Partial<TestemunhaItem>) {
    const next = [...form.testemunhas];
    next[i] = { ...next[i], ...p };
    setForm({ ...form, testemunhas: next });
  }

  function updateObjeto(i: number, p: Partial<ObjetoItem>) {
    const next = [...form.objetos_arrecadados];
    next[i] = { ...next[i], ...p };
    setForm({ ...form, objetos_arrecadados: next });
  }

  function openProcessoModal() {
    setNewProcessoNumero("");
    setNewProcessoDescricao("");
    setProcessoModalError(null);
    setProcessoModalOpen(true);
  }

  function closeProcessoModal() {
    if (savingProcesso) return;
    setProcessoModalOpen(false);
    setProcessoModalError(null);
  }

  async function saveProcessoInline() {
    setProcessoModalError(null);
    const numero = newProcessoNumero.trim();
    if (numero.length < 2) {
      setProcessoModalError("Informe o número do processo.");
      return;
    }
    if (processos.some((p) => p.numero === numero)) {
      setProcessoModalError(
        "Este processo já está cadastrado — selecione-o na lista.",
      );
      return;
    }
    setSavingProcesso(true);
    try {
      const created = await apiRequest<Processo>("/api/cadastros/processos", {
        method: "POST",
        body: JSON.stringify({
          numero,
          descricao: newProcessoDescricao.trim() || null,
          ativo: true,
        }),
      });
      setProcessos((prev) =>
        [...prev.filter((p) => p.numero !== created.numero), created].sort(
          (a, b) => a.numero.localeCompare(b.numero),
        ),
      );
      setForm((prev) => ({ ...prev, processo_numero: created.numero }));
      setProcessoModalOpen(false);
    } catch (err) {
      setProcessoModalError(
        err instanceof Error ? err.message : "Erro ao cadastrar processo.",
      );
    } finally {
      setSavingProcesso(false);
    }
  }

  function handleProcessoModalKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      void saveProcessoInline();
    } else if (e.key === "Escape") {
      e.preventDefault();
      closeProcessoModal();
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!form.processo_numero.trim() || !form.protocolo_numero.trim()) {
      setError("Selecione o processo e informe o número do protocolo.");
      return;
    }
    if (!form.data_lavratura || !form.hora_lavratura) {
      setError("Informe data e hora da lavratura.");
      return;
    }
    if (form.fundamento_legal.trim().length < 5) {
      setError("Fundamento legal deve ter pelo menos 5 caracteres.");
      return;
    }
    const ids = [
      form.unidade_id,
      form.delegacia_id,
      form.cidade_id,
      form.tipo_procedimento_id,
      form.equipe_id,
    ];
    if (ids.some((x) => !x || x < 1)) {
      setError(
        "Selecione unidade, delegacia, cidade, tipo de procedimento e equipe operacional.",
      );
      return;
    }
    try {
      await onSubmit(form);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar.");
    }
  }

  function section(title: string, children: ReactNode) {
    return (
      <div className="rounded-xl border border-shell-border bg-shell-surface p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.1em] text-shell-muted">
          {title}
        </h3>
        {children}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {section(
        "Identificação e vínculos institucionais",
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <label className="text-sm">
            <span className="text-shell-muted">Processo</span>
            <div className="mt-1 flex flex-col gap-2 sm:flex-row sm:items-stretch">
              <select
                className={`${inputClass()} flex-1`}
                value={form.processo_numero}
                onChange={(e) =>
                  setForm({ ...form, processo_numero: e.target.value })
                }
                required
              >
                <option value="">Selecione</option>
                {processosAtivos.map((p) => (
                  <option key={p.numero} value={p.numero}>
                    {p.numero}
                    {p.descricao ? ` — ${p.descricao}` : ""}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={openProcessoModal}
                className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-2 text-xs font-semibold text-shell-text hover:bg-[#2a4f86] sm:py-0"
                title="Cadastrar um processo sem perder os dados deste formulário"
              >
                + Novo processo
              </button>
            </div>
          </label>
          <label className="text-sm">
            <span className="text-shell-muted">
              Número do protocolo (Prot.)
            </span>
            <input
              className={`${inputClass()} mt-1 ${
                !form.processo_numero ? "cursor-not-allowed opacity-60" : ""
              }`}
              value={form.protocolo_numero}
              onChange={(e) =>
                setForm({ ...form, protocolo_numero: e.target.value })
              }
              disabled={!form.processo_numero}
              placeholder={
                form.processo_numero
                  ? "Ex.: PROT-2025-0001"
                  : "Selecione um processo primeiro"
              }
              required
            />
            {!form.processo_numero ? (
              <span className="mt-1 block text-xs text-shell-muted">
                O protocolo é vinculado ao processo escolhido acima.
              </span>
            ) : null}
          </label>
          <label className="text-sm">
            <span className="text-shell-muted">Unidade responsável</span>
            <select
              className={`${inputClass()} mt-1`}
              value={form.unidade_id || ""}
              onChange={(e) =>
                setForm({ ...form, unidade_id: Number(e.target.value) })
              }
              required
            >
              <option value="">Selecione</option>
              {unidades.map((u) => (
                <option key={String(u.id)} value={String(u.id)}>
                  {String(u.nome)}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-shell-muted">Cidade</span>
            <select
              className={`${inputClass()} mt-1`}
              value={form.cidade_id || ""}
              onChange={(e) =>
                setForm({ ...form, cidade_id: Number(e.target.value) })
              }
              required
            >
              <option value="">Selecione</option>
              {cidades.map((c) => (
                <option key={String(c.id)} value={String(c.id)}>
                  {String(c.nome)} ({String(c.uf_sigla)})
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-shell-muted">Delegacia</span>
            <select
              className={`${inputClass()} mt-1`}
              value={form.delegacia_id || ""}
              onChange={(e) =>
                setForm({ ...form, delegacia_id: Number(e.target.value) })
              }
              required
            >
              <option value="">Selecione</option>
              {delegaciasFiltradas.map((d) => (
                <option key={String(d.id)} value={String(d.id)}>
                  {String(d.nome)}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-shell-muted">Data da lavratura</span>
            <input
              type="date"
              className={`${inputClass()} mt-1`}
              value={form.data_lavratura}
              onChange={(e) =>
                setForm({ ...form, data_lavratura: e.target.value })
              }
              required
            />
          </label>
          <label className="text-sm">
            <span className="text-shell-muted">Hora</span>
            <input
              type="time"
              className={`${inputClass()} mt-1`}
              value={form.hora_lavratura}
              onChange={(e) =>
                setForm({ ...form, hora_lavratura: e.target.value })
              }
              required
            />
          </label>
        </div>,
      )}

      {section(
        "Autoridade e procedimento",
        <div className="space-y-4">
          <div className="flex flex-wrap items-end gap-3">
            <label className="block text-sm flex-1" style={{ minWidth: 280 }}>
              <span className="text-shell-muted">Equipe operacional</span>
              <select
                className={`${inputClass()} mt-1`}
                value={form.equipe_id || ""}
                onChange={(e) =>
                  setForm({ ...form, equipe_id: Number(e.target.value) })
                }
                required
              >
                <option value="">Selecione</option>
                {equipesAtivas.map((eq) => (
                  <option key={eq.id} value={eq.id}>
                    Equipe {eq.numero}
                    {eq.nome ? ` — ${eq.nome}` : ""} ({eq.agentes_count}{" "}
                    agente{eq.agentes_count === 1 ? "" : "s"})
                  </option>
                ))}
              </select>
            </label>
            <Link
              href="/cadastros/equipes"
              className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-2 text-xs font-semibold text-shell-text"
            >
              Gerenciar equipes
            </Link>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <label className="text-sm">
              <span className="text-shell-muted">
                Autoridade policial (delegado da equipe)
              </span>
              <input
                className={`${readonlyClass()} mt-1`}
                value={
                  equipeSelecionada
                    ? `${equipeSelecionada.delegado_nome ?? "—"}${
                        equipeSelecionada.delegado_matricula
                          ? ` (${equipeSelecionada.delegado_matricula})`
                          : ""
                      }`
                    : "Selecione uma equipe"
                }
                readOnly
              />
            </label>
            <label className="text-sm">
              <span className="text-shell-muted">Escrivão (da equipe)</span>
              <input
                className={`${readonlyClass()} mt-1`}
                value={
                  equipeSelecionada
                    ? equipeSelecionada.escrivao_nome ?? "—"
                    : "Selecione uma equipe"
                }
                readOnly
              />
            </label>
            <label className="text-sm">
              <span className="text-shell-muted">Tipo de procedimento</span>
              <select
                className={`${inputClass()} mt-1`}
                value={form.tipo_procedimento_id || ""}
                onChange={(e) =>
                  setForm({
                    ...form,
                    tipo_procedimento_id: Number(e.target.value),
                  })
                }
                required
              >
                <option value="">Selecione</option>
                {tipos.map((t) => (
                  <option key={String(t.id)} value={String(t.id)}>
                    {String(t.nome)}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              <span className="text-shell-muted">Número do procedimento</span>
              <input
                className={`${inputClass()} mt-1`}
                value={form.procedimento_numero}
                onChange={(e) =>
                  setForm({ ...form, procedimento_numero: e.target.value })
                }
                required
              />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="text-shell-muted">Fundamento legal</span>
              <textarea
                className={`${inputClass()} mt-1 min-h-28`}
                value={form.fundamento_legal}
                onChange={(e) =>
                  setForm({ ...form, fundamento_legal: e.target.value })
                }
                required
              />
            </label>
          </div>

          <div className="rounded border border-shell-border p-3">
            <p className="mb-2 text-xs uppercase tracking-[0.1em] text-shell-muted">
              Agentes integrantes da equipe selecionada
            </p>
            {form.equipe_id === 0 ? (
              <p className="text-sm text-shell-muted">
                Selecione uma equipe para visualizar seus agentes.
              </p>
            ) : agentesPreview.length === 0 ? (
              <p className="text-sm text-shell-muted">
                Nenhum agente vinculado a esta equipe.
              </p>
            ) : (
              <ul className="list-disc space-y-1 pl-5 text-sm text-shell-text">
                {agentesPreview.map((m) => (
                  <li key={m.id}>
                    {m.nome} — {m.matricula}
                    {m.funcao_padrao ? ` (${m.funcao_padrao})` : ""}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>,
      )}

      {section(
        "Local e diligência",
        <div className="space-y-3">
          <label className="text-sm block">
            <span className="text-shell-muted">Endereço da busca</span>
            <textarea
              className={`${inputClass()} mt-1 min-h-24`}
              value={form.endereco_busca}
              onChange={(e) =>
                setForm({ ...form, endereco_busca: e.target.value })
              }
              required
            />
          </label>
          <label className="text-sm block">
            <span className="text-shell-muted">Alvo</span>
            <input
              className={`${inputClass()} mt-1`}
              value={form.alvo_busca}
              onChange={(e) => setForm({ ...form, alvo_busca: e.target.value })}
              required
            />
          </label>
        </div>,
      )}

      {section(
        "Objetos arrecadados",
        <div className="space-y-2">
          <button
            type="button"
            className="rounded border border-shell-border px-3 py-1 text-xs text-shell-text"
            onClick={() =>
              setForm({
                ...form,
                objetos_arrecadados: [
                  ...form.objetos_arrecadados,
                  {
                    descricao: "",
                    quantidade: 1,
                    acondicionamento: "",
                    observacao: "",
                  },
                ],
              })
            }
          >
            Adicionar linha
          </button>
          {form.objetos_arrecadados.map((item, idx) => (
            <div key={`obj-${idx}`} className="grid grid-cols-1 gap-2 md:grid-cols-4">
              <input
                className={inputClass()}
                placeholder="Descrição"
                value={item.descricao}
                onChange={(e) => updateObjeto(idx, { descricao: e.target.value })}
              />
              <input
                type="number"
                min={1}
                className={inputClass()}
                value={item.quantidade}
                onChange={(e) =>
                  updateObjeto(idx, {
                    quantidade: Number(e.target.value || 1),
                  })
                }
              />
              <input
                className={inputClass()}
                placeholder="Acondicionamento"
                value={item.acondicionamento}
                onChange={(e) =>
                  updateObjeto(idx, { acondicionamento: e.target.value })
                }
              />
              <input
                className={inputClass()}
                placeholder="Obs."
                value={item.observacao}
                onChange={(e) =>
                  updateObjeto(idx, { observacao: e.target.value })
                }
              />
            </div>
          ))}
        </div>,
      )}

      {section(
        "Testemunhas",
        <div className="space-y-2">
          <button
            type="button"
            className="rounded border border-shell-border px-3 py-1 text-xs text-shell-text"
            onClick={() =>
              setForm({
                ...form,
                testemunhas: [
                  ...form.testemunhas,
                  { nome: "", documento: "", contato: "" },
                ],
              })
            }
          >
            Adicionar linha
          </button>
          {form.testemunhas.map((item, idx) => (
            <div key={`tes-${idx}`} className="grid grid-cols-1 gap-2 md:grid-cols-3">
              <input
                className={inputClass()}
                placeholder="Nome"
                value={item.nome}
                onChange={(e) => updateTestemunha(idx, { nome: e.target.value })}
              />
              <input
                className={inputClass()}
                placeholder="Documento"
                value={item.documento}
                onChange={(e) =>
                  updateTestemunha(idx, { documento: e.target.value })
                }
              />
              <input
                className={inputClass()}
                placeholder="Contato"
                value={item.contato}
                onChange={(e) =>
                  updateTestemunha(idx, { contato: e.target.value })
                }
              />
            </div>
          ))}
        </div>,
      )}

      {section(
        "Encerramento",
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <label className="text-sm md:col-span-2">
            <span className="text-shell-muted">Nome na linha de assinatura</span>
            <input
              className={`${inputClass()} mt-1`}
              value={form.assinatura_responsavel}
              onChange={(e) =>
                setForm({ ...form, assinatura_responsavel: e.target.value })
              }
              required
            />
          </label>
          <label className="text-sm md:col-span-2">
            <span className="text-shell-muted">Observações</span>
            <textarea
              className={`${inputClass()} mt-1 min-h-24`}
              value={form.observacoes}
              onChange={(e) =>
                setForm({ ...form, observacoes: e.target.value })
              }
            />
          </label>
        </div>,
      )}

      {error ? (
        <p className="rounded border border-red-700/60 bg-red-950/30 p-3 text-sm text-red-300">
          {error}
        </p>
      ) : null}

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg border border-shell-accent/50 bg-shell-accentBlue px-5 py-2 text-sm font-semibold text-shell-text hover:bg-[#2a4f86] disabled:opacity-60"
        >
          {submitting ? "Salvando..." : "Salvar"}
        </button>
      </div>

      {processoModalOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={(ev) => {
            if (ev.target === ev.currentTarget) closeProcessoModal();
          }}
        >
          <div
            className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-xl border border-shell-border bg-shell-surface p-6 shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="acba-novo-processo-titulo"
          >
            <h3
              id="acba-novo-processo-titulo"
              className="text-lg font-semibold text-shell-text"
            >
              Cadastrar novo processo
            </h3>
            <p className="mt-1 text-sm text-shell-muted">
              Os dados já preenchidos no ACBA são mantidos. O processo
              cadastrado é selecionado automaticamente ao salvar.
            </p>

            <div className="mt-4 flex flex-col gap-3">
              <label className="block text-sm">
                <span className="text-shell-muted">Número do processo</span>
                <input
                  className={`${inputClass()} mt-1`}
                  value={newProcessoNumero}
                  onChange={(e) => setNewProcessoNumero(e.target.value)}
                  onKeyDown={handleProcessoModalKeyDown}
                  placeholder="Ex.: 0001234-56.2025.8.07.0001"
                  autoFocus
                  disabled={savingProcesso}
                />
              </label>
              <label className="block text-sm">
                <span className="text-shell-muted">Descrição (opcional)</span>
                <input
                  className={`${inputClass()} mt-1`}
                  value={newProcessoDescricao}
                  onChange={(e) => setNewProcessoDescricao(e.target.value)}
                  onKeyDown={handleProcessoModalKeyDown}
                  placeholder="Ex.: Operação Aurora — alvo 1"
                  disabled={savingProcesso}
                />
              </label>
            </div>

            {processoModalError ? (
              <p className="mt-3 rounded border border-red-700/60 bg-red-950/30 p-3 text-sm text-red-300">
                {processoModalError}
              </p>
            ) : null}

            <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={closeProcessoModal}
                disabled={savingProcesso}
                className="rounded border border-shell-border px-4 py-2 text-sm text-shell-text disabled:opacity-60"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => void saveProcessoInline()}
                disabled={savingProcesso}
                className="rounded border border-shell-accent/50 bg-shell-accentBlue px-4 py-2 text-sm font-semibold text-shell-text hover:bg-[#2a4f86] disabled:opacity-60"
              >
                {savingProcesso ? "Salvando..." : "Cadastrar e usar"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </form>
  );
}
