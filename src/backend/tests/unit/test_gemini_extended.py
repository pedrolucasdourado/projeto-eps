from __future__ import annotations

import json

import pytest

from app.services import gemini_vision_service as service


pytestmark = pytest.mark.unit


def test_tipos_to_extra_empty():
    assert service._tipos_to_extra(None) == ""
    assert service._tipos_to_extra([]) == ""


def test_tipos_to_extra_sorted():
    tipos = [{"id": 2, "nome": "B"}, {"id": 1, "nome": "A"}]
    assert service._tipos_to_extra(tipos) == "1:A|2:B"


def test_build_prompt_com_tipos_includes_catalog():
    prompt = service._build_prompt_com_tipos(
        [{"id": 1, "nome": "Celular"}], "foco na tela"
    )
    assert "Celular" in prompt
    assert "foco na tela" in prompt
    assert "tipo_id" in prompt


def test_parse_json_resposta_invalid_json():
    desc, tipo_id, tipo_nome = service._parse_json_resposta("texto puro", [])
    assert desc == "texto puro"
    assert tipo_id is None


def test_parse_json_resposta_invalid_type_id():
    desc, tipo_id, tipo_nome = service._parse_json_resposta(
        '{"tipo_id": "x", "descricao": "Item"}', [{"id": 1, "nome": "A"}]
    )
    assert desc == "Item"
    assert tipo_id is None


def test_descrever_material_missing_api_key(monkeypatch):
    monkeypatch.setattr(service.settings, "gemini_api_key", "")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        service.descrever_material([b"img"], mime_types=["image/jpeg"])


def _patch_genai_client(monkeypatch, response_text: str):
    class FakeUsage:
        total_token_count = 42

    class FakeResponse:
        text = response_text
        usage_metadata = FakeUsage()

    class FakeModels:
        def generate_content(self, model, contents, config=None):
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    import google.genai as genai_module

    monkeypatch.setattr(genai_module, "Client", lambda api_key: FakeClient())


def test_descrever_material_success(monkeypatch):
    monkeypatch.setattr(service.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(service.settings, "gemini_model", "gemini-test")
    _patch_genai_client(monkeypatch, '{"tipo_id": 1, "descricao": "Celular preto"}')

    result = service.descrever_material(
        [b"img"],
        mime_types=["image/jpeg"],
        tipos_disponiveis=[{"id": 1, "nome": "Celular"}],
    )
    assert result.descricao == "Celular preto"
    assert result.tipo_id_sugerido == 1


def test_descrever_material_empty_response(monkeypatch):
    monkeypatch.setattr(service.settings, "gemini_api_key", "test-key")
    _patch_genai_client(monkeypatch, "")

    with pytest.raises(RuntimeError, match="vazia"):
        service.descrever_material([b"img"])
