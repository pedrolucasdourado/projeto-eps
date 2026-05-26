from __future__ import annotations

import pytest

from app.services import gemini_vision_service as service


pytestmark = pytest.mark.unit


def test_hash_images_is_stable_and_includes_extra_context():
    images = [b"image-one", b"image-two"]

    first = service._hash_images(images, extra="tipos")
    second = service._hash_images(images, extra="tipos")
    different_extra = service._hash_images(images, extra="outros-tipos")

    assert first == second
    assert first != different_extra


def test_parse_json_resposta_extracts_markdown_json_and_type_name():
    tipos = [{"id": 1, "nome": "Celular"}, {"id": 2, "nome": "Notebook"}]
    raw = '```json\n{"tipo_id": 2, "descricao": "Notebook preto"}\n```'

    descricao, tipo_id, tipo_nome = service._parse_json_resposta(raw, tipos)

    assert descricao == "Notebook preto"
    assert tipo_id == 2
    assert tipo_nome == "Notebook"


def test_parse_json_resposta_ignores_unknown_type_id():
    tipos = [{"id": 1, "nome": "Celular"}]

    descricao, tipo_id, tipo_nome = service._parse_json_resposta(
        '{"tipo_id": 999, "descricao": "Item sem tipo"}',
        tipos,
    )

    assert descricao == "Item sem tipo"
    assert tipo_id is None
    assert tipo_nome is None


def test_descrever_material_requires_images():
    with pytest.raises(ValueError) as exc:
        service.descrever_material([])

    assert "imagem" in str(exc.value)
