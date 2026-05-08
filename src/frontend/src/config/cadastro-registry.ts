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
    };

export type CadastroDefinition = {
  title: string;
  apiPath: string;
  columns: { key: string; label: string }[];
  fields: CatalogField[];
};

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
  autoridades: {
    title: "Autoridades policiais",
    apiPath: "/api/cadastros/autoridades",
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
  "membros-equipe": {
    title: "Membros da equipe operacional",
    apiPath: "/api/cadastros/membros-equipe",
    columns: [
      { key: "nome", label: "Nome" },
      { key: "matricula", label: "Matrícula" },
      { key: "funcao_padrao", label: "Função padrão" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      { kind: "text", name: "matricula", label: "Matrícula", required: true },
      { kind: "text", name: "funcao_padrao", label: "Função padrão" },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
  condutores: {
    title: "Condutores de operações",
    apiPath: "/api/cadastros/condutores",
    columns: [
      { key: "nome", label: "Nome" },
      { key: "matricula", label: "Matrícula" },
      { key: "ativo", label: "Ativo" },
    ],
    fields: [
      { kind: "text", name: "nome", label: "Nome", required: true },
      { kind: "text", name: "matricula", label: "Matrícula" },
      { kind: "checkbox", name: "ativo", label: "Ativo" },
    ],
  },
};
