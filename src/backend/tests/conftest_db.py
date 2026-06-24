"""Fixture de PostgreSQL para testes de integração com banco real."""

from __future__ import annotations

import glob
import os
from pathlib import Path

import psycopg2
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _database_url() -> str:
    return os.environ.get("DATABASE_URL", "")


def postgres_available() -> bool:
    url = _database_url()
    if not url or "dummy" in url:
        return False
    try:
        conn = psycopg2.connect(url)
        conn.close()
        return True
    except Exception:
        return False


def _apply_migrations() -> None:
    url = _database_url()
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()
    sql_files = sorted(
        glob.glob(str(REPO_ROOT / "database" / "flyway" / "sql" / "V*.sql")),
        key=lambda p: Path(p).name,
    )
    for sql_file in sql_files:
        with open(sql_file, encoding="utf-8") as handle:
            sql = handle.read()
        try:
            cur.execute(sql)
        except psycopg2.Error as exc:
            msg = str(exc).lower()
            if "already exists" in msg or "duplicate key" in msg:
                continue
            raise RuntimeError(f"Falha ao aplicar {sql_file}: {exc}") from exc
    cur.close()
    conn.close()


@pytest.fixture(scope="session")
def postgres_db():
    if not postgres_available():
        pytest.skip("PostgreSQL indisponível (defina DATABASE_URL)")
    _apply_migrations()
    yield
