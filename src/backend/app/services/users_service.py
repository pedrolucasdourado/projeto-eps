"""Casos de uso de gestão de usuários (rota de administrador)."""

import bcrypt
from fastapi import HTTPException, status
from psycopg2 import Error as PsycopgError

from app.repositories import users_repo
from app.schemas import UserCreate, UserRead, UserUpdate


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


def _to_read(row: dict) -> UserRead:
    return UserRead(
        id=row["id"],
        email=row["email"],
        full_name=row.get("full_name"),
        role=row["role"],
        ativo=bool(row.get("ativo", True)),
        delegado_id=row.get("delegado_id"),
        escrivao_id=row.get("escrivao_id"),
        agente_id=row.get("agente_id"),
        created_at=row["created_at"],
    )


def list_users(role: str | None = None, q: str | None = None) -> list[UserRead]:
    rows = users_repo.list_users(role=role, q=q)
    return [_to_read(r) for r in rows]


def get_user(user_id: int) -> UserRead:
    row = users_repo.get_user(user_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )
    return _to_read(row)


def _resolve_cadastro_id(payload: UserCreate) -> int | None:
    """Resolve qual cadastro o usuário recebe conforme o papel pedido.

    Apenas um id pode ser informado; deve corresponder ao papel.
    """
    mapping = {
        "delegado": payload.delegado_id,
        "escrivao": payload.escrivao_id,
        "agente": payload.agente_id,
    }
    chosen = mapping.get(payload.role)
    outros = [
        v for k, v in mapping.items() if v is not None and k != payload.role
    ]
    if outros:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Informe apenas o id do cadastro correspondente ao papel "
                "selecionado."
            ),
        )
    return chosen


def create_user(payload: UserCreate) -> UserRead:
    existing = users_repo.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com este e-mail.",
        )

    cadastro_id = _resolve_cadastro_id(payload)
    if cadastro_id is not None:
        if not users_repo.cadastro_existe_e_livre(payload.role, cadastro_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Cadastro selecionado não existe ou já está vinculado a "
                    "outro usuário."
                ),
            )

    try:
        new_id = users_repo.insert_user(
            email=payload.email,
            password_hash=_hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role,
            ativo=payload.ativo,
        )
    except PsycopgError as exc:
        if getattr(exc, "pgcode", None) == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário com este e-mail.",
            ) from exc
        raise

    if cadastro_id is not None:
        users_repo.link_user_to_cadastro(payload.role, cadastro_id, new_id)

    return get_user(new_id)


def update_user(user_id: int, payload: UserUpdate) -> UserRead:
    target = users_repo.get_user(user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    # Vínculos: aceita 0 como "desvincular"; só relevante se o papel suporta.
    if target["role"] in ("delegado", "escrivao", "agente"):
        novo_vinculo = {
            "delegado": payload.delegado_id,
            "escrivao": payload.escrivao_id,
            "agente": payload.agente_id,
        }[target["role"]]
        if novo_vinculo is not None:
            if novo_vinculo == 0:
                users_repo.desvincular_qualquer(user_id)
            else:
                dono = users_repo.cadastro_dono_user_id(
                    target["role"], novo_vinculo
                )
                if dono is not None and dono != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Este cadastro já está vinculado a outro usuário.",
                    )
                users_repo.desvincular_qualquer(user_id)
                users_repo.link_user_to_cadastro(
                    target["role"], novo_vinculo, user_id
                )

    users_repo.update_user(
        user_id,
        full_name=payload.full_name,
        password_hash=_hash_password(payload.password) if payload.password else None,
        ativo=payload.ativo,
    )
    return get_user(user_id)


def delete_user(user_id: int) -> None:
    target = users_repo.get_user(user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )
    if target["role"] == "administrador":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Administradores não podem ser excluídos por esta rota. "
                "Desative o cadastro em vez de apagar."
            ),
        )
    users_repo.delete_user(user_id)
