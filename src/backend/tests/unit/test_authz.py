from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.schemas import UserPublic
from app.services import authz


pytestmark = pytest.mark.unit


def _user(role: str, **kwargs) -> UserPublic:
    return UserPublic(
        id=1,
        email=f"{role}@example.com",
        full_name=f"{role} Teste",
        role=role,  # type: ignore[arg-type]
        **kwargs,
    )


def test_administrador_cannot_access_acba():
    with pytest.raises(HTTPException) as exc:
        authz.assert_can_access_acba(_user("administrador"))

    assert exc.value.status_code == 403
    assert "Administradores" in exc.value.detail


def test_delegado_has_unrestricted_acba_scope():
    assert authz.acba_equipe_scope(_user("delegado", delegado_id=10)) is None


def test_escrivao_scope_uses_linked_teams(monkeypatch):
    seen_params = []

    def fake_fetch_all(_query, params):
        seen_params.append(params)
        return [{"id": "3"}, {"id": 5}]

    monkeypatch.setattr(authz, "fetch_all", fake_fetch_all)

    scope = authz.acba_equipe_scope(_user("escrivao", escrivao_id=20))

    assert scope == [3, 5]
    assert seen_params == [(20,)]


def test_assert_can_update_acba_blocks_agent():
    with pytest.raises(HTTPException) as exc:
        authz.assert_can_update_acba(
            _user("agente", agente_id=30),
            equipe_id=1,
            pdf_gerado_at=None,
        )

    assert exc.value.status_code == 403
    assert "Agentes" in exc.value.detail


def test_assert_can_update_acba_blocks_escrivao_after_pdf(monkeypatch):
    monkeypatch.setattr(authz, "acba_equipe_scope", lambda user: [1])

    with pytest.raises(HTTPException) as exc:
        authz.assert_can_update_acba(
            _user("escrivao", escrivao_id=20),
            equipe_id=1,
            pdf_gerado_at=datetime.now(timezone.utc),
        )

    assert exc.value.status_code == 409
    assert "PDF" in exc.value.detail


def test_acba_temporal_scope_only_applies_to_agent():
    assert authz.acba_temporal_agente_id(_user("agente", agente_id=30)) == 30
    assert authz.acba_temporal_agente_id(_user("delegado", delegado_id=10)) is None
