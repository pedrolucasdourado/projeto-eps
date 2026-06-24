"""Testes unitários para MaterialService."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.schemas.materiais import MaterialCreate, MaterialUpdate
from app.services.materiais_service import MaterialService


pytestmark = pytest.mark.unit


def _row(material_id: int = 1) -> dict:
    return {
        "id": material_id,
        "acba_id": 10,
        "tipo_id": 2,
        "descricao": "Celular preto",
        "descricao_revisada": None,
        "revisado": False,
        "categoria_docx": "informatica",
    }


@pytest.fixture
def svc():
    return MaterialService()


def test_get_returns_material(svc, monkeypatch):
    from app.services import materiais_service as ms
    from app.repositories import materiais_repository as repo

    monkeypatch.setattr(repo, "get_by_id", lambda mid: _row(mid))

    result = svc.get(1)

    assert result["id"] == 1
    assert result["descricao"] == "Celular preto"


def test_get_raises_404_when_not_found(svc, monkeypatch):
    from app.repositories import materiais_repository as repo

    monkeypatch.setattr(repo, "get_by_id", lambda mid: None)

    with pytest.raises(HTTPException) as exc:
        svc.get(99)

    assert exc.value.status_code == 404


def test_list_by_acba_delegates_to_repo(svc, monkeypatch):
    from app.repositories import materiais_repository as repo

    captured = {}

    def fake_list(acba_id, tipo_id=None, categoria_docx=None):
        captured["acba_id"] = acba_id
        captured["tipo_id"] = tipo_id
        captured["categoria_docx"] = categoria_docx
        return [_row()]

    monkeypatch.setattr(repo, "list_by_acba", fake_list)

    result = svc.list_by_acba(10, tipo_id=2)

    assert captured == {"acba_id": 10, "tipo_id": 2, "categoria_docx": None}
    assert len(result) == 1


def test_delete_raises_404_when_not_found(svc, monkeypatch):
    from app.repositories import materiais_repository as repo

    monkeypatch.setattr(repo, "delete", lambda mid: False)

    with pytest.raises(HTTPException) as exc:
        svc.delete(99)

    assert exc.value.status_code == 404


def test_delete_succeeds(svc, monkeypatch):
    from app.repositories import materiais_repository as repo

    deleted = []
    monkeypatch.setattr(repo, "delete", lambda mid: deleted.append(mid) or True)

    svc.delete(1)

    assert deleted == [1]


def test_marcar_revisado_rejects_empty_description(svc, monkeypatch):
    from app.repositories import materiais_repository as repo

    monkeypatch.setattr(repo, "get_by_id", lambda mid: _row(mid))

    with pytest.raises(HTTPException) as exc:
        svc.marcar_revisado(1, "   ")

    assert exc.value.status_code == 400
    assert "vazia" in exc.value.detail


def test_marcar_revisado_persists_description(svc, monkeypatch):
    from app.repositories import materiais_repository as repo

    monkeypatch.setattr(repo, "get_by_id", lambda mid: _row(mid))
    monkeypatch.setattr(
        repo,
        "marcar_revisado",
        lambda mid, desc: {**_row(mid), "descricao_revisada": desc, "revisado": True},
    )

    result = svc.marcar_revisado(1, "  Celular Apple iPhone 13  ")

    assert result["revisado"] is True
    assert result["descricao_revisada"] == "Celular Apple iPhone 13"


def test_count_pendentes_delegates_to_repo(svc, monkeypatch):
    from app.repositories import materiais_repository as repo

    monkeypatch.setattr(repo, "count_pendentes_revisao", lambda acba_id: 3)

    assert svc.count_pendentes_revisao(10) == 3
