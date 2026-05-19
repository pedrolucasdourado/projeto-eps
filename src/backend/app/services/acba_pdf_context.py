"""Contexto Jinja compartilhado entre exportação DOCX e HTML/PDF."""

from __future__ import annotations

import base64
import io
from typing import Any, Callable

from markupsafe import Markup

from app.acba_schemas import AcbaDetail
from app.services.pattern_image import render_pattern_png

_MESES_PT = (
    "",
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def _split_materiais(detail: AcbaDetail) -> tuple[list[dict], list[dict]]:
    informatica: list[dict] = []
    geral: list[dict] = []
    for m in detail.materiais:
        if m.get("categoria_docx") == "informatica":
            informatica.append(m)
        else:
            geral.append(m)
    informatica.sort(key=lambda x: x.get("item_num", 0))
    geral.sort(key=lambda x: x.get("item_num", 0))
    return informatica, geral


def _format_senha_docx(m: dict, doc: Any) -> Any:
    from docxtpl import InlineImage
    from docx.shared import Mm

    inf = m.get("informatica") or {}
    tipo = inf.get("senha_tipo") or "nenhuma"
    if tipo == "texto":
        return inf.get("senha_texto") or "—"
    if tipo == "padrao":
        pontos = inf.get("senha_padrao_pontos") or []
        try:
            png = render_pattern_png(pontos)
            return InlineImage(doc, io.BytesIO(png), width=Mm(32))
        except Exception:
            return "Padrão: " + " → ".join(str(p) for p in pontos)
    if tipo == "biometria":
        extra = inf.get("senha_observacao") or ""
        return f"Biometria {('— ' + extra) if extra else ''}".strip()
    if tipo == "desconhecida":
        return "Desconhecida"
    return "—"


def _format_senha_html(m: dict) -> str | Markup:
    inf = m.get("informatica") or {}
    tipo = inf.get("senha_tipo") or "nenhuma"
    if tipo == "texto":
        return inf.get("senha_texto") or "—"
    if tipo == "padrao":
        pontos = inf.get("senha_padrao_pontos") or []
        try:
            png = render_pattern_png(pontos, size=240)
            b64 = base64.b64encode(png).decode("ascii")
            return Markup(
                f'<img class="senha-padrao" alt="Padrão de desbloqueio" '
                f'src="data:image/png;base64,{b64}" />'
            )
        except Exception:
            return "Padrão: " + " → ".join(str(p) for p in pontos)
    if tipo == "biometria":
        extra = inf.get("senha_observacao") or ""
        return f"Biometria {('— ' + extra) if extra else ''}".strip()
    if tipo == "desconhecida":
        return "Desconhecida"
    return "—"


def _material_descricao(m: dict) -> str:
    desc = (m.get("descricao") or "").strip()
    loc = (m.get("localizacao") or "").strip()
    if loc:
        return f"{desc} — Local: {loc}" if desc else f"Local: {loc}"
    return desc or "—"


def _agentes_lines(detail: AcbaDetail) -> str:
    if not detail.agentes_equipe:
        return "—"
    return "\n".join(
        f"{i}. {m.nome} — Mat.: {m.matricula} — Função: {m.funcao_padrao or '—'}"
        for i, m in enumerate(detail.agentes_equipe, start=1)
    )


def _agentes_narrativa(detail: AcbaDetail) -> str:
    """Frase para o parágrafo introdutório do auto oficial."""
    if not detail.agentes_equipe:
        return "—"
    partes = [
        f"{m.nome}, matrícula {m.matricula or '—'}"
        for m in detail.agentes_equipe
    ]
    if len(partes) == 1:
        return partes[0]
    if len(partes) == 2:
        return f"{partes[0]} e {partes[1]}"
    return ", ".join(partes[:-1]) + f" e {partes[-1]}"


def _testemunhas_lines(detail: AcbaDetail) -> str:
    if not detail.testemunhas:
        return "—"
    lines: list[str] = []
    for i, t in enumerate(detail.testemunhas, start=1):
        head = (
            f"{i}. {t.get('nome', '')} — CPF: {t.get('cpf', '—')} "
            f"— RG: {t.get('rg', '—')}"
        )
        if t.get("tipo") == "arrombamento":
            head += " — TESTEMUNHA DE ARROMBAMENTO (Art. 245 §4º CPP)"
        lines.append(head)
        lines.append(f"   Filiação: {t.get('filiacao', '—')}")
        lines.append(f"   Endereço: {t.get('endereco', '—')}")
        if t.get("tipo") == "geral":
            if t.get("cidade"):
                lines.append(f"   Cidade: {t['cidade']}")
            if t.get("telefone"):
                lines.append(f"   Telefone: {t['telefone']}")
        else:
            arr = t.get("arrombamento") or {}
            obs = (arr.get("observacoes") or "").strip()
            if obs:
                lines.append(f"   Obs.: {obs}")
    return "\n".join(lines)


def _testemunhas_split(
    detail: AcbaDetail,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    gerais: list[dict[str, Any]] = []
    arrombamento: list[dict[str, Any]] = []
    for t in detail.testemunhas:
        base = {
            "nome": t.get("nome", ""),
            "cpf": t.get("cpf", "—"),
            "rg": t.get("rg", "—"),
            "filiacao": t.get("filiacao", "—"),
            "endereco": t.get("endereco", "—"),
        }
        if t.get("tipo") == "arrombamento":
            extras = t.get("arrombamento") or {}
            arrombamento.append(
                {**base, "observacoes": (extras.get("observacoes") or "—")}
            )
        else:
            gerais.append(
                {
                    **base,
                    "cidade": t.get("cidade") or "—",
                    "telefone": t.get("telefone") or "—",
                }
            )
    return gerais, arrombamento


def _morador_context(detail: AcbaDetail) -> dict[str, Any]:
    if detail.morador_ausente_245_4 or not detail.morador_nome.strip():
        return {
            "morador_presente": False,
            "morador_nome": "—",
            "morador_cpf": "—",
            "morador_rg": "—",
            "morador_filiacao": "—",
            "morador_telefone": "—",
        }
    return {
        "morador_presente": True,
        "morador_nome": detail.morador_nome,
        "morador_cpf": detail.morador_cpf or "—",
        "morador_rg": detail.morador_rg or "—",
        "morador_filiacao": detail.morador_filiacao or "—",
        "morador_telefone": detail.morador_telefone or "—",
    }


def _date_context(detail: AcbaDetail) -> dict[str, str]:
    d = detail.data_lavratura
    mes = _MESES_PT[d.month] if 1 <= d.month <= 12 else str(d.month)
    return {
        "data_dia": f"{d.day:02d}",
        "data_mes_nome": mes,
        "data_ano": str(d.year),
    }


def build_context(
    detail: AcbaDetail,
    *,
    senha_formatter: Callable[[dict], Any],
) -> dict[str, Any]:
    informatica, geral = _split_materiais(detail)
    testemunhas_gerais, testemunhas_arrombamento = _testemunhas_split(detail)

    def _enrich(m: dict) -> dict:
        out = dict(m)
        out["descricao_completa"] = _material_descricao(m)
        out["senha_render"] = senha_formatter(m)
        return out

    agentes = list(detail.agentes_equipe)
    return {
        **_morador_context(detail),
        **_date_context(detail),
        "processo_numero": detail.processo_numero,
        "protocolo_numero": detail.protocolo_numero,
        "processo_descricao": detail.processo_descricao or "—",
        "unidade": detail.unidade_nome,
        "delegacia": detail.delegacia_nome,
        "cidade": detail.cidade_nome,
        "uf_sigla": detail.uf_sigla,
        "uf_nome": detail.uf_nome,
        "data_lavratura": detail.data_lavratura.strftime("%d/%m/%Y"),
        "hora_lavratura": detail.hora_lavratura.strftime("%H:%M"),
        "delegado": detail.delegado_nome,
        "delegado_matricula": detail.delegado_matricula or "—",
        "autoridade": detail.delegado_nome,
        "autoridade_matricula": detail.delegado_matricula or "—",
        "escrivao": detail.escrivao_nome,
        "tipo_procedimento": detail.tipo_procedimento_nome,
        "procedimento_numero": detail.procedimento_numero,
        "fundamento_legal": detail.fundamento_legal,
        "endereco_busca": detail.endereco_busca,
        "alvo_busca": detail.alvo_busca,
        "nome_vara_criminal": detail.nome_vara_criminal or "—",
        "nome_juiz": detail.nome_juiz or "—",
        "equipe_numero": detail.equipe_numero,
        "equipe_nome": detail.equipe_nome or "—",
        "equipe_texto": _agentes_lines(detail),
        "agentes_narrativa": _agentes_narrativa(detail),
        "agentes_equipe": agentes,
        "agente_1": agentes[0] if len(agentes) > 0 else None,
        "agente_2": agentes[1] if len(agentes) > 1 else None,
        "testemunhas_texto": _testemunhas_lines(detail),
        "testemunhas_gerais": testemunhas_gerais,
        "testemunhas_arrombamento": testemunhas_arrombamento,
        "observacoes": detail.observacoes or "—",
        "assinatura_responsavel": detail.assinatura_responsavel,
        "arrombamento_245_2": detail.arrombamento_245_2,
        "arrombamento_245_2_obs": detail.arrombamento_245_2_obs or "—",
        "forca_coisas_245_3": detail.forca_coisas_245_3,
        "forca_coisas_245_3_obs": detail.forca_coisas_245_3_obs or "—",
        "morador_ausente_245_4": detail.morador_ausente_245_4,
        "morador_ausente_245_4_obs": detail.morador_ausente_245_4_obs or "—",
        "materiais_informatica": [_enrich(m) for m in informatica],
        "materiais_geral": [_enrich(m) for m in geral],
    }
