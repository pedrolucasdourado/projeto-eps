"""Helpers de autorização baseados em papel (RBAC) e escopo por equipe.

Convenções:

* ``administrador``  — gerencia usuários e cadastros, mas é proibido de
                       acessar/operar ACBA (HTTP 403 em qualquer rota /api/acba).
* ``delegado``       — leitura/edição de TODOS os ACBA, mesmo após geração do PDF.
* ``escrivao``       — leitura/edição apenas dos ACBA das equipes em que é
                       escrivão titular; edição é bloqueada quando o ACBA já
                       teve PDF gerado.
* ``agente``         — apenas leitura/busca dos ACBA das equipes em que é
                       (ou foi) membro, restrito ao(s) período(s) em que o
                       vínculo estava ativo (ver V12__vinculos_equipe_temporais).
                       Não cria, não edita, não exclui.

Escopo de equipe:
``acba_equipe_scope`` retorna a lista de ``equipe_id`` que o usuário pode
enxergar (``None`` = sem restrição). Para o agente, a lista inclui TODAS
as equipes em que ele já esteve — passadas e atuais — porque o filtro
fino por *data do ACBA* dentro de cada período é aplicado no repositório
via ``acba_temporal_agente_id`` (ver ``acba_repository.list_all``).
"""

from typing import Iterable

from fastapi import HTTPException, status

from app.db import fetch_all
from app.schemas import UserPublic


def assert_can_access_acba(user: UserPublic) -> None:
    """Aborta com 403 se o papel não pode operar no módulo ACBA."""
    if user.role == "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Administradores não acessam ACBA. Faça login com um usuário "
                "delegado, escrivão ou agente."
            ),
        )


def assert_role(user: UserPublic, allowed: Iterable[str]) -> None:
    if user.role not in set(allowed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para esta operação.",
        )


def assert_can_create_acba(user: UserPublic) -> None:
    """Apenas delegado e escrivão criam ACBA."""
    assert_can_access_acba(user)
    if user.role not in ("delegado", "escrivao"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agentes não podem criar ACBA.",
        )


def assert_can_delete_acba(user: UserPublic) -> None:
    """Apenas delegado pode excluir."""
    assert_can_access_acba(user)
    if user.role != "delegado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o delegado pode excluir um ACBA.",
        )


def acba_equipe_scope(user: UserPublic) -> list[int] | None:
    """Lista de IDs de equipes que o usuário pode enxergar.

    Retorna ``None`` quando não há restrição (delegado).
    Lista vazia significa "sem acesso a nenhuma equipe" — o serviço deve
    devolver lista vazia ou 404 conforme o caso.
    """
    if user.role == "delegado":
        return None
    if user.role == "administrador":
        return []
    if user.role == "escrivao" and user.escrivao_id:
        rows = fetch_all(
            "SELECT id FROM equipes_operacionais WHERE escrivao_id = %s",
            (user.escrivao_id,),
        )
        return [int(r["id"]) for r in rows]
    if user.role == "agente" and user.agente_id:
        # Inclui equipes em que o agente já passou. O recorte por período
        # — só ver ACBAs lavrados durante o vínculo — é aplicado depois,
        # na query do repositório, via acba_temporal_agente_id.
        rows = fetch_all(
            """
            SELECT DISTINCT equipe_id AS id
            FROM equipe_operacional_vinculos
            WHERE agente_id = %s
            """,
            (user.agente_id,),
        )
        return [int(r["id"]) for r in rows]
    # Usuário operacional sem vínculo: sem acesso a nenhuma equipe.
    return []


def acba_temporal_agente_id(user: UserPublic) -> int | None:
    """Quando o usuário é agente, devolve o ``agente_id`` que o repositório
    deve usar para filtrar ACBAs por período de vínculo.

    Para os demais papéis devolve ``None`` (sem filtro temporal): o delegado
    enxerga tudo, e o escrivão enxerga tudo da(s) equipe(s) em que ele é
    titular — não há, hoje, conceito de "ex-escrivão titular com período".
    """
    if user.role == "agente" and user.agente_id:
        return user.agente_id
    return None


def acba_visivel_para(
    user: UserPublic, equipe_id: int, data_lavratura
) -> bool:
    """Indica se o agente pode ver UM ACBA específico considerando o período.

    Usado pelo serviço para esconder (404) ACBAs que ficam fora dos
    períodos do agente, mesmo sendo da equipe certa. Para os demais
    papéis a função sempre retorna ``True`` — o controle de acesso a
    nível de equipe já é suficiente.
    """
    if user.role != "agente" or not user.agente_id:
        return True
    rows = fetch_all(
        """
        SELECT 1
        FROM equipe_operacional_vinculos
        WHERE agente_id = %s
          AND equipe_id = %s
          AND %s >= data_inicio
          AND (data_fim IS NULL OR %s <= data_fim)
        LIMIT 1
        """,
        (user.agente_id, equipe_id, data_lavratura, data_lavratura),
    )
    return bool(rows)


def assert_team_scope_contains(
    user: UserPublic, equipe_id: int, *, action: str = "acessar"
) -> None:
    """Aborta com 403 se a equipe está fora do escopo do usuário."""
    scope = acba_equipe_scope(user)
    if scope is None:
        return
    if equipe_id not in set(scope):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Você não pode {action} ACBAs desta equipe.",
        )


def assert_can_edit_after_pdf(user: UserPublic, pdf_gerado_at) -> None:
    """Bloqueia o escrivão de editar após o PDF ter sido gerado.

    O delegado segue podendo editar (não há bloqueio). Agente não chega
    aqui — é barrado antes em ``assert_can_update_acba``.
    """
    if not pdf_gerado_at:
        return
    if user.role == "escrivao":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Este ACBA já teve o PDF gerado. O escrivão não pode mais "
                "editá-lo — solicite ao delegado responsável."
            ),
        )


def assert_can_update_acba(user: UserPublic, equipe_id: int, pdf_gerado_at) -> None:
    """Composição das regras de edição: papel + escopo + estado do PDF."""
    assert_can_access_acba(user)
    if user.role == "agente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agentes não podem editar ACBA.",
        )
    assert_team_scope_contains(user, equipe_id, action="editar")
    assert_can_edit_after_pdf(user, pdf_gerado_at)
