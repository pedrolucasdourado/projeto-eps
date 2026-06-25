from typing import Any

from app.db import ensure, execute_query, fetch_all, fetch_one


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
    row = ensure(row)
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
    return fetch_all(
        """
        SELECT c.id, c.nome, c.uf_id, u.sigla AS uf_sigla, u.nome AS uf_nome,
               c.ativo, c.created_at
        FROM cidades c
        JOIN ufs u ON u.id = c.uf_id
        WHERE (%(uf_id)s IS NULL OR c.uf_id = %(uf_id)s)
          AND (%(like)s IS NULL OR c.nome ILIKE %(like)s)
        ORDER BY u.sigla, c.nome
        """,
        {"uf_id": uf_id, "like": like},
    )


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
    row = ensure(row)
    full = get_cidade(row["id"])
    full = ensure(full)
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
    row = ensure(row)
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
    return fetch_all(
        """
        SELECT d.id, d.nome, d.unidade_id, d.cidade_id, d.ativo, d.created_at,
               u.nome AS unidade_nome,
               c.nome AS cidade_nome,
               uf.sigla AS uf_sigla
        FROM delegacias d
        LEFT JOIN unidades_responsaveis u ON u.id = d.unidade_id
        LEFT JOIN cidades c ON c.id = d.cidade_id
        LEFT JOIN ufs uf ON uf.id = c.uf_id
        WHERE (%(unidade_id)s IS NULL OR d.unidade_id = %(unidade_id)s)
          AND (%(cidade_id)s IS NULL OR d.cidade_id = %(cidade_id)s)
          AND (%(like)s IS NULL OR d.nome ILIKE %(like)s)
        ORDER BY d.nome
        """,
        {
            "unidade_id": unidade_id,
            "cidade_id": cidade_id,
            "like": like,
        },
    )


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
    row = ensure(row)
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
    row = ensure(row)
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
    return fetch_all(
        """
        SELECT d.id, d.nome, d.matricula, d.delegacia_id, d.unidade_id, d.ativo, d.created_at,
               dl.nome AS delegacia_nome,
               u.nome AS unidade_nome
        FROM delegados d
        LEFT JOIN delegacias dl ON dl.id = d.delegacia_id
        LEFT JOIN unidades_responsaveis u ON u.id = d.unidade_id
        WHERE (%(delegacia_id)s IS NULL OR d.delegacia_id = %(delegacia_id)s)
          AND (%(unidade_id)s IS NULL OR d.unidade_id = %(unidade_id)s)
          AND (
              %(like)s IS NULL
              OR d.nome ILIKE %(like)s
              OR COALESCE(d.matricula, '') ILIKE %(like)s
          )
        ORDER BY d.nome
        """,
        {
            "delegacia_id": delegacia_id,
            "unidade_id": unidade_id,
            "like": like,
        },
    )


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
    row = ensure(row)
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
    return fetch_all(
        """
        SELECT e.id, e.nome, e.delegacia_id, e.unidade_id, e.ativo, e.created_at,
               d.nome AS delegacia_nome,
               u.nome AS unidade_nome
        FROM escrivaos e
        LEFT JOIN delegacias d ON d.id = e.delegacia_id
        LEFT JOIN unidades_responsaveis u ON u.id = e.unidade_id
        WHERE (%(delegacia_id)s IS NULL OR e.delegacia_id = %(delegacia_id)s)
          AND (%(unidade_id)s IS NULL OR e.unidade_id = %(unidade_id)s)
          AND (%(like)s IS NULL OR e.nome ILIKE %(like)s)
        ORDER BY e.nome
        """,
        {
            "delegacia_id": delegacia_id,
            "unidade_id": unidade_id,
            "like": like,
        },
    )


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
    row = ensure(row)
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


def _agentes_atuais_resumo(equipes: list[dict[str, Any]]) -> str | None:
    if not equipes:
        return None
    return "; ".join(
        e["equipe_numero"] + (f" — {e['equipe_nome']}" if e["equipe_nome"] else "")
        for e in equipes
    )


def _enriquecer_agentes_com_equipes_atuais(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Anexa a cada agente o vetor ``equipes_atuais`` (vínculos abertos)
    e dois campos derivados úteis para a tabela:

    * ``equipe_atual_resumo`` — texto pronto para a coluna da listagem;
    * ``primeira_data_ingresso`` — a data de ingresso mais antiga ainda
      em vigor (útil quando o agente está em uma equipe só).
    """
    if not rows:
        return rows
    ids = [r["id"] for r in rows]
    vinculos = fetch_all(
        """
        SELECT v.agente_id,
               e.id    AS equipe_id,
               e.numero AS equipe_numero,
               e.nome   AS equipe_nome,
               v.data_inicio
        FROM equipe_operacional_vinculos v
        JOIN equipes_operacionais e ON e.id = v.equipe_id
        WHERE v.agente_id = ANY(%s) AND v.data_fim IS NULL
        ORDER BY v.data_inicio, e.numero
        """,
        (ids,),
    )
    by_agente: dict[int, list[dict[str, Any]]] = {}
    for v in vinculos:
        by_agente.setdefault(int(v["agente_id"]), []).append(
            {
                "equipe_id": int(v["equipe_id"]),
                "equipe_numero": v["equipe_numero"],
                "equipe_nome": v["equipe_nome"],
                "data_inicio": v["data_inicio"],
            }
        )
    for r in rows:
        equipes = by_agente.get(int(r["id"]), [])
        r["equipes_atuais"] = equipes
        r["equipe_atual_resumo"] = _agentes_atuais_resumo(equipes)
        r["primeira_data_ingresso"] = (
            equipes[0]["data_inicio"] if equipes else None
        )
    return rows


def list_agentes(q: str | None = None) -> list[dict]:
    like = _like(q)
    if like:
        rows = fetch_all(
            """
            SELECT id, nome, matricula, funcao_padrao, ativo, created_at
            FROM agentes
            WHERE nome ILIKE %(like)s OR matricula ILIKE %(like)s
            ORDER BY nome
            """,
            {"like": like},
        )
    else:
        rows = fetch_all(
            """
            SELECT id, nome, matricula, funcao_padrao, ativo, created_at
            FROM agentes
            ORDER BY nome
            """
        )
    return _enriquecer_agentes_com_equipes_atuais(rows)


def get_agente(aid: int) -> dict | None:
    row = fetch_one(
        """
        SELECT id, nome, matricula, funcao_padrao, ativo, created_at
        FROM agentes
        WHERE id = %s
        """,
        (aid,),
    )
    if row is None:
        return None
    _enriquecer_agentes_com_equipes_atuais([row])
    return row


def list_historico_equipes_do_agente(aid: int) -> list[dict]:
    """Histórico completo de vínculos do agente com equipes.

    Inclui vínculos ativos (``data_fim IS NULL``) e encerrados, ordenados
    do mais recente para o mais antigo. ``ativo`` é um booleano derivado
    para o frontend distinguir as duas categorias sem precisar olhar
    ``data_fim``.
    """
    return fetch_all(
        """
        SELECT v.id,
               v.equipe_id,
               e.numero AS equipe_numero,
               e.nome   AS equipe_nome,
               v.data_inicio,
               v.data_fim,
               v.motivo_saida,
               (v.data_fim IS NULL) AS ativo
        FROM equipe_operacional_vinculos v
        JOIN equipes_operacionais e ON e.id = v.equipe_id
        WHERE v.agente_id = %s
        ORDER BY v.data_inicio DESC, v.id DESC
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
    row = ensure(row)
    _enriquecer_agentes_com_equipes_atuais([row])
    return row


def update_agente(aid: int, data: dict[str, Any]) -> dict | None:
    row = fetch_one(
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
    if row is None:
        return None
    _enriquecer_agentes_com_equipes_atuais([row])
    return row


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
               SELECT COUNT(*) FROM equipe_operacional_vinculos v
               WHERE v.equipe_id = e.id AND v.data_fim IS NULL
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
    sql = (
        _EQUIPE_SELECT
        + "\n        WHERE "
        + " AND ".join(where)
        + "\n        ORDER BY e.numero"
    )
    return fetch_all(sql, params)


def get_equipe(eid: int) -> dict | None:
    return fetch_one(
        _EQUIPE_SELECT + "\n        WHERE e.id = %s",
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
    row = ensure(row)
    full = get_equipe(row["id"])
    full = ensure(full)
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
    """Agentes atualmente vinculados à equipe (vínculos abertos)."""
    return fetch_all(
        """
        SELECT a.id, a.nome, a.matricula, a.funcao_padrao, a.ativo, a.created_at
        FROM equipe_operacional_vinculos v
        JOIN agentes a ON a.id = v.agente_id
        WHERE v.equipe_id = %s AND v.data_fim IS NULL
        ORDER BY a.nome
        """,
        (eid,),
    )


def set_agentes_da_equipe(eid: int, agente_ids: list[int]) -> None:
    """Atualiza a composição da equipe preservando o histórico.

    Em vez de apagar e reinserir (o que perderia os períodos passados),
    aplicamos um diff entre os vínculos vigentes (``data_fim IS NULL``) e
    a lista nova:

      * agentes que saíram → fecha o vínculo aberto com ``data_fim`` hoje;
      * agentes que entraram → cria um vínculo novo com ``data_inicio`` hoje;
      * agentes que continuam → não toca.
    """
    desejados: set[int] = set()
    for aid in agente_ids:
        desejados.add(int(aid))

    rows = fetch_all(
        """
        SELECT agente_id
        FROM equipe_operacional_vinculos
        WHERE equipe_id = %s AND data_fim IS NULL
        """,
        (eid,),
    )
    atuais: set[int] = {int(r["agente_id"]) for r in rows}

    saindo = atuais - desejados
    entrando = desejados - atuais

    for aid in saindo:
        execute_query(
            """
            UPDATE equipe_operacional_vinculos
               SET data_fim = CURRENT_DATE
             WHERE equipe_id = %s AND agente_id = %s AND data_fim IS NULL
            """,
            (eid, aid),
        )

    for aid in entrando:
        execute_query(
            """
            INSERT INTO equipe_operacional_vinculos
                (equipe_id, agente_id, data_inicio)
            VALUES (%s, %s, CURRENT_DATE)
            """,
            (eid, aid),
        )


def list_acbas_da_equipe(eid: int) -> list[dict]:
    return fetch_all(
        """
        SELECT a.id, a.processo_numero, a.protocolo_numero,
               a.data_lavratura, a.alvo_busca,
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


# --- Processos ---


_PROCESSO_SELECT = """
    SELECT p.numero, p.descricao, p.ativo, p.created_at,
           COALESCE((
               SELECT COUNT(*) FROM acba_records a
               WHERE a.processo_numero = p.numero
           ), 0)::int AS acbas_count
    FROM processos p
"""


def list_processos(q: str | None = None) -> list[dict]:
    like = _like(q)
    if like:
        return fetch_all(
            _PROCESSO_SELECT
            + "\n            WHERE p.numero ILIKE %(like)s"
            + " OR COALESCE(p.descricao, '') ILIKE %(like)s"
            + "\n            ORDER BY p.numero",
            {"like": like},
        )
    return fetch_all(_PROCESSO_SELECT + "\n        ORDER BY p.numero")


def get_processo(numero: str) -> dict | None:
    return fetch_one(
        _PROCESSO_SELECT + "\n        WHERE p.numero = %s",
        (numero,),
    )


def insert_processo(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO processos (numero, descricao, ativo)
        VALUES (%(numero)s, %(descricao)s, %(ativo)s)
        RETURNING numero
        """,
        data,
    )
    row = ensure(row)
    full = get_processo(row["numero"])
    full = ensure(full)
    return full


def update_processo(numero: str, data: dict[str, Any]) -> dict | None:
    row = fetch_one(
        """
        UPDATE processos
        SET descricao = %(descricao)s,
            ativo = %(ativo)s
        WHERE numero = %(numero)s
        RETURNING numero
        """,
        {**data, "numero": numero},
    )
    if not row:
        return None
    return get_processo(numero)


def delete_processo(numero: str) -> None:
    execute_query("DELETE FROM processos WHERE numero = %s", (numero,))


# --- Tipos de material ---


def list_tipos_material(q: str | None = None) -> list[dict]:
    like = _like(q)
    if like:
        return fetch_all(
            """
            SELECT id, nome, tabela_documento, ativo, created_at
            FROM tipos_material
            WHERE nome ILIKE %(like)s
            ORDER BY nome
            """,
            {"like": like},
        )
    return fetch_all(
        """
        SELECT id, nome, tabela_documento, ativo, created_at
        FROM tipos_material
        ORDER BY nome
        """
    )


def get_tipo_material(tid: int) -> dict | None:
    return fetch_one(
        """
        SELECT id, nome, tabela_documento, ativo, created_at
        FROM tipos_material WHERE id = %s
        """,
        (tid,),
    )


def insert_tipo_material(data: dict[str, Any]) -> dict:
    row = fetch_one(
        """
        INSERT INTO tipos_material (nome, tabela_documento, ativo)
        VALUES (%(nome)s, %(tabela_documento)s, %(ativo)s)
        RETURNING id, nome, tabela_documento, ativo, created_at
        """,
        data,
    )
    row = ensure(row)
    return row


def update_tipo_material(tid: int, data: dict[str, Any]) -> dict | None:
    return fetch_one(
        """
        UPDATE tipos_material
        SET nome = %(nome)s,
            tabela_documento = %(tabela_documento)s,
            ativo = %(ativo)s
        WHERE id = %(id)s
        RETURNING id, nome, tabela_documento, ativo, created_at
        """,
        {**data, "id": tid},
    )


def delete_tipo_material(tid: int) -> None:
    execute_query("DELETE FROM tipos_material WHERE id = %s", (tid,))
