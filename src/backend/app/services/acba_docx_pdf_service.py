"""Renderiza o ACBA em DOCX (via docxtpl) e converte em PDF com LibreOffice.

O template oficial precisa usar a sintaxe Jinja do docxtpl. Veja
`templates/README.md` para a lista de variáveis e os blocos de loop esperados.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
from typing import Any

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm

from app.acba_schemas import AcbaDetail
from app.config import settings
from app.services.pattern_image import render_pattern_png


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


def _format_senha(m: dict, doc: DocxTemplate) -> Any:
    """Devolve um valor renderizável para a célula SENHA do template.

    - texto       → string com a senha
    - padrao      → InlineImage do PNG do padrão
    - biometria   → texto fixo + observação
    - nenhuma     → '—'
    - desconhecida → 'Desconhecida'
    """
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


def _agentes_lines(detail: AcbaDetail) -> str:
    if not detail.agentes_equipe:
        return "—"
    return "\n".join(
        f"{i}. {m.nome} — Mat.: {m.matricula} — Função: {m.funcao_padrao or '—'}"
        for i, m in enumerate(detail.agentes_equipe, start=1)
    )


def _testemunhas_lines(detail: AcbaDetail) -> str:
    """Texto multilinhas para o campo `{{ testemunhas_texto }}` no template.

    Cada testemunha aparece com sua qualificação completa. Testemunhas de
    arrombamento (Art. 245 §4º do CPP) carregam um campo extra de observações.
    """
    if not detail.testemunhas:
        return "—"
    lines: list[str] = []
    for i, t in enumerate(detail.testemunhas, start=1):
        head = (
            f"{i}. {t.get('nome','')} — CPF: {t.get('cpf','—')} "
            f"— RG: {t.get('rg','—')}"
        )
        if t.get("tipo") == "arrombamento":
            head += " — TESTEMUNHA DE ARROMBAMENTO (Art. 245 §4º CPP)"
        lines.append(head)
        lines.append(f"   Filiação: {t.get('filiacao','—')}")
        lines.append(f"   Endereço: {t.get('endereco','—')}")
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
    """Separa as testemunhas em (gerais, arrombamento) para uso em tabelas."""
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
    """Bloco do morador presente. Quando o morador estava ausente (§4º),
    todos os campos vão como '—' e a flag `morador_presente` fica False."""
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


def build_context(detail: AcbaDetail, doc: DocxTemplate) -> dict[str, Any]:
    informatica, geral = _split_materiais(detail)
    testemunhas_gerais, testemunhas_arrombamento = _testemunhas_split(detail)

    def _enrich(m: dict) -> dict:
        out = dict(m)
        out["senha_render"] = _format_senha(m, doc)
        return out

    return {
        **_morador_context(detail),
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
        "testemunhas_texto": _testemunhas_lines(detail),
        "testemunhas_gerais": testemunhas_gerais,
        "testemunhas_arrombamento": testemunhas_arrombamento,
        "observacoes": detail.observacoes or "—",
        "assinatura_responsavel": detail.assinatura_responsavel,
        # Art. 245 §§ 2º, 3º e 4º do CPP — flags + observações.
        # No template DOCX use `Sim`/`Não` para os booleans:
        #   {% if arrombamento_245_2 %}Sim{% else %}Não{% endif %}
        "arrombamento_245_2": detail.arrombamento_245_2,
        "arrombamento_245_2_obs": detail.arrombamento_245_2_obs or "—",
        "forca_coisas_245_3": detail.forca_coisas_245_3,
        "forca_coisas_245_3_obs": detail.forca_coisas_245_3_obs or "—",
        "morador_ausente_245_4": detail.morador_ausente_245_4,
        "morador_ausente_245_4_obs": detail.morador_ausente_245_4_obs or "—",
        "materiais_informatica": [_enrich(m) for m in informatica],
        "materiais_geral": [_enrich(m) for m in geral],
    }


def _find_libreoffice() -> str:
    cmd = (settings.libreoffice_cmd or "").strip()
    if cmd:
        return cmd
    return shutil.which("soffice") or shutil.which("libreoffice") or "soffice"


def render_acba_pdf_bytes(detail: AcbaDetail) -> bytes:
    template_path = settings.acba_docx_template_path
    if not os.path.isfile(template_path):
        raise FileNotFoundError(
            f"Template DOCX não encontrado em {template_path}. "
            "Coloque o modelo oficial (com placeholders) ou gere o template padrão."
        )

    doc = DocxTemplate(template_path)
    context = build_context(detail, doc)
    doc.render(context)

    tmpdir = tempfile.mkdtemp(prefix="acba_pdf_")
    try:
        docx_path = os.path.join(tmpdir, "acba_preenchido.docx")
        doc.save(docx_path)

        soffice = _find_libreoffice()
        env = {**os.environ, "HOME": "/tmp"}
        subprocess.run(
            [
                soffice,
                "--headless",
                "--nologo",
                "--nofirststartwizard",
                "--convert-to",
                "pdf",
                "--outdir",
                tmpdir,
                docx_path,
            ],
            check=True,
            env=env,
            timeout=180,
            capture_output=True,
            text=True,
        )
        base = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(tmpdir, f"{base}.pdf")
        if not os.path.isfile(pdf_path):
            raise RuntimeError("LibreOffice não gerou o arquivo PDF.")
        with open(pdf_path, "rb") as handle:
            return handle.read()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
