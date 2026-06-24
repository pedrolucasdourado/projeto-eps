from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.acba_schemas import AcbaCreate, AcbaDetail, AcbaListItem, AcbaUpdate
from app.config import settings
from app.repositories import audit_repo
from app.routers.auth import get_authenticated_user
from app.schemas import UserPublic
from app.services import acba_docx_pdf_service, acba_html_pdf_service, authz
from app.services.acba_service import AcbaService

router = APIRouter()
service = AcbaService()


def _client_info(request: Request) -> tuple[str | None, str | None]:
    """Extrai IP e user-agent do request para a auditoria."""
    ip = (
        (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        or (request.client.host if request.client else None)
    )
    ua = request.headers.get("user-agent")
    return ip, ua


def _user_can_access_acba(
    user: UserPublic = Depends(get_authenticated_user),
) -> UserPublic:
    authz.assert_can_access_acba(user)
    return user


def _user_can_create_acba(
    user: UserPublic = Depends(get_authenticated_user),
) -> UserPublic:
    authz.assert_can_create_acba(user)
    return user


def _user_can_update_acba(
    user: UserPublic = Depends(get_authenticated_user),
) -> UserPublic:
    authz.assert_can_access_acba(user)
    if user.role == "agente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agentes não podem editar ACBA.",
        )
    return user


def _user_can_delete_acba(
    user: UserPublic = Depends(get_authenticated_user),
) -> UserPublic:
    authz.assert_can_delete_acba(user)
    return user


@router.get("/", response_model=list[AcbaListItem])
def list_records(
    tipo_material_id: int | None = Query(default=None, ge=1),
    user: UserPublic = Depends(_user_can_access_acba),
) -> list[AcbaListItem]:
    return service.list_all(user=user, tipo_material_id=tipo_material_id)


@router.post("/", response_model=AcbaDetail, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: AcbaCreate,
    request: Request,
    user: UserPublic = Depends(_user_can_create_acba),
) -> AcbaDetail:
    ip, ua = _client_info(request)
    return service.create(payload, user=user, ip=ip, user_agent=ua)


@router.get("/{record_id}/pdf")
def generate_pdf(
    record_id: int,
    request: Request,
    user: UserPublic = Depends(_user_can_access_acba),
) -> Response:
    record = service.get_by_id(record_id, user=user)
    service.assert_pdf_pronto(record)
    render_pdf = (
        acba_html_pdf_service.render_acba_pdf_bytes
        if settings.acba_pdf_renderer.strip().lower() == "html"
        else acba_docx_pdf_service.render_acba_pdf_bytes
    )
    try:
        content = render_pdf(record)
    except FileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao gerar PDF: {exc}",
        ) from exc
    # PDF gerado com sucesso: marca a flag e registra na auditoria. A partir
    # de agora o escrivão fica bloqueado de editar este ACBA (regra de negócio).
    ip, ua = _client_info(request)
    service.mark_pdf_gerado(record_id, user=user, ip=ip, user_agent=ua)
    safe_protocolo = record.protocolo_numero.replace("/", "_").replace(" ", "_")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="acba_{safe_protocolo}.pdf"'
            )
        },
    )


@router.get("/{record_id}", response_model=AcbaDetail)
def get_record(
    record_id: int,
    user: UserPublic = Depends(_user_can_access_acba),
) -> AcbaDetail:
    return service.get_by_id(record_id, user=user)


@router.put("/{record_id}", response_model=AcbaDetail)
def update_record(
    record_id: int,
    payload: AcbaUpdate,
    request: Request,
    user: UserPublic = Depends(_user_can_update_acba),
) -> AcbaDetail:
    ip, ua = _client_info(request)
    return service.update(record_id, payload, user=user, ip=ip, user_agent=ua)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    request: Request,
    user: UserPublic = Depends(_user_can_delete_acba),
) -> Response:
    ip, ua = _client_info(request)
    service.delete(record_id, user=user, ip=ip, user_agent=ua)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Auditoria --------------------------------------------------------------


@router.get("/{record_id}/auditoria")
def list_audit(
    record_id: int,
    user: UserPublic = Depends(_user_can_access_acba),
) -> list[dict]:
    """Histórico (resumido) das alterações de um ACBA.

    Mantém compatibilidade de leitura com o escopo do usuário: agente/escrivão
    só veem auditoria de ACBAs que podem ler. Administrador é barrado em
    ``get_by_id`` antes de chegar aqui.
    """
    # Reaproveita a checagem de visibilidade do detalhe (escopo por equipe,
    # 404 quando fora do escopo, 403 para admin).
    service.get_by_id(record_id, user=user)
    return audit_repo.list_for_acba(record_id)


@router.get("/{record_id}/auditoria/{audit_id}")
def get_audit_entry(
    record_id: int,
    audit_id: int,
    user: UserPublic = Depends(_user_can_access_acba),
) -> dict:
    """Devolve uma entrada completa (com snapshots before/after)."""
    service.get_by_id(record_id, user=user)
    row = audit_repo.get_entry(audit_id)
    if not row or int(row["acba_id"]) != record_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrada de auditoria não encontrada.",
        )
    return row


__all__ = ["router", "service"]
