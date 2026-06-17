"""Testes unitários adicionais para users_service (update, get, list)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.schemas import UserUpdate
from app.services import users_service


pytestmark = pytest.mark.unit


def _row(**overrides) -> dict:
    base = {
        "id": 10,
        "email": "escrivao@example.com",
        "full_name": "Escrivão Teste",
        "role": "escrivao",
        "ativo": True,
        "delegado_id": None,
        "escrivao_id": 5,
        "agente_id": None,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    base.update(overrides)
    return base


def test_get_user_returns_user(monkeypatch):
    monkeypatch.setattr(users_service.users_repo, "get_user", lambda uid: _row())

    result = users_service.get_user(10)

    assert result.id == 10
    assert result.role == "escrivao"
    assert result.escrivao_id == 5


def test_get_user_raises_404_when_not_found(monkeypatch):
    monkeypatch.setattr(users_service.users_repo, "get_user", lambda uid: None)

    with pytest.raises(HTTPException) as exc:
        users_service.get_user(99)

    assert exc.value.status_code == 404


def test_list_users_returns_mapped_list(monkeypatch):
    monkeypatch.setattr(
        users_service.users_repo,
        "list_users",
        lambda role, q: [_row(), _row(id=11, email="agente@example.com", role="agente", escrivao_id=None, agente_id=7)],
    )

    result = users_service.list_users(role="escrivao", q=None)

    assert len(result) == 2
    assert result[0].id == 10
    assert result[1].agente_id == 7


def test_delete_user_calls_repo(monkeypatch):
    deleted = []
    monkeypatch.setattr(users_service.users_repo, "get_user", lambda uid: _row(role="escrivao"))
    monkeypatch.setattr(users_service.users_repo, "delete_user", lambda uid: deleted.append(uid))

    users_service.delete_user(10)

    assert deleted == [10]


def test_delete_user_raises_404_when_missing(monkeypatch):
    monkeypatch.setattr(users_service.users_repo, "get_user", lambda uid: None)

    with pytest.raises(HTTPException) as exc:
        users_service.delete_user(99)

    assert exc.value.status_code == 404


def test_update_user_changes_name_and_status(monkeypatch):
    calls = {}
    monkeypatch.setattr(users_service.users_repo, "get_user", lambda uid: _row())
    monkeypatch.setattr(users_service.users_repo, "desvincular_qualquer", lambda uid: None)
    monkeypatch.setattr(users_service.users_repo, "link_user_to_cadastro", lambda *a: None)
    monkeypatch.setattr(users_service.users_repo, "cadastro_dono_user_id", lambda role, cid: None)
    monkeypatch.setattr(
        users_service.users_repo,
        "update_user",
        lambda uid, **kw: calls.update(kw),
    )
    # get_user after update
    monkeypatch.setattr(
        users_service.users_repo,
        "get_user",
        lambda uid: _row(full_name="Novo Nome", ativo=False),
    )

    result = users_service.update_user(
        10,
        UserUpdate(full_name="Novo Nome", ativo=False),
    )

    assert result.full_name == "Novo Nome"
    assert result.ativo is False


def test_update_user_raises_404_when_not_found(monkeypatch):
    monkeypatch.setattr(users_service.users_repo, "get_user", lambda uid: None)

    with pytest.raises(HTTPException) as exc:
        users_service.update_user(99, UserUpdate())

    assert exc.value.status_code == 404
