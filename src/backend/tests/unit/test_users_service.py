from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.schemas import UserCreate
from app.services import users_service


pytestmark = pytest.mark.unit


def _user_row(**overrides) -> dict:
    row = {
        "id": 12,
        "email": "agente@example.com",
        "full_name": "Agente Teste",
        "role": "agente",
        "ativo": True,
        "delegado_id": None,
        "escrivao_id": None,
        "agente_id": 4,
        "created_at": datetime.now(timezone.utc),
    }
    row.update(overrides)
    return row


def test_create_user_links_matching_cadastro(monkeypatch):
    calls = []

    monkeypatch.setattr(users_service, "_hash_password", lambda plain: "HASHED")
    monkeypatch.setattr(users_service.users_repo, "get_user_by_email", lambda email: None)
    monkeypatch.setattr(
        users_service.users_repo,
        "cadastro_existe_e_livre",
        lambda role, cadastro_id: role == "agente" and cadastro_id == 4,
    )
    monkeypatch.setattr(
        users_service.users_repo,
        "insert_user",
        lambda **kwargs: calls.append(("insert", kwargs)) or 12,
    )
    monkeypatch.setattr(
        users_service.users_repo,
        "link_user_to_cadastro",
        lambda role, cadastro_id, user_id: calls.append(
            ("link", role, cadastro_id, user_id)
        ),
    )
    monkeypatch.setattr(users_service.users_repo, "get_user", lambda user_id: _user_row())

    result = users_service.create_user(
        UserCreate(
            email="agente@example.com",
            password="secret123",
            full_name="Agente Teste",
            role="agente",
            agente_id=4,
        )
    )

    assert result.id == 12
    assert result.agente_id == 4
    assert calls[0] == (
        "insert",
        {
            "email": "agente@example.com",
            "password_hash": "HASHED",
            "full_name": "Agente Teste",
            "role": "agente",
            "ativo": True,
        },
    )
    assert calls[1] == ("link", "agente", 4, 12)


def test_create_user_rejects_duplicate_email(monkeypatch):
    monkeypatch.setattr(
        users_service.users_repo,
        "get_user_by_email",
        lambda email: _user_row(email=email),
    )

    with pytest.raises(HTTPException) as exc:
        users_service.create_user(
            UserCreate(
                email="agente@example.com",
                password="secret123",
                full_name="Agente Teste",
                role="agente",
            )
        )

    assert exc.value.status_code == 409


def test_create_user_rejects_cadastro_from_another_role(monkeypatch):
    monkeypatch.setattr(users_service.users_repo, "get_user_by_email", lambda email: None)

    with pytest.raises(HTTPException) as exc:
        users_service.create_user(
            UserCreate(
                email="delegado@example.com",
                password="secret123",
                full_name="Delegado Teste",
                role="delegado",
                delegado_id=1,
                agente_id=4,
            )
        )

    assert exc.value.status_code == 400
    assert "papel" in exc.value.detail


def test_delete_user_blocks_administrador(monkeypatch):
    deleted = []
    monkeypatch.setattr(
        users_service.users_repo,
        "get_user",
        lambda user_id: _user_row(role="administrador", agente_id=None),
    )
    monkeypatch.setattr(
        users_service.users_repo,
        "delete_user",
        lambda user_id: deleted.append(user_id),
    )

    with pytest.raises(HTTPException) as exc:
        users_service.delete_user(1)

    assert exc.value.status_code == 409
    assert deleted == []
