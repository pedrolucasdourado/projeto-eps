from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg2 import Error as PsycopgError

from app.repositories import catalog_repo
from app.routers.auth import get_authenticated_user
from app.schemas import UserPublic
from app.schemas.catalog import (
    AgenteCreate,
    AgenteRead,
    AgenteUpdate,
    CidadeCreate,
    CidadeRead,
    CidadeUpdate,
    DelegaciaCreate,
    DelegaciaRead,
    DelegaciaUpdate,
    DelegadoCreate,
    DelegadoRead,
    DelegadoUpdate,
    EquipeAcbaItem,
    EquipeAgentesUpdate,
    EquipeOperacionalCreate,
    EquipeOperacionalRead,
    EquipeOperacionalUpdate,
    EscrivaoCreate,
    EscrivaoRead,
    EscrivaoUpdate,
    ProcessoCreate,
    ProcessoRead,
    ProcessoUpdate,
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


# --- Delegados ---


@router.get("/delegados", response_model=list[DelegadoRead])
def list_delegados(
    q: str | None = Query(None),
    delegacia_id: int | None = Query(None),
    unidade_id: int | None = Query(None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[DelegadoRead]:
    rows = catalog_repo.list_delegados(q=q, delegacia_id=delegacia_id, unidade_id=unidade_id)
    return [DelegadoRead.model_validate(r) for r in rows]


@router.post("/delegados", response_model=DelegadoRead, status_code=status.HTTP_201_CREATED)
def create_delegado(body: DelegadoCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> DelegadoRead:
    row = catalog_repo.insert_delegado(body.model_dump())
    return DelegadoRead.model_validate(row)


@router.get("/delegados/{delegado_id}", response_model=DelegadoRead)
def get_delegado(delegado_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> DelegadoRead:
    row = catalog_repo.get_delegado(delegado_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Delegado não encontrado.")
    return DelegadoRead.model_validate(row)


@router.put("/delegados/{delegado_id}", response_model=DelegadoRead)
def update_delegado(
    delegado_id: int,
    body: DelegadoUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> DelegadoRead:
    row = catalog_repo.get_delegado(delegado_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Delegado não encontrado.")
    merged = _merge(
        ("nome", "matricula", "delegacia_id", "unidade_id", "ativo"),
        row,
        body.model_dump(exclude_unset=True),
    )
    updated = catalog_repo.update_delegado(delegado_id, merged)
    assert updated is not None
    return DelegadoRead.model_validate(updated)


@router.delete("/delegados/{delegado_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delegado(delegado_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_delegado(delegado_id)
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


# --- Agentes (cadastro de policiais operacionais) ---


@router.get("/agentes", response_model=list[AgenteRead])
def list_agentes(q: str | None = Query(None), _user: UserPublic = Depends(get_authenticated_user)) -> list[AgenteRead]:
    rows = catalog_repo.list_agentes(q)
    return [AgenteRead.model_validate(r) for r in rows]


@router.post("/agentes", response_model=AgenteRead, status_code=status.HTTP_201_CREATED)
def create_agente(body: AgenteCreate, *, _user: UserPublic = Depends(get_authenticated_user)) -> AgenteRead:
    try:
        row = catalog_repo.insert_agente(body.model_dump())
    except PsycopgError as exc:
        _raise_pg(exc)
    return AgenteRead.model_validate(row)


@router.get("/agentes/{agente_id}", response_model=AgenteRead)
def get_agente(agente_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> AgenteRead:
    row = catalog_repo.get_agente(agente_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Agente não encontrado.")
    return AgenteRead.model_validate(row)


@router.put("/agentes/{agente_id}", response_model=AgenteRead)
def update_agente(
    agente_id: int,
    body: AgenteUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> AgenteRead:
    row = catalog_repo.get_agente(agente_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Agente não encontrado.")
    merged = _merge(("nome", "matricula", "funcao_padrao", "ativo"), row, body.model_dump(exclude_unset=True))
    try:
        updated = catalog_repo.update_agente(agente_id, merged)
    except PsycopgError as exc:
        _raise_pg(exc)
    assert updated is not None
    return AgenteRead.model_validate(updated)


@router.delete("/agentes/{agente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agente(agente_id: int, *, _user: UserPublic = Depends(get_authenticated_user)) -> None:
    try:
        catalog_repo.delete_agente(agente_id)
    except PsycopgError as exc:
        _raise_pg(exc)


# --- Equipes operacionais ---


@router.get("/equipes", response_model=list[EquipeOperacionalRead])
def list_equipes(
    q: str | None = Query(None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[EquipeOperacionalRead]:
    rows = catalog_repo.list_equipes(q)
    return [EquipeOperacionalRead.model_validate(r) for r in rows]


@router.post(
    "/equipes",
    response_model=EquipeOperacionalRead,
    status_code=status.HTTP_201_CREATED,
)
def create_equipe(
    body: EquipeOperacionalCreate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> EquipeOperacionalRead:
    try:
        row = catalog_repo.insert_equipe(body.model_dump())
    except PsycopgError as exc:
        _raise_pg(exc)
    return EquipeOperacionalRead.model_validate(row)


@router.get("/equipes/{equipe_id}", response_model=EquipeOperacionalRead)
def get_equipe(
    equipe_id: int,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> EquipeOperacionalRead:
    row = catalog_repo.get_equipe(equipe_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada.")
    return EquipeOperacionalRead.model_validate(row)


@router.put("/equipes/{equipe_id}", response_model=EquipeOperacionalRead)
def update_equipe(
    equipe_id: int,
    body: EquipeOperacionalUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> EquipeOperacionalRead:
    row = catalog_repo.get_equipe(equipe_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada.")
    merged = _merge(
        ("numero", "nome", "delegado_id", "escrivao_id", "ativo"),
        row,
        body.model_dump(exclude_unset=True),
    )
    try:
        updated = catalog_repo.update_equipe(equipe_id, merged)
    except PsycopgError as exc:
        _raise_pg(exc)
    assert updated is not None
    return EquipeOperacionalRead.model_validate(updated)


@router.delete("/equipes/{equipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipe(
    equipe_id: int,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> None:
    try:
        catalog_repo.delete_equipe(equipe_id)
    except PsycopgError as exc:
        _raise_pg(exc)


@router.get("/equipes/{equipe_id}/agentes", response_model=list[AgenteRead])
def list_equipe_agentes(
    equipe_id: int,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[AgenteRead]:
    if not catalog_repo.get_equipe(equipe_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada.")
    rows = catalog_repo.list_agentes_da_equipe(equipe_id)
    return [AgenteRead.model_validate(r) for r in rows]


@router.put("/equipes/{equipe_id}/agentes", response_model=list[AgenteRead])
def set_equipe_agentes(
    equipe_id: int,
    body: EquipeAgentesUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[AgenteRead]:
    if not catalog_repo.get_equipe(equipe_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada.")
    try:
        catalog_repo.set_agentes_da_equipe(equipe_id, body.agente_ids)
    except PsycopgError as exc:
        _raise_pg(exc)
    rows = catalog_repo.list_agentes_da_equipe(equipe_id)
    return [AgenteRead.model_validate(r) for r in rows]


@router.get("/equipes/{equipe_id}/acbas", response_model=list[EquipeAcbaItem])
def list_equipe_acbas(
    equipe_id: int,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[EquipeAcbaItem]:
    if not catalog_repo.get_equipe(equipe_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada.")
    rows = catalog_repo.list_acbas_da_equipe(equipe_id)
    return [EquipeAcbaItem.model_validate(r) for r in rows]


# --- Processos ---


@router.get("/processos", response_model=list[ProcessoRead])
def list_processos(
    q: str | None = Query(None),
    _user: UserPublic = Depends(get_authenticated_user),
) -> list[ProcessoRead]:
    rows = catalog_repo.list_processos(q)
    return [ProcessoRead.model_validate(r) for r in rows]


@router.post(
    "/processos",
    response_model=ProcessoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_processo(
    body: ProcessoCreate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> ProcessoRead:
    try:
        row = catalog_repo.insert_processo(body.model_dump())
    except PsycopgError as exc:
        _raise_pg(exc)
    return ProcessoRead.model_validate(row)


@router.get("/processos/{numero}", response_model=ProcessoRead)
def get_processo(
    numero: str,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> ProcessoRead:
    row = catalog_repo.get_processo(numero)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")
    return ProcessoRead.model_validate(row)


@router.put("/processos/{numero}", response_model=ProcessoRead)
def update_processo(
    numero: str,
    body: ProcessoUpdate,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> ProcessoRead:
    row = catalog_repo.get_processo(numero)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")
    merged = _merge(("descricao", "ativo"), row, body.model_dump(exclude_unset=True))
    try:
        updated = catalog_repo.update_processo(numero, merged)
    except PsycopgError as exc:
        _raise_pg(exc)
    assert updated is not None
    return ProcessoRead.model_validate(updated)


@router.delete("/processos/{numero}", status_code=status.HTTP_204_NO_CONTENT)
def delete_processo(
    numero: str,
    *,
    _user: UserPublic = Depends(get_authenticated_user),
) -> None:
    try:
        catalog_repo.delete_processo(numero)
    except PsycopgError as exc:
        _raise_pg(exc)
