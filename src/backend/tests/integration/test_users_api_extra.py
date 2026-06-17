"""Testes de integração para as rotas de usuários (get, update, delete)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.schemas import UserRead, UserUpdate
from app.services import users_service


pytestmark = pytest.mark.integration


def _user_read(**overrides) -> UserRead:
    base = dict(
        id=5,
        email="escrivao@example.com",
        full_name="Escrivão Teste",
        role="escrivao",
        ativo=True,
        escrivao_id=20,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    base.update(overrides)
    return UserRead(**base)


def test_get_user_by_id(monkeypatch, client, authenticated_as, admin_user):
    authenticated_as(admin_user)
    monkeypatch.setattr(users_service, "get_user", lambda uid: _user_read(id=uid))

    response = client.get("/api/users/5")

    assert response.status_code == 200
    assert response.json()["id"] == 5
    assert response.json()["role"] == "escrivao"


def test_create_user_via_api(monkeypatch, client, authenticated_as, admin_user):
    authenticated_as(admin_user)
    monkeypatch.setattr(users_service, "create_user", lambda payload: _user_read())

    response = client.post(
        "/api/users/",
        json={
            "email": "escrivao@example.com",
            "password": "Senha@123",
            "full_name": "Escrivão Teste",
            "role": "escrivao",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "escrivao@example.com"


def test_update_user_via_api(monkeypatch, client, authenticated_as, admin_user):
    authenticated_as(admin_user)
    monkeypatch.setattr(
        users_service,
        "update_user",
        lambda uid, payload: _user_read(full_name="Novo Nome"),
    )

    response = client.put("/api/users/5", json={"full_name": "Novo Nome"})

    assert response.status_code == 200
    assert response.json()["full_name"] == "Novo Nome"


def test_delete_user_via_api(monkeypatch, client, authenticated_as, admin_user):
    authenticated_as(admin_user)
    deleted = []
    monkeypatch.setattr(users_service, "delete_user", lambda uid: deleted.append(uid))

    response = client.delete("/api/users/5")

    assert response.status_code == 204
    assert deleted == [5]


def test_non_admin_cannot_get_user(client, authenticated_as, escrivao_user):
    authenticated_as(escrivao_user)

    response = client.get("/api/users/1")

    assert response.status_code == 403
