"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { apiRequest } from "@/lib/api";
import type { AgenteBrief, EquipeOperacional } from "@/types/acba";

type Agente = AgenteBrief & { ativo?: boolean };

type NovoAgente = {
  nome: string;
  matricula: string;
  funcao_padrao: string;
};

function inputClass() {
  return "w-full rounded-lg border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text outline-none focus:border-shell-accent";
}

function emptyNovo(): NovoAgente {
  return { nome: "", matricula: "", funcao_padrao: "" };
}

export default function EquipeAgentesPage() {
  const params = useParams<{ id: string }>();
  const equipeId = Number(params.id);

  const [equipe, setEquipe] = useState<EquipeOperacional | null>(null);
  const [agentesEquipe, setAgentesEquipe] = useState<Agente[]>([]);
  const [todos, setTodos] = useState<Agente[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [busca, setBusca] = useState("");
  const [adicionarOpen, setAdicionarOpen] = useState(false);
  const [selecionados, setSelecionados] = useState<Set<number>>(new Set());

  const [novoOpen, setNovoOpen] = useState(false);
  const [novo, setNovo] = useState<NovoAgente>(emptyNovo());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [eq, ags, allAgs] = await Promise.all([
        apiRequest<EquipeOperacional>(`/api/cadastros/equipes/${equipeId}`),
        apiRequest<Agente[]>(`/api/cadastros/equipes/${equipeId}/agentes`),
        apiRequest<Agente[]>(`/api/cadastros/agentes`),
      ]);
      setEquipe(eq);
      setAgentesEquipe(ags);
      setTodos(allAgs);
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

  const agentesIds = useMemo(
    () => new Set(agentesEquipe.map((m) => m.id)),
    [agentesEquipe],
  );

  const candidatos = useMemo(() => {
    const term = busca.trim().toLowerCase();
    return todos
      .filter((a) => !agentesIds.has(a.id))
      .filter((a) => {
        if (!term) return true;
        return (
          a.nome.toLowerCase().includes(term) ||
          a.matricula.toLowerCase().includes(term)
        );
      });
  }, [todos, agentesIds, busca]);

  async function salvarAgentes(novoConjunto: number[]) {
    setSaving(true);
    setError(null);
    try {
      const atualizados = await apiRequest<Agente[]>(
        `/api/cadastros/equipes/${equipeId}/agentes`,
        {
          method: "PUT",
          body: JSON.stringify({ agente_ids: novoConjunto }),
        },
      );
      setAgentesEquipe(atualizados);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao salvar agentes.");
    } finally {
      setSaving(false);
    }
  }

  async function removerAgente(id: number) {
    if (!confirm("Remover este agente da equipe?")) return;
    const novoConjunto = agentesEquipe.filter((a) => a.id !== id).map((a) => a.id);
    await salvarAgentes(novoConjunto);
  }

  function toggleCandidato(id: number) {
    setSelecionados((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function confirmarAdicionar() {
    if (selecionados.size === 0) {
      setAdicionarOpen(false);
      return;
    }
    const novoConjunto = Array.from(
      new Set([
        ...agentesEquipe.map((a) => a.id),
        ...Array.from(selecionados),
      ]),
    );
    await salvarAgentes(novoConjunto);
    setSelecionados(new Set());
    setAdicionarOpen(false);
  }

  async function criarNovoAgente() {
    setError(null);
    if (!novo.nome.trim() || !novo.matricula.trim()) {
      setError("Preencha nome e matrícula do agente.");
      return;
    }
    try {
      const criado = await apiRequest<Agente>(`/api/cadastros/agentes`, {
        method: "POST",
        body: JSON.stringify({
          nome: novo.nome.trim(),
          matricula: novo.matricula.trim(),
          funcao_padrao: novo.funcao_padrao.trim() || null,
          ativo: true,
        }),
      });
      const novoConjunto = Array.from(
        new Set([...agentesEquipe.map((a) => a.id), criado.id]),
      );
      await salvarAgentes(novoConjunto);
      setTodos((prev) => [...prev, criado]);
      setNovo(emptyNovo());
      setNovoOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao criar agente.");
    }
  }

  if (!Number.isFinite(equipeId)) {
    return <p className="text-red-300">ID inválido.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
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
                Agentes da equipe{" "}
                <span className="font-mono">{equipe.numero}</span>
                {equipe.nome ? ` — ${equipe.nome}` : ""}
              </>
            ) : (
              "Agentes da equipe"
            )}
          </h2>
          {equipe ? (
            <p className="text-xs text-shell-muted">
              {agentesEquipe.length} agente(s) vinculado(s) • Delegado:{" "}
              {equipe.delegado_nome ?? "—"} • Escrivão:{" "}
              {equipe.escrivao_nome ?? "—"}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => {
              setSelecionados(new Set());
              setBusca("");
              setAdicionarOpen(true);
            }}
            className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-2 text-sm font-semibold text-shell-text"
          >
            Adicionar agentes existentes
          </button>
          <button
            type="button"
            onClick={() => {
              setNovo(emptyNovo());
              setNovoOpen(true);
            }}
            className="rounded border border-shell-border px-3 py-2 text-sm text-shell-text"
          >
            Cadastrar novo agente
          </button>
        </div>
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
              <th className="px-4 py-3">Nome</th>
              <th className="px-4 py-3">Matrícula</th>
              <th className="px-4 py-3">Função</th>
              <th className="px-4 py-3">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-shell-muted">
                  Carregando...
                </td>
              </tr>
            ) : agentesEquipe.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-shell-muted">
                  Nenhum agente vinculado a esta equipe.
                </td>
              </tr>
            ) : (
              agentesEquipe.map((a) => (
                <tr key={a.id} className="border-t border-shell-border/70">
                  <td className="px-4 py-3 text-shell-text">{a.nome}</td>
                  <td className="px-4 py-3 text-shell-text">{a.matricula}</td>
                  <td className="px-4 py-3 text-shell-text">
                    {a.funcao_padrao ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void removerAgente(a.id)}
                      className="text-red-300 hover:underline disabled:opacity-60"
                    >
                      Remover da equipe
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {adicionarOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-shell-border bg-shell-surface p-6 shadow-2xl">
            <h3 className="mb-3 text-lg font-semibold text-shell-text">
              Adicionar agentes à equipe
            </h3>
            <input
              className={inputClass()}
              placeholder="Buscar por nome ou matrícula"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
            <div className="mt-4 max-h-72 overflow-y-auto rounded border border-shell-border p-2">
              {candidatos.length === 0 ? (
                <p className="px-2 py-3 text-sm text-shell-muted">
                  Nenhum agente disponível para adicionar.
                </p>
              ) : (
                candidatos.map((a) => (
                  <label
                    key={a.id}
                    className="flex items-center gap-2 px-2 py-1 text-sm text-shell-text"
                  >
                    <input
                      type="checkbox"
                      checked={selecionados.has(a.id)}
                      onChange={() => toggleCandidato(a.id)}
                    />
                    {a.nome} — {a.matricula}
                    {a.funcao_padrao ? ` (${a.funcao_padrao})` : ""}
                  </label>
                ))
              )}
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded border border-shell-border px-4 py-2 text-sm text-shell-text"
                onClick={() => setAdicionarOpen(false)}
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={saving}
                className="rounded border border-shell-accent/50 bg-shell-accentBlue px-4 py-2 text-sm font-semibold text-shell-text disabled:opacity-60"
                onClick={() => void confirmarAdicionar()}
              >
                {saving ? "Salvando..." : "Adicionar"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {novoOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-shell-border bg-shell-surface p-6 shadow-2xl">
            <h3 className="mb-3 text-lg font-semibold text-shell-text">
              Cadastrar novo agente e adicionar à equipe
            </h3>
            <div className="flex flex-col gap-3">
              <label className="block text-sm">
                <span className="text-shell-muted">Nome</span>
                <input
                  className={`${inputClass()} mt-1`}
                  value={novo.nome}
                  onChange={(e) => setNovo({ ...novo, nome: e.target.value })}
                />
              </label>
              <label className="block text-sm">
                <span className="text-shell-muted">Matrícula</span>
                <input
                  className={`${inputClass()} mt-1`}
                  value={novo.matricula}
                  onChange={(e) =>
                    setNovo({ ...novo, matricula: e.target.value })
                  }
                />
              </label>
              <label className="block text-sm">
                <span className="text-shell-muted">Função padrão (opcional)</span>
                <input
                  className={`${inputClass()} mt-1`}
                  value={novo.funcao_padrao}
                  onChange={(e) =>
                    setNovo({ ...novo, funcao_padrao: e.target.value })
                  }
                />
              </label>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded border border-shell-border px-4 py-2 text-sm text-shell-text"
                onClick={() => setNovoOpen(false)}
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={saving}
                className="rounded border border-shell-accent/50 bg-shell-accentBlue px-4 py-2 text-sm font-semibold text-shell-text disabled:opacity-60"
                onClick={() => void criarNovoAgente()}
              >
                {saving ? "Salvando..." : "Salvar e adicionar"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
