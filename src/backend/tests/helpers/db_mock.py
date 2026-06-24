"""Helpers para simular conexões PostgreSQL nos testes."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from psycopg2 import Error as PsycopgError


class PgError(PsycopgError):
    """Erro PostgreSQL simulado para testes (pgcode mutável)."""

    def __init__(self, pgcode: str | None = None) -> None:
        super().__init__(pgcode or "pg")
        self._pgcode = pgcode

    @property
    def pgcode(self) -> str | None:
        return self._pgcode


class FakeCursor:
    def __init__(
        self,
        *,
        fetchone_results: list[Any] | None = None,
        fetchall_results: list[Any] | None = None,
        rowcount: int = 0,
    ) -> None:
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])
        self.rowcount = rowcount
        self.executes: list[tuple[str, Any]] = []

    def execute(self, query: str, params: Any = None) -> None:
        self.executes.append((query, params))

    def fetchone(self) -> Any:
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def fetchall(self) -> list[Any]:
        return self.fetchall_results

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *args: Any) -> None:
        return None


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self, cursor_factory: Any = None) -> FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        return None


@contextmanager
def fake_connection(cursor: FakeCursor) -> Iterator[FakeConnection]:
    conn = FakeConnection(cursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
