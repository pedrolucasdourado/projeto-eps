"""Rotas REST para materiais apreendidos vinculados a um ACBA.

Endpoint base: /api/acba/{acba_id}/materiais
"""

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)

from pydantic import BaseModel, Field

from app.repositories import catalog_repo, materiais_repository as repo
from app.routers.auth import get_authenticated_user
from app.schemas import UserPublic
from app.schemas.materiais import (
    DescribeResponse,
    IaRunRead,
    MaterialCreate,
    MaterialRead,
    MaterialUpdate,
)
from app.services.acba_service import AcbaService
from app.services.gemini_vision_service import descrever_material
from app.services.materiais_service import MaterialService


class RevisarBody(BaseModel):
    descricao: str = Field(min_length=1)


def _tipos_ativos_para_ia() -> list[dict]:
    return [t for t in catalog_repo.list_tipos_material() if t.get("ativo")]


router = APIRouter()

acba_service = AcbaService()
material_service = MaterialService()


@router.post(
    "/ia/descrever-material",
    response_model=DescribeResponse,
)
async def descrever_anonimo(
    imagens: list[UploadFile] = File(default=[]),
    instrucoes_extra: str | None = Form(default=None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> dict[str, Any]:
    """Versão sem material persistido: usada durante a criação do ACBA,
    quando os materiais ainda só existem no rascunho do front. Recebe imagens,
    chama o Gemini Vision e devolve a descrição. Nada é salvo no banco."""
    if not imagens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie ao menos uma imagem.",
        )
    blobs: list[bytes] = []
    mimes: list[str] = []
    for up in imagens:
        content = await up.read()
        if not content:
            continue
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Imagem '{up.filename}' excede 20 MB.",
            )
        blobs.append(content)
        mimes.append(up.content_type or "image/jpeg")
    if not blobs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma imagem válida recebida.",
        )
    try:
        result = descrever_material(
            blobs,
            mime_types=mimes,
            instrucoes_extra=instrucoes_extra,
            tipos_disponiveis=_tipos_ativos_para_ia(),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao chamar o Gemini Vision: {exc}",
        ) from exc
    return {
        "descricao": result.descricao,
        "revisado": False,
        "cache_hit": False,
        "modelo": result.modelo,
        "prompt_versao": result.prompt_versao,
        "tipo_id_sugerido": result.tipo_id_sugerido,
        "tipo_nome_sugerido": result.tipo_nome_sugerido,
    }


def _ensure_acba_read(acba_id: int, user: UserPublic) -> None:
    """404/403 conforme RBAC e escopo de equipe; equivale a leitura do ACBA."""
    acba_service.get_by_id(acba_id, user=user)


def _ensure_acba_write(acba_id: int, user: UserPublic) -> None:
    """Mesma regra que a edição do auto principal (PDF, escopo, papel)."""
    acba_service.assert_can_write_materiais(acba_id, user=user)


@router.get("/{acba_id}/materiais", response_model=list[MaterialRead])
def list_materiais(
    acba_id: int,
    tipo_id: int | None = Query(default=None, ge=1),
    categoria_docx: str | None = Query(default=None, pattern="^(informatica|geral)$"),
    user: UserPublic = Depends(get_authenticated_user),
) -> list[dict[str, Any]]:
    _ensure_acba_read(acba_id, user)
    return material_service.list_by_acba(
        acba_id, tipo_id=tipo_id, categoria_docx=categoria_docx
    )


@router.post(
    "/{acba_id}/materiais",
    response_model=MaterialRead,
    status_code=status.HTTP_201_CREATED,
)
def create_material(
    acba_id: int,
    payload: MaterialCreate,
    user: UserPublic = Depends(get_authenticated_user),
) -> dict[str, Any]:
    _ensure_acba_write(acba_id, user)
    return material_service.create(acba_id, payload)


@router.get("/{acba_id}/materiais/{material_id}", response_model=MaterialRead)
def get_material(
    acba_id: int,
    material_id: int,
    user: UserPublic = Depends(get_authenticated_user),
) -> dict[str, Any]:
    _ensure_acba_read(acba_id, user)
    mat = material_service.get(material_id)
    if mat["acba_id"] != acba_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material não pertence ao ACBA informado.",
        )
    return mat


@router.put("/{acba_id}/materiais/{material_id}", response_model=MaterialRead)
def update_material(
    acba_id: int,
    material_id: int,
    payload: MaterialUpdate,
    user: UserPublic = Depends(get_authenticated_user),
) -> dict[str, Any]:
    _ensure_acba_write(acba_id, user)
    mat = material_service.get(material_id)
    if mat["acba_id"] != acba_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material não pertence ao ACBA informado.",
        )
    return material_service.update(material_id, payload)


@router.delete(
    "/{acba_id}/materiais/{material_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_material(
    acba_id: int,
    material_id: int,
    user: UserPublic = Depends(get_authenticated_user),
) -> Response:
    _ensure_acba_write(acba_id, user)
    mat = material_service.get(material_id)
    if mat["acba_id"] != acba_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material não pertence ao ACBA informado.",
        )
    material_service.delete(material_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{acba_id}/materiais/{material_id}/descrever",
    response_model=DescribeResponse,
)
async def descrever(
    acba_id: int,
    material_id: int,
    imagens: list[UploadFile] = File(default=[]),
    instrucoes_extra: str | None = Form(default=None),
    forcar: bool = Form(default=False),
    user: UserPublic = Depends(get_authenticated_user),
) -> dict[str, Any]:
    """Recebe 1+ imagens em multipart, manda ao Gemini Vision e devolve a descrição.

    As imagens não são persistidas; só passam pelo backend em memória. O texto bruto
    da IA é salvo em `descricao_ia_raw` e a `descricao` do material é
    sobrescrita se ainda não tiver sido revisada por um humano.
    """
    _ensure_acba_write(acba_id, user)
    mat = material_service.get(material_id)
    if mat["acba_id"] != acba_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material não pertence ao ACBA informado.",
        )
    if not imagens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie ao menos uma imagem.",
        )

    blobs: list[bytes] = []
    mimes: list[str] = []
    for up in imagens:
        content = await up.read()
        if not content:
            continue
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Imagem '{up.filename}' excede 20 MB.",
            )
        blobs.append(content)
        mimes.append(up.content_type or "image/jpeg")

    if not blobs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma imagem válida recebida.",
        )

    try:
        result = descrever_material(
            blobs,
            mime_types=mimes,
            instrucoes_extra=instrucoes_extra,
            tipos_disponiveis=_tipos_ativos_para_ia(),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao chamar o Gemini Vision: {exc}",
        ) from exc

    cache_hit = False
    if not forcar:
        existing = repo.find_ia_run(material_id, result.request_hash)
        if existing:
            cache_hit = True
            result.descricao = existing["resposta"]

    repo.insert_ia_run(
        material_id=material_id,
        modelo=result.modelo,
        prompt_versao=result.prompt_versao,
        request_hash=result.request_hash,
        resposta=result.descricao,
        custo_tokens=result.custo_tokens,
    )
    repo.set_descricao_ia(material_id, result.descricao)
    return {
        "descricao": result.descricao,
        "revisado": False,
        "cache_hit": cache_hit,
        "modelo": result.modelo,
        "prompt_versao": result.prompt_versao,
        "tipo_id_sugerido": result.tipo_id_sugerido,
        "tipo_nome_sugerido": result.tipo_nome_sugerido,
    }


@router.post(
    "/{acba_id}/materiais/{material_id}/revisar",
    response_model=MaterialRead,
)
def revisar(
    acba_id: int,
    material_id: int,
    payload: RevisarBody,
    user: UserPublic = Depends(get_authenticated_user),
) -> dict[str, Any]:
    """Marca a descrição como revisada pelo operador (`revisado=TRUE`)."""
    _ensure_acba_write(acba_id, user)
    mat = material_service.get(material_id)
    if mat["acba_id"] != acba_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material não pertence ao ACBA informado.",
        )
    return material_service.marcar_revisado(material_id, payload.descricao.strip())


@router.get(
    "/{acba_id}/materiais/{material_id}/ia-runs",
    response_model=list[IaRunRead],
)
def ia_runs(
    acba_id: int,
    material_id: int,
    user: UserPublic = Depends(get_authenticated_user),
) -> list[dict[str, Any]]:
    _ensure_acba_read(acba_id, user)
    mat = material_service.get(material_id)
    if mat["acba_id"] != acba_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material não pertence ao ACBA informado.",
        )
    return repo.list_ia_runs(material_id)
