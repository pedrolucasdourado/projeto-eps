export type CatalogField =
  | { kind: "text"; name: string; label: string; required?: boolean }
  | { kind: "checkbox"; name: string; label: string }
  | {
      kind: "select";
      name: string;
      label: string;
      optionsUrl: string;
      optional?: boolean;
      formatOption: (row: Record<string, unknown>) => string;
    }
  | {
      kind: "enum";
      name: string;
      label: string;
      options: { value: string; label: string }[];
      required?: boolean;
    };

export type CatalogColumn = {
  key: string;
  label: string;
  /** Formatter opcional para a célula. Recebe o valor bruto e a linha inteira. */
  format?: (value: unknown, row: Record<string, unknown>) => string;
};

/**
 * Ação extra renderizada na coluna "Ações" de cada linha.
 * Usada para complementar Editar/Excluir com links contextuais
 * (ex.: "Histórico de equipes" no cadastro de agentes).
 */
export type CatalogRowAction = {
  label: string;
  /** Recebe a linha e devolve o href final (já com o id concatenado). */
  href: (row: Record<string, unknown>) => string;
};

export type CadastroDefinition = {
  title: string;
  apiPath: string;
  columns: CatalogColumn[];
  fields: CatalogField[];
  /**
   * Nome do campo que identifica a linha nas rotas (PUT/DELETE) e na chave do React.
   * Default: "id" (PK numérica). Use "numero" para tabelas com PK natural (string),
   * como processos.
   */
  idField?: string;
  /**
   * Quando true, o campo de identificação não pode ser alterado na edição
   * (PK natural ou imutável). O input aparece desabilitado no modo edit.
   */
  identifierLocked?: boolean;
  /** Ações extras (links) por linha, à esquerda dos botões padrão. */
  extraRowActions?: CatalogRowAction[];
  /**
   * Quando true, criação/edição/exclusão só estão disponíveis para o
   * papel ``administrador``. Demais papéis enxergam o cadastro em
   * modo somente-leitura (sem botões Novo/Editar/Excluir). O backend
   * espelha a regra: POST/PUT/DELETE retornam 403 para não-admins.
   */
  adminOnlyMutations?: boolean;
};

function formatDateBR(value: unknown): string {
  if (value == null || value === "") return "—";
  const s = String(value);
  // Para "YYYY-MM-DD" puro, evita o parser do Date jogar para o dia anterior
  // por causa do fuso (ele assume UTC quando não há TZ na string).
  const isoDate = /^\d{4}-\d{2}-\d{2}$/.exec(s);
  if (isoDate) {
    const [y, m, d] = s.split("-");
    return `${d}/${m}/${y}`;
  }
  const dt = new Date(s);
  if (Number.isNaN(dt.getTime())) return s;
  return dt.toLocaleDateString("pt-BR");
}

export const CADASTROS: Record<string, CadastroDefinition> = {
  ufs: {
    title: "UFs",
    apiPath: "/api/cadastros/ufs",
    columns: [
      { key: "sigla", label: "Sigla" },
      { key: "nome", label: "Nome" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "sigla", label: "Sigla", required: true },
      { kind: "text", name: "nome", label: "Nome", required: true },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
  cidades: {
    title: "Cidades",
    apiPath: "/api/cadastros/cidades",
    columns: [
      { key: "nome", label: "Cidade" },
      { key: "uf_sigla", label: "UF" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      {
        kind: "select",
        name: "uf_id",
        label: "UF",
        optionsUrl: "/api/cadastros/ufs",
        formatOption: (r) => `${String(r.sigla)} — ${String(r.nome)}`,
      },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
  unidades: {
    title: "Unidades responsáveis",
    apiPath: "/api/cadastros/unidades",
    columns: [
      { key: "nome", label: "Nome" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
  delegacias: {
    title: "Delegacias",
    apiPath: "/api/cadastros/delegacias",
    columns: [
      { key: "nome", label: "Nome" },
      { key: "unidade_nome", label: "Unidade" },
      { key: "cidade_nome", label: "Cidade" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      {
        kind: "select",
        name: "unidade_id",
        label: "Unidade (opcional)",
        optionsUrl: "/api/cadastros/unidades",
        optional: true,
        formatOption: (r) => String(r.nome),
      },
      {
        kind: "select",
        name: "cidade_id",
        label: "Cidade (opcional)",
        optionsUrl: "/api/cadastros/cidades",
        optional: true,
        formatOption: (r) => `${String(r.nome)} (${String(r.uf_sigla)})`,
      },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
  "tipos-procedimento": {
    title: "Tipos de procedimento",
    apiPath: "/api/cadastros/tipos-procedimento",
    columns: [
      { key: "nome", label: "Nome" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
  delegados: {
    title: "Delegados",
    apiPath: "/api/cadastros/delegados",
    adminOnlyMutations: true,
    columns: [
      { key: "nome", label: "Nome" },
      { key: "matricula", label: "Matrícula" },
      { key: "delegacia_nome", label: "Delegacia" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      { kind: "text", name: "matricula", label: "Matrícula" },
      {
        kind: "select",
        name: "delegacia_id",
        label: "Delegacia (opcional)",
        optionsUrl: "/api/cadastros/delegacias",
        optional: true,
        formatOption: (r) => String(r.nome),
      },
      {
        kind: "select",
        name: "unidade_id",
        label: "Unidade (opcional)",
        optionsUrl: "/api/cadastros/unidades",
        optional: true,
        formatOption: (r) => String(r.nome),
      },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
  escrivaos: {
    title: "Escrivãos",
    apiPath: "/api/cadastros/escrivaos",
    adminOnlyMutations: true,
    columns: [
      { key: "nome", label: "Nome" },
      { key: "delegacia_nome", label: "Delegacia" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      {
        kind: "select",
        name: "delegacia_id",
        label: "Delegacia (opcional)",
        optionsUrl: "/api/cadastros/delegacias",
        optional: true,
        formatOption: (r) => String(r.nome),
      },
      {
        kind: "select",
        name: "unidade_id",
        label: "Unidade (opcional)",
        optionsUrl: "/api/cadastros/unidades",
        optional: true,
        formatOption: (r) => String(r.nome),
      },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
  agentes: {
    title: "Agentes",
    apiPath: "/api/cadastros/agentes",
    adminOnlyMutations: true,
    columns: [
      { key: "nome", label: "Nome" },
      { key: "matricula", label: "Matrícula" },
      { key: "funcao_padrao", label: "Função padrão" },
      {
        key: "equipe_atual_resumo",
        label: "Equipe(s) atual(is)",
        format: (value) => {
          const s = value == null ? "" : String(value).trim();
          return s.length > 0 ? s : "Sem vínculo ativo";
        },
      },
      {
        key: "primeira_data_ingresso",
        label: "Data de ingresso",
        format: (value) => formatDateBR(value),
      },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      { kind: "text", name: "matricula", label: "Matrícula", required: true },
      { kind: "text", name: "funcao_padrao", label: "Função padrão" },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
    extraRowActions: [
      {
        label: "Histórico de equipes",
        href: (row) => `/cadastros/agentes/${String(row.id)}/historico`,
      },
    ],
  },
  "tipos-material": {
    title: "Tipos de material",
    apiPath: "/api/cadastros/tipos-material",
    columns: [
      { key: "nome", label: "Nome" },
      { key: "tabela_documento", label: "Tabela do documento" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      {
        kind: "enum",
        name: "tabela_documento",
        label: "Tabela do documento",
        required: true,
        options: [
          { value: "informatica", label: "Informática (tabela 1)" },
          { value: "geral", label: "Geral (tabela 2)" },
        ],
      },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
  processos: {
    title: "Processos",
    apiPath: "/api/cadastros/processos",
    idField: "numero",
    identifierLocked: true,
    columns: [
      { key: "numero", label: "Número" },
      { key: "descricao", label: "Descrição" },
      { key: "acbas_count", label: "ACBAs" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "numero", label: "Número do processo", required: true },
      { kind: "text", name: "descricao", label: "Descrição" },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
};
