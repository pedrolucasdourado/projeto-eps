from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.acba_schemas import AcbaDetail
from app.routers import acba, auth as auth_router
from app.schemas import UserPublic
from tests.helpers.sample_data import acba_detail_dict


pytestmark = pytest.mark.integration


def _delegado() -> UserPublic:
    return UserPublic(
        id=2,
        email="delegado@example.com",
        full_name="Delegado",
        role="delegado",
        delegado_id=1,
    )


def test_acba_pdf_html_renderer(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    detail = AcbaDetail.model_validate(acba_detail_dict())

    class FakeService:
        def get_by_id(self, record_id, user):
            return detail

        def assert_pdf_pronto(self, record):
            return None

        def mark_pdf_gerado(self, record_id, user, ip=None, user_agent=None):
            return None

    monkeypatch.setattr(acba, "service", FakeService())
    monkeypatch.setattr("app.routers.acba.settings.acba_pdf_renderer", "html")
    monkeypatch.setattr(acba.acba_html_pdf_service, "render_acba_pdf_bytes", lambda d: b"%PDF-fake")

    response = client.get("/api/acba/1/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_acba_pdf_missing_template(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    detail = AcbaDetail.model_validate(acba_detail_dict())

    class FakeService:
        def get_by_id(self, record_id, user):
            return detail

        def assert_pdf_pronto(self, record):
            return None

        def mark_pdf_gerado(self, *a, **k):
            return None

    monkeypatch.setattr(acba, "service", FakeService())
    monkeypatch.setattr(
        acba.acba_html_pdf_service,
        "render_acba_pdf_bytes",
        lambda d: (_ for _ in ()).throw(FileNotFoundError("template")),
    )

    response = client.get("/api/acba/1/pdf")
    assert response.status_code == 503


def test_acba_pdf_generic_error(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    detail = AcbaDetail.model_validate(acba_detail_dict())

    class FakeService:
        def get_by_id(self, record_id, user):
            return detail

        def assert_pdf_pronto(self, record):
            return None

        def mark_pdf_gerado(self, *a, **k):
            return None

    monkeypatch.setattr(acba, "service", FakeService())
    monkeypatch.setattr(
        acba.acba_html_pdf_service,
        "render_acba_pdf_bytes",
        lambda d: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.get("/api/acba/1/pdf")
    assert response.status_code == 500


def test_acba_audit_routes(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    detail = AcbaDetail.model_validate(acba_detail_dict())

    class FakeService:
        def get_by_id(self, record_id, user):
            return detail

    monkeypatch.setattr(acba, "service", FakeService())
    monkeypatch.setattr(acba.audit_repo, "list_for_acba", lambda acba_id: [{"id": 1, "acao": "criado"}])
    monkeypatch.setattr(
        acba.audit_repo,
        "get_entry",
        lambda audit_id: {"id": 1, "acba_id": 1, "acao": "criado"},
    )

    assert client.get("/api/acba/1/auditoria").status_code == 200
    assert client.get("/api/acba/1/auditoria/1").status_code == 200


def test_acba_audit_entry_not_found(monkeypatch, client, authenticated_as):
    authenticated_as(_delegado())
    detail = AcbaDetail.model_validate(acba_detail_dict())

    class FakeService:
        def get_by_id(self, record_id, user):
            return detail

    monkeypatch.setattr(acba, "service", FakeService())
    monkeypatch.setattr(acba.audit_repo, "get_entry", lambda audit_id: None)

    response = client.get("/api/acba/1/auditoria/99")
    assert response.status_code == 404


def test_acba_dependencies_block_agente_edit(client, authenticated_as):
    agente = UserPublic(
        id=5,
        email="agente@example.com",
        full_name="Agente",
        role="agente",
        agente_id=1,
    )
    authenticated_as(agente)
    response = client.put(
        "/api/acba/1",
        json={
            "processo_numero": "0001234-56.2025.8.07.0001",
            "protocolo_numero": "ACBA-001",
            "unidade_id": 1,
            "delegacia_id": 1,
            "cidade_id": 1,
            "data_lavratura": "2026-01-15",
            "hora_lavratura": "10:00:00",
            "tipo_procedimento_id": 1,
            "procedimento_numero": "IPL-001",
            "fundamento_legal": "Mandado judicial válido",
            "endereco_busca": "SQN 100",
            "alvo_busca": "Alvo",
            "assinatura_responsavel": "Delegado",
            "equipe_id": 1,
            "morador_nome": "João",
            "morador_cpf": "12345678901",
            "morador_rg": "1234567",
            "morador_filiacao": "Maria e José",
            "morador_telefone": "61999990000",
            "testemunhas": [],
        },
    )
    assert response.status_code == 403


def test_auth_invalid_token(client, monkeypatch):
    monkeypatch.setattr(auth_router, "get_current_user_from_token", lambda token: None)
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer bad"})
    assert response.status_code == 401
    assert "Token inválido" in response.json()["detail"]
