from datetime import datetime

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


class AutoridadeBase(BaseModel):
    nome: str = Field(min_length=2, max_length=220)
    matricula: str | None = Field(default=None, max_length=80)
    delegacia_id: int | None = None
    unidade_id: int | None = None
    ativo: bool = True


class AutoridadeCreate(AutoridadeBase):
    pass


class AutoridadeUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=220)
    matricula: str | None = Field(default=None, max_length=80)
    delegacia_id: int | None = None
    unidade_id: int | None = None
    ativo: bool | None = None


class AutoridadeRead(AutoridadeBase):
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


class MembroEquipeBase(BaseModel):
    nome: str = Field(min_length=2, max_length=220)
    matricula: str = Field(min_length=1, max_length=80)
    funcao_padrao: str | None = Field(default=None, max_length=120)
    ativo: bool = True


class MembroEquipeCreate(MembroEquipeBase):
    pass


class MembroEquipeUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=220)
    matricula: str | None = Field(default=None, min_length=1, max_length=80)
    funcao_padrao: str | None = Field(default=None, max_length=120)
    ativo: bool | None = None


class MembroEquipeRead(MembroEquipeBase):
    id: int
    created_at: datetime


class CondutorBase(BaseModel):
    nome: str = Field(min_length=2, max_length=220)
    matricula: str | None = Field(default=None, max_length=80)
    ativo: bool = True


class CondutorCreate(CondutorBase):
    pass


class CondutorUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=220)
    matricula: str | None = Field(default=None, max_length=80)
    ativo: bool | None = None


class CondutorRead(CondutorBase):
    id: int
    created_at: datetime
