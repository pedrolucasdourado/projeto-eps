export type TestemunhaItem = {
  nome: string;
  documento: string;
  contato: string;
};

export type AgenteBrief = {
  id: number;
  nome: string;
  matricula: string;
  funcao_padrao?: string | null;
};

export type CategoriaDocx = "informatica" | "geral";

export type SenhaTipo =
  | "nenhuma"
  | "texto"
  | "padrao"
  | "biometria"
  | "desconhecida";

export type InformaticaPayload = {
  senha_tipo: SenhaTipo;
  senha_texto?: string | null;
  senha_padrao_pontos?: number[] | null;
  senha_observacao?: string | null;
};

export type TipoMaterial = {
  id: number;
  nome: string;
  tabela_documento: CategoriaDocx;
  ativo: boolean;
  created_at: string;
};

export type MaterialItem = {
  id?: number;
  acba_id?: number;
  tipo_id: number;
  tipo_nome?: string;
  /** Derivado automaticamente do tipo escolhido — só vem nas respostas do backend. */
  categoria_docx?: CategoriaDocx;
  item_num?: number | null;
  descricao: string;
  descricao_ia_raw?: string | null;
  revisado: boolean;
  acondicionamento?: string | null;
  localizacao?: string | null;
  observacao?: string | null;
  ordem: number;
  informatica?: InformaticaPayload | null;
  created_at?: string;
  updated_at?: string;
};

export type MaterialPayload = Omit<
  MaterialItem,
  "id" | "acba_id" | "tipo_nome" | "created_at" | "updated_at"
>;

export type AcbaFormPayload = {
  processo_numero: string;
  protocolo_numero: string;
  unidade_id: number;
  delegacia_id: number;
  cidade_id: number;
  data_lavratura: string;
  hora_lavratura: string;
  tipo_procedimento_id: number;
  procedimento_numero: string;
  fundamento_legal: string;
  endereco_busca: string;
  alvo_busca: string;
  assinatura_responsavel: string;
  observacoes: string;
  equipe_id: number;
  testemunhas: TestemunhaItem[];
  /** Apenas no fluxo de criação — backend grava em transação junto com o ACBA. */
  materiais?: MaterialPayload[];
};

export type AcbaListItem = {
  id: number;
  processo_numero: string;
  protocolo_numero: string;
  delegacia_nome: string;
  data_lavratura: string;
  alvo_busca: string;
  delegado_nome: string;
  equipe_numero: string;
  equipe_nome?: string | null;
  created_at: string;
  materiais_pendentes_revisao: number;
};

export type AcbaDetail = Omit<AcbaFormPayload, "materiais"> & {
  id: number;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
  unidade_nome: string;
  delegacia_nome: string;
  cidade_nome: string;
  uf_sigla: string;
  uf_nome: string;
  tipo_procedimento_nome: string;
  processo_descricao?: string | null;
  equipe_numero: string;
  equipe_nome?: string | null;
  delegado_id: number;
  delegado_nome: string;
  delegado_matricula?: string | null;
  escrivao_id: number;
  escrivao_nome: string;
  agentes_equipe: AgenteBrief[];
  materiais: MaterialItem[];
  materiais_pendentes_revisao: number;
};

export type Processo = {
  numero: string;
  descricao?: string | null;
  ativo: boolean;
  acbas_count: number;
  created_at: string;
};

export type EquipeOperacional = {
  id: number;
  numero: string;
  nome?: string | null;
  delegado_id: number;
  escrivao_id: number;
  delegado_nome?: string | null;
  delegado_matricula?: string | null;
  escrivao_nome?: string | null;
  ativo: boolean;
  agentes_count: number;
  created_at: string;
};

export type EquipeAcbaItem = {
  id: number;
  processo_numero: string;
  protocolo_numero: string;
  data_lavratura: string;
  alvo_busca: string;
  delegacia_nome?: string | null;
  delegado_nome?: string | null;
};

export type DescribeResponse = {
  descricao: string;
  revisado: boolean;
  cache_hit: boolean;
  modelo: string;
  prompt_versao: string;
};
