from contextlib import contextmanager
from typing import Any, Iterator, Sequence

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings


@contextmanager
def get_connection() -> Iterator[psycopg2.extensions.connection]:
    conn = psycopg2.connect(settings.database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, email, password_hash, full_name, created_at
                FROM users
                WHERE LOWER(email) = LOWER(%s)
                LIMIT 1
                """,
                (email.strip(),),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def fetch_user_by_id(user_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, email, full_name, created_at
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def fetch_one(query: str, params: Sequence[Any] | None = None) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            row = cur.fetchone()
            return dict(row) if row else None


def fetch_all(query: str, params: Sequence[Any] | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            return [dict(row) for row in cur.fetchall()]


def execute_query(query: str, params: Sequence[Any] | None = None) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
