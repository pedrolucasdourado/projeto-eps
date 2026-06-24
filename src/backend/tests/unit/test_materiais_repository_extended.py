from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from app.repositories import materiais_repository as repo
from tests.helpers.db_mock import FakeConnection, FakeCursor


pytestmark = pytest.mark.unit

NOW = datetime(2026, 6, 1, tzinfo=timezone.utc)


def _db_row(**overrides):
    base = {
        "id": 1,
        "acba_id": 10,
        "tipo_id": 1,
        "tipo_nome": "Celular",
        "categoria_docx": "informatica",
        "item_num": 1,
        "descricao": "Smartphone",
        "descricao_ia_raw": None,
        "revisado": False,
        "acondicionamento": None,
        "localizacao": "Mesa",
        "observacao": None,
        "ordem": 0,
        "senha_tipo": "texto",
        "senha_texto": "1234",
        "senha_padrao_pontos": None,
        "senha_observacao": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return base


def test_insert_material_with_cursor_informatica():
    cursor = FakeCursor(
        fetchone_results=[
            {"tabela_documento": "informatica"},
            {"next_num": 2},
            {"id": 5},
        ]
    )
    new_id = repo.insert_material_with_cursor(
        cursor,
        10,
        {
            "tipo_id": 1,
            "descricao": "Notebook",
            "localizacao": "Sala",
            "informatica": {"senha_tipo": "texto", "senha_texto": "abc"},
        },
    )
    assert new_id == 5
    assert len(cursor.executes) == 4


def test_insert_material_with_cursor_geral():
    cursor = FakeCursor(
        fetchone_results=[
            {"tabela_documento": "geral"},
            {"id": 7},
        ]
    )
    new_id = repo.insert_material_with_cursor(
        cursor,
        10,
        {"tipo_id": 2, "descricao": "Documento", "item_num": 3},
    )
    assert new_id == 7


def test_tabela_documento_missing_raises():
    cursor = FakeCursor(fetchone_results=[None])
    with pytest.raises(ValueError, match="não encontrado"):
        repo._tabela_documento_do_tipo(cursor, 99)


def test_create_material(monkeypatch):
    cursor = FakeCursor(
        fetchone_results=[
            {"tabela_documento": "geral"},
            {"next_num": 1},
            {"id": 8},
        ]
    )

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(repo, "get_connection", mock_conn)
    monkeypatch.setattr(repo, "get_by_id", lambda mid: _db_row(id=mid, categoria_docx="geral"))
    created = repo.create(10, {"tipo_id": 1, "descricao": "Item"})
    assert created["id"] == 8


def test_update_material_informatica(monkeypatch):
    cursor = FakeCursor(
        fetchone_results=[
            {"acba_id": 10, "categoria_docx": "geral", "item_num": 1},
            {"tabela_documento": "informatica"},
            {"next_num": 1},
        ]
    )

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(repo, "get_connection", mock_conn)
    monkeypatch.setattr(repo, "get_by_id", lambda mid: _db_row())
    updated = repo.update(
        1,
        {
            "tipo_id": 1,
            "descricao": "Atualizado",
            "informatica": {"senha_tipo": "padrao", "senha_padrao_pontos": [1, 2, 3]},
        },
    )
    assert updated["descricao"] == "Smartphone"


def test_update_material_remove_informatica(monkeypatch):
    cursor = FakeCursor(
        fetchone_results=[
            {"acba_id": 10, "categoria_docx": "informatica", "item_num": 1},
            {"tabela_documento": "geral"},
            {"next_num": 1},
        ]
    )

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(repo, "get_connection", mock_conn)
    monkeypatch.setattr(
        repo,
        "get_by_id",
        lambda mid: _db_row(categoria_docx="geral", senha_tipo=None),
    )
    updated = repo.update(1, {"tipo_id": 2, "descricao": "Outro"})
    assert updated is not None


def test_update_material_not_found(monkeypatch):
    cursor = FakeCursor(fetchone_results=[None])

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(repo, "get_connection", mock_conn)
    assert repo.update(99, {"tipo_id": 1, "descricao": "X"}) is None


def test_set_descricao_ia_keeps_revisado(monkeypatch):
    cursor = FakeCursor(fetchone_results=[{"revisado": True, "descricao": "humana"}])

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(repo, "get_connection", mock_conn)
    monkeypatch.setattr(repo, "get_by_id", lambda mid: _db_row(revisado=True, descricao="humana"))
    result = repo.set_descricao_ia(1, "ia-text")
    assert result["revisado"] is True


def test_set_descricao_ia_not_found(monkeypatch):
    cursor = FakeCursor(fetchone_results=[None])

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(repo, "get_connection", mock_conn)
    assert repo.set_descricao_ia(99, "ia") is None


def test_marcar_revisado(monkeypatch):
    cursor = FakeCursor()

    @contextmanager
    def mock_conn():
        yield FakeConnection(cursor)

    monkeypatch.setattr(repo, "get_connection", mock_conn)
    monkeypatch.setattr(repo, "get_by_id", lambda mid: _db_row(revisado=True))
    row = repo.marcar_revisado(1, "Final")
    assert row["revisado"] is True
