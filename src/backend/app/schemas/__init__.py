from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# Papéis do sistema (espelha o CHECK em users.role).
UserRole = Literal["administrador", "delegado", "escrivao", "agente"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: UserRole = "administrador"
    ativo: bool = True
    # Quando o usuário tem papel operacional (delegado/escrivao/agente), o
    # backend devolve também o id do cadastro vinculado — facilita o frontend
    # decidir, por exemplo, se mostra o botão "Editar".
    delegado_id: int | None = None
    escrivao_id: int | None = None
    agente_id: int | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class TokenPayload(BaseModel):
    sub: int
    email: str


# --- Gestão de usuários (administrador) -------------------------------------


class UserCreate(BaseModel):
    """Payload para o administrador criar um novo usuário operacional.

    Não permite criar outro `administrador` por esta rota — para alterar o
    administrador raiz, é necessário acesso direto ao banco. Isso evita que
    um admin comprometido se replique acidentalmente. Pode ser relaxado se o
    cliente preferir.
    """

    email: EmailStr
    password: str = Field(min_length=6, max_length=120)
    full_name: str = Field(min_length=2, max_length=180)
    role: Literal["delegado", "escrivao", "agente"]
    # Opcional: vincula o login a um cadastro real já existente. Quando
    # informado, o backend valida que o cadastro existe e ainda não tem login.
    delegado_id: int | None = Field(default=None, ge=1)
    escrivao_id: int | None = Field(default=None, ge=1)
    agente_id: int | None = Field(default=None, ge=1)
    ativo: bool = True


class UserUpdate(BaseModel):
    """Atualização de usuário. Campos omitidos não são alterados."""

    full_name: str | None = Field(default=None, min_length=2, max_length=180)
    password: str | None = Field(default=None, min_length=6, max_length=120)
    ativo: bool | None = None
    # Permite trocar o cadastro vinculado (ou desvincular passando 0).
    delegado_id: int | None = Field(default=None, ge=0)
    escrivao_id: int | None = Field(default=None, ge=0)
    agente_id: int | None = Field(default=None, ge=0)


class UserRead(UserPublic):
    created_at: datetime
