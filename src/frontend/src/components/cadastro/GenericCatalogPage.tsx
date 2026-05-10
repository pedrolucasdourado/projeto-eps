"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type { CadastroDefinition, CatalogField } from "@/config/cadastro-registry";
import { apiRequest } from "@/lib/api";

function inputClass() {
  return "w-full rounded-lg border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text outline-none focus:border-shell-accent";
}

function emptyForm(fields: CatalogField[]): Record<string, string | boolean> {
  const o: Record<string, string | boolean> = {};
  for (const f of fields) {
    if (f.kind === "checkbox") o[f.name] = true;
    else if (f.kind === "select") o[f.name] = "";
    else if (f.kind === "enum") o[f.name] = f.options[0]?.value ?? "";
    else o[f.name] = "";
  }
  return o;
}

function serializePayload(fields: CatalogField[], raw: Record<string, string | boolean>) {
  const out: Record<string, unknown> = {};
  for (const f of fields) {
    const v = raw[f.name];
    if (f.kind === "checkbox") {
      out[f.name] = Boolean(v);
      continue;
    }
    if (f.kind === "select") {
      const s = String(v ?? "").trim();
      if (!s) {
        out[f.name] = f.optional ? null : undefined;
      } else {
        out[f.name] = Number(s);
      }
      continue;
    }
    if (f.kind === "enum") {
      out[f.name] = String(v ?? "").trim();
      continue;
    }
    out[f.name] = String(v ?? "").trim();
  }
  return out;
}

export function GenericCatalogPage({ config }: { config: CadastroDefinition }) {
  const idField = config.idField ?? "id";
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string | boolean>>(() =>
    emptyForm(config.fields),
  );
  const [optionCache, setOptionCache] = useState<Record<string, Record<string, unknown>[]>>({});

  const selectFields = useMemo(
    () => config.fields.filter((f): f is Extract<CatalogField, { kind: "select" }> => f.kind === "select"),
    [config.fields],
  );

  const loadOptions = useCallback(async () => {
    const next: Record<string, Record<string, unknown>[]> = {};
    for (const f of selectFields) {
      const data = await apiRequest<Record<string, unknown>[]>(f.optionsUrl);
      next[f.optionsUrl] = data;
    }
    setOptionCache(next);
  }, [selectFields]);

  const loadRows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = q.trim() ? `?q=${encodeURIComponent(q.trim())}` : "";
      const data = await apiRequest<Record<string, unknown>[]>(
        `${config.apiPath}${qs}`,
      );
      setRows(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar.");
    } finally {
      setLoading(false);
    }
  }, [config.apiPath, q]);

  useEffect(() => {
    void loadOptions().catch(() => setError("Erro ao carregar opções."));
  }, [loadOptions]);

  useEffect(() => {
    void loadRows();
  }, [loadRows]);

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm(config.fields));
    setModalOpen(true);
  }

  function openEdit(row: Record<string, unknown>) {
    const idValue = row[idField];
    const id = idValue != null ? String(idValue) : "";
    setEditingId(id);
    const nf = emptyForm(config.fields);
    for (const f of config.fields) {
      const val = row[f.name];
      if (f.kind === "checkbox") nf[f.name] = Boolean(val);
      else if (f.kind === "select") nf[f.name] = val != null ? String(val) : "";
      else if (f.kind === "enum") nf[f.name] = val != null ? String(val) : "";
      else nf[f.name] = val != null ? String(val) : "";
    }
    setForm(nf);
    setModalOpen(true);
  }

  async function saveModal() {
    setError(null);
    const payload = serializePayload(config.fields, form);
    for (const f of config.fields) {
      if (f.kind === "text" && f.required && !String(payload[f.name] ?? "").trim()) {
        setError(`Preencha ${f.label}.`);
        return;
      }
      if (
        f.kind === "select" &&
        !f.optional &&
        (payload[f.name] === undefined || payload[f.name] === null)
      ) {
        setError(`Selecione ${f.label}.`);
        return;
      }
      if (
        f.kind === "enum" &&
        f.required &&
        !String(payload[f.name] ?? "").trim()
      ) {
        setError(`Selecione ${f.label}.`);
        return;
      }
    }
    try {
      if (editingId == null) {
        await apiRequest(`${config.apiPath}`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
      } else {
        const updatePayload = { ...payload };
        if (config.identifierLocked) {
          delete updatePayload[idField];
        }
        await apiRequest(
          `${config.apiPath}/${encodeURIComponent(editingId)}`,
          {
            method: "PUT",
            body: JSON.stringify(updatePayload),
          },
        );
      }
      setModalOpen(false);
      await loadRows();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao salvar.");
    }
  }

  async function removeRow(id: string) {
    if (!confirm("Confirma exclusão?")) return;
    setError(null);
    try {
      await apiRequest(`${config.apiPath}/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      await loadRows();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao excluir.");
    }
  }

  function renderCell(row: Record<string, unknown>, key: string) {
    const v = row[key];
    if (typeof v === "boolean") return v ? "Sim" : "Não";
    if (v == null) return "—";
    return String(v);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-shell-text">{config.title}</h2>
        <button
          type="button"
          onClick={openCreate}
          className="rounded-lg border border-shell-accent/50 bg-shell-accentBlue px-4 py-2 text-sm font-semibold text-shell-text"
        >
          Novo registro
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          className={inputClass()}
          placeholder="Buscar..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ maxWidth: 320 }}
        />
        <button
          type="button"
          onClick={() => void loadRows()}
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
              {config.columns.map((c) => (
                <th key={c.key} className="px-4 py-3">
                  {c.label}
                </th>
              ))}
              <th className="px-4 py-3">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={config.columns.length + 1} className="px-4 py-6 text-shell-muted">
                  Carregando...
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={config.columns.length + 1} className="px-4 py-6 text-shell-muted">
                  Nenhum registro.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr
                  key={String(row[idField])}
                  className="border-t border-shell-border/70"
                >
                  {config.columns.map((c) => (
                    <td key={c.key} className="px-4 py-3 text-shell-text">
                      {renderCell(row, c.key)}
                    </td>
                  ))}
                  <td className="space-x-2 px-4 py-3">
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
                      onClick={() => removeRow(String(row[idField]))}
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
              {editingId == null ? "Novo" : "Editar"}
            </h3>
            <div className="flex flex-col gap-3">
              {config.fields.map((f) => {
                if (f.kind === "text") {
                  const isLockedIdentifier =
                    config.identifierLocked === true &&
                    editingId != null &&
                    f.name === idField;
                  return (
                    <label key={f.name} className="block text-sm">
                      <span className="text-shell-muted">{f.label}</span>
                      <input
                        className={`${inputClass()} mt-1 ${
                          isLockedIdentifier ? "opacity-60" : ""
                        }`}
                        value={String(form[f.name] ?? "")}
                        onChange={(e) =>
                          setForm({ ...form, [f.name]: e.target.value })
                        }
                        disabled={isLockedIdentifier}
                      />
                    </label>
                  );
                }
                if (f.kind === "checkbox") {
                  return (
                    <label key={f.name} className="flex items-center gap-2 text-sm text-shell-text">
                      <input
                        type="checkbox"
                        checked={Boolean(form[f.name])}
                        onChange={(e) =>
                          setForm({ ...form, [f.name]: e.target.checked })
                        }
                      />
                      {f.label}
                    </label>
                  );
                }
                if (f.kind === "enum") {
                  return (
                    <label key={f.name} className="block text-sm">
                      <span className="text-shell-muted">{f.label}</span>
                      <select
                        className={`${inputClass()} mt-1`}
                        value={String(form[f.name] ?? "")}
                        onChange={(e) =>
                          setForm({ ...form, [f.name]: e.target.value })
                        }
                      >
                        {!f.required ? <option value="">—</option> : null}
                        {f.options.map((o) => (
                          <option key={o.value} value={o.value}>
                            {o.label}
                          </option>
                        ))}
                      </select>
                    </label>
                  );
                }
                const opts = optionCache[f.optionsUrl] ?? [];
                return (
                  <label key={f.name} className="block text-sm">
                    <span className="text-shell-muted">{f.label}</span>
                    <select
                      className={`${inputClass()} mt-1`}
                      value={String(form[f.name] ?? "")}
                      onChange={(e) =>
                        setForm({ ...form, [f.name]: e.target.value })
                      }
                    >
                      <option value="">{f.optional ? "—" : "Selecione"}</option>
                      {opts.map((o) => (
                        <option key={String(o.id)} value={String(o.id)}>
                          {f.formatOption(o)}
                        </option>
                      ))}
                    </select>
                  </label>
                );
              })}
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
                onClick={() => void saveModal()}
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
