from __future__ import annotations

from datetime import datetime, timezone

import pytest
from psycopg2 import Error

from app.routers import cadastros
from tests.helpers import sample_data as sd


pytestmark = pytest.mark.integration


def _ts():
    return datetime(2026, 6, 1, tzinfo=timezone.utc)


@pytest.fixture
def admin_auth(authenticated_as, admin_user):
    authenticated_as(admin_user)
    return admin_user


@pytest.fixture
def delegado_auth(authenticated_as, delegado_user):
    authenticated_as(delegado_user)
    return delegado_user


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_uf_crud(client, admin_auth, monkeypatch):
    row = sd.uf_row()
    monkeypatch.setattr(cadastros.catalog_repo, "list_ufs", lambda q=None: [row])
    monkeypatch.setattr(cadastros.catalog_repo, "get_uf", lambda uid: row if uid == 1 else None)
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "insert_uf",
        lambda data: {**row, **data, "id": 2},
    )
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "update_uf",
        lambda uid, data: {**row, **data},
    )
    monkeypatch.setattr(cadastros.catalog_repo, "delete_uf", lambda uid: None)

    assert client.get("/api/cadastros/ufs").status_code == 200
    assert client.post("/api/cadastros/ufs", json={"sigla": "GO", "nome": "Goiás", "ativo": True}).status_code == 201
    assert client.get("/api/cadastros/ufs/1").status_code == 200
    assert client.get("/api/cadastros/ufs/99").status_code == 404
    assert client.put("/api/cadastros/ufs/1", json={"sigla": "DF", "nome": "DF", "ativo": True}).status_code == 200
    assert client.delete("/api/cadastros/ufs/1").status_code == 204


def test_cidade_crud(client, admin_auth, monkeypatch):
    row = sd.cidade_row()
    monkeypatch.setattr(cadastros.catalog_repo, "list_cidades", lambda q=None, uf_id=None: [row])
    monkeypatch.setattr(cadastros.catalog_repo, "get_cidade", lambda cid: row)
    monkeypatch.setattr(cadastros.catalog_repo, "insert_cidade", lambda data: {**row, **data})
    monkeypatch.setattr(cadastros.catalog_repo, "update_cidade", lambda cid, data: {**row, **data})
    monkeypatch.setattr(cadastros.catalog_repo, "delete_cidade", lambda cid: None)

    assert client.get("/api/cadastros/cidades").status_code == 200
    assert client.post(
        "/api/cadastros/cidades",
        json={"nome": "Gama", "uf_id": 1, "ativo": True},
    ).status_code == 201
    assert client.get("/api/cadastros/cidades/1").status_code == 200
    assert client.put(
        "/api/cadastros/cidades/1",
        json={"nome": "Brasília", "uf_id": 1, "ativo": True},
    ).status_code == 200
    assert client.delete("/api/cadastros/cidades/1").status_code == 204


def test_unidade_delegacia_tipo_proc(client, admin_auth, monkeypatch):
    monkeypatch.setattr(cadastros.catalog_repo, "list_unidades", lambda q=None: [sd.unidade_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "get_unidade", lambda uid: sd.unidade_row())
    monkeypatch.setattr(cadastros.catalog_repo, "insert_unidade", lambda data: sd.unidade_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "update_unidade", lambda uid, data: sd.unidade_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "delete_unidade", lambda uid: None)

    monkeypatch.setattr(
        cadastros.catalog_repo,
        "list_delegacias",
        lambda q=None, unidade_id=None, cidade_id=None: [sd.delegacia_row()],
    )
    monkeypatch.setattr(cadastros.catalog_repo, "get_delegacia", lambda did: sd.delegacia_row())
    monkeypatch.setattr(cadastros.catalog_repo, "insert_delegacia", lambda data: sd.delegacia_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "update_delegacia", lambda did, data: sd.delegacia_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "delete_delegacia", lambda did: None)

    monkeypatch.setattr(cadastros.catalog_repo, "list_tipos_procedimento", lambda q=None: [sd.tipo_proc_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "get_tipo_procedimento", lambda tid: sd.tipo_proc_row())
    monkeypatch.setattr(cadastros.catalog_repo, "insert_tipo_procedimento", lambda data: sd.tipo_proc_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "update_tipo_procedimento", lambda tid, data: sd.tipo_proc_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "delete_tipo_procedimento", lambda tid: None)

    for path in ("/api/cadastros/unidades", "/api/cadastros/delegacias", "/api/cadastros/tipos-procedimento"):
        assert client.get(path).status_code == 200


def test_delegado_admin_only(client, delegado_auth, monkeypatch):
    monkeypatch.setattr(cadastros.catalog_repo, "insert_delegado", lambda data: sd.delegado_row())
    response = client.post(
        "/api/cadastros/delegados",
        json={
            "nome": "Novo",
            "matricula": "999",
            "delegacia_id": 1,
            "unidade_id": 1,
            "ativo": True,
        },
    )
    assert response.status_code == 403


def test_delegado_crud_admin(client, admin_auth, monkeypatch):
    row = sd.delegado_row()
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "list_delegados",
        lambda q=None, delegacia_id=None, unidade_id=None: [row],
    )
    monkeypatch.setattr(cadastros.catalog_repo, "get_delegado", lambda did: row if did == 1 else None)
    monkeypatch.setattr(cadastros.catalog_repo, "insert_delegado", lambda data: {**row, **data})
    monkeypatch.setattr(cadastros.catalog_repo, "update_delegado", lambda did, data: {**row, **data})
    monkeypatch.setattr(cadastros.catalog_repo, "delete_delegado", lambda did: None)

    assert client.get("/api/cadastros/delegados").status_code == 200
    assert client.post(
        "/api/cadastros/delegados",
        json={
            "nome": "Novo",
            "matricula": "999",
            "delegacia_id": 1,
            "unidade_id": 1,
            "ativo": True,
        },
    ).status_code == 201
    assert client.put(
        "/api/cadastros/delegados/1",
        json={
            "nome": "Novo",
            "matricula": "999",
            "delegacia_id": 1,
            "unidade_id": 1,
            "ativo": True,
        },
    ).status_code == 200
    assert client.delete("/api/cadastros/delegados/1").status_code == 204


def test_escrivao_agente_equipe_processo_tipo_material(client, admin_auth, monkeypatch):
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "list_escrivaos",
        lambda q=None, delegacia_id=None, unidade_id=None: [sd.escrivao_row()],
    )
    monkeypatch.setattr(cadastros.catalog_repo, "get_escrivao", lambda eid: sd.escrivao_row())
    monkeypatch.setattr(cadastros.catalog_repo, "insert_escrivao", lambda data: sd.escrivao_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "update_escrivao", lambda eid, data: sd.escrivao_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "delete_escrivao", lambda eid: None)

    monkeypatch.setattr(cadastros.catalog_repo, "list_agentes", lambda q=None: [sd.agente_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "get_agente", lambda aid: sd.agente_row())
    monkeypatch.setattr(cadastros.catalog_repo, "insert_agente", lambda data: sd.agente_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "update_agente", lambda aid, data: sd.agente_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "delete_agente", lambda aid: None)
    monkeypatch.setattr(cadastros.catalog_repo, "list_historico_equipes_do_agente", lambda aid: [])

    monkeypatch.setattr(cadastros.catalog_repo, "list_equipes", lambda q=None: [sd.equipe_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "get_equipe", lambda eid: sd.equipe_row())
    monkeypatch.setattr(cadastros.catalog_repo, "insert_equipe", lambda data: sd.equipe_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "update_equipe", lambda eid, data: sd.equipe_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "delete_equipe", lambda eid: None)
    monkeypatch.setattr(cadastros.catalog_repo, "list_agentes_da_equipe", lambda eid: [sd.agente_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "set_agentes_da_equipe", lambda eid, ids: None)
    monkeypatch.setattr(cadastros.catalog_repo, "list_acbas_da_equipe", lambda eid: [])

    monkeypatch.setattr(cadastros.catalog_repo, "list_processos", lambda q=None: [sd.processo_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "get_processo", lambda num: sd.processo_row())
    monkeypatch.setattr(cadastros.catalog_repo, "insert_processo", lambda data: sd.processo_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "update_processo", lambda num, data: sd.processo_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "delete_processo", lambda num: None)

    monkeypatch.setattr(cadastros.catalog_repo, "list_tipos_material", lambda q=None: [sd.tipo_material_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "get_tipo_material", lambda tid: sd.tipo_material_row())
    monkeypatch.setattr(cadastros.catalog_repo, "insert_tipo_material", lambda data: sd.tipo_material_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "update_tipo_material", lambda tid, data: sd.tipo_material_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "delete_tipo_material", lambda tid: None)

    paths = [
        "/api/cadastros/escrivaos",
        "/api/cadastros/agentes",
        "/api/cadastros/equipes",
        "/api/cadastros/processos",
        "/api/cadastros/tipos-material",
    ]
    for path in paths:
        assert client.get(path).status_code == 200

    assert client.get("/api/cadastros/agentes/1/equipes/historico").status_code == 200
    assert client.get("/api/cadastros/equipes/1/agentes").status_code == 200
    assert client.put("/api/cadastros/equipes/1/agentes", json={"agente_ids": [1]}).status_code == 200
    assert client.get("/api/cadastros/equipes/1/acbas").status_code == 200


def test_raise_pg_conflict():
    from fastapi import HTTPException
    from tests.helpers.db_mock import PgError

    with pytest.raises(HTTPException):
        cadastros._raise_pg(PgError("23505"))


def test_merge_helper():
    merged = cadastros._merge(("a", "b"), {"a": 1, "b": 2, "c": 3}, {"b": 9})
    assert merged == {"a": 1, "b": 9}
