from typing import Any

from psycopg2.extras import RealDictCursor

from app.db import execute_query, fetch_all, fetch_one, get_connection
from app.repositories import materiais_repository


_ACBA_JOIN_BLOCK = """
    FROM acba_records a
    JOIN processos pr ON pr.numero = a.processo_numero
    JOIN unidades_responsaveis u ON u.id = a.unidade_id
    JOIN delegacias d ON d.id = a.delegacia_id
    JOIN cidades c ON c.id = a.cidade_id
    JOIN ufs uf ON uf.id = c.uf_id
    JOIN tipos_procedimento tp ON tp.id = a.tipo_procedimento_id
    JOIN equipes_operacionais eq ON eq.id = a.equipe_id
    JOIN delegados dl ON dl.id = eq.delegado_id
    JOIN escrivaos es ON es.id = eq.escrivao_id
"""

_LIST_ALL_ACBA_SQL = """
    SELECT
        a.id,
        a.processo_numero,
        a.protocolo_numero,
        a.data_lavratura,
        a.alvo_busca,
        a.created_at,
        a.pdf_gerado_at,
        d.nome AS delegacia_nome,
        dl.nome AS delegado_nome,
        eq.numero AS equipe_numero,
        eq.nome AS equipe_nome,
        COALESCE((
            SELECT COUNT(*)::int FROM acba_materiais m
            WHERE m.acba_id = a.id AND m.revisado = FALSE
        ), 0) AS materiais_pendentes_revisao
    FROM acba_records a
    JOIN processos pr ON pr.numero = a.processo_numero
    JOIN unidades_responsaveis u ON u.id = a.unidade_id
    JOIN delegacias d ON d.id = a.delegacia_id
    JOIN cidades c ON c.id = a.cidade_id
    JOIN ufs uf ON uf.id = c.uf_id
    JOIN tipos_procedimento tp ON tp.id = a.tipo_procedimento_id
    JOIN equipes_operacionais eq ON eq.id = a.equipe_id
    JOIN delegados dl ON dl.id = eq.delegado_id
    JOIN escrivaos es ON es.id = eq.escrivao_id
    WHERE (%(tipo_material_id)s IS NULL OR EXISTS (
        SELECT 1 FROM acba_materiais m
        WHERE m.acba_id = a.id AND m.tipo_id = %(tipo_material_id)s
    ))
    AND (NOT %(filter_equipes)s OR a.equipe_id = ANY(%(equipe_ids)s))
    AND (%(temporal_agente_id)s IS NULL OR EXISTS (
        SELECT 1 FROM equipe_operacional_vinculos v
        WHERE v.agente_id = %(temporal_agente_id)s
          AND v.equipe_id = a.equipe_id
          AND a.data_lavratura >= v.data_inicio
          AND (v.data_fim IS NULL OR a.data_lavratura <= v.data_fim)
    ))
    ORDER BY a.created_at DESC
"""


_INSERT_ACBA_SQL = """
    INSERT INTO acba_records (
        processo_numero, protocolo_numero,
        unidade_id, delegacia_id, cidade_id,
        data_lavratura, hora_lavratura,
        tipo_procedimento_id,
        procedimento_numero, fundamento_legal, endereco_busca, alvo_busca,
        nome_vara_criminal, nome_juiz,
        assinatura_responsavel, observacoes,
        arrombamento_245_2, arrombamento_245_2_obs,
        forca_coisas_245_3, forca_coisas_245_3_obs,
        morador_ausente_245_4, morador_ausente_245_4_obs,
        morador_nome, morador_cpf, morador_rg,
        morador_filiacao, morador_telefone,
        equipe_id, created_by_user_id
    ) VALUES (
        %(processo_numero)s, %(protocolo_numero)s,
        %(unidade_id)s, %(delegacia_id)s, %(cidade_id)s,
        %(data_lavratura)s, %(hora_lavratura)s,
        %(tipo_procedimento_id)s,
        %(procedimento_numero)s, %(fundamento_legal)s, %(endereco_busca)s, %(alvo_busca)s,
        %(nome_vara_criminal)s, %(nome_juiz)s,
        %(assinatura_responsavel)s, %(observacoes)s,
        %(arrombamento_245_2)s, %(arrombamento_245_2_obs)s,
        %(forca_coisas_245_3)s, %(forca_coisas_245_3_obs)s,
        %(morador_ausente_245_4)s, %(morador_ausente_245_4_obs)s,
        %(morador_nome)s, %(morador_cpf)s, %(morador_rg)s,
        %(morador_filiacao)s, %(morador_telefone)s,
        %(equipe_id)s, %(created_by_user_id)s
    )
    RETURNING id
"""


_INSERT_TESTEMUNHA_SQL = """
    INSERT INTO acba_testemunhas
        (acba_id, nome, cpf, rg, filiacao, endereco,
         cidade, telefone, tipo, ordem)
    VALUES (
        %(acba_id)s, %(nome)s, %(cpf)s, %(rg)s,
        %(filiacao)s, %(endereco)s,
        %(cidade)s, %(telefone)s, %(tipo)s, %(ordem)s
    )
    RETURNING id
"""


_INSERT_TESTEMUNHA_ARROMBAMENTO_SQL = """
    INSERT INTO acba_testemunhas_arrombamento (testemunha_id, observacoes)
    VALUES (%(testemunha_id)s, %(observacoes)s)
"""


def _insert_testemunhas_with_cursor(
    cur: Any, acba_id: int, testemunhas: list[dict[str, Any]]
) -> None:
    """Insere super-classe + parcial exclusiva em uma única transação.

    `testemunhas` é a lista já validada pelo schema. Para testemunhas gerais
    grava `cidade` e `telefone` (nullable); para testemunhas de arrombamento
    grava `arrombamento.observacoes` na sub-classe.
    """
    for ordem, raw in enumerate(testemunhas):
        tipo = raw.get("tipo", "geral")
        is_arrombamento = tipo == "arrombamento"
        cur.execute(
            _INSERT_TESTEMUNHA_SQL,
            {
                "acba_id": acba_id,
                "nome": raw["nome"],
                "cpf": raw["cpf"],
                "rg": raw["rg"],
                "filiacao": raw["filiacao"],
                "endereco": raw["endereco"],
                "cidade": None if is_arrombamento else raw.get("cidade") or None,
                "telefone": None if is_arrombamento else raw.get("telefone") or None,
                "tipo": tipo,
                "ordem": ordem,
            },
        )
        new = cur.fetchone()
        if new is None:
            raise RuntimeError("Falha ao inserir testemunha.")
        if is_arrombamento:
            extras = raw.get("arrombamento") or {}
            cur.execute(
                _INSERT_TESTEMUNHA_ARROMBAMENTO_SQL,
                {
                    "testemunha_id": int(new["id"]),
                    "observacoes": str(extras.get("observacoes", "") or ""),
                },
            )


def _list_testemunhas(acba_id: int) -> list[dict[str, Any]]:
    """Lista as testemunhas do ACBA já com a especialização (LEFT JOIN)."""
    rows = fetch_all(
        """
        SELECT t.id, t.nome, t.cpf, t.rg, t.filiacao, t.endereco,
               t.cidade, t.telefone, t.tipo, t.ordem,
               ta.observacoes AS arrombamento_observacoes
        FROM acba_testemunhas t
        LEFT JOIN acba_testemunhas_arrombamento ta
            ON ta.testemunha_id = t.id
        WHERE t.acba_id = %s
        ORDER BY t.ordem, t.id
        """,
        (acba_id,),
    )
    out: list[dict[str, Any]] = []
    for r in rows:
        item: dict[str, Any] = {
            "id": r["id"],
            "tipo": r["tipo"],
            "nome": r["nome"],
            "cpf": r["cpf"],
            "rg": r["rg"],
            "filiacao": r["filiacao"],
            "endereco": r["endereco"],
            "cidade": r["cidade"],
            "telefone": r["telefone"],
            "ordem": r["ordem"],
        }
        if r["tipo"] == "arrombamento":
            item["arrombamento"] = {
                "observacoes": r["arrombamento_observacoes"] or "",
            }
        out.append(item)
    return out


class AcbaRepository:
    def create(
        self,
        row: dict[str, Any],
        materiais: list[dict[str, Any]],
        created_by_user_id: int,
    ) -> dict:
        """Insere ACBA + testemunhas + materiais em uma única transação.

        `materiais` é uma lista de payloads já validados (formato igual ao
        aceito por `materiais_repository.insert_material_with_cursor`).
        `row['testemunhas']` é a lista já validada pelo schema (dicts com
        `tipo` e, quando aplicável, `qualificacao`)."""
        testemunhas = row.pop("testemunhas", []) or []
        params = {**row, "created_by_user_id": created_by_user_id}
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(_INSERT_ACBA_SQL, params)
                fetched = cur.fetchone()
                if fetched is None:
                    raise RuntimeError("Falha ao inserir ACBA.")
                new_id = int(fetched["id"])
                _insert_testemunhas_with_cursor(cur, new_id, testemunhas)
                for mat in materiais:
                    materiais_repository.insert_material_with_cursor(
                        cur, new_id, mat
                    )
        detail = self.get_by_id(new_id)
        assert detail is not None
        return detail

    def list_all(
        self,
        tipo_material_id: int | None = None,
        equipe_ids: list[int] | None = None,
        temporal_agente_id: int | None = None,
    ) -> list[dict]:
        """Lista ACBAs com filtros opcionais.

        ``equipe_ids`` é o escopo do usuário:
          * ``None`` — sem restrição (delegado);
          * lista vazia — sem acesso a nenhuma equipe (retorna vazio rapidamente);
          * lista com IDs — restringe pelos IDs informados (escrivão/agente).

        ``temporal_agente_id`` (apenas para o papel agente) restringe o
        retorno aos ACBAs cuja ``data_lavratura`` cai dentro de algum dos
        períodos em que o agente esteve vinculado à equipe do ACBA. Sem
        esse filtro, um agente que pertence a duas equipes diferentes em
        momentos distintos veria registros de fora dos seus períodos.
        """
        if equipe_ids is not None and len(equipe_ids) == 0:
            return []
        params: dict[str, Any] = {
            "tipo_material_id": tipo_material_id,
            "filter_equipes": equipe_ids is not None,
            "equipe_ids": list(equipe_ids) if equipe_ids is not None else [],
            "temporal_agente_id": temporal_agente_id,
        }
        return fetch_all(_LIST_ALL_ACBA_SQL, params)

    def get_by_id(self, record_id: int) -> dict | None:
        row = fetch_one(
            """
            SELECT
                a.*,
                u.nome AS unidade_nome,
                d.nome AS delegacia_nome,
                c.nome AS cidade_nome,
                uf.sigla AS uf_sigla,
                uf.nome AS uf_nome,
                tp.nome AS tipo_procedimento_nome,
                pr.descricao AS processo_descricao,
                eq.numero AS equipe_numero,
                eq.nome AS equipe_nome,
                eq.delegado_id AS delegado_id,
                eq.escrivao_id AS escrivao_id,
                dl.nome AS delegado_nome,
                dl.matricula AS delegado_matricula,
                es.nome AS escrivao_nome
            """
            + _ACBA_JOIN_BLOCK
            + "\n            WHERE a.id = %s",
            (record_id,),
        )
        if not row:
            return None
        # Snapshot histórico: lista os agentes que estavam na equipe na
        # data de lavratura do ACBA, considerando os períodos de vínculo
        # (não os membros vigentes hoje).
        agentes = fetch_all(
            """
            SELECT a.id, a.nome, a.matricula, a.funcao_padrao
            FROM equipe_operacional_vinculos v
            JOIN agentes a ON a.id = v.agente_id
            WHERE v.equipe_id = %s
              AND %s >= v.data_inicio
              AND (v.data_fim IS NULL OR %s <= v.data_fim)
            ORDER BY a.nome
            """,
            (row["equipe_id"], row["data_lavratura"], row["data_lavratura"]),
        )
        row["agentes_equipe"] = agentes
        row["testemunhas"] = _list_testemunhas(record_id)
        row["materiais"] = materiais_repository.list_by_acba(record_id)
        row["materiais_pendentes_revisao"] = (
            materiais_repository.count_pendentes_revisao(record_id)
        )
        return row

    def update(self, record_id: int, row: dict[str, Any]) -> dict | None:
        testemunhas = row.pop("testemunhas", []) or []
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE acba_records SET
                        processo_numero = %(processo_numero)s,
                        protocolo_numero = %(protocolo_numero)s,
                        unidade_id = %(unidade_id)s,
                        delegacia_id = %(delegacia_id)s,
                        cidade_id = %(cidade_id)s,
                        data_lavratura = %(data_lavratura)s,
                        hora_lavratura = %(hora_lavratura)s,
                        tipo_procedimento_id = %(tipo_procedimento_id)s,
                        procedimento_numero = %(procedimento_numero)s,
                        fundamento_legal = %(fundamento_legal)s,
                        endereco_busca = %(endereco_busca)s,
                        alvo_busca = %(alvo_busca)s,
                        nome_vara_criminal = %(nome_vara_criminal)s,
                        nome_juiz = %(nome_juiz)s,
                        assinatura_responsavel = %(assinatura_responsavel)s,
                        observacoes = %(observacoes)s,
                        arrombamento_245_2 = %(arrombamento_245_2)s,
                        arrombamento_245_2_obs = %(arrombamento_245_2_obs)s,
                        forca_coisas_245_3 = %(forca_coisas_245_3)s,
                        forca_coisas_245_3_obs = %(forca_coisas_245_3_obs)s,
                        morador_ausente_245_4 = %(morador_ausente_245_4)s,
                        morador_ausente_245_4_obs = %(morador_ausente_245_4_obs)s,
                        morador_nome = %(morador_nome)s,
                        morador_cpf = %(morador_cpf)s,
                        morador_rg = %(morador_rg)s,
                        morador_filiacao = %(morador_filiacao)s,
                        morador_telefone = %(morador_telefone)s,
                        equipe_id = %(equipe_id)s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %(record_id)s
                    RETURNING id
                    """,
                    {**row, "record_id": record_id},
                )
                updated = cur.fetchone()
                if not updated:
                    return None
                # Substitui todas as testemunhas ( remove a
                # qualificação de arrombamento associada).
                cur.execute(
                    "DELETE FROM acba_testemunhas WHERE acba_id = %s",
                    (record_id,),
                )
                _insert_testemunhas_with_cursor(cur, record_id, testemunhas)
        return self.get_by_id(record_id)

    def delete(self, record_id: int) -> None:
        execute_query("DELETE FROM acba_records WHERE id = %s", (record_id,))

    def mark_pdf_gerado(self, record_id: int, user_id: int) -> None:
        """Marca o ACBA como tendo PDF gerado (ou atualiza a marcação)."""
        execute_query(
            """
            UPDATE acba_records
            SET pdf_gerado_at = CURRENT_TIMESTAMP,
                pdf_gerado_por_user_id = %s
            WHERE id = %s
            """,
            (user_id, record_id),
        )
