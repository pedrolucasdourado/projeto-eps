from fastapi import HTTPException, status
from psycopg2 import Error

from app.acba_schemas import AcbaCreate, AcbaDetail, AcbaListItem, AcbaUpdate
from app.config import settings
from app.repositories import audit_repo
from app.repositories.acba_repository import AcbaRepository
from app.schemas import UserPublic
from app.services import authz


class AcbaService:
    def __init__(self) -> None:
        self.repository = AcbaRepository()

    # ------------------------------------------------------------------
    # Listagem / leitura
    # ------------------------------------------------------------------

    def list_all(
        self,
        *,
        user: UserPublic,
        tipo_material_id: int | None = None,
    ) -> list[AcbaListItem]:
        authz.assert_can_access_acba(user)
        scope = authz.acba_equipe_scope(user)
        rows = self.repository.list_all(
            tipo_material_id=tipo_material_id,
            equipe_ids=scope,
        )
        return [AcbaListItem.model_validate(r) for r in rows]

    def get_by_id(self, record_id: int, *, user: UserPublic) -> AcbaDetail:
        authz.assert_can_access_acba(user)
        row = self.repository.get_by_id(record_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro ACBA não encontrado.",
            )
        # Esconde o registro de equipes fora do escopo (404 em vez de 403
        # para não vazar a existência do ACBA).
        scope = authz.acba_equipe_scope(user)
        if scope is not None and int(row["equipe_id"]) not in set(scope):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro ACBA não encontrado.",
            )
        return AcbaDetail.model_validate(row)

    # ------------------------------------------------------------------
    # Mutações
    # ------------------------------------------------------------------

    def create(
        self,
        payload: AcbaCreate,
        *,
        user: UserPublic,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AcbaDetail:
        authz.assert_can_create_acba(user)
        # Escrivão só pode criar ACBA da própria equipe; delegado: qualquer
        # equipe; administrador já foi barrado em assert_can_create_acba.
        if user.role == "escrivao":
            authz.assert_team_scope_contains(
                user, payload.equipe_id, action="criar"
            )

        body = payload.model_dump()
        materiais = body.pop("materiais", []) or []
        try:
            row = self.repository.create(body, materiais, user.id)
        except Exception as exc:
            self._reraise_pg(exc, on_update=False)
            raise

        detail = AcbaDetail.model_validate(row)
        audit_repo.log_audit(
            acba_id=detail.id,
            user=user,
            acao="criado",
            snapshot_after=detail,
            ip=ip,
            user_agent=user_agent,
        )
        return detail

    def update(
        self,
        record_id: int,
        payload: AcbaUpdate,
        *,
        user: UserPublic,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AcbaDetail:
        authz.assert_can_access_acba(user)

        # Lê estado atual para validar permissões e registrar snapshot_before.
        current_row = self.repository.get_by_id(record_id)
        if not current_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro ACBA não encontrado.",
            )
        current = AcbaDetail.model_validate(current_row)

        authz.assert_can_update_acba(
            user,
            equipe_id=current.equipe_id,
            pdf_gerado_at=current.pdf_gerado_at,
        )
        # Mudança de equipe também tem que estar no escopo do escrivão.
        if user.role == "escrivao" and payload.equipe_id != current.equipe_id:
            authz.assert_team_scope_contains(
                user, payload.equipe_id, action="mover este ACBA para"
            )

        body = payload.model_dump()
        try:
            row = self.repository.update(record_id, body)
        except Exception as exc:
            self._reraise_pg(exc, on_update=True)
            raise
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro ACBA não encontrado.",
            )

        updated = AcbaDetail.model_validate(row)
        audit_repo.log_audit(
            acba_id=record_id,
            user=user,
            acao="editado",
            snapshot_before=current,
            snapshot_after=updated,
            ip=ip,
            user_agent=user_agent,
        )
        return updated

    def delete(
        self,
        record_id: int,
        *,
        user: UserPublic,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        authz.assert_can_delete_acba(user)
        current_row = self.repository.get_by_id(record_id)
        if not current_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro ACBA não encontrado.",
            )
        current = AcbaDetail.model_validate(current_row)
        # Auditoria registrada ANTES da exclusão para preservar o snapshot
        # mesmo com ON DELETE CASCADE (a entrada de auditoria também é
        # excluída — alternativa documentada no migration).
        audit_repo.log_audit(
            acba_id=record_id,
            user=user,
            acao="excluido",
            snapshot_before=current,
            ip=ip,
            user_agent=user_agent,
        )
        self.repository.delete(record_id)

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------

    def assert_pdf_pronto(self, record: AcbaDetail) -> None:
        """Levanta 409 se houver material com descrição da IA ainda não revisada."""
        if settings.acba_permitir_pdf_com_pendencia:
            return
        if record.materiais_pendentes_revisao > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"{record.materiais_pendentes_revisao} material(is) com descrição "
                    "pendente de revisão. Confirme cada item antes de exportar o PDF."
                ),
            )

    def mark_pdf_gerado(
        self,
        record_id: int,
        *,
        user: UserPublic,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Marca o PDF como gerado e registra na auditoria."""
        self.repository.mark_pdf_gerado(record_id, user.id)
        audit_repo.log_audit(
            acba_id=record_id,
            user=user,
            acao="pdf_gerado",
            ip=ip,
            user_agent=user_agent,
        )

    # ------------------------------------------------------------------
    # Materiais (delegação de autorização)
    # ------------------------------------------------------------------

    def assert_can_write_materiais(
        self, record_id: int, *, user: UserPublic
    ) -> AcbaDetail:
        """Garante que o usuário pode gravar materiais deste ACBA.

        Usa as mesmas regras de edição do auto principal: agente bloqueado,
        escrivão precisa pertencer à equipe e o ACBA não pode ter PDF gerado;
        delegado livre.
        """
        record = self.get_by_id(record_id, user=user)
        authz.assert_can_update_acba(
            user,
            equipe_id=record.equipe_id,
            pdf_gerado_at=record.pdf_gerado_at,
        )
        return record

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _reraise_pg(exc: Exception, *, on_update: bool) -> None:
        if not isinstance(exc, Error):
            return
        if exc.pgcode == "23505":
            detail = (
                "Já existe um material com este número de item nesta tabela "
                "do auto. Ajuste o número ou deixe em branco para usar o próximo."
                if (not on_update) and "item_num" in str(exc).lower()
                else "Já existe um ACBA com este número de protocolo."
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=detail
            ) from exc
        if exc.pgcode == "23503":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Processo informado não está cadastrado, "
                "ou um tipo de material informado não existe.",
            ) from exc
        if exc.pgcode == "23514":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Dados de senha de algum material são inconsistentes "
                    "(verifique senha_tipo, senha_texto e senha_padrao_pontos)."
                ),
            ) from exc


__all__ = ["AcbaService"]
