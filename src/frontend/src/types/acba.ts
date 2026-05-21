export type TestemunhaTipo = "geral" | "arrombamento";

/**
 * Especialização exclusiva da testemunha de arrombamento (Art. 245 §4º).
 * Persistida na sub-classe `acba_testemunhas_arrombamento`.
 */
export type TestemunhaArrombamentoExtras = {
  observacoes: string;
};

/**
 * Super-classe `acba_testemunhas`. Campos comuns a toda testemunha
 * (nome, cpf, rg, filiação, endereço); cidade e telefone são preenchidos
 * apenas para testemunhas gerais; `arrombamento` (com observações) é
 * preenchido apenas para testemunhas vizinhas (§4º).
 */
export type TestemunhaItem = {
  id?: number;
  tipo: TestemunhaTipo;
  nome: string;
  cpf: string;
  rg: string;
  filiacao: string;
  endereco: string;
  cidade?: string | null;
  telefone?: string | null;
  arrombamento?: TestemunhaArrombamentoExtras | null;
};

export type AgenteBrief = {
  id: number;
  nome: string;
  matricula: string;
  funcao_padrao?: string | null;
};

export type EquipeAtualBrief = {
  equipe_id: number;
  equipe_numero: string;
  equipe_nome?: string | null;
  /** ISO date (YYYY-MM-DD) — quando o agente entrou nesta equipe. */
  data_inicio: string;
};

export type AgenteListing = AgenteBrief & {
  ativo: boolean;
  created_at: string;
  /** Vínculos de equipe abertos hoje (vazio se o agente não está em nenhuma). */
  equipes_atuais: EquipeAtualBrief[];
  /**
   * Texto pronto pra tabela: "01 — Tático Alfa; 02 — Antientorpecentes".
   * `null` quando o agente não tem vínculo ativo.
   */
  equipe_atual_resumo?: string | null;
  /** ISO date — data de ingresso mais antiga ainda em vigor. */
  primeira_data_ingresso?: string | null;
};

/** Linha do histórico equipe↔agente (passagens encerradas + ativas). */
export type AgenteEquipeVinculo = {
  id: number;
  equipe_id: number;
  equipe_numero: string;
  equipe_nome?: string | null;
  data_inicio: string;
  data_fim?: string | null;
  motivo_saida?: string | null;
  ativo: boolean;
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
  nome_vara_criminal: string;
  nome_juiz: string;
  assinatura_responsavel: string;
  observacoes: string;
  equipe_id: number;
  testemunhas: TestemunhaItem[];
  /** Bloco do Art. 245 §§ 2º, 3º e 4º do CPP. */
  arrombamento_245_2: boolean;
  arrombamento_245_2_obs: string;
  forca_coisas_245_3: boolean;
  forca_coisas_245_3_obs: string;
  morador_ausente_245_4: boolean;
  morador_ausente_245_4_obs: string;
  /**
   * Qualificação do morador presente. Aparece no formulário apenas quando
   * `morador_ausente_245_4 === false`; nesse caso TODOS os campos abaixo
   * são obrigatórios. Quando o morador estava ausente, ficam vazios.
   */
  morador_nome: string;
  morador_cpf: string;
  morador_rg: string;
  morador_filiacao: string;
  morador_telefone: string;
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
  /** ISO timestamp (UTC) da última geração do PDF; null quando nunca gerado. */
  pdf_gerado_at?: string | null;
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
  /** Timestamp ISO da última geração do PDF (null = nunca gerado). */
  pdf_gerado_at?: string | null;
  pdf_gerado_por_user_id?: number | null;
};

/** Auditoria do ACBA — uma entrada por alteração. */
export type AcbaAuditEntry = {
  id: number;
  acba_id: number;
  user_id: number | null;
  user_email: string;
  user_full_name: string | null;
  user_role: "administrador" | "delegado" | "escrivao" | "agente";
  acao: "criado" | "editado" | "excluido" | "pdf_gerado";
  changed_at: string;
  ip: string | null;
  user_agent: string | null;
  changes: Record<string, { de: unknown; para: unknown }> | null;
  snapshot_before?: Record<string, unknown> | null;
  snapshot_after?: Record<string, unknown> | null;
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
  tipo_id_sugerido?: number | null;
  tipo_nome_sugerido?: string | null;
};
