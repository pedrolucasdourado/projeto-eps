from __future__ import annotations

import pytest

from app.routers import cadastros
from tests.helpers import sample_data as sd
from tests.helpers.db_mock import PgError


pytestmark = pytest.mark.integration


@pytest.fixture
def admin_auth(authenticated_as, admin_user):
    authenticated_as(admin_user)
    return admin_user


def _patch_all_lists(monkeypatch):
    monkeypatch.setattr(cadastros.catalog_repo, "list_unidades", lambda q=None: [sd.unidade_row()])
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "list_delegacias",
        lambda q=None, unidade_id=None, cidade_id=None: [sd.delegacia_row()],
    )
    monkeypatch.setattr(cadastros.catalog_repo, "list_tipos_procedimento", lambda q=None: [sd.tipo_proc_row()])
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "list_delegados",
        lambda q=None, delegacia_id=None, unidade_id=None: [sd.delegado_row()],
    )
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "list_escrivaos",
        lambda q=None, delegacia_id=None, unidade_id=None: [sd.escrivao_row()],
    )
    monkeypatch.setattr(cadastros.catalog_repo, "list_agentes", lambda q=None: [sd.agente_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "list_equipes", lambda q=None: [sd.equipe_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "list_processos", lambda q=None: [sd.processo_row()])
    monkeypatch.setattr(cadastros.catalog_repo, "list_tipos_material", lambda q=None: [sd.tipo_material_row()])


@pytest.mark.parametrize(
    "path,payload",
    [
        (
            "/api/cadastros/unidades/1",
            {"nome": "Unidade Nova", "ativo": True},
        ),
        (
            "/api/cadastros/delegacias/1",
            {"nome": "Delegacia Nova", "unidade_id": 1, "cidade_id": 1, "ativo": True},
        ),
        (
            "/api/cadastros/tipos-procedimento/1",
            {"nome": "Tipo Novo", "ativo": True},
        ),
        (
            "/api/cadastros/delegados/1",
            {
                "nome": "Delegado Novo",
                "matricula": "123",
                "delegacia_id": 1,
                "unidade_id": 1,
                "ativo": True,
            },
        ),
        (
            "/api/cadastros/escrivaos/1",
            {"nome": "Escrivao Novo", "delegacia_id": 1, "unidade_id": 1, "ativo": True},
        ),
        (
            "/api/cadastros/agentes/1",
            {
                "nome": "Agente Novo",
                "matricula": "A99",
                "funcao_padrao": "Agente",
                "ativo": True,
            },
        ),
        (
            "/api/cadastros/equipes/1",
            {
                "numero": "02",
                "nome": "Equipe Beta",
                "delegado_id": 1,
                "escrivao_id": 1,
                "ativo": True,
            },
        ),
        (
            "/api/cadastros/processos/P1",
            {"descricao": "Atualizado"},
        ),
        (
            "/api/cadastros/tipos-material/1",
            {"nome": "Tablet", "tabela_documento": "informatica", "ativo": True},
        ),
        (
            "/api/cadastros/cidades/1",
            {"nome": "Brasilia", "uf_id": 1, "ativo": True},
        ),
        (
            "/api/cadastros/ufs/1",
            {"sigla": "DF", "nome": "Distrito Federal", "ativo": True},
        ),
    ],
)
def test_cadastros_update_success(client, admin_auth, monkeypatch, path, payload):
    _patch_all_lists(monkeypatch)
    monkeypatch.setattr(cadastros.catalog_repo, "get_unidade", lambda uid: sd.unidade_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_unidade", lambda uid, data: sd.unidade_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "get_delegacia", lambda did: sd.delegacia_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_delegacia", lambda did, data: sd.delegacia_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "get_tipo_procedimento", lambda tid: sd.tipo_proc_row())
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "update_tipo_procedimento",
        lambda tid, data: sd.tipo_proc_row(**data),
    )
    monkeypatch.setattr(cadastros.catalog_repo, "get_delegado", lambda did: sd.delegado_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_delegado", lambda did, data: sd.delegado_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "get_escrivao", lambda eid: sd.escrivao_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_escrivao", lambda eid, data: sd.escrivao_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "get_agente", lambda aid: sd.agente_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_agente", lambda aid, data: sd.agente_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "get_equipe", lambda eid: sd.equipe_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_equipe", lambda eid, data: sd.equipe_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "get_processo", lambda num: sd.processo_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_processo", lambda num, data: sd.processo_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "get_tipo_material", lambda tid: sd.tipo_material_row())
    monkeypatch.setattr(
        cadastros.catalog_repo,
        "update_tipo_material",
        lambda tid, data: sd.tipo_material_row(**data),
    )
    monkeypatch.setattr(cadastros.catalog_repo, "get_cidade", lambda cid: sd.cidade_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_cidade", lambda cid, data: sd.cidade_row(**data))
    monkeypatch.setattr(cadastros.catalog_repo, "get_uf", lambda uid: sd.uf_row())
    monkeypatch.setattr(cadastros.catalog_repo, "update_uf", lambda uid, data: sd.uf_row(**data))

    assert client.put(path, json=payload).status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/api/cadastros/unidades/1",
        "/api/cadastros/delegacias/1",
        "/api/cadastros/tipos-procedimento/1",
        "/api/cadastros/delegados/1",
        "/api/cadastros/escrivaos/1",
        "/api/cadastros/agentes/1",
        "/api/cadastros/equipes/1",
        "/api/cadastros/processos/P1",
        "/api/cadastros/tipos-material/1",
        "/api/cadastros/cidades/1",
        "/api/cadastros/ufs/1",
    ],
)
def test_cadastros_delete_success(client, admin_auth, monkeypatch, path):
    monkeypatch.setattr(cadastros.catalog_repo, "delete_unidade", lambda uid: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_delegacia", lambda did: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_tipo_procedimento", lambda tid: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_delegado", lambda did: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_escrivao", lambda eid: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_agente", lambda aid: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_equipe", lambda eid: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_processo", lambda num: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_tipo_material", lambda tid: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_cidade", lambda cid: None)
    monkeypatch.setattr(cadastros.catalog_repo, "delete_uf", lambda uid: None)
    assert client.delete(path).status_code == 204


def test_cadastros_get_by_id_success(client, admin_auth, monkeypatch):
    monkeypatch.setattr(cadastros.catalog_repo, "get_unidade", lambda uid: sd.unidade_row())
    monkeypatch.setattr(cadastros.catalog_repo, "get_delegacia", lambda did: sd.delegacia_row())
    monkeypatch.setattr(cadastros.catalog_repo, "get_tipo_procedimento", lambda tid: sd.tipo_proc_row())
    monkeypatch.setattr(cadastros.catalog_repo, "get_delegado", lambda did: sd.delegado_row())
    monkeypatch.setattr(cadastros.catalog_repo, "get_escrivao", lambda eid: sd.escrivao_row())
    monkeypatch.setattr(cadastros.catalog_repo, "get_agente", lambda aid: sd.agente_row())
    monkeypatch.setattr(cadastros.catalog_repo, "get_equipe", lambda eid: sd.equipe_row())
    monkeypatch.setattr(cadastros.catalog_repo, "get_processo", lambda num: sd.processo_row())
    monkeypatch.setattr(cadastros.catalog_repo, "get_tipo_material", lambda tid: sd.tipo_material_row())

    for path in (
        "/api/cadastros/unidades/1",
        "/api/cadastros/delegacias/1",
        "/api/cadastros/tipos-procedimento/1",
        "/api/cadastros/delegados/1",
        "/api/cadastros/escrivaos/1",
        "/api/cadastros/agentes/1",
        "/api/cadastros/equipes/1",
        "/api/cadastros/processos/P1",
        "/api/cadastros/tipos-material/1",
    ):
        assert client.get(path).status_code == 200


def test_cadastros_update_cidade_pg(client, admin_auth, monkeypatch):
    monkeypatch.setattr(cadastros.catalog_repo, "get_cidade", lambda cid: sd.cidade_row())

    def boom(cid, data):
        raise PgError("23505")

    monkeypatch.setattr(cadastros.catalog_repo, "update_cidade", boom)
    response = client.put(
        "/api/cadastros/cidades/1",
        json={"nome": "Brasilia", "uf_id": 1, "ativo": True},
    )
    assert response.status_code == 409
