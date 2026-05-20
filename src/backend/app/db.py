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


# Bloco padrão para SELECT em users: já traz papel, flag de ativo e os ids
# do cadastro vinculado (LEFT JOIN — só um dos três fica preenchido por vez).
_USER_SELECT = """
    SELECT u.id, u.email, u.password_hash, u.full_name, u.role, u.ativo,
           u.created_at,
           d.id  AS delegado_id,
           es.id AS escrivao_id,
           ag.id AS agente_id
    FROM users u
    LEFT JOIN delegados d  ON d.user_id  = u.id
    LEFT JOIN escrivaos es ON es.user_id = u.id
    LEFT JOIN agentes   ag ON ag.user_id = u.id
"""


def fetch_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                {_USER_SELECT}
                WHERE LOWER(u.email) = LOWER(%s)
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
                f"""
                {_USER_SELECT}
                WHERE u.id = %s
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
