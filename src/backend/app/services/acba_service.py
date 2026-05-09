from fastapi import HTTPException, status
from psycopg2 import Error

from app.acba_schemas import AcbaCreate, AcbaDetail, AcbaListItem, AcbaUpdate
from app.repositories.acba_repository import AcbaRepository


class AcbaService:
    def __init__(self) -> None:
        self.repository = AcbaRepository()

    def create(self, payload: AcbaCreate, created_by_user_id: int) -> AcbaDetail:
        body = payload.model_dump()
        try:
            row = self.repository.create(body, created_by_user_id)
        except Exception as exc:
            if isinstance(exc, Error) and exc.pgcode == "23505":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já existe um auto com este número.",
                ) from exc
            raise
        return AcbaDetail.model_validate(row)

    def list_all(self) -> list[AcbaListItem]:
        rows = self.repository.list_all()
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
                    detail="Já existe um auto com este número.",
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
