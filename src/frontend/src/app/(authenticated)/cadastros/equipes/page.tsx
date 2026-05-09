"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiRequest } from "@/lib/api";
import type { EquipeOperacional } from "@/types/acba";

type RefRow = { id: number; nome: string; matricula?: string | null };

function inputClass() {
  return "w-full rounded-lg border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text outline-none focus:border-shell-accent";
}

type FormState = {
  numero: string;
  nome: string;
  delegado_id: string;
  escrivao_id: string;
  ativo: boolean;
};

function emptyForm(): FormState {
  return {
    numero: "",
    nome: "",
    delegado_id: "",
    escrivao_id: "",
    ativo: true,
  };
}

export default function EquipesPage() {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<EquipeOperacional[]>([]);
  const [delegados, setDelegados] = useState<RefRow[]>([]);
  const [escrivaos, setEscrivaos] = useState<RefRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);

  const loadRefs = useCallback(async () => {
    try {
      const [d, e] = await Promise.all([
        apiRequest<RefRow[]>("/api/cadastros/delegados"),
        apiRequest<RefRow[]>("/api/cadastros/escrivaos"),
      ]);
      setDelegados(d);
      setEscrivaos(e);
    } catch {
      setError("Não foi possível carregar delegados/escrivãos.");
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = q.trim() ? `?q=${encodeURIComponent(q.trim())}` : "";
      const data = await apiRequest<EquipeOperacional[]>(
        `/api/cadastros/equipes${qs}`,
      );
      setRows(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar.");
    } finally {
      setLoading(false);
    }
  }, [q]);

  useEffect(() => {
    void loadRefs();
  }, [loadRefs]);

  useEffect(() => {
    void load();
  }, [load]);

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm());
    setModalOpen(true);
  }

  function openEdit(row: EquipeOperacional) {
    setEditingId(row.id);
    setForm({
      numero: row.numero,
      nome: row.nome ?? "",
      delegado_id: String(row.delegado_id),
      escrivao_id: String(row.escrivao_id),
      ativo: row.ativo,
    });
    setModalOpen(true);
  }

  async function save() {
    setError(null);
    if (!form.numero.trim()) {
      setError("Informe o número/identificador da equipe.");
      return;
    }
    if (!form.delegado_id || !form.escrivao_id) {
      setError("Selecione o delegado e o escrivão da equipe.");
      return;
    }
    const payload = {
      numero: form.numero.trim(),
      nome: form.nome.trim() ? form.nome.trim() : null,
      delegado_id: Number(form.delegado_id),
      escrivao_id: Number(form.escrivao_id),
      ativo: form.ativo,
    };
    try {
      if (editingId == null) {
        await apiRequest("/api/cadastros/equipes", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      } else {
        await apiRequest(`/api/cadastros/equipes/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      }
      setModalOpen(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao salvar.");
    }
  }

  async function remove(id: number) {
    if (!confirm("Excluir a equipe? Isto pode falhar se houver ACBAs vinculados.")) {
      return;
    }
    setError(null);
    try {
      await apiRequest(`/api/cadastros/equipes/${id}`, { method: "DELETE" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao excluir.");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-shell-text">
          Equipes operacionais
        </h2>
        <button
          type="button"
          onClick={openCreate}
          className="rounded-lg border border-shell-accent/50 bg-shell-accentBlue px-4 py-2 text-sm font-semibold text-shell-text"
        >
          Nova equipe
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          className={inputClass()}
          placeholder="Buscar por número ou nome..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ maxWidth: 320 }}
        />
        <button
          type="button"
          onClick={() => void load()}
          className="rounded border border-shell-border px-3 py-2 text-sm text-shell-text"
        >
          Filtrar
        </button>
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
              <th className="px-4 py-3">Número</th>
              <th className="px-4 py-3">Nome</th>
              <th className="px-4 py-3">Delegado</th>
              <th className="px-4 py-3">Escrivão</th>
              <th className="px-4 py-3">Agentes</th>
              <th className="px-4 py-3">Ativo</th>
              <th className="px-4 py-3">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-shell-muted">
                  Carregando...
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-shell-muted">
                  Nenhuma equipe cadastrada.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="border-t border-shell-border/70">
                  <td className="px-4 py-3 font-mono text-shell-text">{row.numero}</td>
                  <td className="px-4 py-3 text-shell-text">{row.nome ?? "—"}</td>
                  <td className="px-4 py-3 text-shell-text">
                    {row.delegado_nome ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-shell-text">
                    {row.escrivao_nome ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-shell-text">{row.agentes_count}</td>
                  <td className="px-4 py-3 text-shell-text">
                    {row.ativo ? "Sim" : "Não"}
                  </td>
                  <td className="space-x-2 px-4 py-3">
                    <Link
                      href={`/cadastros/equipes/${row.id}/agentes`}
                      className="text-shell-accent hover:underline"
                    >
                      Agentes
                    </Link>
                    <Link
                      href={`/cadastros/equipes/${row.id}/acbas`}
                      className="text-shell-accent hover:underline"
                    >
                      ACBAs
                    </Link>
                    <button
                      type="button"
                      className="text-shell-accent hover:underline"
                      onClick={() => openEdit(row)}
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      className="text-red-300 hover:underline"
                      onClick={() => void remove(row.id)}
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {modalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-shell-border bg-shell-surface p-6 shadow-2xl">
            <h3 className="mb-4 text-lg font-semibold text-shell-text">
              {editingId == null ? "Nova equipe" : "Editar equipe"}
            </h3>
            <div className="flex flex-col gap-3">
              <label className="block text-sm">
                <span className="text-shell-muted">Número / Identificador</span>
                <input
                  className={`${inputClass()} mt-1`}
                  value={form.numero}
                  onChange={(e) => setForm({ ...form, numero: e.target.value })}
                />
              </label>
              <label className="block text-sm">
                <span className="text-shell-muted">Nome (opcional)</span>
                <input
                  className={`${inputClass()} mt-1`}
                  value={form.nome}
                  onChange={(e) => setForm({ ...form, nome: e.target.value })}
                />
              </label>
              <label className="block text-sm">
                <span className="text-shell-muted">Delegado (autoridade responsável)</span>
                <select
                  className={`${inputClass()} mt-1`}
                  value={form.delegado_id}
                  onChange={(e) =>
                    setForm({ ...form, delegado_id: e.target.value })
                  }
                >
                  <option value="">Selecione</option>
                  {delegados.map((d) => (
                    <option key={d.id} value={String(d.id)}>
                      {d.nome}
                      {d.matricula ? ` (${d.matricula})` : ""}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-shell-muted">Escrivão</span>
                <select
                  className={`${inputClass()} mt-1`}
                  value={form.escrivao_id}
                  onChange={(e) =>
                    setForm({ ...form, escrivao_id: e.target.value })
                  }
                >
                  <option value="">Selecione</option>
                  {escrivaos.map((e) => (
                    <option key={e.id} value={String(e.id)}>
                      {e.nome}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex items-center gap-2 text-sm text-shell-text">
                <input
                  type="checkbox"
                  checked={form.ativo}
                  onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
                />
                Ativo
              </label>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                className="rounded border border-shell-border px-4 py-2 text-sm text-shell-text"
                onClick={() => setModalOpen(false)}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="rounded border border-shell-accent/50 bg-shell-accentBlue px-4 py-2 text-sm font-semibold text-shell-text"
                onClick={() => void save()}
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
