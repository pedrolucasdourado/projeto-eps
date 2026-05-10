from fastapi import HTTPException, status
from psycopg2 import Error

from app.acba_schemas import AcbaCreate, AcbaDetail, AcbaListItem, AcbaUpdate
from app.config import settings
from app.repositories.acba_repository import AcbaRepository


class AcbaService:
    def __init__(self) -> None:
        self.repository = AcbaRepository()

    def create(self, payload: AcbaCreate, created_by_user_id: int) -> AcbaDetail:
        body = payload.model_dump()
        materiais = body.pop("materiais", []) or []
        try:
            row = self.repository.create(body, materiais, created_by_user_id)
        except Exception as exc:
            if isinstance(exc, Error) and exc.pgcode == "23505":
                # 23505 cobre tanto protocolo duplicado quanto item_num repetido
                # dentro de uma mesma tabela do auto.
                detail = (
                    "Já existe um material com este número de item nesta tabela "
                    "do auto. Ajuste o número ou deixe em branco para usar o próximo."
                    if "item_num" in str(exc).lower()
                    else "Já existe um ACBA com este número de protocolo."
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail=detail
                ) from exc
            if isinstance(exc, Error) and exc.pgcode == "23503":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Processo informado não está cadastrado, "
                    "ou um tipo de material informado não existe.",
                ) from exc
            if isinstance(exc, Error) and exc.pgcode == "23514":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Dados de senha de algum material são inconsistentes "
                        "(verifique senha_tipo, senha_texto e senha_padrao_pontos)."
                    ),
                ) from exc
            raise
        return AcbaDetail.model_validate(row)

    def list_all(self, tipo_material_id: int | None = None) -> list[AcbaListItem]:
        rows = self.repository.list_all(tipo_material_id=tipo_material_id)
        return [AcbaListItem.model_validate(r) for r in rows]

    def get_by_id(self, record_id: int) -> AcbaDetail:
        row = self.repository.get_by_id(record_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro ACBA não encontrado.",
            )
        return AcbaDetail.model_validate(row)

    def update(self, record_id: int, payload: AcbaUpdate) -> AcbaDetail:
        body = payload.model_dump()
        try:
            row = self.repository.update(record_id, body)
        except Exception as exc:
            if isinstance(exc, Error) and exc.pgcode == "23505":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já existe um ACBA com este número de protocolo.",
                ) from exc
            if isinstance(exc, Error) and exc.pgcode == "23503":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Processo informado não está cadastrado.",
                ) from exc
            raise
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro ACBA não encontrado.",
            )
        return AcbaDetail.model_validate(row)

    def delete(self, record_id: int) -> None:
        if not self.repository.get_by_id(record_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro ACBA não encontrado.",
            )
        self.repository.delete(record_id)

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
