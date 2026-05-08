from typing import Any

from psycopg2.extras import Json

from app.db import execute_query, fetch_all, fetch_one


class AcbaRepository:
    def create(self, row: dict[str, Any], membro_ids: list[int], created_by_user_id: int) -> dict:
        inserted = fetch_one(
            """
            INSERT INTO acba_records (
                numero_auto, unidade_id, delegacia_id, cidade_id,
                data_lavratura, hora_lavratura,
                autoridade_id, escrivao_id, tipo_procedimento_id,
                procedimento_numero, fundamento_legal, endereco_busca, alvo_busca,
                condutor_id, assinatura_responsavel, observacoes,
                testemunhas, objetos_arrecadados, created_by_user_id
            ) VALUES (
                %(numero_auto)s, %(unidade_id)s, %(delegacia_id)s, %(cidade_id)s,
                %(data_lavratura)s, %(hora_lavratura)s,
                %(autoridade_id)s, %(escrivao_id)s, %(tipo_procedimento_id)s,
                %(procedimento_numero)s, %(fundamento_legal)s, %(endereco_busca)s, %(alvo_busca)s,
                %(condutor_id)s, %(assinatura_responsavel)s, %(observacoes)s,
                %(testemunhas)s, %(objetos_arrecadados)s, %(created_by_user_id)s
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
        acba_id = inserted["id"]
        self._sync_equipe(acba_id, membro_ids)
        detail = self.get_by_id(acba_id)
        assert detail is not None
        return detail

    def _sync_equipe(self, acba_id: int, membro_ids: list[int]) -> None:
        execute_query(
            "DELETE FROM acba_equipe_membros WHERE acba_id = %s", (acba_id,)
        )
        seen: set[int] = set()
        for mid in membro_ids:
            if mid in seen:
                continue
            seen.add(mid)
            execute_query(
                """
                INSERT INTO acba_equipe_membros (acba_id, membro_id)
                VALUES (%s, %s)
                ON CONFLICT (acba_id, membro_id) DO NOTHING
                """,
                (acba_id, mid),
            )

    def list_all(self) -> list[dict]:
        return fetch_all(
            """
            SELECT
                a.id,
                a.numero_auto,
                a.data_lavratura,
                a.alvo_busca,
                a.created_at,
                d.nome AS delegacia_nome,
                ap.nome AS autoridade_nome
            FROM acba_records a
            JOIN delegacias d ON d.id = a.delegacia_id
            JOIN autoridades_policiais ap ON ap.id = a.autoridade_id
            ORDER BY a.created_at DESC
            """
        )

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
                ap.nome AS autoridade_nome,
                ap.matricula AS autoridade_matricula,
                e.nome AS escrivao_nome,
                tp.nome AS tipo_procedimento_nome,
                co.nome AS condutor_nome,
                co.matricula AS condutor_matricula
            FROM acba_records a
            JOIN unidades_responsaveis u ON u.id = a.unidade_id
            JOIN delegacias d ON d.id = a.delegacia_id
            JOIN cidades c ON c.id = a.cidade_id
            JOIN ufs uf ON uf.id = c.uf_id
            JOIN autoridades_policiais ap ON ap.id = a.autoridade_id
            JOIN escrivaos e ON e.id = a.escrivao_id
            JOIN tipos_procedimento tp ON tp.id = a.tipo_procedimento_id
            JOIN condutores_operacao co ON co.id = a.condutor_id
            WHERE a.id = %s
            """,
            (record_id,),
        )
        if not row:
            return None
        membros = fetch_all(
            """
            SELECT m.id, m.nome, m.matricula, m.funcao_padrao
            FROM acba_equipe_membros x
            JOIN membros_equipe_operacional m ON m.id = x.membro_id
            WHERE x.acba_id = %s
            ORDER BY m.nome
            """,
            (record_id,),
        )
        row["membro_ids"] = [m["id"] for m in membros]
        row["membros_equipe"] = membros
        return row

    def update(self, record_id: int, row: dict[str, Any], membro_ids: list[int]) -> dict | None:
        updated = fetch_one(
            """
            UPDATE acba_records SET
                numero_auto = %(numero_auto)s,
                unidade_id = %(unidade_id)s,
                delegacia_id = %(delegacia_id)s,
                cidade_id = %(cidade_id)s,
                data_lavratura = %(data_lavratura)s,
                hora_lavratura = %(hora_lavratura)s,
                autoridade_id = %(autoridade_id)s,
                escrivao_id = %(escrivao_id)s,
                tipo_procedimento_id = %(tipo_procedimento_id)s,
                procedimento_numero = %(procedimento_numero)s,
                fundamento_legal = %(fundamento_legal)s,
                endereco_busca = %(endereco_busca)s,
                alvo_busca = %(alvo_busca)s,
                condutor_id = %(condutor_id)s,
                assinatura_responsavel = %(assinatura_responsavel)s,
                observacoes = %(observacoes)s,
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
        self._sync_equipe(record_id, membro_ids)
        return self.get_by_id(record_id)

    def delete(self, record_id: int) -> None:
        execute_query("DELETE FROM acba_records WHERE id = %s", (record_id,))
