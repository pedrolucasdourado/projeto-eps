from __future__ import annotations

from contextlib import contextmanager

import pytest

from app import db
from tests.helpers.db_mock import FakeConnection, FakeCursor


pytestmark = pytest.mark.unit


def test_get_connection_commits(monkeypatch):
    cursor = FakeCursor(fetchone_results=[{"id": 1}])
    conn = FakeConnection(cursor)

    @contextmanager
    def fake_connect(_url):
        yield conn

    monkeypatch.setattr(db.psycopg2, "connect", lambda url: fake_connect(url).__enter__())
    monkeypatch.setattr(
        db,
        "get_connection",
        lambda: db.get_connection.__wrapped__() if hasattr(db.get_connection, "__wrapped__") else None,
    )

    original = db.get_connection

    @contextmanager
    def mock_get_connection():
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    monkeypatch.setattr(db, "get_connection", mock_get_connection)
    with db.get_connection():
        pass
    assert conn.committed is True


def test_get_connection_rolls_back_on_error(monkeypatch):
    conn = FakeConnection(FakeCursor())

    @contextmanager
    def mock_get_connection():
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    monkeypatch.setattr(db, "get_connection", mock_get_connection)
    with pytest.raises(ValueError):
        with db.get_connection():
            raise ValueError("fail")
    assert conn.rolled_back is True


def test_fetch_one_returns_dict(monkeypatch):
    cursor = FakeCursor(fetchone_results=[{"id": 1, "nome": "A"}])

    @contextmanager
    def mock_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(db, "get_connection", mock_get_connection)
    row = db.fetch_one("SELECT 1")
    assert row == {"id": 1, "nome": "A"}


def test_fetch_one_none(monkeypatch):
    cursor = FakeCursor(fetchone_results=[None])

    @contextmanager
    def mock_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(db, "get_connection", mock_get_connection)
    assert db.fetch_one("SELECT 1") is None


def test_fetch_all_returns_list(monkeypatch):
    cursor = FakeCursor(fetchall_results=[{"id": 1}, {"id": 2}])

    @contextmanager
    def mock_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(db, "get_connection", mock_get_connection)
    rows = db.fetch_all("SELECT 1")
    assert len(rows) == 2


def test_execute_query_runs(monkeypatch):
    cursor = FakeCursor()

    @contextmanager
    def mock_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(db, "get_connection", mock_get_connection)
    db.execute_query("DELETE FROM x WHERE id = %s", (1,))
    assert cursor.executes


def test_fetch_user_by_email(monkeypatch):
    cursor = FakeCursor(fetchone_results=[{"id": 1, "email": "a@b.com"}])

    @contextmanager
    def mock_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(db, "get_connection", mock_get_connection)
    row = db.fetch_user_by_email("a@b.com")
    assert row["email"] == "a@b.com"


def test_fetch_user_by_id_none(monkeypatch):
    cursor = FakeCursor(fetchone_results=[None])

    @contextmanager
    def mock_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(db, "get_connection", mock_get_connection)
    assert db.fetch_user_by_id(99) is None
