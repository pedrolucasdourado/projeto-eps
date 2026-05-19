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
  MaterialPayload,
  Processo,
  TestemunhaItem,
  TestemunhaTipo,
} from "@/types/acba";

import { MaterialsDraft } from "./materials-draft";
import { MaterialsManager } from "./materials-manager";

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

function emptyTestemunha(tipo: TestemunhaTipo = "geral"): TestemunhaItem {
  return {
    tipo,
    nome: "",
    cpf: "",
    rg: "",
    filiacao: "",
    endereco: "",
    cidade: tipo === "geral" ? "" : null,
    telefone: tipo === "geral" ? "" : null,
    arrombamento: tipo === "arrombamento" ? { observacoes: "" } : null,
  };
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
    nome_vara_criminal: "",
    nome_juiz: "",
    assinatura_responsavel: "",
    observacoes: "",
    equipe_id: 0,
    testemunhas: [],
    arrombamento_245_2: false,
    arrombamento_245_2_obs: "",
    forca_coisas_245_3: false,
    forca_coisas_245_3_obs: "",
    morador_ausente_245_4: false,
    morador_ausente_245_4_obs: "",
    morador_nome: "",
    morador_cpf: "",
    morador_rg: "",
    morador_filiacao: "",
    morador_telefone: "",
    materiais: [],
  };
}

function detailToPayload(d: AcbaDetail): AcbaFormPayload {
  const rawTestemunhas = (d.testemunhas as TestemunhaItem[]) ?? [];
  const testemunhas: TestemunhaItem[] = rawTestemunhas.map((t) => {
    const isArr = t.tipo === "arrombamento";
    return {
      tipo: t.tipo ?? "geral",
      nome: t.nome ?? "",
      cpf: t.cpf ?? "",
      rg: t.rg ?? "",
      filiacao: t.filiacao ?? "",
      endereco: t.endereco ?? "",
      cidade: isArr ? null : t.cidade ?? "",
      telefone: isArr ? null : t.telefone ?? "",
      arrombamento: isArr
        ? { observacoes: t.arrombamento?.observacoes ?? "" }
        : null,
    };
  });
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
    nome_vara_criminal: d.nome_vara_criminal ?? "",
    nome_juiz: d.nome_juiz ?? "",
    assinatura_responsavel: d.assinatura_responsavel,
    observacoes: d.observacoes,
    equipe_id: d.equipe_id,
    testemunhas,
    arrombamento_245_2: d.arrombamento_245_2 ?? false,
    arrombamento_245_2_obs: d.arrombamento_245_2_obs ?? "",
    forca_coisas_245_3: d.forca_coisas_245_3 ?? false,
    forca_coisas_245_3_obs: d.forca_coisas_245_3_obs ?? "",
    morador_ausente_245_4: d.morador_ausente_245_4 ?? false,
    morador_ausente_245_4_obs: d.morador_ausente_245_4_obs ?? "",
    morador_nome: d.morador_nome ?? "",
    morador_cpf: d.morador_cpf ?? "",
    morador_rg: d.morador_rg ?? "",
    morador_filiacao: d.morador_filiacao ?? "",
    morador_telefone: d.morador_telefone ?? "",
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

  function setTestemunhaTipo(i: number, tipo: TestemunhaTipo) {
    const next = [...form.testemunhas];
    const current = next[i];
    next[i] = {
      ...current,
      tipo,
      cidade: tipo === "geral" ? current.cidade ?? "" : null,
      telefone: tipo === "geral" ? current.telefone ?? "" : null,
      arrombamento:
        tipo === "arrombamento"
          ? current.arrombamento ?? { observacoes: "" }
          : null,
    };
    setForm({ ...form, testemunhas: next });
  }

  function updateArrombamentoObs(i: number, observacoes: string) {
    const next = [...form.testemunhas];
    const current = next[i];
    next[i] = { ...current, arrombamento: { observacoes } };
    setForm({ ...form, testemunhas: next });
  }

  function removeTestemunha(i: number) {
    const next = form.testemunhas.filter((_, idx) => idx !== i);
    setForm({ ...form, testemunhas: next });
  }

  function ensureArrombamentoWitness() {
    if (form.testemunhas.some((t) => t.tipo === "arrombamento")) return;
    setForm((prev) => ({
      ...prev,
      testemunhas: [...prev.testemunhas, emptyTestemunha("arrombamento")],
    }));
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
    if (form.arrombamento_245_2 && !form.arrombamento_245_2_obs.trim()) {
      setError(
        "Descreva as circunstâncias do arrombamento de porta (Art. 245, §2º do CPP).",
      );
      return;
    }
    if (form.forca_coisas_245_3 && !form.forca_coisas_245_3_obs.trim()) {
      setError(
        "Descreva o emprego de força contra coisas (Art. 245, §3º do CPP).",
      );
      return;
    }
    if (form.morador_ausente_245_4 && !form.morador_ausente_245_4_obs.trim()) {
      setError(
        "Descreva as circunstâncias da diligência com morador ausente (Art. 245, §4º do CPP).",
      );
      return;
    }
    // Cada testemunha exige a qualificação completa (nome, cpf, rg,
    // filiação, endereço); testemunhas gerais também precisam de cidade
    // e telefone.
    const testemunhaInvalida = form.testemunhas.find((t) => {
      if (
        t.nome.trim().length < 2 ||
        t.cpf.trim().length < 3 ||
        t.rg.trim().length < 1 ||
        t.filiacao.trim().length < 2 ||
        t.endereco.trim().length < 5
      ) {
        return true;
      }
      if (t.tipo === "geral") {
        if (
          (t.cidade ?? "").trim().length < 2 ||
          (t.telefone ?? "").trim().length < 4
        ) {
          return true;
        }
      }
      return false;
    });
    if (testemunhaInvalida) {
      setError(
        testemunhaInvalida.tipo === "arrombamento"
          ? "Toda testemunha de arrombamento (§4º) exige nome, CPF, RG, filiação e endereço."
          : "Toda testemunha exige nome, CPF, RG, filiação, endereço, cidade e telefone.",
      );
      return;
    }
    if (
      form.morador_ausente_245_4 &&
      !form.testemunhas.some((t) => t.tipo === "arrombamento")
    ) {
      setError(
        "Em diligências com morador ausente (Art. 245, §4º do CPP) é " +
          "obrigatório adicionar ao menos uma testemunha vizinha qualificada.",
      );
      return;
    }
    // Quando o morador NÃO estava ausente, a qualificação do morador é
    // obrigatória.
    if (!form.morador_ausente_245_4) {
      if (
        form.morador_nome.trim().length < 2 ||
        form.morador_cpf.trim().length < 3 ||
        form.morador_rg.trim().length < 1 ||
        form.morador_filiacao.trim().length < 2 ||
        form.morador_telefone.trim().length < 4
      ) {
        setError(
          "Informe nome, CPF, RG, filiação e telefone do morador presente.",
        );
        return;
      }
    }
    // Sanitiza: testemunhas gerais não devem carregar `arrombamento`, e
    // vice-versa; ao deixar §4º ativo, o backend já limpa os campos do
    // morador presente, mas zeramos aqui também por segurança.
    const testemunhasFinal: TestemunhaItem[] = form.testemunhas.map((t) =>
      t.tipo === "arrombamento"
        ? {
            ...t,
            cidade: null,
            telefone: null,
            arrombamento: t.arrombamento ?? { observacoes: "" },
          }
        : { ...t, arrombamento: null },
    );
    const morador = form.morador_ausente_245_4
      ? {
          morador_nome: "",
          morador_cpf: "",
          morador_rg: "",
          morador_filiacao: "",
          morador_telefone: "",
        }
      : {
          morador_nome: form.morador_nome,
          morador_cpf: form.morador_cpf,
          morador_rg: form.morador_rg,
          morador_filiacao: form.morador_filiacao,
          morador_telefone: form.morador_telefone,
        };
    try {
      await onSubmit({ ...form, ...morador, testemunhas: testemunhasFinal });
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
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <label className="text-sm block" htmlFor="acba-nome-vara-criminal">
              <span className="text-shell-muted">Vara criminal</span>
              <input
                id="acba-nome-vara-criminal"
                name="nome_vara_criminal"
                autoComplete="off"
                className={`${inputClass()} mt-1`}
                value={form.nome_vara_criminal}
                onChange={(e) =>
                  setForm({ ...form, nome_vara_criminal: e.target.value })
                }
                placeholder="Ex.: 2ª Vara Criminal de Brasília/DF"
              />
            </label>
            <label className="text-sm block" htmlFor="acba-nome-juiz">
              <span className="text-shell-muted">Juiz(a) que expediu o mandado</span>
              <input
                id="acba-nome-juiz"
                name="nome_juiz"
                autoComplete="off"
                className={`${inputClass()} mt-1`}
                value={form.nome_juiz}
                onChange={(e) => setForm({ ...form, nome_juiz: e.target.value })}
                placeholder="Ex.: Dr(a). Nome do(a) Juiz(a)"
              />
            </label>
          </div>
        </div>,
      )}

      {section(
        "Ocorrências da diligência (Art. 245 §§ 2º, 3º e 4º do CPP)",
        <div className="space-y-4">
          <p className="text-xs text-shell-muted">
            Marque a(s) hipótese(s) que se aplicaram à diligência. Quando uma
            caixa for marcada, é obrigatório descrever as circunstâncias no
            campo de observações correspondente.
          </p>

          <div className="rounded-lg border border-shell-border p-3">
            <label className="flex cursor-pointer items-start gap-2 text-sm text-shell-text">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 accent-shell-accent"
                checked={form.arrombamento_245_2}
                onChange={(e) =>
                  setForm({
                    ...form,
                    arrombamento_245_2: e.target.checked,
                    arrombamento_245_2_obs: e.target.checked
                      ? form.arrombamento_245_2_obs
                      : "",
                  })
                }
              />
              <span>
                Houve necessidade de arrombamento de porta ou entrada forçada
                em virtude de desobediência do morador
                <span className="text-shell-muted"> (Art. 245, §2º do CPB)</span>
              </span>
            </label>
            {form.arrombamento_245_2 ? (
              <textarea
                className={`${inputClass()} mt-2 min-h-20`}
                value={form.arrombamento_245_2_obs}
                onChange={(e) =>
                  setForm({ ...form, arrombamento_245_2_obs: e.target.value })
                }
                placeholder="Descreva como ocorreu o arrombamento / entrada forçada..."
                required
              />
            ) : null}
          </div>

          <div className="rounded-lg border border-shell-border p-3">
            <label className="flex cursor-pointer items-start gap-2 text-sm text-shell-text">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 accent-shell-accent"
                checked={form.forca_coisas_245_3}
                onChange={(e) =>
                  setForm({
                    ...form,
                    forca_coisas_245_3: e.target.checked,
                    forca_coisas_245_3_obs: e.target.checked
                      ? form.forca_coisas_245_3_obs
                      : "",
                  })
                }
              />
              <span>
                Foi necessário o emprego da força contra coisas existentes no
                interior da casa em virtude de recalcitrância do morador
                <span className="text-shell-muted"> (Art. 245, §3º do CPB)</span>
              </span>
            </label>
            {form.forca_coisas_245_3 ? (
              <textarea
                className={`${inputClass()} mt-2 min-h-20`}
                value={form.forca_coisas_245_3_obs}
                onChange={(e) =>
                  setForm({ ...form, forca_coisas_245_3_obs: e.target.value })
                }
                placeholder="Descreva o que foi rompido / forçado e as razões..."
                required
              />
            ) : null}
          </div>

          <div className="rounded-lg border border-shell-border p-3">
            <label className="flex cursor-pointer items-start gap-2 text-sm text-shell-text">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 accent-shell-accent"
                checked={form.morador_ausente_245_4}
                onChange={(e) => {
                  const checked = e.target.checked;
                  setForm({
                    ...form,
                    morador_ausente_245_4: checked,
                    morador_ausente_245_4_obs: checked
                      ? form.morador_ausente_245_4_obs
                      : "",
                  });
                  if (checked) ensureArrombamentoWitness();
                }}
              />
              <span>
                O morador estava ausente, sendo necessário o arrombamento de
                porta e emprego da força contra coisas existentes no interior
                da casa
                <span className="text-shell-muted"> (Art. 245, §4º do CPB)</span>
              </span>
            </label>
            {form.morador_ausente_245_4 ? (
              <>
                <textarea
                  className={`${inputClass()} mt-2 min-h-20`}
                  value={form.morador_ausente_245_4_obs}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      morador_ausente_245_4_obs: e.target.value,
                    })
                  }
                  placeholder="Descreva as circunstâncias (horário, modo de arrombamento, etc.)..."
                  required
                />
                <p className="mt-2 rounded border border-amber-700/50 bg-amber-950/30 p-2 text-xs text-amber-200">
                  Nesta hipótese é obrigatório qualificar pelo menos uma{" "}
                  <strong>testemunha vizinha</strong> (com CPF, RG, filiação e
                  endereço) na seção de testemunhas abaixo.
                </p>
              </>
            ) : null}
          </div>
        </div>,
      )}

      {form.morador_ausente_245_4
        ? null
        : section(
            "Morador presente",
            <div className="space-y-3">
              <p className="text-xs text-shell-muted">
                Quando o morador estava presente na diligência, é obrigatório
                qualificá-lo (Art. 245, caput e §1º do CPP). Esta seção fica
                oculta automaticamente quando a hipótese de morador ausente
                (§4º) é marcada acima.
              </p>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <label className="text-sm md:col-span-2">
                  <span className="text-shell-muted">Nome completo</span>
                  <input
                    className={`${inputClass()} mt-1`}
                    value={form.morador_nome}
                    onChange={(e) =>
                      setForm({ ...form, morador_nome: e.target.value })
                    }
                    required
                  />
                </label>
                <label className="text-sm">
                  <span className="text-shell-muted">CPF</span>
                  <input
                    className={`${inputClass()} mt-1`}
                    placeholder="000.000.000-00"
                    value={form.morador_cpf}
                    onChange={(e) =>
                      setForm({ ...form, morador_cpf: e.target.value })
                    }
                    required
                  />
                </label>
                <label className="text-sm">
                  <span className="text-shell-muted">RG</span>
                  <input
                    className={`${inputClass()} mt-1`}
                    placeholder="00.000.000-0"
                    value={form.morador_rg}
                    onChange={(e) =>
                      setForm({ ...form, morador_rg: e.target.value })
                    }
                    required
                  />
                </label>
                <label className="text-sm md:col-span-2">
                  <span className="text-shell-muted">
                    Filiação (pai e/ou mãe)
                  </span>
                  <input
                    className={`${inputClass()} mt-1`}
                    placeholder="Filho(a) de... e..."
                    value={form.morador_filiacao}
                    onChange={(e) =>
                      setForm({ ...form, morador_filiacao: e.target.value })
                    }
                    required
                  />
                </label>
                <label className="text-sm md:col-span-2">
                  <span className="text-shell-muted">Telefone</span>
                  <input
                    className={`${inputClass()} mt-1`}
                    placeholder="(61) 9 9999-9999"
                    value={form.morador_telefone}
                    onChange={(e) =>
                      setForm({ ...form, morador_telefone: e.target.value })
                    }
                    required
                  />
                </label>
              </div>
            </div>,
          )}

      {section(
        "Materiais apreendidos",
        initialDetail?.id ? (
          <MaterialsManager acbaId={initialDetail.id} />
        ) : (
          <MaterialsDraft
            value={form.materiais ?? []}
            onChange={(materiais: MaterialPayload[]) =>
              setForm({ ...form, materiais })
            }
          />
        ),
      )}

      {section(
        form.morador_ausente_245_4
          ? "Testemunhas (vizinha qualificada obrigatória — Art. 245, §4º do CPP)"
          : "Testemunhas",
        <div className="space-y-3">
          <p className="text-xs text-shell-muted">
            Marque cada testemunha como <strong>geral</strong> ou{" "}
            <strong>testemunha de arrombamento (§4º)</strong>. A testemunha de
            arrombamento (vizinha) é obrigatória quando o morador estava
            ausente e dispensa cidade/telefone; em troca permite anotar
            observações.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded border border-shell-border px-3 py-1 text-xs text-shell-text"
              onClick={() =>
                setForm({
                  ...form,
                  testemunhas: [...form.testemunhas, emptyTestemunha("geral")],
                })
              }
            >
              + Testemunha
            </button>
            <button
              type="button"
              className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-1 text-xs font-semibold text-shell-text hover:bg-[#2a4f86]"
              onClick={() =>
                setForm({
                  ...form,
                  testemunhas: [
                    ...form.testemunhas,
                    emptyTestemunha("arrombamento"),
                  ],
                })
              }
            >
              + Testemunha de arrombamento (§4º)
            </button>
          </div>
          {form.morador_ausente_245_4 &&
          !form.testemunhas.some((t) => t.tipo === "arrombamento") ? (
            <p className="rounded border border-amber-700/50 bg-amber-950/30 p-2 text-xs text-amber-200">
              Adicione ao menos uma testemunha de arrombamento (§4º) com
              qualificação completa.
            </p>
          ) : null}
          {form.testemunhas.map((item, idx) => {
            const isArr = item.tipo === "arrombamento";
            return (
              <div
                key={`tes-${idx}`}
                className={`rounded-lg border p-3 ${
                  isArr
                    ? "border-shell-accent/50 bg-shell-accentBlue/10"
                    : "border-shell-border"
                }`}
              >
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <label className="text-xs text-shell-muted">
                    Tipo da testemunha
                    <select
                      className={`${inputClass()} ml-2 inline-block w-auto py-1 text-xs`}
                      value={item.tipo}
                      onChange={(e) =>
                        setTestemunhaTipo(idx, e.target.value as TestemunhaTipo)
                      }
                    >
                      <option value="geral">Geral</option>
                      <option value="arrombamento">Arrombamento (§4º)</option>
                    </select>
                  </label>
                  <button
                    type="button"
                    onClick={() => removeTestemunha(idx)}
                    className="rounded border border-red-700/60 bg-red-950/30 px-2 py-1 text-xs text-red-300"
                    title="Remover testemunha"
                  >
                    Remover
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                  <label className="text-xs text-shell-muted md:col-span-2">
                    Nome completo
                    <input
                      className={`${inputClass()} mt-1`}
                      value={item.nome}
                      onChange={(e) =>
                        updateTestemunha(idx, { nome: e.target.value })
                      }
                      required
                    />
                  </label>
                  <label className="text-xs text-shell-muted">
                    CPF
                    <input
                      className={`${inputClass()} mt-1`}
                      placeholder="000.000.000-00"
                      value={item.cpf}
                      onChange={(e) =>
                        updateTestemunha(idx, { cpf: e.target.value })
                      }
                      required
                    />
                  </label>
                  <label className="text-xs text-shell-muted">
                    RG
                    <input
                      className={`${inputClass()} mt-1`}
                      placeholder="00.000.000-0"
                      value={item.rg}
                      onChange={(e) =>
                        updateTestemunha(idx, { rg: e.target.value })
                      }
                      required
                    />
                  </label>
                  <label className="text-xs text-shell-muted md:col-span-2">
                    Filiação (pai e/ou mãe)
                    <input
                      className={`${inputClass()} mt-1`}
                      placeholder="Filho(a) de... e..."
                      value={item.filiacao}
                      onChange={(e) =>
                        updateTestemunha(idx, { filiacao: e.target.value })
                      }
                      required
                    />
                  </label>
                  <label className="text-xs text-shell-muted md:col-span-2">
                    Endereço completo
                    <input
                      className={`${inputClass()} mt-1`}
                      placeholder="Logradouro, nº, complemento, bairro"
                      value={item.endereco}
                      onChange={(e) =>
                        updateTestemunha(idx, { endereco: e.target.value })
                      }
                      required
                    />
                  </label>
                  {!isArr ? (
                    <>
                      <label className="text-xs text-shell-muted">
                        Cidade
                        <input
                          className={`${inputClass()} mt-1`}
                          placeholder="Cidade/UF"
                          value={item.cidade ?? ""}
                          onChange={(e) =>
                            updateTestemunha(idx, { cidade: e.target.value })
                          }
                          required
                        />
                      </label>
                      <label className="text-xs text-shell-muted">
                        Telefone
                        <input
                          className={`${inputClass()} mt-1`}
                          placeholder="(61) 9 9999-9999"
                          value={item.telefone ?? ""}
                          onChange={(e) =>
                            updateTestemunha(idx, {
                              telefone: e.target.value,
                            })
                          }
                          required
                        />
                      </label>
                    </>
                  ) : (
                    <label className="text-xs text-shell-muted md:col-span-2">
                      Observações da testemunha de arrombamento
                      <textarea
                        className={`${inputClass()} mt-1 min-h-16`}
                        value={item.arrombamento?.observacoes ?? ""}
                        onChange={(e) =>
                          updateArrombamentoObs(idx, e.target.value)
                        }
                        placeholder="Relato livre da testemunha vizinha (opcional)"
                      />
                    </label>
                  )}
                </div>
              </div>
            );
          })}
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
