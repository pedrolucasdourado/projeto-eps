from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.acba_schemas import AcbaCreate, AcbaDetail, AcbaListItem, AcbaUpdate
from app.routers.auth import get_authenticated_user
from app.schemas import UserPublic
from app.services.acba_docx_pdf_service import render_acba_pdf_bytes
from app.services.acba_service import AcbaService

router = APIRouter()
service = AcbaService()


@router.get("/", response_model=list[AcbaListItem])
def list_records(
    tipo_material_id: int | None = Query(default=None, ge=1),
    _: UserPublic = Depends(get_authenticated_user),
) -> list[AcbaListItem]:
    return service.list_all(tipo_material_id=tipo_material_id)


@router.post("/", response_model=AcbaDetail, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: AcbaCreate,
    user: UserPublic = Depends(get_authenticated_user),
) -> AcbaDetail:
    return service.create(payload, user.id)


@router.get("/{record_id}/pdf")
def generate_pdf(
    record_id: int,
    _: UserPublic = Depends(get_authenticated_user),
) -> Response:
    record = service.get_by_id(record_id)
    service.assert_pdf_pronto(record)
    try:
        content = render_acba_pdf_bytes(record)
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
    _: UserPublic = Depends(get_authenticated_user),
) -> AcbaDetail:
    return service.get_by_id(record_id)


@router.put("/{record_id}", response_model=AcbaDetail)
def update_record(
    record_id: int,
    payload: AcbaUpdate,
    _: UserPublic = Depends(get_authenticated_user),
) -> AcbaDetail:
    return service.update(record_id, payload)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    _: UserPublic = Depends(get_authenticated_user),
) -> Response:
    service.delete(record_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
