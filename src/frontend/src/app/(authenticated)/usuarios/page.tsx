"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { apiRequest } from "@/lib/api";

type UserRole = "administrador" | "delegado" | "escrivao" | "agente";

type AdminUser = {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  ativo: boolean;
  delegado_id: number | null;
  escrivao_id: number | null;
  agente_id: number | null;
  created_at: string;
};

type CadastroItem = {
  id: number;
  nome: string;
  matricula?: string | null;
  user_id?: number | null;
};

const ROLE_LABEL: Record<UserRole, string> = {
  administrador: "Administrador",
  delegado: "Delegado",
  escrivao: "Escrivão",
  agente: "Agente",
};

const FORM_ROLES: { value: Exclude<UserRole, "administrador">; label: string }[] = [
  { value: "delegado", label: "Delegado" },
  { value: "escrivao", label: "Escrivão" },
  { value: "agente", label: "Agente" },
];

function cadastroEndpoint(role: Exclude<UserRole, "administrador">): string {
  return {
    delegado: "/api/cadastros/delegados",
    escrivao: "/api/cadastros/escrivaos",
    agente: "/api/cadastros/agentes",
  }[role];
}

export default function UsuariosPage() {
  const [items, setItems] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<AdminUser | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiRequest<AdminUser[]>("/api/users/");
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleToggleAtivo(u: AdminUser) {
    try {
      await apiRequest(`/api/users/${u.id}`, {
        method: "PUT",
        body: JSON.stringify({ ativo: !u.ativo }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar.");
    }
  }

  async function handleDelete(u: AdminUser) {
    if (!confirm(`Excluir o usuário ${u.email}?`)) return;
    try {
      await apiRequest(`/api/users/${u.id}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir.");
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-shell-text">Usuários</h2>
          <p className="text-sm text-shell-muted">
            Cadastro de delegados, escrivãos e agentes com acesso ao sistema.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setEditing(null);
            setShowForm(true);
          }}
          className="rounded-lg border border-shell-accent/50 bg-shell-accentBlue px-4 py-2 text-sm font-semibold text-shell-text"
        >
          Novo usuário
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
              <th className="px-4 py-3">Nome</th>
              <th className="px-4 py-3">E-mail</th>
              <th className="px-4 py-3">Papel</th>
              <th className="px-4 py-3">Vínculo</th>
              <th className="px-4 py-3">Ativo</th>
              <th className="px-4 py-3">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td className="px-4 py-6 text-shell-muted" colSpan={6}>
                  Carregando...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-shell-muted" colSpan={6}>
                  Nenhum usuário cadastrado.
                </td>
              </tr>
            ) : (
              items.map((u) => (
                <tr key={u.id} className="border-t border-shell-border/70">
                  <td className="px-4 py-3 text-shell-text">
                    {u.full_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-shell-text">{u.email}</td>
                  <td className="px-4 py-3 text-shell-text">
                    {ROLE_LABEL[u.role]}
                  </td>
                  <td className="px-4 py-3 text-xs text-shell-muted">
                    {u.delegado_id
                      ? `Delegado #${u.delegado_id}`
                      : u.escrivao_id
                        ? `Escrivão #${u.escrivao_id}`
                        : u.agente_id
                          ? `Agente #${u.agente_id}`
                          : "—"}
                  </td>
                  <td className="px-4 py-3 text-xs">
                    {u.ativo ? (
                      <span className="rounded bg-green-900/40 px-2 py-1 text-green-200">
                        ativo
                      </span>
                    ) : (
                      <span className="rounded bg-red-900/40 px-2 py-1 text-red-300">
                        inativo
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setEditing(u);
                          setShowForm(true);
                        }}
                        className="rounded border border-shell-border bg-shell-surface px-2 py-1 text-xs text-shell-text hover:border-shell-accent hover:text-shell-accent"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleToggleAtivo(u)}
                        className="rounded border border-shell-border bg-shell-surface px-2 py-1 text-xs text-shell-text hover:border-shell-accent hover:text-shell-accent"
                      >
                        {u.ativo ? "Desativar" : "Reativar"}
                      </button>
                      {u.role !== "administrador" ? (
                        <button
                          type="button"
                          onClick={() => void handleDelete(u)}
                          className="rounded border border-red-700/60 bg-red-950/30 px-2 py-1 text-xs text-red-300"
                        >
                          Excluir
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showForm ? (
        <UserForm
          target={editing}
          onClose={() => {
            setShowForm(false);
            setEditing(null);
          }}
          onSaved={() => {
            setShowForm(false);
            setEditing(null);
            void load();
          }}
        />
      ) : null}
    </div>
  );
}

function UserForm({
  target,
  onClose,
  onSaved,
}: {
  target: AdminUser | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = Boolean(target);
  const [email, setEmail] = useState(target?.email ?? "");
  const [fullName, setFullName] = useState(target?.full_name ?? "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Exclude<UserRole, "administrador">>(
    target && target.role !== "administrador" ? target.role : "delegado",
  );
  const [cadastroId, setCadastroId] = useState<number | "">(
    target?.delegado_id ?? target?.escrivao_id ?? target?.agente_id ?? "",
  );
  const [ativo, setAtivo] = useState<boolean>(target?.ativo ?? true);
  const [cadastros, setCadastros] = useState<CadastroItem[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const roleParaCadastro = useMemo(() => {
    if (isEdit && target && target.role !== "administrador") return target.role;
    return role;
  }, [isEdit, role, target]);

  useEffect(() => {
    // Edição de administrador não permite trocar papel/vínculo: oculta o select.
    if (isEdit && target?.role === "administrador") return;
    let cancel = false;
    async function load() {
      try {
        const data = await apiRequest<CadastroItem[]>(
          cadastroEndpoint(roleParaCadastro),
        );
        if (!cancel) setCadastros(data);
      } catch (err) {
        if (!cancel)
          setError(err instanceof Error ? err.message : "Erro ao carregar cadastros.");
      }
    }
    void load();
    return () => {
      cancel = true;
    };
  }, [roleParaCadastro, isEdit, target]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (isEdit && target) {
        const body: Record<string, unknown> = {
          full_name: fullName,
          ativo,
        };
        if (password) body.password = password;
        if (target.role !== "administrador") {
          // Permite trocar/desvincular o cadastro (0 = desvincular).
          const v = cadastroId === "" ? 0 : Number(cadastroId);
          if (target.role === "delegado") body.delegado_id = v;
          if (target.role === "escrivao") body.escrivao_id = v;
          if (target.role === "agente") body.agente_id = v;
        }
        await apiRequest(`/api/users/${target.id}`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
      } else {
        const body: Record<string, unknown> = {
          email,
          password,
          full_name: fullName,
          role,
          ativo,
        };
        if (cadastroId !== "") {
          if (role === "delegado") body.delegado_id = Number(cadastroId);
          if (role === "escrivao") body.escrivao_id = Number(cadastroId);
          if (role === "agente") body.agente_id = Number(cadastroId);
        }
        await apiRequest("/api/users/", {
          method: "POST",
          body: JSON.stringify(body),
        });
      }
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-lg rounded-2xl border border-shell-border bg-shell-surface p-6 shadow-2xl"
      >
        <h3 className="text-lg font-semibold text-shell-text">
          {isEdit ? "Editar usuário" : "Novo usuário"}
        </h3>
        <p className="mt-1 text-xs text-shell-muted">
          {isEdit
            ? "Atualize os dados; a senha só é alterada se preenchida."
            : "Crie um usuário e vincule (opcional) a um cadastro existente."}
        </p>

        <div className="mt-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-shell-muted">
              Nome completo
            </label>
            <input
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-1 w-full rounded border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-shell-muted">
              E-mail
            </label>
            <input
              type="email"
              required
              disabled={isEdit}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text disabled:opacity-60"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-shell-muted">
              Senha {isEdit ? "(deixe em branco para manter)" : ""}
            </label>
            <input
              type="password"
              required={!isEdit}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text"
              minLength={6}
            />
          </div>

          {!isEdit ? (
            <div>
              <label className="block text-xs font-medium text-shell-muted">
                Papel
              </label>
              <select
                value={role}
                onChange={(e) =>
                  setRole(
                    e.target.value as Exclude<UserRole, "administrador">,
                  )
                }
                className="mt-1 w-full rounded border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text"
              >
                {FORM_ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <p className="text-xs text-shell-muted">
              Papel: <strong>{ROLE_LABEL[target!.role]}</strong>
            </p>
          )}

          {(!isEdit || (isEdit && target?.role !== "administrador")) && (
            <div>
              <label className="block text-xs font-medium text-shell-muted">
                Cadastro vinculado{" "}
                <span className="text-shell-muted/70">(opcional)</span>
              </label>
              <select
                value={cadastroId}
                onChange={(e) =>
                  setCadastroId(
                    e.target.value === "" ? "" : Number(e.target.value),
                  )
                }
                className="mt-1 w-full rounded border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text"
              >
                <option value="">— sem vínculo —</option>
                {cadastros.map((c) => (
                  <option
                    key={c.id}
                    value={c.id}
                    disabled={
                      Boolean(c.user_id) &&
                      c.user_id !== (target?.id ?? -1)
                    }
                  >
                    {c.nome}
                    {c.matricula ? ` — ${c.matricula}` : ""}
                    {c.user_id && c.user_id !== (target?.id ?? -1)
                      ? " (já vinculado)"
                      : ""}
                  </option>
                ))}
              </select>
            </div>
          )}

          <label className="flex items-center gap-2 text-sm text-shell-text">
            <input
              type="checkbox"
              checked={ativo}
              onChange={(e) => setAtivo(e.target.checked)}
            />
            Ativo
          </label>
        </div>

        {error ? (
          <p className="mt-3 rounded border border-red-700/60 bg-red-950/30 p-2 text-xs text-red-300">
            {error}
          </p>
        ) : null}

        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-shell-border bg-shell-surface px-3 py-2 text-sm text-shell-text"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={saving}
            className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-2 text-sm font-semibold text-shell-text disabled:opacity-60"
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </div>
  );
}
