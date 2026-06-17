from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.config import settings
from app.db import fetch_user_by_email, fetch_user_by_id
from app.schemas import LoginRequest, LoginResponse, UserPublic


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError:
        return None


def _row_to_user_public(row: dict) -> UserPublic:
    return UserPublic(
        id=row["id"],
        email=row["email"],
        full_name=row.get("full_name"),
        role=row.get("role") or "administrador",
        ativo=bool(row.get("ativo", True)),
        delegado_id=row.get("delegado_id"),
        escrivao_id=row.get("escrivao_id"),
        agente_id=row.get("agente_id"),
    )


def login(body: LoginRequest) -> LoginResponse | None:
    row = fetch_user_by_email(body.email)
    if not row or not verify_password(body.password, row["password_hash"]):
        return None
    # Usuário desativado: comportamento idêntico a credenciais inválidas para
    # não revelar a existência do e-mail.
    if not row.get("ativo", True):
        return None
    token = create_access_token(row["id"], row["email"])
    return LoginResponse(access_token=token, user=_row_to_user_public(row))


def get_current_user_from_token(token: str) -> UserPublic | None:
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = int(str(payload["sub"]))
    row = fetch_user_by_id(user_id)
    if not row:
        return None
    # Tokens emitidos antes de uma desativação param de funcionar
    # imediatamente — preferimos isso a exigir lista de revogação.
    if not row.get("ativo", True):
        return None
    return _row_to_user_public(row)
