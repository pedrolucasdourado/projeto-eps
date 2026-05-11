"use client";

import {
  ChangeEvent,
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
  MaterialPayload,
  SenhaTipo,
  TipoMaterial,
} from "@/types/acba";

import { PatternInput } from "./pattern-input";

type Props = {
  value: MaterialPayload[];
  onChange: (next: MaterialPayload[]) => void;
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

function emptyDraft(tipos: TipoMaterial[]): MaterialPayload {
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

/**
 * Componente usado APENAS na criação do ACBA — os materiais ficam em memória
 * (no estado do formulário pai) e são enviados juntos no POST /api/acba.
 * Após o ACBA existir, a tela de edição usa o MaterialsManager (CRUD por item).
 */
export function MaterialsDraft({ value, onChange }: Props) {
  const [tipos, setTipos] = useState<TipoMaterial[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [draft, setDraft] = useState<MaterialPayload | null>(null);

  useEffect(() => {
    void apiRequest<TipoMaterial[]>("/api/cadastros/tipos-material")
      .then(setTipos)
      .catch(() =>
        setError("Falha ao carregar catálogo de tipos de material."),
      );
  }, []);

  function startNew() {
    setEditingIdx(null);
    setDraft(emptyDraft(tipos));
  }

  function startEdit(idx: number) {
    setEditingIdx(idx);
    setDraft({ ...value[idx] });
  }

  function cancelEdit() {
    setDraft(null);
    setEditingIdx(null);
  }

  function saveDraft() {
    if (!draft) return;
    if (!draft.descricao.trim() || !draft.tipo_id) return;
    const next = [...value];
    if (editingIdx == null) next.push(draft);
    else next[editingIdx] = draft;
    onChange(next);
    cancelEdit();
  }

  function removeAt(idx: number) {
    if (!confirm("Remover este material?")) return;
    const next = [...value];
    next.splice(idx, 1);
    onChange(next);
    if (editingIdx === idx) cancelEdit();
  }

  function toggleRevisado(idx: number, revisado: boolean) {
    const next = [...value];
    next[idx] = { ...next[idx], revisado };
    onChange(next);
  }

  const informatica = useMemo(
    () =>
      value
        .map((m, i) => ({ m, i }))
        .filter(({ m }) => tabelaDoTipo(tipos, m.tipo_id) === "informatica"),
    [value, tipos],
  );
  const geral = useMemo(
    () =>
      value
        .map((m, i) => ({ m, i }))
        .filter(({ m }) => tabelaDoTipo(tipos, m.tipo_id) !== "informatica"),
    [value, tipos],
  );
  const pendentes = value.filter((m) => !m.revisado).length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-shell-muted">
          Os materiais são salvos junto com o ACBA. A IA pode preencher a
          descrição a partir das imagens (que <strong>não</strong> são
          armazenadas).
        </p>
        <div className="flex items-center gap-2">
          {pendentes > 0 ? (
            <span className="rounded border border-amber-700/60 bg-amber-950/30 px-2 py-1 text-xs text-amber-200">
              {pendentes} pendente(s) de revisão
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

      <DraftTable
        title="Material de informática (tabela 1 do auto)"
        showSenha
        rows={informatica}
        onEdit={(i) => startEdit(i)}
        onRemove={removeAt}
        onToggleRevisado={toggleRevisado}
      />
      <DraftTable
        title="Demais materiais (tabela 2 do auto)"
        rows={geral}
        onEdit={(i) => startEdit(i)}
        onRemove={removeAt}
        onToggleRevisado={toggleRevisado}
      />

      {draft ? (
        <DraftEditor
          value={draft}
          tipos={tipos}
          onChange={setDraft}
          isNew={editingIdx == null}
          onSave={saveDraft}
          onCancel={cancelEdit}
        />
      ) : null}
    </div>
  );
}

function DraftTable({
  title,
  rows,
  showSenha,
  onEdit,
  onRemove,
  onToggleRevisado,
}: {
  title: string;
  rows: { m: MaterialPayload; i: number }[];
  showSenha?: boolean;
  onEdit: (idx: number) => void;
  onRemove: (idx: number) => void;
  onToggleRevisado: (idx: number, revisado: boolean) => void;
}) {
  return (
    <div className="rounded border border-shell-border">
      <p className="border-b border-shell-border bg-[#0f141c] px-3 py-2 text-xs uppercase tracking-[0.1em] text-shell-muted">
        {title}
      </p>
      {rows.length === 0 ? (
        <p className="p-3 text-sm text-shell-muted">Nenhum material no rascunho.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="bg-[#0c1118] text-shell-muted">
            <tr>
              <th className="px-3 py-2 w-12">#</th>
              <th className="px-3 py-2">Tipo / descrição</th>
              {showSenha ? <th className="px-3 py-2 w-40">Senha</th> : null}
              <th className="px-3 py-2 w-32">Revisão</th>
              <th className="px-3 py-2 w-32">Ações</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ m, i }, n) => (
              <tr key={i} className="border-t border-shell-border/60 align-top">
                <td className="px-3 py-2 font-mono">
                  {m.item_num ?? `~${n + 1}`}
                </td>
                <td className="px-3 py-2">
                  <p className="text-shell-text">
                    {m.descricao || (
                      <span className="text-shell-muted">(sem descrição)</span>
                    )}
                  </p>
                  {m.localizacao ? (
                    <p className="text-xs text-shell-muted">
                      Local: {m.localizacao}
                    </p>
                  ) : null}
                </td>
                {showSenha ? (
                  <td className="px-3 py-2 text-xs text-shell-muted">
                    <SenhaPreview info={m.informatica ?? null} />
                  </td>
                ) : null}
                <td className="px-3 py-2 text-xs">
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={m.revisado}
                      onChange={(e) => onToggleRevisado(i, e.target.checked)}
                    />
                    <span
                      className={`rounded px-2 py-1 ${
                        m.revisado
                          ? "bg-green-900/40 text-green-200"
                          : "bg-amber-900/40 text-amber-200"
                      }`}
                    >
                      {m.revisado ? "Revisado" : "Pendente"}
                    </span>
                  </label>
                </td>
                <td className="space-x-1 px-3 py-2 text-xs">
                  <button
                    type="button"
                    onClick={() => onEdit(i)}
                    className="rounded border border-shell-border px-2 py-1 text-shell-text"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => onRemove(i)}
                    className="rounded border border-red-700/60 px-2 py-1 text-red-300"
                  >
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function SenhaPreview({ info }: { info: InformaticaPayload | null }) {
  if (!info || info.senha_tipo === "nenhuma") return <span>—</span>;
  if (info.senha_tipo === "texto")
    return <span>{info.senha_texto ?? "—"}</span>;
  if (info.senha_tipo === "padrao")
    return (
      <span className="font-mono">
        {(info.senha_padrao_pontos ?? []).join(" → ") || "—"}
      </span>
    );
  if (info.senha_tipo === "biometria")
    return (
      <span>
        Biometria{info.senha_observacao ? ` — ${info.senha_observacao}` : ""}
      </span>
    );
  return <span>Desconhecida</span>;
}

function DraftEditor({
  value,
  tipos,
  onChange,
  isNew,
  onSave,
  onCancel,
}: {
  value: MaterialPayload;
  tipos: TipoMaterial[];
  onChange: (next: MaterialPayload) => void;
  isNew: boolean;
  onSave: () => void;
  onCancel: () => void;
}) {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [describing, setDescribing] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiNote, setAiNote] = useState<string | null>(null);

  function update(patch: Partial<MaterialPayload>) {
    onChange({ ...value, ...patch });
  }

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
    setFiles(ev.target.files ? Array.from(ev.target.files) : []);
  }

  async function describe() {
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
        "/api/acba/ia/descrever-material",
        { method: "POST", body: form },
      );
      const patch: Partial<MaterialPayload> = {
        descricao: res.descricao,
        descricao_ia_raw: res.descricao,
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
        `Descrição gerada (modelo ${res.modelo}).${notaTipo} Revise antes de marcar como revisado.`,
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
  const tabelaAtual: CategoriaDocx =
    tipoSelecionado?.tabela_documento ?? "geral";

  return (
    <div className="rounded-xl border border-shell-accent/60 bg-shell-surface p-4 space-y-3">
      <p className="text-sm font-semibold text-shell-text">
        {isNew ? "Novo material" : "Editar material"}
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
          disabled={describing || files.length === 0}
          className="rounded border border-shell-accent/50 bg-shell-accentBlue px-3 py-1 text-xs text-shell-text disabled:opacity-60"
        >
          {describing ? "Analisando..." : "Identificar tipo e gerar descrição"}
        </button>
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
            Em branco = próximo livre nesta tabela.
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

      <label className="flex items-center gap-2 text-sm text-shell-text">
        <input
          type="checkbox"
          checked={value.revisado}
          onChange={(e) => update({ revisado: e.target.checked })}
        />
        Já revisei esta descrição
      </label>

      <div className="flex flex-wrap items-center justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded border border-shell-border px-3 py-1 text-sm text-shell-text"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={onSave}
          disabled={!value.descricao.trim() || !value.tipo_id}
          className="rounded border border-shell-accent/50 bg-shell-accentBlue px-4 py-1 text-sm font-semibold text-shell-text disabled:opacity-60"
        >
          {isNew ? "Adicionar ao ACBA" : "Salvar no rascunho"}
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
    if (t === "texto") onUpdate({ senha_tipo: t, senha_padrao_pontos: null });
    else if (t === "padrao") onUpdate({ senha_tipo: t, senha_texto: null });
    else onUpdate({ senha_tipo: t, senha_texto: null, senha_padrao_pontos: null });
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
              name="senha_tipo_draft"
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
            Toque ou arraste pelos pontos na ordem do desenho informado.
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
