from __future__ import annotations

from datetime import datetime, timezone

from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from app.repositories import materiais_repository as repo
from app.services.materiais_service import MaterialService
from app.schemas.materiais import MaterialCreate, MaterialUpdate
from tests.helpers.db_mock import FakeCursor, PgError, fake_connection


pytestmark = pytest.mark.unit

NOW = datetime(2026, 6, 1, tzinfo=timezone.utc)


def _row(**overrides):
    base = {
        "id": 1,
        "acba_id": 10,
        "tipo_id": 1,
        "tipo_nome": "Celular",
        "categoria_docx": "informatica",
        "item_num": 1,
        "descricao": "Smartphone",
        "descricao_ia_raw": None,
        "revisado": False,
        "acondicionamento": None,
        "localizacao": "Mesa",
        "observacao": None,
        "ordem": 0,
        "senha_tipo": "texto",
        "senha_texto": "1234",
        "senha_padrao_pontos": None,
        "senha_observacao": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return base


def test_row_to_dict_informatica():
    out = repo._row_to_dict(_row())
    assert out["informatica"]["senha_tipo"] == "texto"


def test_row_to_dict_geral():
    out = repo._row_to_dict(_row(categoria_docx="geral", senha_tipo=None))
    assert out["informatica"] is None


def test_list_by_acba_filters(monkeypatch):
    captured = {}

    def fake_fetch_all(query, params=None):
        captured["params"] = params
        return [_row()]

    monkeypatch.setattr(repo, "fetch_all", fake_fetch_all)
    items = repo.list_by_acba(10, tipo_id=2, categoria_docx="geral")
    assert len(items) == 1
    assert captured["params"]["tipo_id"] == 2


def test_get_by_id_none(monkeypatch):
    monkeypatch.setattr(repo, "fetch_one", lambda q, p=None: None)
    assert repo.get_by_id(1) is None


def test_count_pendentes(monkeypatch):
    monkeypatch.setattr(repo, "fetch_one", lambda q, p=None: {"c": 3})
    assert repo.count_pendentes_revisao(1) == 3


def test_find_and_list_ia_runs(monkeypatch):
    monkeypatch.setattr(repo, "fetch_one", lambda q, p=None: {"resposta": "x"})
    monkeypatch.setattr(repo, "fetch_all", lambda q, p=None: [{"id": 1}])
    assert repo.find_ia_run(1, "hash")["resposta"] == "x"
    assert repo.list_ia_runs(1)


def test_material_service_get_not_found(monkeypatch):
    monkeypatch.setattr(repo, "get_by_id", lambda mid: None)
    with pytest.raises(HTTPException) as exc:
        MaterialService().get(1)
    assert exc.value.status_code == 404


def test_material_service_create_pg_errors(monkeypatch):
    svc = MaterialService()
    monkeypatch.setattr(repo, "create", lambda *a, **k: (_ for _ in ()).throw(PgError("23505")))
    with pytest.raises(HTTPException) as exc:
        svc.create(1, MaterialCreate.model_validate({
            "tipo_id": 1,
            "descricao": "Item",
            "localizacao": "Sala",
            "categoria_docx": "geral",
        }))
    assert exc.value.status_code == 409


def test_material_service_marcar_revisado_empty(monkeypatch):
    monkeypatch.setattr(repo, "get_by_id", lambda mid: _row())
    with pytest.raises(HTTPException) as exc:
        MaterialService().marcar_revisado(1, "   ")
    assert exc.value.status_code == 400


def test_material_service_delete_not_found(monkeypatch):
    monkeypatch.setattr(repo, "delete", lambda mid: False)
    with pytest.raises(HTTPException) as exc:
        MaterialService().delete(1)
    assert exc.value.status_code == 404


def test_insert_ia_run_executes(monkeypatch):
    monkeypatch.setattr(repo, "fetch_one", lambda q, p=None: {"id": 1, "material_id": 1})
    result = repo.insert_ia_run(1, "m", "v1", "hash", "resp", 10)
    assert result["id"] == 1


def test_set_descricao_ia(monkeypatch):
    cursor = FakeCursor(
        fetchone_results=[{"revisado": False, "descricao": "old"}],
    )

    @contextmanager
    def mock_conn():
        from tests.helpers.db_mock import FakeConnection
        yield FakeConnection(cursor)

    monkeypatch.setattr(repo, "get_connection", mock_conn)
    monkeypatch.setattr(repo, "get_by_id", lambda mid: _row())
    repo.set_descricao_ia(1, "desc")


def test_material_service_update_success(monkeypatch):
    monkeypatch.setattr(repo, "get_by_id", lambda mid: _row())
    monkeypatch.setattr(repo, "update", lambda mid, payload: _row(descricao="Atualizado"))
    svc = MaterialService()
    updated = svc.update(
        1,
        MaterialUpdate.model_validate({"tipo_id": 1, "descricao": "Atualizado", "localizacao": "Sala"}),
    )
    assert updated["descricao"] == "Atualizado"


def test_material_service_update_not_found_after(monkeypatch):
    monkeypatch.setattr(repo, "get_by_id", lambda mid: _row())
    monkeypatch.setattr(repo, "update", lambda mid, payload: None)
    with pytest.raises(HTTPException) as exc:
        MaterialService().update(
            1,
            MaterialUpdate.model_validate({"tipo_id": 1, "descricao": "X", "localizacao": "Sala"}),
        )
    assert exc.value.status_code == 404


def test_material_service_marcar_revisado_success(monkeypatch):
    monkeypatch.setattr(repo, "get_by_id", lambda mid: _row())
    monkeypatch.setattr(repo, "marcar_revisado", lambda mid, desc: _row(descricao=desc, revisado=True))
    result = MaterialService().marcar_revisado(1, "Final")
    assert result["revisado"] is True


def test_delete_material(monkeypatch):
    cursor = FakeCursor(rowcount=1)

    @contextmanager
    def mock_conn():
        from tests.helpers.db_mock import FakeConnection
        yield FakeConnection(cursor)

    monkeypatch.setattr(repo, "get_connection", mock_conn)
    assert repo.delete(1) is True
