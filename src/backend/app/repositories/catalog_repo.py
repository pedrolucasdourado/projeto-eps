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


# --- Delegados ---


def list_delegados(
    q: str | None = None,
    delegacia_id: int | None = None,
    unidade_id: int | None = None,
) -> list[dict]:
    like = _like(q)
    params: dict[str, Any] = {}
    where = ["1=1"]
    if delegacia_id is not None:
        where.append("d.delegacia_id = %(delegacia_id)s")
        params["delegacia_id"] = delegacia_id
    if unidade_id is not None:
        where.append("d.unidade_id = %(unidade_id)s")
        params["unidade_id"] = unidade_id
    if like:
        where.append(
            "(d.nome ILIKE %(like)s OR COALESCE(d.matricula,'') ILIKE %(like)s)"
        )
        params["like"] = like
    sql = f"""
        SELECT d.id, d.nome, d.matricula, d.delegacia_id, d.unidade_id, d.ativo, d.created_at,
               dl.nome AS delegacia_nome,
               u.nome AS unidade_nome
        FROM delegados d
        LEFT JOIN delegacias dl ON dl.id = d.delegacia_id
        LEFT JOIN unidades_responsaveis u ON u.id = d.unidade_id
        WHERE {' AND '.join(where)}
        ORDER BY d.nome
    """
    return fetch_all(sql, params)


def get_delegado(did: int) -> dict | None:
    return fetch_one(
        """
        SELECT d.id, d.nome, d.matricula, d.delegacia_id, d.unidade_id, d.ativo, d.created_at,
               dl.nome AS delegacia_nome,
               u.nome AS unidade_nome
        FROM delegados d
        LEFT JOIN delegacias dl ON dl.id = d.delegacia_id
        LEFT JOIN unidades_responsaveis u ON u.id = d.unidade_id
        WHERE d.id = %s
        """,
        (did,),
    )


def insert_delegado(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO delegados (nome, matricula, delegacia_id, unidade_id, ativo)
        VALUES (%(nome)s, %(matricula)s, %(delegacia_id)s, %(unidade_id)s, %(ativo)s)
        RETURNING id
        """,
        data,
    )
    assert row is not None
    return get_delegado(row["id"])  # type: ignore[return-value]


def update_delegado(did: int, data: dict[str, Any]) -> dict | None:
    row = fetch_one(
        """
        UPDATE delegados
        SET nome = %(nome)s,
            matricula = %(matricula)s,
            delegacia_id = %(delegacia_id)s,
            unidade_id = %(unidade_id)s,
            ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id
        """,
        {**data, "id": did},
    )
    if not row:
        return None
    return get_delegado(did)


def delete_delegado(did: int) -> None:
    execute_query("DELETE FROM delegados WHERE id = %s", (did,))


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


# --- Agentes (membros operacionais) ---


def list_agentes(q: str | None = None) -> list[dict]:
    like = _like(q)
    if like:
        return fetch_all(
            """
            SELECT id, nome, matricula, funcao_padrao, ativo, created_at
            FROM agentes
            WHERE nome ILIKE %(like)s OR matricula ILIKE %(like)s
            ORDER BY nome
            """,
            {"like": like},
        )
    return fetch_all(
        """
        SELECT id, nome, matricula, funcao_padrao, ativo, created_at
        FROM agentes
        ORDER BY nome
        """
    )


def get_agente(aid: int) -> dict | None:
    return fetch_one(
        """
        SELECT id, nome, matricula, funcao_padrao, ativo, created_at
        FROM agentes
        WHERE id = %s
        """,
        (aid,),
    )


def insert_agente(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO agentes (nome, matricula, funcao_padrao, ativo)
        VALUES (%(nome)s, %(matricula)s, %(funcao_padrao)s, %(ativo)s)
        RETURNING id, nome, matricula, funcao_padrao, ativo, created_at
        """,
        data,
    )
    assert row is not None
    return row


def update_agente(aid: int, data: dict[str, Any]) -> dict | None:
    return fetch_one(
        """
        UPDATE agentes
        SET nome = %(nome)s,
            matricula = %(matricula)s,
            funcao_padrao = %(funcao_padrao)s,
            ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id, nome, matricula, funcao_padrao, ativo, created_at
        """,
        {**data, "id": aid},
    )


def delete_agente(aid: int) -> None:
    execute_query("DELETE FROM agentes WHERE id = %s", (aid,))


# --- Equipes operacionais ---


_EQUIPE_SELECT = """
    SELECT e.id, e.numero, e.nome, e.ativo, e.created_at,
           e.delegado_id, e.escrivao_id,
           d.nome AS delegado_nome,
           d.matricula AS delegado_matricula,
           es.nome AS escrivao_nome,
           COALESCE((
               SELECT COUNT(*) FROM equipe_operacional_membros em
               WHERE em.equipe_id = e.id
           ), 0)::int AS agentes_count
    FROM equipes_operacionais e
    JOIN delegados d ON d.id = e.delegado_id
    JOIN escrivaos es ON es.id = e.escrivao_id
"""


def list_equipes(q: str | None = None) -> list[dict]:
    like = _like(q)
    params: dict[str, Any] = {}
    where = ["1=1"]
    if like:
        where.append("(e.numero ILIKE %(like)s OR COALESCE(e.nome,'') ILIKE %(like)s)")
        params["like"] = like
    sql = f"""
        {_EQUIPE_SELECT}
        WHERE {' AND '.join(where)}
        ORDER BY e.numero
    """
    return fetch_all(sql, params)


def get_equipe(eid: int) -> dict | None:
    return fetch_one(
        f"""
        {_EQUIPE_SELECT}
        WHERE e.id = %s
        """,
        (eid,),
    )


def insert_equipe(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO equipes_operacionais
            (numero, nome, delegado_id, escrivao_id, ativo)
        VALUES
            (%(numero)s, %(nome)s, %(delegado_id)s, %(escrivao_id)s, %(ativo)s)
        RETURNING id
        """,
        data,
    )
    assert row is not None
    full = get_equipe(row["id"])
    assert full is not None
    return full


def update_equipe(eid: int, data: dict[str, Any]) -> dict | None:
    row = fetch_one(
        """
        UPDATE equipes_operacionais
        SET numero = %(numero)s,
            nome = %(nome)s,
            delegado_id = %(delegado_id)s,
            escrivao_id = %(escrivao_id)s,
            ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id
        """,
        {**data, "id": eid},
    )
    if not row:
        return None
    return get_equipe(eid)


def delete_equipe(eid: int) -> None:
    execute_query("DELETE FROM equipes_operacionais WHERE id = %s", (eid,))


def list_agentes_da_equipe(eid: int) -> list[dict]:
    return fetch_all(
        """
        SELECT a.id, a.nome, a.matricula, a.funcao_padrao, a.ativo, a.created_at
        FROM equipe_operacional_membros em
        JOIN agentes a ON a.id = em.agente_id
        WHERE em.equipe_id = %s
        ORDER BY a.nome
        """,
        (eid,),
    )


def set_agentes_da_equipe(eid: int, agente_ids: list[int]) -> None:
    execute_query("DELETE FROM equipe_operacional_membros WHERE equipe_id = %s", (eid,))
    seen: set[int] = set()
    for aid in agente_ids:
        if aid in seen:
            continue
        seen.add(aid)
        execute_query(
            """
            INSERT INTO equipe_operacional_membros (equipe_id, agente_id)
            VALUES (%s, %s)
            ON CONFLICT (equipe_id, agente_id) DO NOTHING
            """,
            (eid, aid),
        )


def list_acbas_da_equipe(eid: int) -> list[dict]:
    return fetch_all(
        """
        SELECT a.id, a.numero_auto, a.data_lavratura, a.alvo_busca,
               dl.nome AS delegacia_nome,
               d.nome AS delegado_nome
        FROM acba_records a
        LEFT JOIN delegacias dl ON dl.id = a.delegacia_id
        LEFT JOIN equipes_operacionais eq ON eq.id = a.equipe_id
        LEFT JOIN delegados d ON d.id = eq.delegado_id
        WHERE a.equipe_id = %s
        ORDER BY a.data_lavratura DESC, a.id DESC
        """,
        (eid,),
    )
