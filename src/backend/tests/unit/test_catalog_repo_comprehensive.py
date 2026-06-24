from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.repositories import catalog_repo
from tests.helpers import sample_data as sd


pytestmark = pytest.mark.unit


def _patch_fetch_all(monkeypatch, rows):
    monkeypatch.setattr(catalog_repo, "fetch_all", lambda q, p=None: rows)


def _patch_fetch_one(monkeypatch, row):
    monkeypatch.setattr(catalog_repo, "fetch_one", lambda q, p=None: row)


@pytest.mark.parametrize(
    "func,kwargs",
    [
        (catalog_repo.list_unidades, {}),
        (catalog_repo.list_tipos_procedimento, {}),
        (catalog_repo.list_delegados, {}),
        (catalog_repo.list_escrivaos, {}),
        (catalog_repo.list_equipes, {}),
        (catalog_repo.list_processos, {}),
        (catalog_repo.list_tipos_material, {}),
    ],
)
def test_catalog_list_functions(func, kwargs, monkeypatch):
    _patch_fetch_all(monkeypatch, [{"id": 1}])
    assert func(**kwargs)


def test_get_functions_return_row(monkeypatch):
    monkeypatch.setattr(catalog_repo, "fetch_one", lambda q, p=None: {"id": 1, "nome": "X", "numero": "P1"})
    monkeypatch.setattr(catalog_repo, "fetch_all", lambda q, p=None: [])
    assert catalog_repo.get_unidade(1)["id"] == 1
    assert catalog_repo.get_delegacia(1)["id"] == 1
    assert catalog_repo.get_tipo_procedimento(1)["id"] == 1
    assert catalog_repo.get_delegado(1)["id"] == 1
    assert catalog_repo.get_escrivao(1)["id"] == 1
    assert catalog_repo.get_agente(1)["id"] == 1
    assert catalog_repo.get_equipe(1)["id"] == 1
    assert catalog_repo.get_processo("P1")["numero"] == "P1"
    assert catalog_repo.get_tipo_material(1)["id"] == 1


def test_list_agentes_enriched(monkeypatch):
    now = datetime.now(timezone.utc)
    calls = {"n": 0}

    def fake_fetch_all(query, params=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return [
                {
                    "id": 1,
                    "nome": "Ag",
                    "matricula": "A1",
                    "funcao_padrao": "Agente",
                    "ativo": True,
                    "created_at": now,
                }
            ]
        return []

    monkeypatch.setattr(catalog_repo, "fetch_all", fake_fetch_all)
    rows = catalog_repo.list_agentes()
    assert rows[0]["id"] == 1


def test_insert_functions_return_row(monkeypatch):
    now = datetime.now(timezone.utc)

    def fake_fetch_one(query, params=None):
        base = {"id": 9, "created_at": now}
        if isinstance(params, dict):
            base.update(params)
        return base

    monkeypatch.setattr(catalog_repo, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(catalog_repo, "fetch_all", lambda q, p=None: [])
    assert catalog_repo.insert_unidade({"nome": "U", "ativo": True})["id"] == 9
    assert catalog_repo.insert_delegacia(
        {"nome": "D", "unidade_id": 1, "cidade_id": 1, "ativo": True}
    )["id"] == 9
    assert catalog_repo.insert_tipo_procedimento({"nome": "T", "ativo": True})["id"] == 9
    assert catalog_repo.insert_delegado(
        {
            "nome": "Del",
            "matricula": "1",
            "delegacia_id": 1,
            "unidade_id": 1,
            "ativo": True,
        }
    )["id"] == 9
    assert catalog_repo.insert_escrivao(
        {"nome": "Esc", "delegacia_id": 1, "unidade_id": 1, "ativo": True}
    )["id"] == 9
    assert catalog_repo.insert_agente(
        {"nome": "Ag", "matricula": "A1", "funcao_padrao": "Agente", "ativo": True}
    )["id"] == 9
    assert catalog_repo.insert_equipe(
        {
            "numero": "01",
            "nome": "Eq",
            "delegado_id": 1,
            "escrivao_id": 1,
            "ativo": True,
        }
    )["id"] == 9
    assert catalog_repo.insert_processo({"numero": "P1", "descricao": "Desc"})["id"] == 9
    assert catalog_repo.insert_tipo_material(
        {"nome": "Celular", "categoria_docx": "informatica", "ativo": True}
    )["id"] == 9


def test_update_functions(monkeypatch):
    monkeypatch.setattr(
        catalog_repo,
        "fetch_one",
        lambda q, p=None: {"id": 1, "nome": "Atualizado"},
    )
    monkeypatch.setattr(catalog_repo, "fetch_all", lambda q, p=None: [])
    assert catalog_repo.update_unidade(1, {"nome": "U", "ativo": True})
    assert catalog_repo.update_delegacia(
        1, {"nome": "D", "unidade_id": 1, "cidade_id": 1, "ativo": True}
    )
    assert catalog_repo.update_tipo_procedimento(1, {"nome": "T", "ativo": True})
    assert catalog_repo.update_delegado(
        1,
        {
            "nome": "Del",
            "matricula": "1",
            "delegacia_id": 1,
            "unidade_id": 1,
            "ativo": True,
        },
    )
    assert catalog_repo.update_escrivao(
        1, {"nome": "Esc", "delegacia_id": 1, "unidade_id": 1, "ativo": True}
    )
    assert catalog_repo.update_agente(
        1, {"nome": "Ag", "matricula": "A1", "funcao_padrao": "Agente", "ativo": True}
    )
    assert catalog_repo.update_equipe(
        1,
        {
            "numero": "01",
            "nome": "Eq",
            "delegado_id": 1,
            "escrivao_id": 1,
            "ativo": True,
        },
    )
    assert catalog_repo.update_processo("P1", {"numero": "P1", "descricao": "D"})
    assert catalog_repo.update_tipo_material(
        1, {"nome": "Celular", "categoria_docx": "informatica", "ativo": True}
    )


def test_delete_functions_execute(monkeypatch):
    calls = []
    monkeypatch.setattr(catalog_repo, "execute_query", lambda q, p=None: calls.append(q))
    catalog_repo.delete_unidade(1)
    catalog_repo.delete_delegacia(1)
    catalog_repo.delete_tipo_procedimento(1)
    catalog_repo.delete_delegado(1)
    catalog_repo.delete_escrivao(1)
    catalog_repo.delete_agente(1)
    catalog_repo.delete_equipe(1)
    catalog_repo.delete_processo("P1")
    catalog_repo.delete_tipo_material(1)
    assert len(calls) == 9


def test_enriquecer_agentes_com_equipes(monkeypatch):
    now = datetime.now(timezone.utc)
    rows = [{"id": 1, "nome": "Ag"}]
    monkeypatch.setattr(
        catalog_repo,
        "fetch_all",
        lambda q, p=None: [
            {
                "agente_id": 1,
                "equipe_id": 1,
                "equipe_numero": "01",
                "equipe_nome": "Alfa",
                "data_inicio": now.date(),
            }
        ],
    )
    enriched = catalog_repo._enriquecer_agentes_com_equipes_atuais(rows)
    assert enriched[0]["equipe_atual_resumo"]


def test_list_historico_equipes(monkeypatch):
    _patch_fetch_all(monkeypatch, [{"equipe_id": 1}])
    assert catalog_repo.list_historico_equipes_do_agente(1)


def test_get_uf_and_update(monkeypatch):
    monkeypatch.setattr(catalog_repo, "fetch_one", lambda q, p=None: {"id": 1, "sigla": "GO", "nome": "Goiás", "ativo": True})
    assert catalog_repo.get_uf(1)["sigla"] == "GO"
    assert catalog_repo.update_uf(1, {"sigla": "GO", "nome": "Goiás", "ativo": True})


def test_list_delegacias_filters(monkeypatch):
    captured = {}

    def fake_fetch_all(query, params=None):
        captured["params"] = params
        return []

    monkeypatch.setattr(catalog_repo, "fetch_all", fake_fetch_all)
    catalog_repo.list_delegacias("del", unidade_id=1, cidade_id=2)
    assert captured["params"]["unidade_id"] == 1
    assert captured["params"]["cidade_id"] == 2


def test_list_equipes_and_processos(monkeypatch):
    monkeypatch.setattr(catalog_repo, "fetch_all", lambda q, p=None: [{"id": 1}])
    assert catalog_repo.list_equipes("alfa")
    assert catalog_repo.list_processos("P1")


def test_list_agentes_da_equipe(monkeypatch):
    _patch_fetch_all(monkeypatch, [sd.agente_row()])
    assert catalog_repo.list_agentes_da_equipe(1)


def test_set_agentes_da_equipe(monkeypatch):
    executed = []
    monkeypatch.setattr(catalog_repo, "execute_query", lambda q, p=None: executed.append((q, p)))
    monkeypatch.setattr(catalog_repo, "fetch_all", lambda q, p=None: [])
    catalog_repo.set_agentes_da_equipe(1, [1, 2])
    assert executed


def test_list_acbas_da_equipe(monkeypatch):
    _patch_fetch_all(monkeypatch, [{"id": 1}])
    assert catalog_repo.list_acbas_da_equipe(1)
