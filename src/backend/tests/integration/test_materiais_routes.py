from __future__ import annotations

from datetime import datetime, timezone
import io

import pytest

from app.routers import materiais as materiais_router
from app.schemas import UserPublic
from app.services.gemini_vision_service import GeminiResult


pytestmark = pytest.mark.integration


def _delegado() -> UserPublic:
    return UserPublic(
        id=2,
        email="delegado@example.com",
        full_name="Delegado",
        role="delegado",
        delegado_id=1,
    )


def _material(acba_id=1, material_id=10):
    now = datetime.now(timezone.utc)
    return {
        "id": material_id,
        "acba_id": acba_id,
        "item_num": 1,
        "categoria_docx": "geral",
        "descricao": "Item teste",
        "localizacao": "Sala",
        "tipo_id": 1,
        "tipo_nome": "Outros",
        "revisado": False,
        "created_at": now,
        "updated_at": now,
    }


def test_descrever_anonimo_sem_imagem(client, authenticated_as):
    authenticated_as(_delegado())
    response = client.post("/api/acba/ia/descrever-material")
    assert response.status_code == 400


def test_descrever_anonimo_com_imagem(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    monkeypatch.setattr(
        materiais_router,
        "descrever_material",
        lambda *a, **k: GeminiResult(
            descricao="Notebook",
            modelo="gemini-test",
            prompt_versao="v2",
            request_hash="abc",
            tipo_id_sugerido=1,
            tipo_nome_sugerido="Notebook",
        ),
    )
    monkeypatch.setattr(materiais_router.catalog_repo, "list_tipos_material", lambda q=None: [{"id": 1, "nome": "Notebook", "ativo": True}])

    files = {"imagens": ("foto.jpg", io.BytesIO(b"fake-image"), "image/jpeg")}
    response = client.post("/api/acba/ia/descrever-material", files=files)
    assert response.status_code == 200
    assert response.json()["descricao"] == "Notebook"


def test_materiais_crud_flow(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    mat = _material()

    class FakeAcbaService:
        def get_by_id(self, acba_id, user):
            return type("R", (), {"equipe_id": 1, "pdf_gerado_at": None})()

        def assert_can_write_materiais(self, acba_id, user):
            return type("R", (), {"equipe_id": 1, "pdf_gerado_at": None})()

    class FakeMaterialService:
        def list_by_acba(self, acba_id, **kwargs):
            return [mat]

        def get(self, material_id):
            return mat

        def create(self, acba_id, payload):
            return mat

        def update(self, material_id, payload):
            return mat

        def delete(self, material_id):
            return None

        def marcar_revisado(self, material_id, descricao):
            return {**mat, "descricao": descricao, "revisado": True}

    monkeypatch.setattr(materiais_router, "acba_service", FakeAcbaService())
    monkeypatch.setattr(materiais_router, "material_service", FakeMaterialService())
    monkeypatch.setattr(materiais_router.repo, "list_ia_runs", lambda mid: [])

    assert client.get("/api/acba/1/materiais").status_code == 200
    assert client.post(
        "/api/acba/1/materiais",
        json={
            "tipo_id": 1,
            "descricao": "Novo item",
            "localizacao": "Sala",
            "categoria_docx": "geral",
        },
    ).status_code == 201
    assert client.get("/api/acba/1/materiais/10").status_code == 200
    assert client.put(
        "/api/acba/1/materiais/10",
        json={"descricao": "Atualizado", "localizacao": "Sala", "tipo_id": 1},
    ).status_code == 200
    assert client.post(
        "/api/acba/1/materiais/10/revisar",
        json={"descricao": "Revisado pelo operador"},
    ).status_code == 200
    assert client.get("/api/acba/1/materiais/10/ia-runs").status_code == 200
    assert client.delete("/api/acba/1/materiais/10").status_code == 204


def test_descrever_material_endpoint(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    mat = _material()

    class FakeAcbaService:
        def assert_can_write_materiais(self, acba_id, user):
            return None

    class FakeMaterialService:
        def get(self, material_id):
            return mat

    monkeypatch.setattr(materiais_router, "acba_service", FakeAcbaService())
    monkeypatch.setattr(materiais_router, "material_service", FakeMaterialService())
    monkeypatch.setattr(
        materiais_router,
        "descrever_material",
        lambda *a, **k: GeminiResult(
            descricao="Celular preto",
            modelo="gemini-test",
            prompt_versao="v2",
            request_hash="hash123",
            tipo_id_sugerido=1,
            tipo_nome_sugerido="Celular",
        ),
    )
    monkeypatch.setattr(materiais_router.catalog_repo, "list_tipos_material", lambda q=None: [])
    monkeypatch.setattr(materiais_router.repo, "find_ia_run", lambda mid, h: None)
    monkeypatch.setattr(materiais_router.repo, "insert_ia_run", lambda **k: {"id": 1})
    monkeypatch.setattr(materiais_router.repo, "set_descricao_ia", lambda mid, desc: mat)

    files = {"imagens": ("foto.jpg", io.BytesIO(b"fake-image"), "image/jpeg")}
    response = client.post("/api/acba/1/materiais/10/descrever", files=files)
    assert response.status_code == 200
    assert response.json()["descricao"] == "Celular preto"


def test_descrever_material_cache_hit(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    mat = _material()

    class FakeAcbaService:
        def assert_can_write_materiais(self, acba_id, user):
            return None

    class FakeMaterialService:
        def get(self, material_id):
            return mat

    monkeypatch.setattr(materiais_router, "acba_service", FakeAcbaService())
    monkeypatch.setattr(materiais_router, "material_service", FakeMaterialService())
    monkeypatch.setattr(
        materiais_router,
        "descrever_material",
        lambda *a, **k: GeminiResult(
            descricao="novo",
            modelo="gemini-test",
            prompt_versao="v2",
            request_hash="hash123",
            tipo_id_sugerido=None,
            tipo_nome_sugerido=None,
        ),
    )
    monkeypatch.setattr(materiais_router.catalog_repo, "list_tipos_material", lambda q=None: [])
    monkeypatch.setattr(
        materiais_router.repo,
        "find_ia_run",
        lambda mid, h: {"resposta": "cache"},
    )
    monkeypatch.setattr(materiais_router.repo, "insert_ia_run", lambda **k: {"id": 1})
    monkeypatch.setattr(materiais_router.repo, "set_descricao_ia", lambda mid, desc: mat)

    files = {"imagens": ("foto.jpg", io.BytesIO(b"x"), "image/jpeg")}
    response = client.post("/api/acba/1/materiais/10/descrever", files=files)
    assert response.status_code == 200
    assert response.json()["cache_hit"] is True
    assert response.json()["descricao"] == "cache"


def test_descrever_material_gemini_error(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    mat = _material()

    class FakeAcbaService:
        def assert_can_write_materiais(self, acba_id, user):
            return None

    class FakeMaterialService:
        def get(self, material_id):
            return mat

    monkeypatch.setattr(materiais_router, "acba_service", FakeAcbaService())
    monkeypatch.setattr(materiais_router, "material_service", FakeMaterialService())
    monkeypatch.setattr(
        materiais_router,
        "descrever_material",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    monkeypatch.setattr(materiais_router.catalog_repo, "list_tipos_material", lambda q=None: [])

    files = {"imagens": ("foto.jpg", io.BytesIO(b"x"), "image/jpeg")}
    response = client.post("/api/acba/1/materiais/10/descrever", files=files)
    assert response.status_code == 503


def test_revisar_wrong_acba(client, authenticated_as, monkeypatch):
    authenticated_as(_delegado())

    class FakeAcbaService:
        def assert_can_write_materiais(self, acba_id, user):
            return None

    class FakeMaterialService:
        def get(self, material_id):
            return _material(acba_id=99)

    monkeypatch.setattr(materiais_router, "acba_service", FakeAcbaService())
    monkeypatch.setattr(materiais_router, "material_service", FakeMaterialService())

    response = client.post(
        "/api/acba/1/materiais/10/revisar",
        json={"descricao": "Revisado"},
    )
    assert response.status_code == 404


def test_material_wrong_acba_returns_404(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())

    class FakeAcbaService:
        def get_by_id(self, acba_id, user):
            return type("R", (), {"equipe_id": 1, "pdf_gerado_at": None})()

        def assert_can_write_materiais(self, acba_id, user):
            return type("R", (), {"equipe_id": 1, "pdf_gerado_at": None})()

    class FakeMaterialService:
        def get(self, material_id):
            return _material(acba_id=99)

    monkeypatch.setattr(materiais_router, "acba_service", FakeAcbaService())
    monkeypatch.setattr(materiais_router, "material_service", FakeMaterialService())

    response = client.get("/api/acba/1/materiais/10")
    assert response.status_code == 404
