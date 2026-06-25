from typing import Any, NoReturn

from fastapi import HTTPException, status

from app.repositories import materiais_repository as repo
from app.schemas.materiais import MaterialCreate, MaterialUpdate


class MaterialService:
    def list_by_acba(
        self,
        acba_id: int,
        tipo_id: int | None = None,
        categoria_docx: str | None = None,
    ) -> list[dict[str, Any]]:
        return repo.list_by_acba(acba_id, tipo_id=tipo_id, categoria_docx=categoria_docx)

    def get(self, material_id: int) -> dict[str, Any]:
        row = repo.get_by_id(material_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material não encontrado.",
            )
        return row

    def create(self, acba_id: int, payload: MaterialCreate) -> dict[str, Any]:
        try:
            return repo.create(acba_id, payload.model_dump())
        except Exception as exc:
            if getattr(exc, "pgcode", None):
                self._raise_pg(exc)
            raise

    def update(self, material_id: int, payload: MaterialUpdate) -> dict[str, Any]:
        self.get(material_id)  # 404 cedo
        try:
            row = repo.update(material_id, payload.model_dump())
        except Exception as exc:
            if getattr(exc, "pgcode", None):
                self._raise_pg(exc)
            raise
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material não encontrado.",
            )
        return row

    def delete(self, material_id: int) -> None:
        if not repo.delete(material_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material não encontrado.",
            )

    def marcar_revisado(
        self, material_id: int, descricao_final: str
    ) -> dict[str, Any]:
        self.get(material_id)
        if not descricao_final or not descricao_final.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A descrição revisada não pode ficar vazia.",
            )
        row = repo.marcar_revisado(material_id, descricao_final.strip())
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material não encontrado.",
            )
        return row

    def count_pendentes_revisao(self, acba_id: int) -> int:
        return repo.count_pendentes_revisao(acba_id)

    def _raise_pg(self, exc: Exception) -> NoReturn:
        code = getattr(exc, "pgcode", None)
        if code == "23503":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referência inválida (tipo de material ou ACBA inexistente).",
            ) from exc
        if code == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Já existe um material com este número de item nesta tabela "
                    "do auto. Escolha outro número ou deixe em branco para usar o próximo."
                ),
            ) from exc
        if code == "23514":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Dados de senha inconsistentes com o tipo escolhido "
                    "(verifique senha_tipo, senha_texto e senha_padrao_pontos)."
                ),
            ) from exc
        raise exc
