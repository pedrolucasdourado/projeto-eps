from __future__ import annotations

from contextlib import contextmanager
from datetime import date

import pytest

from app.repositories import acba_repository
from app.repositories.acba_repository import (
    AcbaRepository,
    _insert_testemunhas_with_cursor,
    _list_testemunhas,
)
from tests.helpers.db_mock import FakeConnection, FakeCursor


pytestmark = pytest.mark.unit


def test_list_testemunhas_geral_and_arrombamento(monkeypatch):
    monkeypatch.setattr(
        acba_repository,
        "fetch_all",
        lambda q, p=None: [
            {
                "id": 1,
                "tipo": "geral",
                "nome": "A",
                "cpf": "1",
                "rg": "1",
                "filiacao": "F",
                "endereco": "Rua",
                "cidade": "Gama",
                "telefone": "999",
                "ordem": 0,
                "arrombamento_observacoes": None,
            },
            {
                "id": 2,
                "tipo": "arrombamento",
                "nome": "B",
                "cpf": "2",
                "rg": "2",
                "filiacao": "F",
                "endereco": "Rua",
                "cidade": None,
                "telefone": None,
                "ordem": 1,
                "arrombamento_observacoes": "viu",
            },
        ],
    )
    rows = _list_testemunhas(1)
    assert rows[0]["cidade"] == "Gama"
    assert rows[1]["arrombamento"]["observacoes"] == "viu"


def test_insert_testemunhas_with_cursor():
    cursor = FakeCursor(fetchone_results=[{"id": 10}, {"id": 11}])
    _insert_testemunhas_with_cursor(
        cursor,
        1,
        [
            {
                "tipo": "geral",
                "nome": "A",
                "cpf": "1",
                "rg": "1",
                "filiacao": "F",
                "endereco": "Rua",
                "cidade": "Gama",
                "telefone": "999",
            },
            {
                "tipo": "arrombamento",
                "nome": "B",
                "cpf": "2",
                "rg": "2",
                "filiacao": "F",
                "endereco": "Rua",
                "arrombamento": {"observacoes": "obs"},
            },
        ],
    )
    assert len(cursor.executes) == 3


def test_insert_testemunhas_failure_raises():
    cursor = FakeCursor(fetchone_results=[None])
    with pytest.raises(RuntimeError, match="testemunha"):
        _insert_testemunhas_with_cursor(
            cursor,
            1,
            [
                {
                    "tipo": "geral",
                    "nome": "A",
                    "cpf": "1",
                    "rg": "1",
                    "filiacao": "F",
                    "endereco": "Rua",
                }
            ],
        )


def test_get_by_id_enriches_record(monkeypatch):
    base_row = {
        "id": 1,
        "equipe_id": 5,
        "data_lavratura": date(2026, 1, 15),
        "processo_numero": "P1",
    }

    def fake_fetch_all(query, params=None):
        if "equipe_operacional_vinculos" in query:
            return [{"id": 3, "nome": "Agente", "matricula": "A1", "funcao_padrao": "Agente"}]
        if "acba_testemunhas" in query:
            return []
        return []

    monkeypatch.setattr(acba_repository, "fetch_one", lambda q, p=None: dict(base_row))
    monkeypatch.setattr(acba_repository, "fetch_all", fake_fetch_all)
    monkeypatch.setattr(
        "app.repositories.materiais_repository.list_by_acba",
        lambda acba_id: [{"id": 1}],
    )
    monkeypatch.setattr(
        "app.repositories.materiais_repository.count_pendentes_revisao",
        lambda acba_id: 2,
    )

    row = AcbaRepository().get_by_id(1)
    assert row["agentes_equipe"]
    assert row["materiais_pendentes_revisao"] == 2


def test_get_by_id_missing_returns_none(monkeypatch):
    monkeypatch.setattr(acba_repository, "fetch_one", lambda q, p=None: None)
    assert AcbaRepository().get_by_id(99) is None


def test_create_acba_transaction(monkeypatch):
    cursor = FakeCursor(fetchone_results=[{"id": 42}])
    detail = {
        "id": 42,
        "equipe_id": 1,
        "data_lavratura": date(2026, 1, 1),
        "processo_numero": "P1",
        "testemunhas": [],
        "materiais": [],
        "materiais_pendentes_revisao": 0,
        "agentes_equipe": [],
    }

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(acba_repository, "get_connection", mock_conn)
    monkeypatch.setattr(
        "app.repositories.materiais_repository.insert_material_with_cursor",
        lambda cur, acba_id, mat: 1,
    )
    monkeypatch.setattr(AcbaRepository, "get_by_id", lambda self, rid: detail)

    row = AcbaRepository().create(
        {"processo_numero": "P1", "testemunhas": []},
        [{"tipo_id": 1, "descricao": "Item"}],
        created_by_user_id=1,
    )
    assert row["id"] == 42


def test_update_acba_replaces_testemunhas(monkeypatch):
    cursor = FakeCursor(fetchone_results=[{"id": 1}])
    detail = {"id": 1, "equipe_id": 1, "data_lavratura": date(2026, 1, 1), "testemunhas": []}

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(acba_repository, "get_connection", mock_conn)
    monkeypatch.setattr(AcbaRepository, "get_by_id", lambda self, rid: detail)

    updated = AcbaRepository().update(1, {"processo_numero": "P1", "testemunhas": []})
    assert updated["id"] == 1
    assert any("DELETE FROM acba_testemunhas" in q for q, _ in cursor.executes)


def test_update_acba_not_found(monkeypatch):
    cursor = FakeCursor(fetchone_results=[None])

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(acba_repository, "get_connection", mock_conn)
    assert AcbaRepository().update(99, {"processo_numero": "P1"}) is None


def test_delete_and_mark_pdf(monkeypatch):
    executed = []
    monkeypatch.setattr(acba_repository, "execute_query", lambda q, p=None: executed.append((q, p)))
    repo = AcbaRepository()
    repo.delete(1)
    repo.mark_pdf_gerado(1, user_id=2)
    assert len(executed) == 2
