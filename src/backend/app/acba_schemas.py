from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.schemas.materiais import MaterialCreate


class TestemunhaItem(BaseModel):
    nome: str = Field(min_length=2, max_length=180)
    documento: str = Field(min_length=2, max_length=80)
    contato: str = Field(min_length=2, max_length=120)


def _clean_testemunhas(items: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if not isinstance(items, list):
        return out
    for raw in items:
        if not isinstance(raw, dict):
            continue
        nome = str(raw.get("nome", "")).strip()
        documento = str(raw.get("documento", "")).strip()
        contato = str(raw.get("contato", "")).strip()
        if len(nome) >= 2 and len(documento) >= 2 and len(contato) >= 2:
            out.append({"nome": nome, "documento": documento, "contato": contato})
    return out


class AcbaBase(BaseModel):
    processo_numero: str = Field(min_length=2, max_length=60)
    protocolo_numero: str = Field(min_length=2, max_length=60)
    unidade_id: int = Field(ge=1)
    delegacia_id: int = Field(ge=1)
    cidade_id: int = Field(ge=1)
    data_lavratura: date
    hora_lavratura: time
    tipo_procedimento_id: int = Field(ge=1)
    procedimento_numero: str = Field(min_length=2, max_length=120)
    fundamento_legal: str = Field(min_length=5)
    endereco_busca: str = Field(min_length=5)
    alvo_busca: str = Field(min_length=2, max_length=220)
    assinatura_responsavel: str = Field(min_length=2, max_length=220)
    observacoes: str = ""
    equipe_id: int = Field(ge=1)
    testemunhas: list[TestemunhaItem] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_json_lists(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if "testemunhas" in out:
            out["testemunhas"] = _clean_testemunhas(out.get("testemunhas"))
        return out


class AcbaCreate(AcbaBase):
    materiais: list[MaterialCreate] = Field(default_factory=list)


class AcbaUpdate(AcbaBase):
    pass


class AgenteBrief(BaseModel):
    id: int
    nome: str
    matricula: str
    funcao_padrao: str | None = None


class AcbaListItem(BaseModel):
    id: int
    processo_numero: str
    protocolo_numero: str
    delegacia_nome: str
    data_lavratura: date
    alvo_busca: str
    delegado_nome: str
    equipe_numero: str
    equipe_nome: str | None = None
    created_at: datetime
    materiais_pendentes_revisao: int = 0


class AcbaDetail(BaseModel):
    id: int
    processo_numero: str
    protocolo_numero: str
    unidade_id: int
    delegacia_id: int
    cidade_id: int
    data_lavratura: date
    hora_lavratura: time
    tipo_procedimento_id: int
    procedimento_numero: str
    fundamento_legal: str
    endereco_busca: str
    alvo_busca: str
    assinatura_responsavel: str
    observacoes: str
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

    unidade_nome: str
    delegacia_nome: str
    cidade_nome: str
    uf_sigla: str
    uf_nome: str
    tipo_procedimento_nome: str
    processo_descricao: str | None = None

    equipe_id: int
    equipe_numero: str
    equipe_nome: str | None = None
    delegado_id: int
    delegado_nome: str
    delegado_matricula: str | None = None
    escrivao_id: int
    escrivao_nome: str

    agentes_equipe: list[AgenteBrief]
    testemunhas: list[dict[str, Any]]
    materiais: list[dict[str, Any]] = Field(default_factory=list)
    materiais_pendentes_revisao: int = 0
