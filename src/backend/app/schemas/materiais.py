from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


CategoriaDocx = Literal["informatica", "geral"]
SenhaTipo = Literal["nenhuma", "texto", "padrao", "biometria", "desconhecida"]


class InformaticaPayload(BaseModel):
    senha_tipo: SenhaTipo = "nenhuma"
    senha_texto: str | None = Field(default=None, max_length=255)
    senha_padrao_pontos: list[int] | None = None
    senha_observacao: str | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> "InformaticaPayload":
        if self.senha_tipo == "texto":
            if not (self.senha_texto and self.senha_texto.strip()):
                raise ValueError(
                    "Para senha_tipo='texto' informe senha_texto."
                )
        elif self.senha_tipo == "padrao":
            pts = self.senha_padrao_pontos or []
            if not 4 <= len(pts) <= 9:
                raise ValueError(
                    "Padrão de bloqueio precisa de 4 a 9 pontos."
                )
            if any(p < 1 or p > 9 for p in pts):
                raise ValueError("Pontos do padrão devem estar entre 1 e 9.")
            if len(set(pts)) != len(pts):
                raise ValueError("Pontos do padrão não podem repetir.")
        return self


class MaterialBase(BaseModel):
    tipo_id: int = Field(ge=1)
    descricao: str = Field(min_length=1)
    descricao_ia_raw: str | None = None
    revisado: bool = False
    item_num: int | None = Field(default=None, ge=1)
    acondicionamento: str | None = Field(default=None, max_length=160)
    localizacao: str | None = None
    observacao: str | None = None
    ordem: int = 0
    informatica: InformaticaPayload | None = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(MaterialBase):
    """Update completo (PUT). Espera-se o payload inteiro."""

    pass


class MaterialReorder(BaseModel):
    """Atualiza apenas a ordem de N materiais de um ACBA."""

    materiais: list[dict] = Field(default_factory=list)
    # cada item: { "id": int, "ordem": int, "item_num": int }


class MaterialRead(MaterialBase):
    id: int
    acba_id: int
    item_num: int
    categoria_docx: CategoriaDocx
    tipo_nome: str
    created_at: datetime
    updated_at: datetime


class DescribeRequest(BaseModel):
    """Body opcional para customizar a chamada do Gemini."""

    instrucoes_extra: str | None = Field(default=None, max_length=2000)
    forcar: bool = False  # ignora cache


class DescribeResponse(BaseModel):
    descricao: str
    revisado: bool = False
    cache_hit: bool
    modelo: str
    prompt_versao: str


class IaRunRead(BaseModel):
    id: int
    material_id: int
    modelo: str
    prompt_versao: str
    request_hash: str
    resposta: str
    custo_tokens: int | None = None
    created_at: datetime
