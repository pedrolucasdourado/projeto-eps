from datetime import date, datetime

from pydantic import BaseModel, Field


class UFBase(BaseModel):
    sigla: str = Field(min_length=2, max_length=8)
    nome: str = Field(min_length=2, max_length=160)
    ativo: bool = True


class UFCreate(UFBase):
    pass


class UFUpdate(BaseModel):
    sigla: str | None = Field(default=None, min_length=2, max_length=8)
    nome: str | None = Field(default=None, min_length=2, max_length=160)
    ativo: bool | None = None


class UFRead(UFBase):
    id: int
    created_at: datetime


class CidadeBase(BaseModel):
    nome: str = Field(min_length=2, max_length=180)
    uf_id: int
    ativo: bool = True


class CidadeCreate(CidadeBase):
    pass


class CidadeUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=180)
    uf_id: int | None = None
    ativo: bool | None = None


class CidadeRead(CidadeBase):
    id: int
    uf_sigla: str
    uf_nome: str
    created_at: datetime


class UnidadeBase(BaseModel):
    nome: str = Field(min_length=2, max_length=220)
    ativo: bool = True


class UnidadeCreate(UnidadeBase):
    pass


class UnidadeUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=220)
    ativo: bool | None = None


class UnidadeRead(UnidadeBase):
    id: int
    created_at: datetime


class DelegaciaBase(BaseModel):
    nome: str = Field(min_length=2, max_length=220)
    unidade_id: int | None = None
    cidade_id: int | None = None
    ativo: bool = True


class DelegaciaCreate(DelegaciaBase):
    pass


class DelegaciaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=220)
    unidade_id: int | None = None
    cidade_id: int | None = None
    ativo: bool | None = None


class DelegaciaRead(DelegaciaBase):
    id: int
    unidade_nome: str | None = None
    cidade_nome: str | None = None
    uf_sigla: str | None = None
    created_at: datetime


class TipoProcedimentoBase(BaseModel):
    nome: str = Field(min_length=2, max_length=180)
    ativo: bool = True


class TipoProcedimentoCreate(TipoProcedimentoBase):
    pass


class TipoProcedimentoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=180)
    ativo: bool | None = None


class TipoProcedimentoRead(TipoProcedimentoBase):
    id: int
    created_at: datetime


class DelegadoBase(BaseModel):
    nome: str = Field(min_length=2, max_length=220)
    matricula: str | None = Field(default=None, max_length=80)
    delegacia_id: int | None = None
    unidade_id: int | None = None
    ativo: bool = True


class DelegadoCreate(DelegadoBase):
    pass


class DelegadoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=220)
    matricula: str | None = Field(default=None, max_length=80)
    delegacia_id: int | None = None
    unidade_id: int | None = None
    ativo: bool | None = None


class DelegadoRead(DelegadoBase):
    id: int
    delegacia_nome: str | None = None
    unidade_nome: str | None = None
    created_at: datetime


class EscrivaoBase(BaseModel):
    nome: str = Field(min_length=2, max_length=220)
    delegacia_id: int | None = None
    unidade_id: int | None = None
    ativo: bool = True


class EscrivaoCreate(EscrivaoBase):
    pass


class EscrivaoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=220)
    delegacia_id: int | None = None
    unidade_id: int | None = None
    ativo: bool | None = None


class EscrivaoRead(EscrivaoBase):
    id: int
    delegacia_nome: str | None = None
    unidade_nome: str | None = None
    created_at: datetime


class AgenteBase(BaseModel):
    nome: str = Field(min_length=2, max_length=220)
    matricula: str = Field(min_length=1, max_length=80)
    funcao_padrao: str | None = Field(default=None, max_length=120)
    ativo: bool = True


class AgenteCreate(AgenteBase):
    pass


class AgenteUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=220)
    matricula: str | None = Field(default=None, min_length=1, max_length=80)
    funcao_padrao: str | None = Field(default=None, max_length=120)
    ativo: bool | None = None


class AgenteRead(AgenteBase):
    id: int
    created_at: datetime


class EquipeAtualBrief(BaseModel):
    """Resumo de uma equipe em que o agente está atualmente vinculado."""

    equipe_id: int
    equipe_numero: str
    equipe_nome: str | None = None
    data_inicio: date


class AgenteListing(AgenteRead):
    """``AgenteRead`` enriquecido para visualização em lista/detalhe.

    Inclui, sem custo extra para quem só precisa do agente "puro", a
    composição atual de equipes (vínculos abertos) e um resumo textual
    pronto para tabelas.
    """

    equipes_atuais: list[EquipeAtualBrief] = Field(default_factory=list)
    equipe_atual_resumo: str | None = None
    primeira_data_ingresso: date | None = None


class AgenteEquipeVinculo(BaseModel):
    """Linha do histórico equipe↔agente.

    Retorna todos os períodos (abertos e fechados) em que o agente
    pertenceu àquela equipe, em ordem cronológica decrescente
    (mais recente primeiro).
    """

    id: int
    equipe_id: int
    equipe_numero: str
    equipe_nome: str | None = None
    data_inicio: date
    data_fim: date | None = None
    motivo_saida: str | None = None
    ativo: bool


class EquipeOperacionalBase(BaseModel):
    numero: str = Field(min_length=1, max_length=40)
    nome: str | None = Field(default=None, max_length=220)
    delegado_id: int = Field(ge=1)
    escrivao_id: int = Field(ge=1)
    ativo: bool = True


class EquipeOperacionalCreate(EquipeOperacionalBase):
    pass


class EquipeOperacionalUpdate(BaseModel):
    numero: str | None = Field(default=None, min_length=1, max_length=40)
    nome: str | None = Field(default=None, max_length=220)
    delegado_id: int | None = None
    escrivao_id: int | None = None
    ativo: bool | None = None


class EquipeOperacionalRead(EquipeOperacionalBase):
    id: int
    agentes_count: int = 0
    delegado_nome: str | None = None
    delegado_matricula: str | None = None
    escrivao_nome: str | None = None
    created_at: datetime


class EquipeAgentesUpdate(BaseModel):
    agente_ids: list[int] = Field(default_factory=list)


class EquipeAcbaItem(BaseModel):
    id: int
    processo_numero: str
    protocolo_numero: str
    data_lavratura: date
    alvo_busca: str
    delegacia_nome: str | None = None
    delegado_nome: str | None = None


class ProcessoBase(BaseModel):
    numero: str = Field(min_length=2, max_length=60)
    descricao: str | None = Field(default=None, max_length=220)
    ativo: bool = True


class ProcessoCreate(ProcessoBase):
    pass


class ProcessoUpdate(BaseModel):
    descricao: str | None = Field(default=None, max_length=220)
    ativo: bool | None = None


class ProcessoRead(ProcessoBase):
    acbas_count: int = 0
    created_at: datetime


class TipoMaterialBase(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    tabela_documento: str = Field(pattern=r"^(informatica|geral)$")
    ativo: bool = True


class TipoMaterialCreate(TipoMaterialBase):
    pass


class TipoMaterialUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    tabela_documento: str | None = Field(
        default=None, pattern=r"^(informatica|geral)$"
    )
    ativo: bool | None = None


class TipoMaterialRead(TipoMaterialBase):
    id: int
    created_at: datetime
