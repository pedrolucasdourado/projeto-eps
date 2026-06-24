from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException

from app.repositories.acba_repository import AcbaRepository
from app.schemas import UserPublic
from app.services import authz
from tests.helpers.db_mock import FakeCursor


pytestmark = pytest.mark.unit


def test_acba_repository_list_empty_scope():
    repo = AcbaRepository()
    assert repo.list_all(equipe_ids=[]) == []


def test_acba_repository_list_all_with_filters(monkeypatch):
    captured = {}

    def fake_fetch_all(query, params=None):
        captured["params"] = params
        return [{"id": 1}]

    monkeypatch.setattr("app.repositories.acba_repository.fetch_all", fake_fetch_all)
    repo = AcbaRepository()
    rows = repo.list_all(tipo_material_id=2, equipe_ids=[1], temporal_agente_id=3)
    assert rows == [{"id": 1}]
    assert captured["params"]["tipo_material_id"] == 2


def test_authz_escrivao_scope(monkeypatch):
    monkeypatch.setattr(
        authz,
        "fetch_all",
        lambda q, p=None: [{"id": 5}, {"id": 6}],
    )
    user = UserPublic(id=1, email="e@p.com", full_name="E", role="escrivao", escrivao_id=2)
    assert authz.acba_equipe_scope(user) == [5, 6]


def test_authz_agente_scope(monkeypatch):
    monkeypatch.setattr(
        authz,
        "fetch_all",
        lambda q, p=None: [{"id": 7}],
    )
    user = UserPublic(id=1, email="a@p.com", full_name="A", role="agente", agente_id=3)
    assert authz.acba_equipe_scope(user) == [7]
    assert authz.acba_temporal_agente_id(user) == 3


def test_authz_assert_team_scope(monkeypatch):
    monkeypatch.setattr(authz, "fetch_all", lambda q, p=None: [{"id": 1}])
    user = UserPublic(id=1, email="e@p.com", full_name="E", role="escrivao", escrivao_id=2)
    authz.assert_team_scope_contains(user, 1, action="editar")
    with pytest.raises(HTTPException):
        authz.assert_team_scope_contains(user, 99, action="editar")


def test_authz_can_edit_after_pdf_blocks_escrivao():
    user = UserPublic(id=1, email="e@p.com", full_name="E", role="escrivao", escrivao_id=2)
    with pytest.raises(HTTPException) as exc:
        authz.assert_can_edit_after_pdf(user, datetime.now(timezone.utc))
    assert exc.value.status_code == 409


def test_authz_visivel_para_agente(monkeypatch):
    monkeypatch.setattr(
        authz,
        "fetch_all",
        lambda q, p=None: [{"id": 1}],
    )
    user = UserPublic(id=1, email="a@p.com", full_name="A", role="agente", agente_id=3)
    assert authz.acba_visivel_para(user, 1, date(2026, 1, 1)) is True
