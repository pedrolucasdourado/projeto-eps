from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.schemas import UserRead
from app.services import users_service


pytestmark = pytest.mark.integration


def test_users_routes_require_admin(
    client,
    authenticated_as,
    delegado_user,
):
    authenticated_as(delegado_user)

    response = client.get("/api/users/")

    assert response.status_code == 403


def test_list_users_delegates_to_service(
    monkeypatch,
    client,
    authenticated_as,
    admin_user,
):
    authenticated_as(admin_user)
    captured = {}

    def fake_list_users(role=None, q=None):
        captured["role"] = role
        captured["q"] = q
        return [
            UserRead(
                id=2,
                email="delegado@example.com",
                full_name="Delegado Teste",
                role="delegado",
                ativo=True,
                delegado_id=10,
                created_at=datetime(2026, 5, 26, tzinfo=timezone.utc),
            )
        ]

    monkeypatch.setattr(users_service, "list_users", fake_list_users)

    response = client.get("/api/users/?role=delegado&q=teste")

    assert response.status_code == 200
    assert captured == {"role": "delegado", "q": "teste"}
    body = response.json()
    assert body[0]["email"] == "delegado@example.com"
    assert body[0]["role"] == "delegado"
    assert body[0]["delegado_id"] == 10
