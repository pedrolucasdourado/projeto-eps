from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from app.routers import acba


pytestmark = pytest.mark.integration


def test_list_acba_uses_authenticated_user_and_filters(
    monkeypatch,
    client,
    authenticated_as,
    delegado_user,
):
    authenticated_as(delegado_user)
    captured = {}

    class FakeAcbaService:
        def list_all(self, *, user, tipo_material_id=None):
            captured["user_id"] = user.id
            captured["tipo_material_id"] = tipo_material_id
            return [
                {
                    "id": 1,
                    "processo_numero": "PROC-001",
                    "protocolo_numero": "ACBA-001",
                    "delegacia_nome": "Delegacia Teste",
                    "data_lavratura": date(2026, 5, 26),
                    "alvo_busca": "Alvo Teste",
                    "delegado_nome": "Delegado Teste",
                    "equipe_numero": "EQ-1",
                    "equipe_nome": "Equipe Alfa",
                    "created_at": datetime(2026, 5, 26, tzinfo=timezone.utc),
                    "materiais_pendentes_revisao": 0,
                    "pdf_gerado_at": None,
                }
            ]

    monkeypatch.setattr(acba, "service", FakeAcbaService())

    response = client.get("/api/acba/?tipo_material_id=3")

    assert response.status_code == 200
    assert captured == {"user_id": delegado_user.id, "tipo_material_id": 3}
    body = response.json()
    assert body[0]["protocolo_numero"] == "ACBA-001"
    assert body[0]["equipe_nome"] == "Equipe Alfa"
