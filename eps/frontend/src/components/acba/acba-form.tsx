"use client";

import {
  type ReactNode,
  FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import { apiRequest } from "@/lib/api";
import type {
  AcbaDetail,
  AcbaFormPayload,
  ObjetoItem,
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

function emptyPayload(): AcbaFormPayload {
  return {
    numero_auto: "",
    unidade_id: 0,
    delegacia_id: 0,
    cidade_id: 0,
    data_lavratura: "",
    hora_lavratura: "",
    autoridade_id: 0,
    escrivao_id: 0,
    tipo_procedimento_id: 0,
    procedimento_numero: "",
    fundamento_legal: "",
    endereco_busca: "",
    alvo_busca: "",
    condutor_id: 0,
    assinatura_responsavel: "",
    observacoes: "",
    membro_ids: [],
    testemunhas: [],
    objetos_arrecadados: [],
  };
}

function detailToPayload(d: AcbaDetail): AcbaFormPayload {
  return {
    numero_auto: d.numero_auto,
    unidade_id: d.unidade_id,
    delegacia_id: d.delegacia_id,
    cidade_id: d.cidade_id,
    data_lavratura: d.data_lavratura.slice(0, 10),
    hora_lavratura: d.hora_lavratura.length >= 5 ? d.hora_lavratura.slice(0, 5) : d.hora_lavratura,
    autoridade_id: d.autoridade_id,
    escrivao_id: d.escrivao_id,
    tipo_procedimento_id: d.tipo_procedimento_id,
    procedimento_numero: d.procedimento_numero,
    fundamento_legal: d.fundamento_legal,
    endereco_busca: d.endereco_busca,
    alvo_busca: d.alvo_busca,
    condutor_id: d.condutor_id,
    assinatura_responsavel: d.assinatura_responsavel,
    observacoes: d.observacoes,
    membro_ids: [...d.membro_ids],
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
  const [autoridades, setAutoridades] = useState<Record<string, unknown>[]>([]);
  const [escrivaos, setEscrivaos] = useState<Record<string, unknown>[]>([]);
  const [membros, setMembros] = useState<Record<string, unknown>[]>([]);
  const [condutores, setCondutores] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    if (initialDetail) setForm(detailToPayload(initialDetail));
  }, [initialDetail]);

  useEffect(() => {
    async function load() {
      try {
        const [
          u,
          c,
          d,
          t,
          a,
          e,
          m,
          co,
        ] = await Promise.all([
          apiRequest<Record<string, unknown>[]>("/api/cadastros/unidades"),
          apiRequest<Record<string, unknown>[]>("/api/cadastros/cidades"),
          apiRequest<Record<string, unknown>[]>("/api/cadastros/delegacias"),
          apiRequest<Record<string, unknown>[]>("/api/cadastros/tipos-procedimento"),
          apiRequest<Record<string, unknown>[]>("/api/cadastros/autoridades"),
          apiRequest<Record<string, unknown>[]>("/api/cadastros/escrivaos"),
          apiRequest<Record<string, unknown>[]>("/api/cadastros/membros-equipe"),
          apiRequest<Record<string, unknown>[]>("/api/cadastros/condutores"),
        ]);
        setUnidades(u);
        setCidades(c);
        setDelegacias(d);
        setTipos(t);
        setAutoridades(a);
        setEscrivaos(e);
        setMembros(m);
        setCondutores(co);
      } catch {
        setError("Não foi possível carregar cadastros auxiliares.");
      }
    }
    void load();
  }, []);

  const delegaciasFiltradas = useMemo(() => {
    return delegacias.filter((row) => {
      const uid = form.unidade_id ? Number(form.unidade_id) : null;
      const cid = form.cidade_id ? Number(form.cidade_id) : null;
      if (uid && row.unidade_id != null && Number(row.unidade_id) !== uid) return false;
      if (cid && row.cidade_id != null && Number(row.cidade_id) !== cid) return false;
      return true;
    });
  }, [delegacias, form.unidade_id, form.cidade_id]);

  const autoridadesFiltradas = useMemo(() => {
    const did = form.delegacia_id ? Number(form.delegacia_id) : null;
    const uid = form.unidade_id ? Number(form.unidade_id) : null;
    return autoridades.filter((row) => {
      if (did) {
        if (row.delegacia_id == null || Number(row.delegacia_id) !== did) return false;
      }
      if (uid) {
        if (row.unidade_id == null || Number(row.unidade_id) !== uid) return false;
      }
      return true;
    });
  }, [autoridades, form.delegacia_id, form.unidade_id]);

  const escrivaosFiltrados = useMemo(() => {
    const did = form.delegacia_id ? Number(form.delegacia_id) : null;
    const uid = form.unidade_id ? Number(form.unidade_id) : null;
    return escrivaos.filter((row) => {
      if (did) {
        if (row.delegacia_id == null || Number(row.delegacia_id) !== did) return false;
      }
      if (uid) {
        if (row.unidade_id == null || Number(row.unidade_id) !== uid) return false;
      }
      return true;
    });
  }, [escrivaos, form.delegacia_id, form.unidade_id]);

  function toggleMembro(id: number) {
    setForm((prev) => {
      const set = new Set(prev.membro_ids);
      if (set.has(id)) set.delete(id);
      else set.add(id);
      return { ...prev, membro_ids: Array.from(set) };
    });
  }

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

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
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
      form.autoridade_id,
      form.escrivao_id,
      form.tipo_procedimento_id,
      form.condutor_id,
    ];
    if (ids.some((x) => !x || x < 1)) {
      setError("Selecione unidade, delegacia, cidade, autoridade, escrivão, tipo e condutor.");
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
            <span className="text-shell-muted">Número do auto</span>
            <input
              className={`${inputClass()} mt-1`}
              value={form.numero_auto}
              onChange={(e) => setForm({ ...form, numero_auto: e.target.value })}
              required
            />
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
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <label className="text-sm md:col-span-2">
            <span className="text-shell-muted">Autoridade policial</span>
            <select
              className={`${inputClass()} mt-1`}
              value={form.autoridade_id || ""}
              onChange={(e) =>
                setForm({ ...form, autoridade_id: Number(e.target.value) })
              }
              required
            >
              <option value="">Selecione</option>
              {autoridadesFiltradas.map((a) => (
                <option key={String(a.id)} value={String(a.id)}>
                  {String(a.nome)}
                  {a.matricula ? ` (${String(a.matricula)})` : ""}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm md:col-span-2">
            <span className="text-shell-muted">Escrivão</span>
            <select
              className={`${inputClass()} mt-1`}
              value={form.escrivao_id || ""}
              onChange={(e) =>
                setForm({ ...form, escrivao_id: Number(e.target.value) })
              }
              required
            >
              <option value="">Selecione</option>
              {escrivaosFiltrados.map((x) => (
                <option key={String(x.id)} value={String(x.id)}>
                  {String(x.nome)}
                </option>
              ))}
            </select>
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
        "Equipe operacional (cadastro)",
        <div className="max-h-56 space-y-2 overflow-y-auto rounded border border-shell-border p-3">
          {membros.map((m) => (
            <label key={String(m.id)} className="flex items-center gap-2 text-sm text-shell-text">
              <input
                type="checkbox"
                checked={form.membro_ids.includes(Number(m.id))}
                onChange={() => toggleMembro(Number(m.id))}
              />
              {String(m.nome)} — {String(m.matricula)}
              {m.funcao_padrao ? ` (${String(m.funcao_padrao)})` : ""}
            </label>
          ))}
          {membros.length === 0 ? (
            <p className="text-shell-muted">Cadastre membros em Cadastros auxiliares.</p>
          ) : null}
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
            <span className="text-shell-muted">Condutor da operação</span>
            <select
              className={`${inputClass()} mt-1`}
              value={form.condutor_id || ""}
              onChange={(e) =>
                setForm({ ...form, condutor_id: Number(e.target.value) })
              }
              required
            >
              <option value="">Selecione</option>
              {condutores.map((c) => (
                <option key={String(c.id)} value={String(c.id)}>
                  {String(c.nome)}
                  {c.matricula ? ` (${String(c.matricula)})` : ""}
                </option>
              ))}
            </select>
          </label>
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
    </form>
  );
}
