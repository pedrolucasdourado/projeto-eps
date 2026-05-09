from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, Field, model_validator


class TestemunhaItem(BaseModel):
    nome: str = Field(min_length=2, max_length=180)
    documento: str = Field(min_length=2, max_length=80)
    contato: str = Field(min_length=2, max_length=120)


class ObjetoItem(BaseModel):
    descricao: str = Field(min_length=2, max_length=300)
    quantidade: int = Field(ge=1, le=999999)
    acondicionamento: str = Field(min_length=2, max_length=120)
    observacao: str = Field(default="", max_length=300)


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


def _clean_objetos(items: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    for raw in items:
        if not isinstance(raw, dict):
            continue
        descricao = str(raw.get("descricao", "")).strip()
        acondicionamento = str(raw.get("acondicionamento", "")).strip()
        observacao = str(raw.get("observacao", "") or "").strip()
        try:
            quantidade = int(raw.get("quantidade", 1))
        except (TypeError, ValueError):
            quantidade = 0
        if len(descricao) >= 2 and quantidade >= 1 and len(acondicionamento) >= 2:
            out.append(
                {
                    "descricao": descricao,
                    "quantidade": quantidade,
                    "acondicionamento": acondicionamento,
                    "observacao": observacao,
                }
            )
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
    objetos_arrecadados: list[ObjetoItem] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_json_lists(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if "testemunhas" in out:
            out["testemunhas"] = _clean_testemunhas(out.get("testemunhas"))
        if "objetos_arrecadados" in out:
            out["objetos_arrecadados"] = _clean_objetos(out.get("objetos_arrecadados"))
        return out


class AcbaCreate(AcbaBase):
    pass


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
    objetos_arrecadados: list[dict[str, Any]]
