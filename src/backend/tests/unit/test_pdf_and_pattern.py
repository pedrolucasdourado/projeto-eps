from __future__ import annotations

import pytest

from app.acba_schemas import AcbaDetail
from app.services.acba_pdf_context import build_context, _format_senha_html
from app.services.pattern_image import render_pattern_png, _grid_xy
from tests.helpers.sample_data import acba_detail_dict


pytestmark = pytest.mark.unit


def test_grid_xy_valid_points():
    x, y = _grid_xy(1, 10, 50)
    assert isinstance(x, int) and isinstance(y, int)


def test_grid_xy_invalid_point():
    with pytest.raises(ValueError):
        _grid_xy(10, 10, 50)


def test_render_pattern_png_returns_bytes():
    png = render_pattern_png([1, 2, 5, 8], size=120)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_pattern_png_empty_raises():
    with pytest.raises(ValueError):
        render_pattern_png([])


def test_format_senha_html_texto():
    html = _format_senha_html(
        {"informatica": {"senha_tipo": "texto", "senha_texto": "abc"}}
    )
    assert "abc" in str(html)


def test_format_senha_html_padrao():
    html = _format_senha_html(
        {"informatica": {"senha_tipo": "padrao", "senha_padrao_pontos": [1, 2, 3]}}
    )
    assert "Padrão" in str(html)


def test_format_senha_html_biometria():
    html = _format_senha_html(
        {"informatica": {"senha_tipo": "biometria", "senha_observacao": "digital"}}
    )
    assert "Biometria" in str(html)


def test_build_context_contains_core_fields():
    detail = AcbaDetail.model_validate(acba_detail_dict())
    ctx = build_context(detail, senha_formatter=lambda m: "SENHA")
    assert ctx["processo_numero"] == detail.processo_numero
    assert ctx["delegado"] == detail.delegado_nome
    assert len(ctx["materiais_informatica"]) >= 1
    assert len(ctx["materiais_geral"]) >= 1
    assert ctx["testemunhas_gerais"]
    assert ctx["testemunhas_arrombamento"]


def test_format_senha_html_desconhecida():
    html = _format_senha_html({"informatica": {"senha_tipo": "desconhecida"}})
    assert "Desconhecida" in str(html)


def test_format_senha_html_nenhuma():
    html = _format_senha_html({"informatica": {"senha_tipo": "nenhuma"}})
    assert "—" in str(html)


def test_format_senha_docx_texto():
    from app.services.acba_pdf_context import _format_senha_docx

    result = _format_senha_docx(
        {"informatica": {"senha_tipo": "texto", "senha_texto": "abc"}},
        doc=object(),
    )
    assert result == "abc"


def test_format_senha_docx_biometria():
    from app.services.acba_pdf_context import _format_senha_docx

    result = _format_senha_docx(
        {"informatica": {"senha_tipo": "biometria", "senha_observacao": "digital"}},
        doc=object(),
    )
    assert "Biometria" in str(result)


def test_build_context_with_arrombamento_flags():
    detail = AcbaDetail.model_validate(
        acba_detail_dict(
            arrombamento_245_2=True,
            arrombamento_245_2_obs="Porta forçada",
            forca_coisas_245_3=True,
            forca_coisas_245_3_obs="Objeto pesado",
        )
    )
    ctx = build_context(detail, senha_formatter=lambda m: "SENHA")
    assert ctx["arrombamento_245_2"] is True
    assert ctx["forca_coisas_245_3"] is True

    detail = AcbaDetail.model_validate(
        acba_detail_dict(
            morador_ausente_245_4=True,
            morador_ausente_245_4_obs="Morador viajando",
            morador_nome="",
            testemunhas=[
                {
                    "tipo": "arrombamento",
                    "nome": "Vizinho",
                    "cpf": "111",
                    "rg": "1",
                    "filiacao": "F",
                    "endereco": "Rua",
                    "arrombamento": {"observacoes": "viu"},
                }
            ],
        )
    )
    ctx = build_context(detail, senha_formatter=_format_senha_html)
    assert ctx["morador_presente"] is False
