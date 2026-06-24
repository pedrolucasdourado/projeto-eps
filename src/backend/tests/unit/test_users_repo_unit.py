from __future__ import annotations

from contextlib import contextmanager

import pytest

from app.repositories import users_repo
from tests.helpers.db_mock import FakeCursor, fake_connection


pytestmark = pytest.mark.unit


def test_list_users_with_filters(monkeypatch):
    captured = {}

    def fake_fetch_all(query, params=None):
        captured["params"] = params
        return [{"id": 1}]

    monkeypatch.setattr(users_repo, "fetch_all", fake_fetch_all)
    users_repo.list_users(role="delegado", q="test")
    assert captured["params"]["role"] == "delegado"


def test_get_user_by_email(monkeypatch):
    monkeypatch.setattr(users_repo, "fetch_one", lambda q, p=None: {"id": 1})
    assert users_repo.get_user_by_email("a@b.com")["id"] == 1


def test_insert_user(monkeypatch):
    cursor = FakeCursor(fetchone_results=[{"id": 42}])

    @contextmanager
    def mock_conn():
        from tests.helpers.db_mock import FakeConnection
        yield FakeConnection(cursor)

    monkeypatch.setattr(users_repo, "get_connection", mock_conn)
    user_id = users_repo.insert_user(
        email="x@y.com",
        password_hash="hash",
        full_name="Nome",
        role="delegado",
        ativo=True,
    )
    assert user_id == 42


def test_update_user_not_found(monkeypatch):
    cursor = FakeCursor(fetchone_results=[None])

    @contextmanager
    def mock_conn():
        from tests.helpers.db_mock import FakeConnection
        yield FakeConnection(cursor)

    monkeypatch.setattr(users_repo, "get_connection", mock_conn)
    assert users_repo.update_user(1, full_name="N", password_hash=None, ativo=None) is None


def test_delete_user(monkeypatch):
    cursor = FakeCursor()

    @contextmanager
    def mock_conn():
        from tests.helpers.db_mock import FakeConnection
        yield FakeConnection(cursor)

    monkeypatch.setattr(users_repo, "get_connection", mock_conn)
    users_repo.delete_user(1)
    assert cursor.executes


def test_link_user_invalid_role():
    with pytest.raises(ValueError):
        users_repo.link_user_to_cadastro("invalido", 1, 1)


def test_cadastro_existe_e_livre_false(monkeypatch):
    monkeypatch.setattr(users_repo, "fetch_one", lambda q, p=None: None)
    assert users_repo.cadastro_existe_e_livre("delegado", 1) is False


def test_cadastro_existe_e_livre_true(monkeypatch):
    monkeypatch.setattr(users_repo, "fetch_one", lambda q, p=None: {"id": 1, "user_id": None})
    assert users_repo.cadastro_existe_e_livre("delegado", 1) is True


def test_cadastro_dono_user_id(monkeypatch):
    monkeypatch.setattr(users_repo, "fetch_one", lambda q, p=None: {"user_id": 7})
    assert users_repo.cadastro_dono_user_id("agente", 1) == 7


def test_desvincular_qualquer(monkeypatch):
    cursor = FakeCursor()

    @contextmanager
    def mock_conn():
        from tests.helpers.db_mock import FakeConnection
        yield FakeConnection(cursor)

    monkeypatch.setattr(users_repo, "get_connection", mock_conn)
    users_repo.desvincular_qualquer(1)
    assert len(cursor.executes) == 3
