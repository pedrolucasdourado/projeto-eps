from typing import Any

from psycopg2.extras import Json

from app.db import execute_query, fetch_all, fetch_one


_ACBA_JOIN_BLOCK = """
    FROM acba_records a
    JOIN unidades_responsaveis u ON u.id = a.unidade_id
    JOIN delegacias d ON d.id = a.delegacia_id
    JOIN cidades c ON c.id = a.cidade_id
    JOIN ufs uf ON uf.id = c.uf_id
    JOIN tipos_procedimento tp ON tp.id = a.tipo_procedimento_id
    JOIN equipes_operacionais eq ON eq.id = a.equipe_id
    JOIN delegados dl ON dl.id = eq.delegado_id
    JOIN escrivaos es ON es.id = eq.escrivao_id
"""


class AcbaRepository:
    def create(self, row: dict[str, Any], created_by_user_id: int) -> dict:
        inserted = fetch_one(
            """
            INSERT INTO acba_records (
                numero_auto, unidade_id, delegacia_id, cidade_id,
                data_lavratura, hora_lavratura,
                tipo_procedimento_id,
                procedimento_numero, fundamento_legal, endereco_busca, alvo_busca,
                assinatura_responsavel, observacoes,
                equipe_id, testemunhas, objetos_arrecadados, created_by_user_id
            ) VALUES (
                %(numero_auto)s, %(unidade_id)s, %(delegacia_id)s, %(cidade_id)s,
                %(data_lavratura)s, %(hora_lavratura)s,
                %(tipo_procedimento_id)s,
                %(procedimento_numero)s, %(fundamento_legal)s, %(endereco_busca)s, %(alvo_busca)s,
                %(assinatura_responsavel)s, %(observacoes)s,
                %(equipe_id)s, %(testemunhas)s, %(objetos_arrecadados)s, %(created_by_user_id)s
            )
            RETURNING id
            """,
            {
                **row,
                "testemunhas": Json(row["testemunhas"]),
                "objetos_arrecadados": Json(row["objetos_arrecadados"]),
                "created_by_user_id": created_by_user_id,
            },
        )
        if inserted is None:
            raise RuntimeError("Falha ao inserir ACBA.")
        detail = self.get_by_id(inserted["id"])
        assert detail is not None
        return detail

    def list_all(self) -> list[dict]:
        return fetch_all(
            f"""
            SELECT
                a.id,
                a.numero_auto,
                a.data_lavratura,
                a.alvo_busca,
                a.created_at,
                d.nome AS delegacia_nome,
                dl.nome AS delegado_nome,
                eq.numero AS equipe_numero,
                eq.nome AS equipe_nome
            {_ACBA_JOIN_BLOCK}
            ORDER BY a.created_at DESC
            """
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
        return row

    def update(self, record_id: int, row: dict[str, Any]) -> dict | None:
        updated = fetch_one(
            """
            UPDATE acba_records SET
                numero_auto = %(numero_auto)s,
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
                objetos_arrecadados = %(objetos_arrecadados)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %(record_id)s
            RETURNING id
            """,
            {
                **row,
                "record_id": record_id,
                "testemunhas": Json(row["testemunhas"]),
                "objetos_arrecadados": Json(row["objetos_arrecadados"]),
            },
        )
        if not updated:
            return None
        return self.get_by_id(record_id)

    def delete(self, record_id: int) -> None:
        execute_query("DELETE FROM acba_records WHERE id = %s", (record_id,))
