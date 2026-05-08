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

export type MembroEquipeBrief = {
  id: number;
  nome: string;
  matricula: string;
  funcao_padrao?: string | null;
};

export type AcbaFormPayload = {
  numero_auto: string;
  unidade_id: number;
  delegacia_id: number;
  cidade_id: number;
  data_lavratura: string;
  hora_lavratura: string;
  autoridade_id: number;
  escrivao_id: number;
  tipo_procedimento_id: number;
  procedimento_numero: string;
  fundamento_legal: string;
  endereco_busca: string;
  alvo_busca: string;
  condutor_id: number;
  assinatura_responsavel: string;
  observacoes: string;
  membro_ids: number[];
  testemunhas: TestemunhaItem[];
  objetos_arrecadados: ObjetoItem[];
};

export type AcbaListItem = {
  id: number;
  numero_auto: string;
  delegacia_nome: string;
  data_lavratura: string;
  alvo_busca: string;
  autoridade_nome: string;
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
  autoridade_nome: string;
  autoridade_matricula?: string | null;
  escrivao_nome: string;
  tipo_procedimento_nome: string;
  condutor_nome: string;
  condutor_matricula?: string | null;
  membros_equipe: MembroEquipeBrief[];
};
