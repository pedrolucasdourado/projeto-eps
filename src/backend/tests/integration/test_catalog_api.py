from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.routers import cadastros


pytestmark = pytest.mark.integration


def test_list_ufs_requires_authentication(client):
    response = client.get("/api/cadastros/ufs")

    assert response.status_code == 401


def test_list_ufs_returns_catalog_rows(
    monkeypatch,
    client,
    authenticated_as,
    admin_user,
):
    authenticated_as(admin_user)
    captured = {}

    def fake_list_ufs(q=None):
        captured["q"] = q
        return [
            {
                "id": 1,
                "sigla": "DF",
                "nome": "Distrito Federal",
                "ativo": True,
                "created_at": datetime(2026, 5, 26, tzinfo=timezone.utc),
            }
        ]

    monkeypatch.setattr(cadastros.catalog_repo, "list_ufs", fake_list_ufs)

    response = client.get("/api/cadastros/ufs?q=distrito")

    assert response.status_code == 200
    assert captured == {"q": "distrito"}
    assert response.json() == [
        {
            "id": 1,
            "sigla": "DF",
            "nome": "Distrito Federal",
            "ativo": True,
            "created_at": "2026-05-26T00:00:00Z",
        }
    ]


def test_create_delegado_requires_admin_role(
    monkeypatch,
    client,
    authenticated_as,
    delegado_user,
):
    authenticated_as(delegado_user)
    calls = []
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "insert_delegado",
        lambda payload: calls.append(payload),
    )

    response = client.post(
        "/api/cadastros/delegados",
        json={
            "nome": "Delegado Novo",
            "matricula": "M-1",
            "delegacia_id": None,
            "unidade_id": None,
            "ativo": True,
        },
    )

    assert response.status_code == 403
    assert calls == []
