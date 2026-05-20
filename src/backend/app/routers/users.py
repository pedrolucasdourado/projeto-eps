"""Rotas REST para gestão de usuários.

Toda esta rota é restrita ao papel ``administrador``. As leituras já
filtram por papel via query string ``role``, o que cobre o uso típico do
front (listar agentes, escrivãos, delegados separadamente).
"""

from fastapi import APIRouter, Depends, Query, Response, status

from app.routers.auth import get_authenticated_user
from app.schemas import UserCreate, UserPublic, UserRead, UserUpdate
from app.services import authz, users_service


router = APIRouter()


def _admin(
    user: UserPublic = Depends(get_authenticated_user),
) -> UserPublic:
    """Garante que somente administrador acessa as rotas de usuários."""
    authz.assert_role(user, ["administrador"])
    return user


@router.get("/", response_model=list[UserRead])
def list_users(
    role: str | None = Query(None, pattern="^(administrador|delegado|escrivao|agente)$"),
    q: str | None = Query(None),
    _admin: UserPublic = Depends(_admin),
) -> list[UserRead]:
    return users_service.list_users(role=role, q=q)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _admin: UserPublic = Depends(_admin),
) -> UserRead:
    return users_service.create_user(payload)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, _admin: UserPublic = Depends(_admin)) -> UserRead:
    return users_service.get_user(user_id)


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    _admin: UserPublic = Depends(_admin),
) -> UserRead:
    return users_service.update_user(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, _admin: UserPublic = Depends(_admin)) -> Response:
    users_service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
