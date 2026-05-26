from __future__ import annotations

import bcrypt
import pytest

from app.schemas import LoginRequest
from app.services import auth_service


pytestmark = pytest.mark.unit


def _user_row(password_hash: str, *, ativo: bool = True) -> dict:
    return {
        "id": 7,
        "email": "user@example.com",
        "password_hash": password_hash,
        "full_name": "Usuario Teste",
        "role": "delegado",
        "ativo": ativo,
        "delegado_id": 11,
        "escrivao_id": None,
        "agente_id": None,
    }


def test_login_returns_token_and_public_user(monkeypatch):
    password_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode("utf-8")
    monkeypatch.setattr(
        auth_service,
        "fetch_user_by_email",
        lambda email: _user_row(password_hash),
    )

    result = auth_service.login(
        LoginRequest(email="user@example.com", password="secret123")
    )

    assert result is not None
    assert result.token_type == "bearer"
    assert result.user.id == 7
    assert result.user.role == "delegado"
    assert result.user.delegado_id == 11

    payload = auth_service.decode_token(result.access_token)
    assert payload is not None
    assert payload["sub"] == "7"
    assert payload["email"] == "user@example.com"


def test_login_rejects_inactive_user(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "fetch_user_by_email",
        lambda email: _user_row("irrelevant", ativo=False),
    )
    monkeypatch.setattr(auth_service, "verify_password", lambda plain, hashed: True)

    result = auth_service.login(
        LoginRequest(email="user@example.com", password="secret123")
    )

    assert result is None


def test_verify_password_handles_invalid_hash():
    assert auth_service.verify_password("secret123", "not-a-bcrypt-hash") is False


def test_current_user_from_token_rejects_inactive_user(monkeypatch):
    token = auth_service.create_access_token(7, "user@example.com")
    monkeypatch.setattr(
        auth_service,
        "fetch_user_by_id",
        lambda user_id: _user_row("irrelevant", ativo=False),
    )

    assert auth_service.get_current_user_from_token(token) is None
