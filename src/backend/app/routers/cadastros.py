from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg2 import Error as PsycopgError

from app.repositories import catalog_repo
from app.routers.auth import get_authenticated_user
from app.schemas import UserPublic
from app.schemas.catalog import (
    AutoridadeCreate,
    AutoridadeRead,
    AutoridadeUpdate,
    CidadeCreate,
    CidadeRead,
    CidadeUpdate,
    CondutorCreate,
    CondutorRead,
    CondutorUpdate,
    DelegaciaCreate,
    DelegaciaRead,
    DelegaciaUpdate,
    EscrivaoCreate,
    EscrivaoRead,
    EscrivaoUpdate,
    MembroEquipeCreate,
    MembroEquipeRead,
    MembroEquipeUpdate,
    TipoProcedimentoCreate,
    TipoProcedimentoRead,
    TipoProcedimentoUpdate,
    UFCreate,
    UFRead,
    UFUpdate,
    UnidadeCreate,
    UnidadeRead,
    UnidadeUpdate,
)

router = APIRouter()


def _merge(keys: tuple[str, ...], row: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    base = {k: row[k] for k in keys}
    base.update(patch)
    return base


def _raise_pg(exc: PsycopgError) -> None:
    code = getattr(exc, "pgcode", None)
    if code == "23503":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir: registro referenciado por outros cadastros.",
        ) from exc
    if code == "23505":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Valor duplicado.",
        ) from exc
    raise exc


# --- UF ---


@router.get("/ufs", response_model=list[UFRead])
def list_ufs(
    q: str | None = Query(None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[UFRead]:
    rows = catalog_repo.list_ufs(q)
    return [UFRead.model_validate(r) for r in rows]


@router.post("/ufs", response_model=UFRead, status_code=status.HTTP_201_CREATED)
def create_uf(body: UFCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> UFRead:
    row = catalog_repo.insert_uf(body.model_dump())
    return UFRead.model_validate(row)


@router.get("/ufs/{uf_id}", response_model=UFRead)
def get_uf(uf_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> UFRead:
    row = catalog_repo.get_uf(uf_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="UF não encontrada.")
    return UFRead.model_validate(row)


@router.put("/ufs/{uf_id}", response_model=UFRead)
def update_uf(
    uf_id: int,
    body: UFUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> UFRead:
    row = catalog_repo.get_uf(uf_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="UF não encontrada.")
    merged = _merge(("sigla", "nome", "ativo"), row, body.model_dump(exclude_unset=True))
    try:
        updated = catalog_repo.update_uf(uf_id, merged)
    except PsycopgError as exc:
        _raise_pg(exc)
    assert updated is not None
    return UFRead.model_validate(updated)


@router.delete("/ufs/{uf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uf(uf_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_uf(uf_id)
    except PsycopgError as exc:
        _raise_pg(exc)


# --- Cidades ---


@router.get("/cidades", response_model=list[CidadeRead])
def list_cidades(
    q: str | None = Query(None),
    uf_id: int | None = Query(None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[CidadeRead]:
    rows = catalog_repo.list_cidades(q=q, uf_id=uf_id)
    return [CidadeRead.model_validate(r) for r in rows]


@router.post("/cidades", response_model=CidadeRead, status_code=status.HTTP_201_CREATED)
def create_cidade(body: CidadeCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> CidadeRead:
    row = catalog_repo.insert_cidade(body.model_dump())
    return CidadeRead.model_validate(row)


@router.get("/cidades/{cidade_id}", response_model=CidadeRead)
def get_cidade(cidade_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> CidadeRead:
    row = catalog_repo.get_cidade(cidade_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cidade não encontrada.")
    return CidadeRead.model_validate(row)


@router.put("/cidades/{cidade_id}", response_model=CidadeRead)
def update_cidade(
    cidade_id: int,
    body: CidadeUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> CidadeRead:
    row = catalog_repo.get_cidade(cidade_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cidade não encontrada.")
    merged = _merge(("nome", "uf_id", "ativo"), row, body.model_dump(exclude_unset=True))
    try:
        updated = catalog_repo.update_cidade(cidade_id, merged)
    except PsycopgError as exc:
        _raise_pg(exc)
    assert updated is not None
    return CidadeRead.model_validate(updated)


@router.delete("/cidades/{cidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cidade(cidade_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_cidade(cidade_id)
    except PsycopgError as exc:
        _raise_pg(exc)


# --- Unidades ---


@router.get("/unidades", response_model=list[UnidadeRead])
def list_unidades(
    q: str | None = Query(None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[UnidadeRead]:
    rows = catalog_repo.list_unidades(q)
    return [UnidadeRead.model_validate(r) for r in rows]


@router.post("/unidades", response_model=UnidadeRead, status_code=status.HTTP_201_CREATED)
def create_unidade(body: UnidadeCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> UnidadeRead:
    row = catalog_repo.insert_unidade(body.model_dump())
    return UnidadeRead.model_validate(row)


@router.get("/unidades/{unidade_id}", response_model=UnidadeRead)
def get_unidade(unidade_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> UnidadeRead:
    row = catalog_repo.get_unidade(unidade_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")
    return UnidadeRead.model_validate(row)


@router.put("/unidades/{unidade_id}", response_model=UnidadeRead)
def update_unidade(
    unidade_id: int,
    body: UnidadeUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> UnidadeRead:
    row = catalog_repo.get_unidade(unidade_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")
    merged = _merge(("nome", "ativo"), row, body.model_dump(exclude_unset=True))
    updated = catalog_repo.update_unidade(unidade_id, merged)
    assert updated is not None
    return UnidadeRead.model_validate(updated)


@router.delete("/unidades/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unidade(unidade_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_unidade(unidade_id)
    except PsycopgError as exc:
        _raise_pg(exc)


# --- Delegacias ---


@router.get("/delegacias", response_model=list[DelegaciaRead])
def list_delegacias(
    q: str | None = Query(None),
    unidade_id: int | None = Query(None),
    cidade_id: int | None = Query(None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[DelegaciaRead]:
    rows = catalog_repo.list_delegacias(q=q, unidade_id=unidade_id, cidade_id=cidade_id)
    return [DelegaciaRead.model_validate(r) for r in rows]


@router.post("/delegacias", response_model=DelegaciaRead, status_code=status.HTTP_201_CREATED)
def create_delegacia(body: DelegaciaCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> DelegaciaRead:
    row = catalog_repo.insert_delegacia(body.model_dump())
    return DelegaciaRead.model_validate(row)


@router.get("/delegacias/{delegacia_id}", response_model=DelegaciaRead)
def get_delegacia(delegacia_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> DelegaciaRead:
    row = catalog_repo.get_delegacia(delegacia_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Delegacia não encontrada.")
    return DelegaciaRead.model_validate(row)


@router.put("/delegacias/{delegacia_id}", response_model=DelegaciaRead)
def update_delegacia(
    delegacia_id: int,
    body: DelegaciaUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> DelegaciaRead:
    row = catalog_repo.get_delegacia(delegacia_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Delegacia não encontrada.")
    merged = _merge(("nome", "unidade_id", "cidade_id", "ativo"), row, body.model_dump(exclude_unset=True))
    updated = catalog_repo.update_delegacia(delegacia_id, merged)
    assert updated is not None
    return DelegaciaRead.model_validate(updated)


@router.delete("/delegacias/{delegacia_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delegacia(delegacia_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_delegacia(delegacia_id)
    except PsycopgError as exc:
        _raise_pg(exc)


# --- Tipos procedimento ---


@router.get("/tipos-procedimento", response_model=list[TipoProcedimentoRead])
def list_tipos(q: str | None = Query(None), _user: UserPublic = Depends(get_authenticated_user)) -> list[TipoProcedimentoRead]:
    rows = catalog_repo.list_tipos_procedimento(q)
    return [TipoProcedimentoRead.model_validate(r) for r in rows]


@router.post(
    "/tipos-procedimento",
    response_model=TipoProcedimentoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tipo(body: TipoProcedimentoCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> TipoProcedimentoRead:
    try:
        row = catalog_repo.insert_tipo_procedimento(body.model_dump())
    except PsycopgError as exc:
        _raise_pg(exc)
    return TipoProcedimentoRead.model_validate(row)


@router.get("/tipos-procedimento/{tipo_id}", response_model=TipoProcedimentoRead)
def get_tipo(tipo_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> TipoProcedimentoRead:
    row = catalog_repo.get_tipo_procedimento(tipo_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tipo não encontrado.")
    return TipoProcedimentoRead.model_validate(row)


@router.put("/tipos-procedimento/{tipo_id}", response_model=TipoProcedimentoRead)
def update_tipo(
    tipo_id: int,
    body: TipoProcedimentoUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> TipoProcedimentoRead:
    row = catalog_repo.get_tipo_procedimento(tipo_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tipo não encontrado.")
    merged = _merge(("nome", "ativo"), row, body.model_dump(exclude_unset=True))
    try:
        updated = catalog_repo.update_tipo_procedimento(tipo_id, merged)
    except PsycopgError as exc:
        _raise_pg(exc)
    assert updated is not None
    return TipoProcedimentoRead.model_validate(updated)


@router.delete("/tipos-procedimento/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo(tipo_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_tipo_procedimento(tipo_id)
    except PsycopgError as exc:
        _raise_pg(exc)


# --- Autoridades ---


@router.get("/autoridades", response_model=list[AutoridadeRead])
def list_autoridades(
    q: str | None = Query(None),
    delegacia_id: int | None = Query(None),
    unidade_id: int | None = Query(None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[AutoridadeRead]:
    rows = catalog_repo.list_autoridades(q=q, delegacia_id=delegacia_id, unidade_id=unidade_id)
    return [AutoridadeRead.model_validate(r) for r in rows]


@router.post("/autoridades", response_model=AutoridadeRead, status_code=status.HTTP_201_CREATED)
def create_autoridade(body: AutoridadeCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> AutoridadeRead:
    row = catalog_repo.insert_autoridade(body.model_dump())
    return AutoridadeRead.model_validate(row)


@router.get("/autoridades/{autoridade_id}", response_model=AutoridadeRead)
def get_autoridade(autoridade_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> AutoridadeRead:
    row = catalog_repo.get_autoridade(autoridade_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Autoridade não encontrada.")
    return AutoridadeRead.model_validate(row)


@router.put("/autoridades/{autoridade_id}", response_model=AutoridadeRead)
def update_autoridade(
    autoridade_id: int,
    body: AutoridadeUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> AutoridadeRead:
    row = catalog_repo.get_autoridade(autoridade_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Autoridade não encontrada.")
    merged = _merge(
        ("nome", "matricula", "delegacia_id", "unidade_id", "ativo"),
        row,
        body.model_dump(exclude_unset=True),
    )
    updated = catalog_repo.update_autoridade(autoridade_id, merged)
    assert updated is not None
    return AutoridadeRead.model_validate(updated)


@router.delete("/autoridades/{autoridade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_autoridade(autoridade_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_autoridade(autoridade_id)
    except PsycopgError as exc:
        _raise_pg(exc)


# --- Escrivãos ---


@router.get("/escrivaos", response_model=list[EscrivaoRead])
def list_escrivaos_route(
    q: str | None = Query(None),
    delegacia_id: int | None = Query(None),
    unidade_id: int | None = Query(None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[EscrivaoRead]:
    rows = catalog_repo.list_escrivaos(q=q, delegacia_id=delegacia_id, unidade_id=unidade_id)
    return [EscrivaoRead.model_validate(r) for r in rows]


@router.post("/escrivaos", response_model=EscrivaoRead, status_code=status.HTTP_201_CREATED)
def create_escrivao(body: EscrivaoCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> EscrivaoRead:
    row = catalog_repo.insert_escrivao(body.model_dump())
    return EscrivaoRead.model_validate(row)


@router.get("/escrivaos/{escrivao_id}", response_model=EscrivaoRead)
def get_escrivao_route(escrivao_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> EscrivaoRead:
    row = catalog_repo.get_escrivao(escrivao_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Escrivão não encontrado.")
    return EscrivaoRead.model_validate(row)


@router.put("/escrivaos/{escrivao_id}", response_model=EscrivaoRead)
def update_escrivao_route(
    escrivao_id: int,
    body: EscrivaoUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> EscrivaoRead:
    row = catalog_repo.get_escrivao(escrivao_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Escrivão não encontrado.")
    merged = _merge(("nome", "delegacia_id", "unidade_id", "ativo"), row, body.model_dump(exclude_unset=True))
    updated = catalog_repo.update_escrivao(escrivao_id, merged)
    assert updated is not None
    return EscrivaoRead.model_validate(updated)


@router.delete("/escrivaos/{escrivao_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_escrivao_route(escrivao_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_escrivao(escrivao_id)
    except PsycopgError as exc:
        _raise_pg(exc)


# --- Membros equipe ---


@router.get("/membros-equipe", response_model=list[MembroEquipeRead])
def list_membros(q: str | None = Query(None), _user: UserPublic = Depends(get_authenticated_user)) -> list[MembroEquipeRead]:
    rows = catalog_repo.list_membros_equipe(q)
    return [MembroEquipeRead.model_validate(r) for r in rows]


@router.post("/membros-equipe", response_model=MembroEquipeRead, status_code=status.HTTP_201_CREATED)
def create_membro(body: MembroEquipeCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> MembroEquipeRead:
    try:
        row = catalog_repo.insert_membro_equipe(body.model_dump())
    except PsycopgError as exc:
        _raise_pg(exc)
    return MembroEquipeRead.model_validate(row)


@router.get("/membros-equipe/{membro_id}", response_model=MembroEquipeRead)
def get_membro(membro_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> MembroEquipeRead:
    row = catalog_repo.get_membro_equipe(membro_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Membro não encontrado.")
    return MembroEquipeRead.model_validate(row)


@router.put("/membros-equipe/{membro_id}", response_model=MembroEquipeRead)
def update_membro(
    membro_id: int,
    body: MembroEquipeUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> MembroEquipeRead:
    row = catalog_repo.get_membro_equipe(membro_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Membro não encontrado.")
    merged = _merge(("nome", "matricula", "funcao_padrao", "ativo"), row, body.model_dump(exclude_unset=True))
    try:
        updated = catalog_repo.update_membro_equipe(membro_id, merged)
    except PsycopgError as exc:
        _raise_pg(exc)
    assert updated is not None
    return MembroEquipeRead.model_validate(updated)


@router.delete("/membros-equipe/{membro_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membro(membro_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_membro_equipe(membro_id)
    except PsycopgError as exc:
        _raise_pg(exc)


# --- Condutores ---


@router.get("/condutores", response_model=list[CondutorRead])
def list_condutores_route(q: str | None = Query(None), _user: UserPublic = Depends(get_authenticated_user)) -> list[CondutorRead]:
    rows = catalog_repo.list_condutores(q)
    return [CondutorRead.model_validate(r) for r in rows]


@router.post("/condutores", response_model=CondutorRead, status_code=status.HTTP_201_CREATED)
def create_condutor(body: CondutorCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> CondutorRead:
    row = catalog_repo.insert_condutor(body.model_dump())
    return CondutorRead.model_validate(row)


@router.get("/condutores/{condutor_id}", response_model=CondutorRead)
def get_condutor_route(condutor_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> CondutorRead:
    row = catalog_repo.get_condutor(condutor_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Condutor não encontrado.")
    return CondutorRead.model_validate(row)


@router.put("/condutores/{condutor_id}", response_model=CondutorRead)
def update_condutor_route(
    condutor_id: int,
    body: CondutorUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> CondutorRead:
    row = catalog_repo.get_condutor(condutor_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Condutor não encontrado.")
    merged = _merge(("nome", "matricula", "ativo"), row, body.model_dump(exclude_unset=True))
    updated = catalog_repo.update_condutor(condutor_id, merged)
    assert updated is not None
    return CondutorRead.model_validate(updated)


@router.delete("/condutores/{condutor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_condutor_route(condutor_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_condutor(condutor_id)
    except PsycopgError as exc:
        _raise_pg(exc)
