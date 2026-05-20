"""Repositório de auditoria do ACBA.

Persiste o histórico imutável da tabela ``acba_audit_log``. Cada linha guarda
quem alterou (id, e-mail, nome, papel), o que mudou (snapshot antes/depois e
um diff calculado pela aplicação), além de IP e user-agent quando disponíveis.

O snapshot é o objeto JSON completo do ACBA (mesmo modelo que ``AcbaDetail``)
serializado em UTC ISO 8601 — assim conseguimos renderizar exatamente a
versão anterior do documento sem precisar reconstruir a partir do diff.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from app.db import fetch_all, fetch_one, get_connection


def _json_safe(value: Any) -> Any:
    """Converte valores não-serializáveis (date/time/Decimal) para string ISO."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat(timespec="seconds")
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    return value


def serialize_snapshot(data: Any) -> dict[str, Any] | None:
    """Garante que o snapshot é um dict serializável em JSON.

    Aceita pydantic models, dicts ou ``None``. Retorna ``None`` quando a
    entrada é falsy — útil ao registrar a ação ``criado`` (sem before) ou
    ``excluido`` (sem after).
    """
    if data is None:
        return None
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    if not isinstance(data, dict):
        return {"value": _json_safe(data)}
    return _json_safe(data)


# Campos do ACBA que normalmente não interessam num diff (mudam a cada
# escrita ou são derivados/redundantes). Mantemos no snapshot completo,
# mas omitimos do diff para deixar a auditoria mais legível.
_DIFF_IGNORE = {
    "updated_at",
    "created_at",
    "agentes_equipe",
    "materiais_pendentes_revisao",
    # Nomes derivados — basta auditar os IDs.
    "unidade_nome",
    "delegacia_nome",
    "cidade_nome",
    "uf_sigla",
    "uf_nome",
    "tipo_procedimento_nome",
    "processo_descricao",
    "equipe_nome",
    "equipe_numero",
    "delegado_nome",
    "delegado_matricula",
    "escrivao_nome",
}


def compute_changes(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Diff superficial entre dois snapshots.

    Retorna `{campo: {"de": valor_antes, "para": valor_depois}}` para cada
    chave em que o valor mudou. Para listas/dicts complexos compara por
    igualdade JSON; o leitor pode abrir o snapshot completo para detalhes.
    """
    before_d = before or {}
    after_d = after or {}
    changes: dict[str, dict[str, Any]] = {}
    keys = (set(before_d.keys()) | set(after_d.keys())) - _DIFF_IGNORE
    for key in keys:
        old = before_d.get(key)
        new = after_d.get(key)
        if old != new:
            changes[key] = {"de": old, "para": new}
    return changes


def log_audit(
    *,
    acba_id: int,
    user: Any,
    acao: str,
    snapshot_before: Any = None,
    snapshot_after: Any = None,
    changes: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Insere uma entrada de auditoria.

    ``user`` é um ``UserPublic`` (ou compatível). Aceitamos ``Any`` por
    conveniência de import — o módulo não depende do schema.
    """
    if acao not in ("criado", "editado", "excluido", "pdf_gerado"):
        raise ValueError(f"Ação inválida para auditoria: {acao}")

    before = serialize_snapshot(snapshot_before)
    after = serialize_snapshot(snapshot_after)
    if changes is None:
        if acao == "editado":
            changes = compute_changes(before, after)
        else:
            changes = {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO acba_audit_log (
                    acba_id, user_id, user_email, user_full_name, user_role,
                    acao, snapshot_before, snapshot_after, changes, ip, user_agent
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s
                )
                """,
                (
                    acba_id,
                    getattr(user, "id", None),
                    getattr(user, "email", "") or "",
                    getattr(user, "full_name", None),
                    getattr(user, "role", "administrador"),
                    acao,
                    json.dumps(before) if before is not None else None,
                    json.dumps(after) if after is not None else None,
                    json.dumps(changes) if changes is not None else None,
                    ip,
                    user_agent,
                ),
            )


def list_for_acba(acba_id: int) -> list[dict]:
    """Lista resumida do histórico (sem snapshots, pra payload menor)."""
    return fetch_all(
        """
        SELECT id, acba_id, user_id, user_email, user_full_name, user_role,
               acao, changed_at, ip, user_agent, changes
        FROM acba_audit_log
        WHERE acba_id = %s
        ORDER BY changed_at DESC, id DESC
        """,
        (acba_id,),
    )


def get_entry(audit_id: int) -> dict | None:
    """Entrada completa, incluindo os snapshots before/after."""
    return fetch_one(
        """
        SELECT id, acba_id, user_id, user_email, user_full_name, user_role,
               acao, changed_at, snapshot_before, snapshot_after, changes,
               ip, user_agent
        FROM acba_audit_log
        WHERE id = %s
        """,
        (audit_id,),
    )
