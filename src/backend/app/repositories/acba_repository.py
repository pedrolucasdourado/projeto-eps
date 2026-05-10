from typing import Any

from psycopg2.extras import Json, RealDictCursor

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


_INSERT_ACBA_SQL = """
    INSERT INTO acba_records (
        processo_numero, protocolo_numero,
        unidade_id, delegacia_id, cidade_id,
        data_lavratura, hora_lavratura,
        tipo_procedimento_id,
        procedimento_numero, fundamento_legal, endereco_busca, alvo_busca,
        assinatura_responsavel, observacoes,
        equipe_id, testemunhas, created_by_user_id
    ) VALUES (
        %(processo_numero)s, %(protocolo_numero)s,
        %(unidade_id)s, %(delegacia_id)s, %(cidade_id)s,
        %(data_lavratura)s, %(hora_lavratura)s,
        %(tipo_procedimento_id)s,
        %(procedimento_numero)s, %(fundamento_legal)s, %(endereco_busca)s, %(alvo_busca)s,
        %(assinatura_responsavel)s, %(observacoes)s,
        %(equipe_id)s, %(testemunhas)s, %(created_by_user_id)s
    )
    RETURNING id
"""


class AcbaRepository:
    def create(
        self,
        row: dict[str, Any],
        materiais: list[dict[str, Any]],
        created_by_user_id: int,
    ) -> dict:
        """Insere ACBA + materiais em uma única transação.

        `materiais` é uma lista de payloads já validados (formato igual ao
        aceito por `materiais_repository.insert_material_with_cursor`)."""
        params = {
            **row,
            "testemunhas": Json(row["testemunhas"]),
            "created_by_user_id": created_by_user_id,
        }
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(_INSERT_ACBA_SQL, params)
                fetched = cur.fetchone()
                if fetched is None:
                    raise RuntimeError("Falha ao inserir ACBA.")
                new_id = int(fetched["id"])
                for mat in materiais:
                    materiais_repository.insert_material_with_cursor(
                        cur, new_id, mat
                    )
        detail = self.get_by_id(new_id)
        assert detail is not None
        return detail

    def list_all(self, tipo_material_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        extra_where = ""
        if tipo_material_id is not None:
            extra_where = """
                AND EXISTS (
                    SELECT 1 FROM acba_materiais m
                    WHERE m.acba_id = a.id AND m.tipo_id = %(tipo_material_id)s
                )
            """
            params["tipo_material_id"] = tipo_material_id
        return fetch_all(
            f"""
            SELECT
                a.id,
                a.processo_numero,
                a.protocolo_numero,
                a.data_lavratura,
                a.alvo_busca,
                a.created_at,
                d.nome AS delegacia_nome,
                dl.nome AS delegado_nome,
                eq.numero AS equipe_numero,
                eq.nome AS equipe_nome,
                COALESCE((
                    SELECT COUNT(*)::int FROM acba_materiais m
                    WHERE m.acba_id = a.id AND m.revisado = FALSE
                ), 0) AS materiais_pendentes_revisao
            {_ACBA_JOIN_BLOCK}
            WHERE 1=1 {extra_where}
            ORDER BY a.created_at DESC
            """,
            params,
        )

    def get_by_id(self, record_id: int) -> dict | None:
        row = fetch_one(
            f"""
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
            {_ACBA_JOIN_BLOCK}
            WHERE a.id = %s
            """,
            (record_id,),
        )
        if not row:
            return None
        agentes = fetch_all(
            """
            SELECT a.id, a.nome, a.matricula, a.funcao_padrao
            FROM equipe_operacional_membros em
            JOIN agentes a ON a.id = em.agente_id
            WHERE em.equipe_id = %s
            ORDER BY a.nome
            """,
            (row["equipe_id"],),
        )
        row["agentes_equipe"] = agentes
        row["materiais"] = materiais_repository.list_by_acba(record_id)
        row["materiais_pendentes_revisao"] = (
            materiais_repository.count_pendentes_revisao(record_id)
        )
        return row

    def update(self, record_id: int, row: dict[str, Any]) -> dict | None:
        updated = fetch_one(
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
                assinatura_responsavel = %(assinatura_responsavel)s,
                observacoes = %(observacoes)s,
                equipe_id = %(equipe_id)s,
                testemunhas = %(testemunhas)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %(record_id)s
            RETURNING id
            """,
            {
                **row,
                "record_id": record_id,
                "testemunhas": Json(row["testemunhas"]),
            },
        )
        if not updated:
            return None
        return self.get_by_id(record_id)

    def delete(self, record_id: int) -> None:
        execute_query("DELETE FROM acba_records WHERE id = %s", (record_id,))
