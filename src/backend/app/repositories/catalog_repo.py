from typing import Any

from app.db import execute_query, fetch_all, fetch_one


def _like(q: str | None) -> str | None:
    if q is None:
        return None
    s = q.strip()
    if not s:
        return None
    return f"%{s}%"


# --- UFs ---


def list_ufs(q: str | None = None) -> list[dict]:
    like = _like(q)
    if like:
        return fetch_all(
            """
            SELECT id, sigla, nome, ativo, created_at
            FROM ufs
            WHERE sigla ILIKE %(like)s OR nome ILIKE %(like)s
            ORDER BY sigla
            """,
            {"like": like},
        )
    return fetch_all(
        """
        SELECT id, sigla, nome, ativo, created_at
        FROM ufs
        ORDER BY sigla
        """
    )


def get_uf(uf_id: int) -> dict | None:
    return fetch_one("SELECT * FROM ufs WHERE id = %s", (uf_id,))


def insert_uf(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO ufs (sigla, nome, ativo)
        VALUES (%(sigla)s, %(nome)s, %(ativo)s)
        RETURNING id, sigla, nome, ativo, created_at
        """,
        data,
    )
    assert row is not None
    return row


def update_uf(uf_id: int, data: dict[str, Any]) -> dict | None:
    return fetch_one(
        """
        UPDATE ufs
        SET sigla = %(sigla)s, nome = %(nome)s, ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id, sigla, nome, ativo, created_at
        """,
        {**data, "id": uf_id},
    )


def delete_uf(uf_id: int) -> None:
    execute_query("DELETE FROM ufs WHERE id = %s", (uf_id,))


# --- Cidades ---


def list_cidades(q: str | None = None, uf_id: int | None = None) -> list[dict]:
    like = _like(q)
    params: dict[str, Any] = {}
    where = ["1=1"]
    if uf_id is not None:
        where.append("c.uf_id = %(uf_id)s")
        params["uf_id"] = uf_id
    if like:
        where.append("c.nome ILIKE %(like)s")
        params["like"] = like
    sql = f"""
        SELECT c.id, c.nome, c.uf_id, u.sigla AS uf_sigla, u.nome AS uf_nome,
               c.ativo, c.created_at
        FROM cidades c
        JOIN ufs u ON u.id = c.uf_id
        WHERE {' AND '.join(where)}
        ORDER BY u.sigla, c.nome
    """
    return fetch_all(sql, params)


def get_cidade(cid: int) -> dict | None:
    return fetch_one(
        """
        SELECT c.*, u.sigla AS uf_sigla, u.nome AS uf_nome
        FROM cidades c
        JOIN ufs u ON u.id = c.uf_id
        WHERE c.id = %s
        """,
        (cid,),
    )


def insert_cidade(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO cidades (nome, uf_id, ativo)
        VALUES (%(nome)s, %(uf_id)s, %(ativo)s)
        RETURNING id, nome, uf_id, ativo, created_at
        """,
        data,
    )
    assert row is not None
    full = get_cidade(row["id"])
    assert full is not None
    return full


def update_cidade(cid: int, data: dict[str, Any]) -> dict | None:
    row = fetch_one(
        """
        UPDATE cidades
        SET nome = %(nome)s, uf_id = %(uf_id)s, ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id
        """,
        {**data, "id": cid},
    )
    if not row:
        return None
    return get_cidade(cid)


def delete_cidade(cid: int) -> None:
    execute_query("DELETE FROM cidades WHERE id = %s", (cid,))


# --- Unidades ---


def list_unidades(q: str | None = None) -> list[dict]:
    like = _like(q)
    if like:
        return fetch_all(
            """
            SELECT id, nome, ativo, created_at
            FROM unidades_responsaveis
            WHERE nome ILIKE %(like)s
            ORDER BY nome
            """,
            {"like": like},
        )
    return fetch_all(
        """
        SELECT id, nome, ativo, created_at
        FROM unidades_responsaveis
        ORDER BY nome
        """
    )


def get_unidade(uid: int) -> dict | None:
    return fetch_one(
        "SELECT id, nome, ativo, created_at FROM unidades_responsaveis WHERE id = %s",
        (uid,),
    )


def insert_unidade(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO unidades_responsaveis (nome, ativo)
        VALUES (%(nome)s, %(ativo)s)
        RETURNING id, nome, ativo, created_at
        """,
        data,
    )
    assert row is not None
    return row


def update_unidade(uid: int, data: dict[str, Any]) -> dict | None:
    return fetch_one(
        """
        UPDATE unidades_responsaveis
        SET nome = %(nome)s, ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id, nome, ativo, created_at
        """,
        {**data, "id": uid},
    )


def delete_unidade(uid: int) -> None:
    execute_query("DELETE FROM unidades_responsaveis WHERE id = %s", (uid,))


# --- Delegacias ---


def list_delegacias(
    q: str | None = None,
    unidade_id: int | None = None,
    cidade_id: int | None = None,
) -> list[dict]:
    like = _like(q)
    params: dict[str, Any] = {}
    where = ["1=1"]
    if unidade_id is not None:
        where.append("d.unidade_id = %(unidade_id)s")
        params["unidade_id"] = unidade_id
    if cidade_id is not None:
        where.append("d.cidade_id = %(cidade_id)s")
        params["cidade_id"] = cidade_id
    if like:
        where.append("d.nome ILIKE %(like)s")
        params["like"] = like
    sql = f"""
        SELECT d.id, d.nome, d.unidade_id, d.cidade_id, d.ativo, d.created_at,
               u.nome AS unidade_nome,
               c.nome AS cidade_nome,
               uf.sigla AS uf_sigla
        FROM delegacias d
        LEFT JOIN unidades_responsaveis u ON u.id = d.unidade_id
        LEFT JOIN cidades c ON c.id = d.cidade_id
        LEFT JOIN ufs uf ON uf.id = c.uf_id
        WHERE {' AND '.join(where)}
        ORDER BY d.nome
    """
    return fetch_all(sql, params)


def get_delegacia(did: int) -> dict | None:
    return fetch_one(
        """
        SELECT d.id, d.nome, d.unidade_id, d.cidade_id, d.ativo, d.created_at,
               u.nome AS unidade_nome,
               c.nome AS cidade_nome,
               uf.sigla AS uf_sigla
        FROM delegacias d
        LEFT JOIN unidades_responsaveis u ON u.id = d.unidade_id
        LEFT JOIN cidades c ON c.id = d.cidade_id
        LEFT JOIN ufs uf ON uf.id = c.uf_id
        WHERE d.id = %s
        """,
        (did,),
    )


def insert_delegacia(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO delegacias (nome, unidade_id, cidade_id, ativo)
        VALUES (%(nome)s, %(unidade_id)s, %(cidade_id)s, %(ativo)s)
        RETURNING id
        """,
        data,
    )
    assert row is not None
    return get_delegacia(row["id"])  # type: ignore[return-value]


def update_delegacia(did: int, data: dict[str, Any]) -> dict | None:
    row = fetch_one(
        """
        UPDATE delegacias
        SET nome = %(nome)s,
            unidade_id = %(unidade_id)s,
            cidade_id = %(cidade_id)s,
            ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id
        """,
        {**data, "id": did},
    )
    if not row:
        return None
    return get_delegacia(did)


def delete_delegacia(did: int) -> None:
    execute_query("DELETE FROM delegacias WHERE id = %s", (did,))


# --- Tipos procedimento ---


def list_tipos_procedimento(q: str | None = None) -> list[dict]:
    like = _like(q)
    if like:
        return fetch_all(
            """
            SELECT id, nome, ativo, created_at
            FROM tipos_procedimento
            WHERE nome ILIKE %(like)s
            ORDER BY nome
            """,
            {"like": like},
        )
    return fetch_all(
        """
        SELECT id, nome, ativo, created_at
        FROM tipos_procedimento
        ORDER BY nome
        """
    )


def get_tipo_procedimento(tid: int) -> dict | None:
    return fetch_one(
        "SELECT id, nome, ativo, created_at FROM tipos_procedimento WHERE id = %s",
        (tid,),
    )


def insert_tipo_procedimento(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO tipos_procedimento (nome, ativo)
        VALUES (%(nome)s, %(ativo)s)
        RETURNING id, nome, ativo, created_at
        """,
        data,
    )
    assert row is not None
    return row


def update_tipo_procedimento(tid: int, data: dict[str, Any]) -> dict | None:
    return fetch_one(
        """
        UPDATE tipos_procedimento
        SET nome = %(nome)s, ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id, nome, ativo, created_at
        """,
        {**data, "id": tid},
    )


def delete_tipo_procedimento(tid: int) -> None:
    execute_query("DELETE FROM tipos_procedimento WHERE id = %s", (tid,))


# --- Autoridades ---


def list_autoridades(
    q: str | None = None,
    delegacia_id: int | None = None,
    unidade_id: int | None = None,
) -> list[dict]:
    like = _like(q)
    params: dict[str, Any] = {}
    where = ["1=1"]
    if delegacia_id is not None:
        where.append("a.delegacia_id = %(delegacia_id)s")
        params["delegacia_id"] = delegacia_id
    if unidade_id is not None:
        where.append("a.unidade_id = %(unidade_id)s")
        params["unidade_id"] = unidade_id
    if like:
        where.append(
            "(a.nome ILIKE %(like)s OR COALESCE(a.matricula,'') ILIKE %(like)s)"
        )
        params["like"] = like
    sql = f"""
        SELECT a.id, a.nome, a.matricula, a.delegacia_id, a.unidade_id, a.ativo, a.created_at,
               d.nome AS delegacia_nome,
               u.nome AS unidade_nome
        FROM autoridades_policiais a
        LEFT JOIN delegacias d ON d.id = a.delegacia_id
        LEFT JOIN unidades_responsaveis u ON u.id = a.unidade_id
        WHERE {' AND '.join(where)}
        ORDER BY a.nome
    """
    return fetch_all(sql, params)


def get_autoridade(aid: int) -> dict | None:
    return fetch_one(
        """
        SELECT a.id, a.nome, a.matricula, a.delegacia_id, a.unidade_id, a.ativo, a.created_at,
               d.nome AS delegacia_nome,
               u.nome AS unidade_nome
        FROM autoridades_policiais a
        LEFT JOIN delegacias d ON d.id = a.delegacia_id
        LEFT JOIN unidades_responsaveis u ON u.id = a.unidade_id
        WHERE a.id = %s
        """,
        (aid,),
    )


def insert_autoridade(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO autoridades_policiais (nome, matricula, delegacia_id, unidade_id, ativo)
        VALUES (%(nome)s, %(matricula)s, %(delegacia_id)s, %(unidade_id)s, %(ativo)s)
        RETURNING id
        """,
        data,
    )
    assert row is not None
    return get_autoridade(row["id"])  # type: ignore[return-value]


def update_autoridade(aid: int, data: dict[str, Any]) -> dict | None:
    row = fetch_one(
        """
        UPDATE autoridades_policiais
        SET nome = %(nome)s,
            matricula = %(matricula)s,
            delegacia_id = %(delegacia_id)s,
            unidade_id = %(unidade_id)s,
            ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id
        """,
        {**data, "id": aid},
    )
    if not row:
        return None
    return get_autoridade(aid)


def delete_autoridade(aid: int) -> None:
    execute_query("DELETE FROM autoridades_policiais WHERE id = %s", (aid,))


# --- Escrivãos ---


def list_escrivaos(
    q: str | None = None,
    delegacia_id: int | None = None,
    unidade_id: int | None = None,
) -> list[dict]:
    like = _like(q)
    params: dict[str, Any] = {}
    where = ["1=1"]
    if delegacia_id is not None:
        where.append("e.delegacia_id = %(delegacia_id)s")
        params["delegacia_id"] = delegacia_id
    if unidade_id is not None:
        where.append("e.unidade_id = %(unidade_id)s")
        params["unidade_id"] = unidade_id
    if like:
        where.append("e.nome ILIKE %(like)s")
        params["like"] = like
    sql = f"""
        SELECT e.id, e.nome, e.delegacia_id, e.unidade_id, e.ativo, e.created_at,
               d.nome AS delegacia_nome,
               u.nome AS unidade_nome
        FROM escrivaos e
        LEFT JOIN delegacias d ON d.id = e.delegacia_id
        LEFT JOIN unidades_responsaveis u ON u.id = e.unidade_id
        WHERE {' AND '.join(where)}
        ORDER BY e.nome
    """
    return fetch_all(sql, params)


def get_escrivao(eid: int) -> dict | None:
    return fetch_one(
        """
        SELECT e.id, e.nome, e.delegacia_id, e.unidade_id, e.ativo, e.created_at,
               d.nome AS delegacia_nome,
               u.nome AS unidade_nome
        FROM escrivaos e
        LEFT JOIN delegacias d ON d.id = e.delegacia_id
        LEFT JOIN unidades_responsaveis u ON u.id = e.unidade_id
        WHERE e.id = %s
        """,
        (eid,),
    )


def insert_escrivao(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO escrivaos (nome, delegacia_id, unidade_id, ativo)
        VALUES (%(nome)s, %(delegacia_id)s, %(unidade_id)s, %(ativo)s)
        RETURNING id
        """,
        data,
    )
    assert row is not None
    return get_escrivao(row["id"])  # type: ignore[return-value]


def update_escrivao(eid: int, data: dict[str, Any]) -> dict | None:
    row = fetch_one(
        """
        UPDATE escrivaos
        SET nome = %(nome)s,
            delegacia_id = %(delegacia_id)s,
            unidade_id = %(unidade_id)s,
            ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id
        """,
        {**data, "id": eid},
    )
    if not row:
        return None
    return get_escrivao(eid)


def delete_escrivao(eid: int) -> None:
    execute_query("DELETE FROM escrivaos WHERE id = %s", (eid,))


# --- Membros equipe ---


def list_membros_equipe(q: str | None = None) -> list[dict]:
    like = _like(q)
    if like:
        return fetch_all(
            """
            SELECT id, nome, matricula, funcao_padrao, ativo, created_at
            FROM membros_equipe_operacional
            WHERE nome ILIKE %(like)s OR matricula ILIKE %(like)s
            ORDER BY nome
            """,
            {"like": like},
        )
    return fetch_all(
        """
        SELECT id, nome, matricula, funcao_padrao, ativo, created_at
        FROM membros_equipe_operacional
        ORDER BY nome
        """
    )


def get_membro_equipe(mid: int) -> dict | None:
    return fetch_one(
        """
        SELECT id, nome, matricula, funcao_padrao, ativo, created_at
        FROM membros_equipe_operacional
        WHERE id = %s
        """,
        (mid,),
    )


def insert_membro_equipe(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO membros_equipe_operacional (nome, matricula, funcao_padrao, ativo)
        VALUES (%(nome)s, %(matricula)s, %(funcao_padrao)s, %(ativo)s)
        RETURNING id, nome, matricula, funcao_padrao, ativo, created_at
        """,
        data,
    )
    assert row is not None
    return row


def update_membro_equipe(mid: int, data: dict[str, Any]) -> dict | None:
    return fetch_one(
        """
        UPDATE membros_equipe_operacional
        SET nome = %(nome)s,
            matricula = %(matricula)s,
            funcao_padrao = %(funcao_padrao)s,
            ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id, nome, matricula, funcao_padrao, ativo, created_at
        """,
        {**data, "id": mid},
    )


def delete_membro_equipe(mid: int) -> None:
    execute_query("DELETE FROM membros_equipe_operacional WHERE id = %s", (mid,))


# --- Condutores ---


def list_condutores(q: str | None = None) -> list[dict]:
    like = _like(q)
    if like:
        return fetch_all(
            """
            SELECT id, nome, matricula, ativo, created_at
            FROM condutores_operacao
            WHERE nome ILIKE %(like)s OR COALESCE(matricula,'') ILIKE %(like)s
            ORDER BY nome
            """,
            {"like": like},
        )
    return fetch_all(
        """
        SELECT id, nome, matricula, ativo, created_at
        FROM condutores_operacao
        ORDER BY nome
        """
    )


def get_condutor(cid: int) -> dict | None:
    return fetch_one(
        """
        SELECT id, nome, matricula, ativo, created_at
        FROM condutores_operacao
        WHERE id = %s
        """,
        (cid,),
    )


def insert_condutor(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO condutores_operacao (nome, matricula, ativo)
        VALUES (%(nome)s, %(matricula)s, %(ativo)s)
        RETURNING id, nome, matricula, ativo, created_at
        """,
        data,
    )
    assert row is not None
    return row


def update_condutor(cid: int, data: dict[str, Any]) -> dict | None:
    return fetch_one(
        """
        UPDATE condutores_operacao
        SET nome = %(nome)s, matricula = %(matricula)s, ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id, nome, matricula, ativo, created_at
        """,
        {**data, "id": cid},
    )


def delete_condutor(cid: int) -> None:
    execute_query("DELETE FROM condutores_operacao WHERE id = %s", (cid,))
