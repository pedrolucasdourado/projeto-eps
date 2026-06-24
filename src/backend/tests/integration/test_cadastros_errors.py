from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.routers import cadastros
from tests.helpers import sample_data as sd
from tests.helpers.db_mock import PgError


pytestmark = pytest.mark.integration


@pytest.fixture
def admin_auth(authenticated_as, admin_user):
    authenticated_as(admin_user)
    return admin_user


def _patch_catalog(monkeypatch, **overrides):
    defaults = {
        "get_unidade": lambda uid: sd.unidade_row() if uid == 1 else None,
        "update_unidade": lambda uid, data: sd.unidade_row(**data),
        "delete_unidade": lambda uid: None,
        "get_delegacia": lambda did: sd.delegacia_row() if did == 1 else None,
        "update_delegacia": lambda did, data: sd.delegacia_row(**data),
        "delete_delegacia": lambda did: None,
        "get_tipo_procedimento": lambda tid: sd.tipo_proc_row() if tid == 1 else None,
        "update_tipo_procedimento": lambda tid, data: sd.tipo_proc_row(**data),
        "delete_tipo_procedimento": lambda tid: None,
        "get_delegado": lambda did: sd.delegado_row() if did == 1 else None,
        "update_delegado": lambda did, data: sd.delegado_row(**data),
        "delete_delegado": lambda did: None,
        "get_escrivao": lambda eid: sd.escrivao_row() if eid == 1 else None,
        "update_escrivao": lambda eid, data: sd.escrivao_row(**data),
        "delete_escrivao": lambda eid: None,
        "get_agente": lambda aid: sd.agente_row() if aid == 1 else None,
        "update_agente": lambda aid, data: sd.agente_row(**data),
        "delete_agente": lambda aid: None,
        "get_equipe": lambda eid: sd.equipe_row() if eid == 1 else None,
        "update_equipe": lambda eid, data: sd.equipe_row(**data),
        "delete_equipe": lambda eid: None,
        "get_processo": lambda num: sd.processo_row() if num == "P1" else None,
        "update_processo": lambda num, data: sd.processo_row(**data),
        "delete_processo": lambda num: None,
        "get_tipo_material": lambda tid: sd.tipo_material_row() if tid == 1 else None,
        "update_tipo_material": lambda tid, data: sd.tipo_material_row(**data),
        "delete_tipo_material": lambda tid: None,
        "get_cidade": lambda cid: sd.cidade_row() if cid == 1 else None,
        "update_cidade": lambda cid, data: sd.cidade_row(**data),
        "delete_cidade": lambda cid: None,
        "get_uf": lambda uid: sd.uf_row() if uid == 1 else None,
        "update_uf": lambda uid, data: sd.uf_row(**data),
        "delete_uf": lambda uid: None,
    }
    defaults.update(overrides)
    for name, fn in defaults.items():
        monkeypatch.setattr(cadastros.catalog_repo, name, fn)


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/cadastros/unidades/99"),
        ("get", "/api/cadastros/delegacias/99"),
        ("get", "/api/cadastros/tipos-procedimento/99"),
        ("get", "/api/cadastros/delegados/99"),
        ("get", "/api/cadastros/escrivaos/99"),
        ("get", "/api/cadastros/agentes/99"),
        ("get", "/api/cadastros/equipes/99"),
        ("get", "/api/cadastros/processos/NOPE"),
        ("get", "/api/cadastros/tipos-material/99"),
        ("get", "/api/cadastros/cidades/99"),
    ],
)
def test_cadastros_get_404(client, admin_auth, monkeypatch, method, path):
    _patch_catalog(monkeypatch)
    response = client.get(path)
    assert response.status_code == 404


def test_cadastros_update_404(client, admin_auth, monkeypatch):
    _patch_catalog(monkeypatch)
    assert client.put("/api/cadastros/unidades/99", json={"nome": "Nova", "ativo": True}).status_code == 404
    assert client.put(
        "/api/cadastros/delegados/99",
        json={
            "nome": "Novo Del",
            "matricula": "1",
            "delegacia_id": 1,
            "unidade_id": 1,
            "ativo": True,
        },
    ).status_code == 404


def test_cadastros_delete_pg_conflict(client, admin_auth, monkeypatch):
    def boom(uid):
        raise PgError("23503")

    _patch_catalog(monkeypatch, delete_unidade=boom)
    assert client.delete("/api/cadastros/unidades/1").status_code == 409


def test_cadastros_update_pg_duplicate(client, admin_auth, monkeypatch):
    def boom(uid, data):
        raise PgError("23505")

    monkeypatch.setattr(cadastros.catalog_repo, "get_uf", lambda uid: sd.uf_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_uf", boom)
    assert (
        client.put(
            "/api/cadastros/ufs/1",
            json={"sigla": "DF", "nome": "Distrito Federal", "ativo": True},
        ).status_code
        == 409
    )


def test_cadastros_post_unidade(client, admin_auth, monkeypatch):
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "insert_unidade",
        lambda data: sd.unidade_row(**data),
    )
    response = client.post("/api/cadastros/unidades", json={"nome": "Nova", "ativo": True})
    assert response.status_code == 201


def test_cadastros_post_processo(client, admin_auth, monkeypatch):
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "insert_processo",
        lambda data: sd.processo_row(**data),
    )
    response = client.post(
        "/api/cadastros/processos",
        json={"numero": "P99", "descricao": "Desc"},
    )
    assert response.status_code == 201


def test_cadastros_post_tipo_material(client, admin_auth, monkeypatch):
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "insert_tipo_material",
        lambda data: sd.tipo_material_row(**data),
    )
    response = client.post(
        "/api/cadastros/tipos-material",
        json={"nome": "Tablet", "tabela_documento": "informatica", "ativo": True},
    )
    assert response.status_code == 201


def test_raise_pg_reraises_unknown_code():
    with pytest.raises(PgError):
        cadastros._raise_pg(PgError("99999"))


def test_raise_pg_fk_on_delete():
    with pytest.raises(HTTPException) as exc:
        cadastros._raise_pg(PgError("23503"))
    assert exc.value.status_code == 409
