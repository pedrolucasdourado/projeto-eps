"use client";

import {
  ChangeEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { apiRequest } from "@/lib/api";
import type {
  CategoriaDocx,
  DescribeResponse,
  InformaticaPayload,
  MaterialItem,
  MaterialPayload,
  SenhaTipo,
  TipoMaterial,
} from "@/types/acba";

import { PatternInput } from "./pattern-input";

type Props = {
  acbaId: number;
};

function emptyInformatica(): InformaticaPayload {
  return {
    senha_tipo: "nenhuma",
    senha_texto: null,
    senha_padrao_pontos: null,
    senha_observacao: null,
  };
}

function tabelaDoTipo(
  tipos: TipoMaterial[],
  tipoId: number,
): CategoriaDocx | undefined {
  return tipos.find((t) => t.id === tipoId)?.tabela_documento;
}

function emptyMaterial(tipos: TipoMaterial[]): MaterialPayload {
  const first = tipos[0];
  const tabela: CategoriaDocx = first?.tabela_documento ?? "geral";
  return {
    tipo_id: first?.id ?? 0,
    descricao: "",
    revisado: false,
    item_num: null,
    acondicionamento: "",
    localizacao: "",
    observacao: "",
    ordem: 0,
    informatica: tabela === "informatica" ? emptyInformatica() : null,
  };
}

function inputClass() {
  return "w-full rounded-lg border border-shell-border bg-shell-bg px-3 py-2 text-sm text-shell-text outline-none focus:border-shell-accent";
}

export function MaterialsManager({ acbaId }: Props) {
  const [tipos, setTipos] = useState<TipoMaterial[]>([]);
  const [items, setItems] = useState<MaterialItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<MaterialPayload | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  // Quando o usuário aciona "Adicionar material" queremos rolar o
  // formulário em foco; `scrollOnOpen` controla isso para não rolar ao
  // editar um item já visível na tabela.
  const editorRef = useRef<HTMLDivElement | null>(null);
  const [scrollOnOpen, setScrollOnOpen] = useState(0);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [t, m] = await Promise.all([
        apiRequest<TipoMaterial[]>("/api/cadastros/tipos-material"),
        apiRequest<MaterialItem[]>(`/api/acba/${acbaId}/materiais`),
      ]);
      setTipos(t);
      setItems(m);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar materiais.");
    } finally {
      setLoading(false);
    }
  }, [acbaId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (scrollOnOpen === 0 || !editorRef.current) return;
    editorRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [scrollOnOpen]);

  function startNew() {
    setEditing(emptyMaterial(tipos));
    setEditingId(null);
    setScrollOnOpen((c) => c + 1);
  }

  function startEdit(m: MaterialItem) {
    setEditingId(m.id ?? null);
    const tabela = m.categoria_docx ?? tabelaDoTipo(tipos, m.tipo_id) ?? "geral";
    setEditing({
      tipo_id: m.tipo_id,
      descricao: m.descricao,
      revisado: m.revisado,
      item_num: m.item_num ?? null,
      acondicionamento: m.acondicionamento ?? "",
      localizacao: m.localizacao ?? "",
      observacao: m.observacao ?? "",
      ordem: m.ordem,
      informatica:
        tabela === "informatica"
          ? m.informatica ?? emptyInformatica()
          : null,
    });
  }

  function cancelEdit() {
    setEditing(null);
    setEditingId(null);
  }

  async function save() {
    if (!editing) return;
    setSaving(true);
    setError(null);
    try {
      if (editingId == null) {
        await apiRequest<MaterialItem>(`/api/acba/${acbaId}/materiais`, {
          method: "POST",
          body: JSON.stringify(editing),
        });
      } else {
        await apiRequest<MaterialItem>(
          `/api/acba/${acbaId}/materiais/${editingId}`,
          { method: "PUT", body: JSON.stringify(editing) },
        );
      }
      await refresh();
      cancelEdit();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar material.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("Remover este material?")) return;
    setError(null);
    try {
      await apiRequest<void>(`/api/acba/${acbaId}/materiais/${id}`, {
        method: "DELETE",
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao remover.");
    }
  }

  async function marcarRevisado(m: MaterialItem) {
    if (!m.id) return;
    setError(null);
    try {
      await apiRequest<MaterialItem>(
        `/api/acba/${acbaId}/materiais/${m.id}/revisar`,
        {
          method: "POST",
          body: JSON.stringify({ descricao: m.descricao }),
        },
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao marcar revisado.");
    }
  }

  const informatica = useMemo(
    () =>
      items.filter(
        (m) =>
          (m.categoria_docx ?? tabelaDoTipo(tipos, m.tipo_id)) === "informatica",
      ),
    [items, tipos],
  );
  const geral = useMemo(
    () =>
      items.filter(
        (m) =>
          (m.categoria_docx ?? tabelaDoTipo(tipos, m.tipo_id)) !== "informatica",
      ),
    [items, tipos],
  );
  const pendentes = items.filter((m) => !m.revisado).length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-[0.1em] text-shell-muted">
          Materiais apreendidos
        </h3>
        <div className="flex items-center gap-2">
          {pendentes > 0 ? (
            <span className="rounded border border-amber-700/60 bg-amber-950/30 px-2 py-1 text-xs text-amber-200">
              {pendentes} material(is) com descrição IA pendente de revisão
            </span>
          ) : null}
          <button
            type="button"
            onClick={startNew}
            disabled={tipos.length === 0}
            className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-1 text-xs font-semibold text-shell-text disabled:opacity-60"
          >
            + Adicionar material
          </button>
        </div>
      </div>

      {error ? (
        <p className="rounded border border-red-700/60 bg-red-950/30 p-2 text-sm text-red-300">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p className="text-sm text-shell-muted">Carregando materiais...</p>
      ) : (
        <div className="space-y-4">
          <MaterialTable
            title="Material de informática"
            items={informatica}
            showSenha
            onEdit={startEdit}
            onDelete={remove}
            onReview={marcarRevisado}
          />
          <MaterialTable
            title="Demais materiais apreendidos"
            items={geral}
            onEdit={startEdit}
            onDelete={remove}
            onReview={marcarRevisado}
          />
        </div>
      )}

      {editing ? (
        <div ref={editorRef}>
          <MaterialEditor
            acbaId={acbaId}
            tipos={tipos}
            value={editing}
            onChange={setEditing}
            saving={saving}
            isNew={editingId == null}
            materialId={editingId}
            onSave={() => void save()}
            onCancel={cancelEdit}
          />
        </div>
      ) : null}
    </div>
  );
}

function MaterialTable({
  title,
  items,
  showSenha,
  onEdit,
  onDelete,
  onReview,
}: {
  title: string;
  items: MaterialItem[];
  showSenha?: boolean;
  onEdit: (m: MaterialItem) => void;
  onDelete: (id: number) => void;
  onReview: (m: MaterialItem) => void;
}) {
  return (
    <div className="rounded border border-shell-border">
      <p className="border-b border-shell-border bg-[#0f141c] px-3 py-2 text-xs uppercase tracking-[0.1em] text-shell-muted">
        {title}
      </p>
      {items.length === 0 ? (
        <p className="p-3 text-sm text-shell-muted">Nenhum material registrado.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="bg-[#0c1118] text-shell-muted">
            <tr>
              <th className="px-3 py-2 w-12">ITEM</th>
              <th className="px-3 py-2">Tipo / descrição</th>
              {showSenha ? <th className="px-3 py-2 w-40">Senha</th> : null}
              <th className="px-3 py-2 w-24">Status</th>
              <th className="px-3 py-2 w-40">Ações</th>
            </tr>
          </thead>
          <tbody>
            {items.map((m) => (
              <tr key={m.id} className="border-t border-shell-border/60 align-top">
                <td className="px-3 py-2 font-mono">{m.item_num}</td>
                <td className="px-3 py-2">
                  <p className="font-medium text-shell-text">{m.tipo_nome}</p>
                  <p className="whitespace-pre-wrap text-shell-muted">
                    {m.descricao}
                  </p>
                  {m.localizacao ? (
                    <p className="text-xs text-shell-muted">
                      Local: {m.localizacao}
                    </p>
                  ) : null}
                </td>
                {showSenha ? (
                  <td className="px-3 py-2 text-xs text-shell-muted">
                    <SenhaCell info={m.informatica ?? null} />
                  </td>
                ) : null}
                <td className="px-3 py-2 text-xs">
                  {m.revisado ? (
                    <span className="rounded bg-green-900/40 px-2 py-1 text-green-200">
                      Revisado
                    </span>
                  ) : (
                    <span className="rounded bg-amber-900/40 px-2 py-1 text-amber-200">
                      Pendente
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 text-xs">
                  <div className="flex flex-wrap gap-1">
                    {!m.revisado ? (
                      <button
                        type="button"
                        onClick={() => onReview(m)}
                        className="rounded border border-green-700/50 px-2 py-1 text-green-200"
                      >
                        Confirmar revisão
                      </button>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => onEdit(m)}
                      className="rounded border border-shell-border px-2 py-1 text-shell-text"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => m.id && onDelete(m.id)}
                      className="rounded border border-red-700/60 px-2 py-1 text-red-300"
                    >
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function SenhaCell({ info }: { info: InformaticaPayload | null }) {
  if (!info || info.senha_tipo === "nenhuma") return <span>—</span>;
  if (info.senha_tipo === "texto") return <span>{info.senha_texto ?? "—"}</span>;
  if (info.senha_tipo === "padrao") {
    return (
      <span className="font-mono">
        {(info.senha_padrao_pontos ?? []).join(" → ") || "—"}
      </span>
    );
  }
  if (info.senha_tipo === "biometria")
    return <span>Biometria{info.senha_observacao ? ` — ${info.senha_observacao}` : ""}</span>;
  return <span>Desconhecida</span>;
}

function MaterialEditor({
  acbaId,
  tipos,
  value,
  onChange,
  saving,
  isNew,
  materialId,
  onSave,
  onCancel,
}: {
  acbaId: number;
  tipos: TipoMaterial[];
  value: MaterialPayload;
  onChange: (next: MaterialPayload) => void;
  saving: boolean;
  isNew: boolean;
  materialId: number | null;
  onSave: () => void;
  onCancel: () => void;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [describing, setDescribing] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiNote, setAiNote] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const update = (patch: Partial<MaterialPayload>) =>
    onChange({ ...value, ...patch });

  function onSelectTipo(ev: ChangeEvent<HTMLSelectElement>) {
    const id = Number(ev.target.value);
    const novaCategoria = tabelaDoTipo(tipos, id) ?? "geral";
    update({
      tipo_id: id,
      informatica:
        novaCategoria === "informatica"
          ? value.informatica ?? emptyInformatica()
          : null,
    });
  }

  function updateInformatica(patch: Partial<InformaticaPayload>) {
    update({
      informatica: { ...(value.informatica ?? emptyInformatica()), ...patch },
    });
  }

  function handleFiles(ev: ChangeEvent<HTMLInputElement>) {
    const list = ev.target.files ? Array.from(ev.target.files) : [];
    setFiles(list);
  }

  async function describe() {
    if (isNew || materialId == null) {
      setAiError("Salve o material antes de gerar a descrição com IA.");
      return;
    }
    if (files.length === 0) {
      setAiError("Selecione ao menos uma imagem.");
      return;
    }
    setDescribing(true);
    setAiError(null);
    setAiNote(null);
    const form = new FormData();
    files.forEach((f) => form.append("imagens", f));
    try {
      const res = await apiRequest<DescribeResponse>(
        `/api/acba/${acbaId}/materiais/${materialId}/descrever`,
        { method: "POST", body: form },
      );
      const patch: Partial<MaterialPayload> = {
        descricao: res.descricao,
        revisado: false,
      };
      let notaTipo = "";
      if (res.tipo_id_sugerido) {
        const sugerido = tipos.find((t) => t.id === res.tipo_id_sugerido);
        if (sugerido) {
          patch.tipo_id = sugerido.id;
          patch.informatica =
            sugerido.tabela_documento === "informatica"
              ? value.informatica ?? emptyInformatica()
              : null;
          notaTipo = ` Tipo identificado: ${sugerido.nome}.`;
        }
      }
      update(patch);
      setAiNote(
        `Descrição gerada (modelo ${res.modelo}${res.cache_hit ? " — do cache" : ""}).${notaTipo} Revise antes de confirmar.`,
      );
      if (fileRef.current) fileRef.current.value = "";
      setFiles([]);
    } catch (err) {
      setAiError(err instanceof Error ? err.message : "Falha ao chamar a IA.");
    } finally {
      setDescribing(false);
    }
  }

  const tipoSelecionado = tipos.find((t) => t.id === value.tipo_id);
  const tabelaAtual: CategoriaDocx = tipoSelecionado?.tabela_documento ?? "geral";

  return (
    <div className="rounded-xl border border-shell-accent/60 bg-shell-surface p-4 space-y-3">
      <p className="text-sm font-semibold text-shell-text">
        {isNew ? "Novo material" : `Editar material #${materialId}`}
      </p>

      <div className="rounded border border-shell-accent/40 bg-shell-bg p-3 space-y-2">
        <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
          1. Identificação automática com IA (Gemini)
        </p>
        <p className="text-xs text-shell-muted">
          Envie imagens do item. A IA escolhe o <strong>tipo de material</strong>{" "}
          (entre os cadastrados) e preenche a descrição. As imagens vão direto
          ao modelo e não são armazenadas.
        </p>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFiles}
          className="text-xs text-shell-muted"
        />
        <button
          type="button"
          onClick={() => void describe()}
          disabled={describing || isNew}
          className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-1 text-xs text-shell-text disabled:opacity-60"
        >
          {describing ? "Analisando..." : "Identificar tipo e gerar descrição"}
        </button>
        {isNew ? (
          <p className="text-xs text-shell-muted">
            Salve o material primeiro para habilitar a IA.
          </p>
        ) : null}
        {aiError ? <p className="text-xs text-red-300">{aiError}</p> : null}
        {aiNote ? <p className="text-xs text-green-300">{aiNote}</p> : null}
      </div>

      <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
        2. Confira / ajuste os dados
      </p>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <label className="text-sm md:col-span-2">
          <span className="text-shell-muted">Tipo de material</span>
          <select
            className={`${inputClass()} mt-1`}
            value={value.tipo_id || ""}
            onChange={onSelectTipo}
            required
          >
            <option value="">Selecione</option>
            {tipos
              .filter((t) => t.ativo)
              .map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nome}
                </option>
              ))}
          </select>
          {tipoSelecionado ? (
            <span className="mt-1 block text-xs text-shell-muted">
              Será listado na tabela{" "}
              <strong>
                {tabelaAtual === "informatica"
                  ? "de informática (tabela 1)"
                  : "geral (tabela 2)"}
              </strong>{" "}
              do auto.
            </span>
          ) : null}
        </label>
        <label className="text-sm">
          <span className="text-shell-muted">Número do item</span>
          <input
            type="number"
            min={1}
            placeholder="Automático"
            className={`${inputClass()} mt-1`}
            value={value.item_num ?? ""}
            onChange={(e) => {
              const v = e.target.value.trim();
              update({ item_num: v === "" ? null : Math.max(1, Number(v)) });
            }}
          />
          <span className="mt-1 block text-xs text-shell-muted">
            Deixe em branco para usar o próximo livre nesta tabela.
          </span>
        </label>
        <label className="text-sm">
          <span className="text-shell-muted">Acondicionamento</span>
          <input
            className={`${inputClass()} mt-1`}
            value={value.acondicionamento ?? ""}
            onChange={(e) => update({ acondicionamento: e.target.value })}
          />
        </label>
        <label className="text-sm md:col-span-2">
          <span className="text-shell-muted">Localização (onde foi achado)</span>
          <input
            className={`${inputClass()} mt-1`}
            value={value.localizacao ?? ""}
            onChange={(e) => update({ localizacao: e.target.value })}
          />
        </label>
        <label className="text-sm md:col-span-2">
          <span className="text-shell-muted">
            Descrição{" "}
            {!value.revisado ? (
              <span className="ml-2 rounded bg-amber-900/40 px-1 text-amber-200">
                pendente de revisão
              </span>
            ) : null}
          </span>
          <textarea
            className={`${inputClass()} mt-1 min-h-28`}
            value={value.descricao}
            onChange={(e) =>
              update({ descricao: e.target.value, revisado: false })
            }
            required
          />
        </label>
        <label className="text-sm md:col-span-2">
          <span className="text-shell-muted">Observação</span>
          <input
            className={`${inputClass()} mt-1`}
            value={value.observacao ?? ""}
            onChange={(e) => update({ observacao: e.target.value })}
          />
        </label>
      </div>

      {tabelaAtual === "informatica" ? (
        <InformaticaSection
          value={value.informatica ?? emptyInformatica()}
          onUpdate={updateInformatica}
        />
      ) : null}

      <div className="flex flex-wrap items-center justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="rounded border border-shell-border px-3 py-1 text-sm text-shell-text"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={onSave}
          disabled={saving || !value.descricao.trim() || !value.tipo_id}
          className="rounded border border-shell-accent/50 bg-shell-accentBlue px-4 py-1 text-sm font-semibold text-shell-text disabled:opacity-60"
        >
          {saving ? "Salvando..." : isNew ? "Adicionar" : "Salvar alterações"}
        </button>
      </div>
    </div>
  );
}

function InformaticaSection({
  value,
  onUpdate,
}: {
  value: InformaticaPayload;
  onUpdate: (p: Partial<InformaticaPayload>) => void;
}) {
  function setTipo(t: SenhaTipo) {
    if (t === "texto") {
      onUpdate({ senha_tipo: t, senha_padrao_pontos: null });
    } else if (t === "padrao") {
      onUpdate({ senha_tipo: t, senha_texto: null });
    } else {
      onUpdate({ senha_tipo: t, senha_texto: null, senha_padrao_pontos: null });
    }
  }

  return (
    <div className="rounded border border-shell-border p-3 space-y-3">
      <p className="text-xs uppercase tracking-[0.1em] text-shell-muted">
        Senha do dispositivo
      </p>
      <div className="flex flex-wrap gap-2 text-sm">
        {(
          [
            ["nenhuma", "Não há"],
            ["texto", "Texto / PIN"],
            ["padrao", "Padrão (desenho)"],
            ["biometria", "Biometria"],
            ["desconhecida", "Desconhecida"],
          ] as [SenhaTipo, string][]
        ).map(([k, label]) => (
          <label
            key={k}
            className={`cursor-pointer rounded border px-3 py-1 ${
              value.senha_tipo === k
                ? "border-shell-accent bg-shell-accentBlue/30 text-shell-text"
                : "border-shell-border text-shell-muted"
            }`}
          >
            <input
              type="radio"
              name="senha_tipo"
              value={k}
              checked={value.senha_tipo === k}
              onChange={() => setTipo(k)}
              className="mr-1"
            />
            {label}
          </label>
        ))}
      </div>

      {value.senha_tipo === "texto" ? (
        <label className="text-sm block">
          <span className="text-shell-muted">Senha / PIN</span>
          <input
            className={`${inputClass()} mt-1`}
            value={value.senha_texto ?? ""}
            onChange={(e) => onUpdate({ senha_texto: e.target.value })}
          />
        </label>
      ) : null}

      {value.senha_tipo === "padrao" ? (
        <div>
          <p className="mb-2 text-xs text-shell-muted">
            Toque ou arraste pelos pontos na ordem do desenho informado. Setas
            indicam direção; círculo verde marca o ponto inicial.
          </p>
          <PatternInput
            value={value.senha_padrao_pontos ?? []}
            onChange={(pts) => onUpdate({ senha_padrao_pontos: pts })}
          />
        </div>
      ) : null}

      {value.senha_tipo === "biometria" ||
      value.senha_tipo === "desconhecida" ||
      value.senha_tipo === "nenhuma" ? (
        <label className="text-sm block">
          <span className="text-shell-muted">Observação (opcional)</span>
          <input
            className={`${inputClass()} mt-1`}
            value={value.senha_observacao ?? ""}
            onChange={(e) => onUpdate({ senha_observacao: e.target.value })}
            placeholder={
              value.senha_tipo === "biometria"
                ? "Ex.: biometria do polegar direito"
                : ""
            }
          />
        </label>
      ) : null}
    </div>
  );
}
