"""Repositório de usuários e vínculos com cadastros (delegado/escrivao/agente)."""

from typing import Any

from psycopg2.extras import RealDictCursor

from app.db import fetch_all, fetch_one, get_connection


_USER_SELECT_LIST = """
    SELECT u.id, u.email, u.full_name, u.role, u.ativo, u.created_at,
           d.id  AS delegado_id,
           es.id AS escrivao_id,
           ag.id AS agente_id
    FROM users u
    LEFT JOIN delegados d  ON d.user_id  = u.id
    LEFT JOIN escrivaos es ON es.user_id = u.id
    LEFT JOIN agentes   ag ON ag.user_id = u.id
"""


def list_users(role: str | None = None, q: str | None = None) -> list[dict]:
    where = ["1=1"]
    params: dict[str, Any] = {}
    if role:
        where.append("u.role = %(role)s")
        params["role"] = role
    if q:
        where.append(
            "(u.email ILIKE %(like)s OR COALESCE(u.full_name,'') ILIKE %(like)s)"
        )
        params["like"] = f"%{q.strip()}%"
    sql = f"""
        {_USER_SELECT_LIST}
        WHERE {' AND '.join(where)}
        ORDER BY u.created_at DESC, u.id DESC
    """
    return fetch_all(sql, params)


def get_user(user_id: int) -> dict | None:
    return fetch_one(
        f"{_USER_SELECT_LIST} WHERE u.id = %s",
        (user_id,),
    )


def get_user_by_email(email: str) -> dict | None:
    return fetch_one(
        f"{_USER_SELECT_LIST} WHERE LOWER(u.email) = LOWER(%s)",
        (email.strip(),),
    )


def insert_user(
    *,
    email: str,
    password_hash: str,
    full_name: str,
    role: str,
    ativo: bool,
) -> int:
    """Insere um usuário e retorna o id gerado.

    Não vincula a cadastro — o serviço faz isso em uma transação só, por
    isso este método usa um cursor próprio.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO users (email, password_hash, full_name, role, ativo)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (email.strip().lower(), password_hash, full_name, role, ativo),
            )
            row = cur.fetchone()
            assert row is not None
            return int(row["id"])


def update_user(
    user_id: int,
    *,
    full_name: str | None,
    password_hash: str | None,
    ativo: bool | None,
) -> dict | None:
    """Atualização parcial. Usa COALESCE para preservar valores omitidos."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE users SET
                    full_name      = COALESCE(%s, full_name),
                    password_hash  = COALESCE(%s, password_hash),
                    ativo          = COALESCE(%s, ativo)
                WHERE id = %s
                RETURNING id
                """,
                (full_name, password_hash, ativo, user_id),
            )
            row = cur.fetchone()
            if not row:
                return None
    return get_user(user_id)


def delete_user(user_id: int) -> None:
    """Exclui o usuário (cadastros vinculados ficam com user_id NULL)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))


# --- Vínculos com cadastros operacionais -----------------------------------

_CADASTRO_LINK_SQL = {
    "delegado": "UPDATE delegados SET user_id = %s WHERE id = %s",
    "escrivao": "UPDATE escrivaos SET user_id = %s WHERE id = %s",
    "agente": "UPDATE agentes SET user_id = %s WHERE id = %s",
}

_CADASTRO_EXISTS_SQL = {
    "delegado": "SELECT id, user_id FROM delegados WHERE id = %s",
    "escrivao": "SELECT id, user_id FROM escrivaos WHERE id = %s",
    "agente": "SELECT id, user_id FROM agentes WHERE id = %s",
}

_CADASTRO_OWNER_SQL = {
    "delegado": "SELECT user_id FROM delegados WHERE id = %s",
    "escrivao": "SELECT user_id FROM escrivaos WHERE id = %s",
    "agente": "SELECT user_id FROM agentes WHERE id = %s",
}

_UNLINK_USER_SQL = (
    "UPDATE delegados SET user_id = NULL WHERE user_id = %s",
    "UPDATE escrivaos SET user_id = NULL WHERE user_id = %s",
    "UPDATE agentes SET user_id = NULL WHERE user_id = %s",
)


def link_user_to_cadastro(role: str, cadastro_id: int, user_id: int | None) -> None:
    """Atualiza ``user_id`` na tabela de cadastro do papel correspondente.

    Passa-se ``user_id=None`` para desvincular. Usa UPDATE direto; UNIQUE no
    cadastro garante 1↔1.
    """
    sql = _CADASTRO_LINK_SQL.get(role)
    if sql is None:
        raise ValueError(f"Papel sem tabela de cadastro: {role}")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, cadastro_id))


def cadastro_existe_e_livre(role: str, cadastro_id: int) -> bool:
    """Confere se o cadastro existe e ainda não está ligado a outro usuário."""
    sql = _CADASTRO_EXISTS_SQL.get(role)
    if sql is None:
        return False
    row = fetch_one(sql, (cadastro_id,))
    if not row:
        return False
    return row["user_id"] is None


def cadastro_dono_user_id(role: str, cadastro_id: int) -> int | None:
    sql = _CADASTRO_OWNER_SQL.get(role)
    if sql is None:
        return None
    row = fetch_one(sql, (cadastro_id,))
    return None if not row else row["user_id"]


def desvincular_qualquer(user_id: int) -> None:
    """Garante que o usuário não está mais ligado a nenhum cadastro."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            for sql in _UNLINK_USER_SQL:
                cur.execute(sql, (user_id,))
