"""Repositório de materiais apreendidos (super-classe + sub-classe informatica).

Toda escrita que envolve super + sub é feita em **uma única transação** usando
`get_connection()`. Leitura faz LEFT JOIN com a sub-classe.
"""

from typing import Any

from psycopg2.extras import RealDictCursor

from app.db import ensure, fetch_all, fetch_one, get_connection


_MATERIAL_SELECT = """
    SELECT
        m.id, m.acba_id, m.tipo_id, m.categoria_docx, m.item_num,
        m.descricao, m.descricao_ia_raw, m.revisado,
        m.acondicionamento, m.localizacao, m.observacao,
        m.ordem, m.created_at, m.updated_at,
        t.nome AS tipo_nome,
        i.senha_tipo, i.senha_texto, i.senha_padrao_pontos, i.senha_observacao
    FROM acba_materiais m
    JOIN tipos_material t ON t.id = m.tipo_id
    LEFT JOIN acba_materiais_informatica i ON i.material_id = m.id
"""


def _row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Achata a linha de SELECT em um dict no formato esperado pela API."""
    if row.get("categoria_docx") == "informatica":
        informatica = {
            "senha_tipo": row.get("senha_tipo") or "nenhuma",
            "senha_texto": row.get("senha_texto"),
            "senha_padrao_pontos": row.get("senha_padrao_pontos"),
            "senha_observacao": row.get("senha_observacao"),
        }
    else:
        informatica = None
    return {
        "id": row["id"],
        "acba_id": row["acba_id"],
        "tipo_id": row["tipo_id"],
        "tipo_nome": row["tipo_nome"],
        "categoria_docx": row["categoria_docx"],
        "item_num": row["item_num"],
        "descricao": row["descricao"],
        "descricao_ia_raw": row.get("descricao_ia_raw"),
        "revisado": row["revisado"],
        "acondicionamento": row.get("acondicionamento"),
        "localizacao": row.get("localizacao"),
        "observacao": row.get("observacao"),
        "ordem": row["ordem"],
        "informatica": informatica,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_by_acba(
    acba_id: int,
    tipo_id: int | None = None,
    categoria_docx: str | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"acba_id": acba_id}
    where = ["m.acba_id = %(acba_id)s"]
    if tipo_id is not None:
        where.append("m.tipo_id = %(tipo_id)s")
        params["tipo_id"] = tipo_id
    if categoria_docx is not None:
        where.append("m.categoria_docx = %(categoria_docx)s")
        params["categoria_docx"] = categoria_docx
    rows = fetch_all(
        f"""
        {_MATERIAL_SELECT}
        WHERE {' AND '.join(where)}
        ORDER BY m.categoria_docx, m.item_num
        """,
        params,
    )
    return [_row_to_dict(r) for r in rows]


def get_by_id(material_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        f"""
        {_MATERIAL_SELECT}
        WHERE m.id = %s
        """,
        (material_id,),
    )
    return _row_to_dict(row) if row else None


def _next_item_num(cur: Any, acba_id: int, categoria_docx: str) -> int:
    cur.execute(
        """
        SELECT COALESCE(MAX(item_num), 0) + 1 AS next_num
        FROM acba_materiais
        WHERE acba_id = %s AND categoria_docx = %s
        """,
        (acba_id, categoria_docx),
    )
    return int(cur.fetchone()["next_num"])


def _tabela_documento_do_tipo(cur: Any, tipo_id: int) -> str:
    """Lê `tabela_documento` do catálogo de tipos. Levanta ValueError se não existir."""
    cur.execute(
        "SELECT tabela_documento FROM tipos_material WHERE id = %s",
        (tipo_id,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Tipo de material {tipo_id} não encontrado.")
    return str(row["tabela_documento"])


def insert_material_with_cursor(
    cur: Any, acba_id: int, payload: dict[str, Any]
) -> int:
    """Insere o par (acba_materiais, acba_materiais_informatica?) reutilizando
    um cursor existente. Útil para batches transacionais (criação do ACBA com
    seus materiais em uma única transação).

    A categoria do material no documento é sempre derivada do `tipos_material`
    do tipo escolhido (`tabela_documento`). O operador pode informar
    `item_num`; se vier vazio, calcula-se o próximo livre."""
    categoria_docx = _tabela_documento_do_tipo(cur, int(payload["tipo_id"]))
    item_num = payload.get("item_num")
    if not item_num:
        item_num = _next_item_num(cur, acba_id, categoria_docx)
    item_num = int(item_num)
    cur.execute(
        """
        INSERT INTO acba_materiais (
            acba_id, tipo_id, categoria_docx, item_num,
            descricao, descricao_ia_raw, revisado,
            acondicionamento, localizacao,
            observacao, ordem
        ) VALUES (
            %(acba_id)s, %(tipo_id)s, %(categoria_docx)s, %(item_num)s,
            %(descricao)s, %(descricao_ia_raw)s, %(revisado)s,
            %(acondicionamento)s, %(localizacao)s,
            %(observacao)s, %(ordem)s
        )
        RETURNING id
        """,
        {
            "acba_id": acba_id,
            "tipo_id": payload["tipo_id"],
            "categoria_docx": categoria_docx,
            "item_num": item_num,
            "descricao": payload["descricao"],
            "descricao_ia_raw": payload.get("descricao_ia_raw"),
            "revisado": bool(payload.get("revisado", False)),
            "acondicionamento": payload.get("acondicionamento"),
            "localizacao": payload.get("localizacao"),
            "observacao": payload.get("observacao"),
            "ordem": payload.get("ordem", 0),
        },
    )
    new_id = int(cur.fetchone()["id"])
    if categoria_docx == "informatica":
        inf = payload.get("informatica") or {"senha_tipo": "nenhuma"}
        cur.execute(
            """
            INSERT INTO acba_materiais_informatica (
                material_id, senha_tipo, senha_texto,
                senha_padrao_pontos, senha_observacao
            ) VALUES (
                %(material_id)s, %(senha_tipo)s, %(senha_texto)s,
                %(senha_padrao_pontos)s, %(senha_observacao)s
            )
            """,
            {
                "material_id": new_id,
                "senha_tipo": inf.get("senha_tipo", "nenhuma"),
                "senha_texto": inf.get("senha_texto"),
                "senha_padrao_pontos": inf.get("senha_padrao_pontos"),
                "senha_observacao": inf.get("senha_observacao"),
            },
        )
    return new_id


def create(acba_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Cria material (super) + informatica (sub) em uma transação."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            new_id = insert_material_with_cursor(cur, acba_id, payload)
    out = get_by_id(new_id)
    out = ensure(out)
    return out


def update(material_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Atualiza material (e sua especialização, criando/removendo conforme
    a tabela do documento associada ao tipo). A categoria é sempre derivada do
    `tabela_documento` do `tipos_material` atual; o operador pode mudar
    `item_num` manualmente."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT acba_id, categoria_docx, item_num FROM acba_materiais WHERE id = %s",
                (material_id,),
            )
            atual = cur.fetchone()
            if not atual:
                return None
            nova_categoria = _tabela_documento_do_tipo(cur, int(payload["tipo_id"]))
            categoria_mudou = atual["categoria_docx"] != nova_categoria

            informado = payload.get("item_num")
            if informado:
                item_num = int(informado)
            elif categoria_mudou:
                item_num = _next_item_num(cur, atual["acba_id"], nova_categoria)
            else:
                item_num = int(atual["item_num"])

            cur.execute(
                """
                UPDATE acba_materiais SET
                    tipo_id = %(tipo_id)s,
                    categoria_docx = %(categoria_docx)s,
                    item_num = %(item_num)s,
                    descricao = %(descricao)s,
                    acondicionamento = %(acondicionamento)s,
                    localizacao = %(localizacao)s,
                    observacao = %(observacao)s,
                    ordem = %(ordem)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %(id)s
                """,
                {
                    "id": material_id,
                    "tipo_id": payload["tipo_id"],
                    "categoria_docx": nova_categoria,
                    "item_num": item_num,
                    "descricao": payload["descricao"],
                    "acondicionamento": payload.get("acondicionamento"),
                    "localizacao": payload.get("localizacao"),
                    "observacao": payload.get("observacao"),
                    "ordem": payload.get("ordem", 0),
                },
            )

            if nova_categoria == "informatica":
                inf = payload.get("informatica") or {"senha_tipo": "nenhuma"}
                cur.execute(
                    """
                    INSERT INTO acba_materiais_informatica (
                        material_id, senha_tipo, senha_texto,
                        senha_padrao_pontos, senha_observacao
                    ) VALUES (
                        %(material_id)s, %(senha_tipo)s, %(senha_texto)s,
                        %(senha_padrao_pontos)s, %(senha_observacao)s
                    )
                    ON CONFLICT (material_id) DO UPDATE SET
                        senha_tipo = EXCLUDED.senha_tipo,
                        senha_texto = EXCLUDED.senha_texto,
                        senha_padrao_pontos = EXCLUDED.senha_padrao_pontos,
                        senha_observacao = EXCLUDED.senha_observacao
                    """,
                    {
                        "material_id": material_id,
                        "senha_tipo": inf.get("senha_tipo", "nenhuma"),
                        "senha_texto": inf.get("senha_texto"),
                        "senha_padrao_pontos": inf.get("senha_padrao_pontos"),
                        "senha_observacao": inf.get("senha_observacao"),
                    },
                )
            else:
                cur.execute(
                    "DELETE FROM acba_materiais_informatica WHERE material_id = %s",
                    (material_id,),
                )
    return get_by_id(material_id)


def delete(material_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM acba_materiais WHERE id = %s", (material_id,))
            return cur.rowcount > 0


def set_descricao_ia(
    material_id: int, descricao_ia_raw: str, descricao_atual: str | None = None
) -> dict[str, Any] | None:
    """Salva o texto bruto da IA e atualiza a `descricao` apenas se ainda não houver
    revisão humana. Marca revisado=FALSE para forçar conferência."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT revisado, descricao FROM acba_materiais WHERE id = %s",
                (material_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            nova_descricao = (
                descricao_atual
                if descricao_atual is not None
                else (descricao_ia_raw if not row["revisado"] else row["descricao"])
            )
            cur.execute(
                """
                UPDATE acba_materiais
                SET descricao = %s,
                    descricao_ia_raw = %s,
                    revisado = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (nova_descricao, descricao_ia_raw, material_id),
            )
    return get_by_id(material_id)


def marcar_revisado(material_id: int, descricao_final: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE acba_materiais
                SET descricao = %s,
                    revisado = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (descricao_final, material_id),
            )
    return get_by_id(material_id)


def count_pendentes_revisao(acba_id: int) -> int:
    row = fetch_one(
        """
        SELECT COUNT(*)::int AS c
        FROM acba_materiais
        WHERE acba_id = %s AND revisado = FALSE
        """,
        (acba_id,),
    )
    return int(row["c"]) if row else 0


def find_ia_run(material_id: int, request_hash: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, material_id, modelo, prompt_versao, request_hash, resposta,
               custo_tokens, created_at
        FROM acba_material_ia_runs
        WHERE material_id = %s AND request_hash = %s
        """,
        (material_id, request_hash),
    )


def insert_ia_run(
    material_id: int,
    modelo: str,
    prompt_versao: str,
    request_hash: str,
    resposta: str,
    custo_tokens: int | None = None,
) -> dict[str, Any]:
    row = fetch_one(
        """
        INSERT INTO acba_material_ia_runs
            (material_id, modelo, prompt_versao, request_hash, resposta, custo_tokens)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (material_id, request_hash) DO UPDATE
            SET resposta = EXCLUDED.resposta,
                custo_tokens = EXCLUDED.custo_tokens
        RETURNING id, material_id, modelo, prompt_versao, request_hash,
                  resposta, custo_tokens, created_at
        """,
        (material_id, modelo, prompt_versao, request_hash, resposta, custo_tokens),
    )
    row = ensure(row)
    return row


def list_ia_runs(material_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, material_id, modelo, prompt_versao, request_hash, resposta,
               custo_tokens, created_at
        FROM acba_material_ia_runs
        WHERE material_id = %s
        ORDER BY created_at DESC
        """,
        (material_id,),
    )
