from __future__ import annotations

import bcrypt
import pytest

from app.routers import auth as auth_router
from app.schemas import UserPublic
from app.services import auth_service


pytestmark = pytest.mark.integration


def _auth_row(password_hash: str, *, ativo: bool = True) -> dict:
    return {
        "id": 9,
        "email": "delegado@example.com",
        "password_hash": password_hash,
        "full_name": "Delegado Teste",
        "role": "delegado",
        "ativo": ativo,
        "delegado_id": 15,
        "escrivao_id": None,
        "agente_id": None,
    }


def test_healthcheck(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_success_returns_token_and_user(monkeypatch, client):
    password_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode("utf-8")
    monkeypatch.setattr(
        auth_service,
        "fetch_user_by_email",
        lambda email: _auth_row(password_hash),
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "delegado@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "delegado@example.com"
    assert body["user"]["role"] == "delegado"
    assert body["user"]["delegado_id"] == 15


def test_login_rejects_invalid_credentials(monkeypatch, client):
    monkeypatch.setattr(auth_service, "fetch_user_by_email", lambda email: None)

    response = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "secret123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha inválidos."


def test_me_requires_bearer_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Não autenticado."


def test_me_returns_authenticated_user(monkeypatch, client):
    user = UserPublic(
        id=9,
        email="delegado@example.com",
        full_name="Delegado Teste",
        role="delegado",
        delegado_id=15,
    )
    monkeypatch.setattr(
        auth_router,
        "get_current_user_from_token",
        lambda token: user if token == "valid-token" else None,
    )

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == 9
    assert response.json()["role"] == "delegado"
