export type TestemunhaItem = {
  nome: string;
  documento: string;
  contato: string;
};

export type ObjetoItem = {
  descricao: string;
  quantidade: number;
  acondicionamento: string;
  observacao: string;
};

export type AgenteBrief = {
  id: number;
  nome: string;
  matricula: string;
  funcao_padrao?: string | null;
};

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
  objetos_arrecadados: ObjetoItem[];
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
};

export type AcbaDetail = AcbaFormPayload & {
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
