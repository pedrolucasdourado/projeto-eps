from datetime import date, datetime, time
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.materiais import MaterialCreate


TestemunhaTipo = Literal["geral", "arrombamento"]


class TestemunhaArrombamentoExtras(BaseModel):
    """Especialização parcial exclusiva (acba_testemunhas_arrombamento).

    Aqui ficam apenas os campos EXCLUSIVOS da testemunha de arrombamento.
    Os campos comuns (nome, cpf, rg, filiação, endereço) vivem na
    super-classe `TestemunhaItem`.
    """

    observacoes: str = ""


class TestemunhaItem(BaseModel):
    """Super-classe (acba_testemunhas).

    Campos comuns a toda testemunha: nome, cpf, rg, filiação e endereço.
    Testemunhas gerais qualificam cidade e telefone; testemunhas de
    arrombamento (Art. 245 §4º do CPP) qualificam observações via
    `arrombamento` (sub-classe 1:1, parcial exclusiva).
    """

    tipo: TestemunhaTipo = "geral"
    nome: str = Field(min_length=2, max_length=180)
    cpf: str = Field(min_length=3, max_length=20)
    rg: str = Field(min_length=1, max_length=40)
    filiacao: str = Field(min_length=2, max_length=220)
    endereco: str = Field(min_length=5)
    cidade: str | None = Field(default=None, max_length=120)
    telefone: str | None = Field(default=None, max_length=40)
    arrombamento: TestemunhaArrombamentoExtras | None = None

    @model_validator(mode="after")
    def _validate_tipo_coerencia(self) -> "TestemunhaItem":
        # Sub-classe parcial exclusiva: só testemunhas de arrombamento têm
        # a especialização (espelha o trigger trg_check_testemunha_arrombamento).
        if self.tipo == "arrombamento":
            # cidade e telefone são exclusivos da testemunha geral; ignorá-los
            # silenciosamente garante coerência com a tabela.
            self.cidade = None
            self.telefone = None
            if self.arrombamento is None:
                self.arrombamento = TestemunhaArrombamentoExtras()
        else:
            if self.arrombamento is not None:
                raise ValueError(
                    "Apenas testemunhas do tipo 'arrombamento' podem ter "
                    "observações de arrombamento."
                )
        return self


class MoradorPresente(BaseModel):
    """Qualificação do morador presente na diligência (Art. 245 caput e §1º
    do CPP)."""

    nome: str = Field(min_length=2, max_length=180)
    cpf: str = Field(min_length=3, max_length=20)
    rg: str = Field(min_length=1, max_length=40)
    filiacao: str = Field(min_length=2, max_length=220)
    telefone: str = Field(min_length=4, max_length=40)


def _clean_testemunhas(items: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    for raw in items:
        if not isinstance(raw, dict):
            continue
        tipo = str(raw.get("tipo", "geral")).strip().lower() or "geral"
        if tipo not in ("geral", "arrombamento"):
            tipo = "geral"
        cleaned: dict[str, Any] = {
            "tipo": tipo,
            "nome": str(raw.get("nome", "")).strip(),
            "cpf": str(raw.get("cpf", "")).strip(),
            "rg": str(raw.get("rg", "")).strip(),
            "filiacao": str(raw.get("filiacao", "")).strip(),
            "endereco": str(raw.get("endereco", "")).strip(),
        }
        if tipo == "geral":
            cidade = str(raw.get("cidade") or "").strip()
            telefone = str(raw.get("telefone") or "").strip()
            cleaned["cidade"] = cidade or None
            cleaned["telefone"] = telefone or None
        else:
            arr = raw.get("arrombamento") or {}
            obs = ""
            if isinstance(arr, dict):
                obs = str(arr.get("observacoes", "")).strip()
            cleaned["arrombamento"] = {"observacoes": obs}
        out.append(cleaned)
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
    nome_vara_criminal: str = Field(default="", max_length=220)
    nome_juiz: str = Field(default="", max_length=220)
    assinatura_responsavel: str = Field(min_length=2, max_length=220)
    observacoes: str = ""
    equipe_id: int = Field(ge=1)
    testemunhas: list[TestemunhaItem] = Field(default_factory=list)
    # Bloco do Art. 245 §§ 2º, 3º e 4º do CPP — cada cenário é independente
    # e pode acumular observações livres do operador.
    arrombamento_245_2: bool = False
    arrombamento_245_2_obs: str = ""
    forca_coisas_245_3: bool = False
    forca_coisas_245_3_obs: str = ""
    morador_ausente_245_4: bool = False
    morador_ausente_245_4_obs: str = ""
    # Qualificação do morador presente. Só é obrigatória/válida quando
    # `morador_ausente_245_4 == False`. Quando o morador estava ausente,
    # estes campos ficam vazios e a testemunha de arrombamento (§4º) assume
    # o papel de pessoa qualificada que presenciou a diligência.
    morador_nome: str = Field(default="", max_length=180)
    morador_cpf: str = Field(default="", max_length=20)
    morador_rg: str = Field(default="", max_length=40)
    morador_filiacao: str = Field(default="", max_length=220)
    morador_telefone: str = Field(default="", max_length=40)

    @model_validator(mode="before")
    @classmethod
    def normalize_json_lists(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if "testemunhas" in out:
            out["testemunhas"] = _clean_testemunhas(out.get("testemunhas"))
        return out

    @model_validator(mode="after")
    def _validate_art_245(self) -> "AcbaBase":
        # Cada hipótese marcada exige observações descrevendo a circunstância,
        # resguardando a validade jurídica do auto.
        if self.arrombamento_245_2 and not self.arrombamento_245_2_obs.strip():
            raise ValueError(
                "Informe as observações do arrombamento de porta "
                "(Art. 245, §2º do CPP)."
            )
        if self.forca_coisas_245_3 and not self.forca_coisas_245_3_obs.strip():
            raise ValueError(
                "Informe as observações do emprego de força contra coisas "
                "(Art. 245, §3º do CPP)."
            )
        if self.morador_ausente_245_4 and not self.morador_ausente_245_4_obs.strip():
            raise ValueError(
                "Informe as observações da diligência com morador ausente "
                "(Art. 245, §4º do CPP)."
            )
        # Quando o morador estava ausente (§4º), é OBRIGATÓRIA pelo menos
        # uma testemunha vizinha qualificada (tipo='arrombamento') — e os
        # campos do morador presente NÃO devem ser preenchidos.
        if self.morador_ausente_245_4:
            if not any(t.tipo == "arrombamento" for t in self.testemunhas):
                raise ValueError(
                    "Em diligências com morador ausente (Art. 245, §4º do "
                    "CPP) é obrigatório adicionar ao menos uma testemunha "
                    "vizinha qualificada (com CPF, RG, filiação e endereço)."
                )
            # Limpa silenciosamente eventual lixo enviado pelo cliente:
            # quando o morador estava ausente, não existe morador presente.
            self.morador_nome = ""
            self.morador_cpf = ""
            self.morador_rg = ""
            self.morador_filiacao = ""
            self.morador_telefone = ""
        else:
            # Morador presente: qualificação completa é obrigatória.
            try:
                MoradorPresente(
                    nome=self.morador_nome,
                    cpf=self.morador_cpf,
                    rg=self.morador_rg,
                    filiacao=self.morador_filiacao,
                    telefone=self.morador_telefone,
                )
            except Exception as exc:
                raise ValueError(
                    "Quando o morador estava presente, é obrigatório informar "
                    "nome, CPF, RG, filiação e telefone do morador."
                ) from exc
        return self


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
    pdf_gerado_at: datetime | None = None


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
    nome_vara_criminal: str = ""
    nome_juiz: str = ""
    assinatura_responsavel: str
    observacoes: str
    arrombamento_245_2: bool = False
    arrombamento_245_2_obs: str = ""
    forca_coisas_245_3: bool = False
    forca_coisas_245_3_obs: str = ""
    morador_ausente_245_4: bool = False
    morador_ausente_245_4_obs: str = ""
    morador_nome: str = ""
    morador_cpf: str = ""
    morador_rg: str = ""
    morador_filiacao: str = ""
    morador_telefone: str = ""
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    # Marcação do último PDF gerado (None = nunca gerado). Quando preenchido,
    # bloqueia a edição pelo escrivão (mas não pelo delegado).
    pdf_gerado_at: datetime | None = None
    pdf_gerado_por_user_id: int | None = None

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
