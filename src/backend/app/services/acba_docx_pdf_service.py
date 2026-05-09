from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Any

from docx import Document

from app.acba_schemas import AcbaDetail
from app.config import settings


def _replace_in_paragraph(paragraph: Any, mapping: dict[str, str]) -> None:
    text = paragraph.text or ""
    if "{{" not in text:
        return
    new_text = text
    for key, val in mapping.items():
        new_text = new_text.replace(f"{{{{{key}}}}}", val)
    paragraph.text = new_text


def _replace_in_document(doc: Document, mapping: dict[str, str]) -> None:
    for p in doc.paragraphs:
        _replace_in_paragraph(p, mapping)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    _replace_in_paragraph(p, mapping)

    for section in doc.sections:
        for block in (section.header, section.footer):
            for p in block.paragraphs:
                _replace_in_paragraph(p, mapping)


def _lines_agentes(detail: AcbaDetail) -> str:
    if not detail.agentes_equipe:
        return "—"
    lines = []
    for i, m in enumerate(detail.agentes_equipe, start=1):
        func = m.funcao_padrao or "—"
        lines.append(f"{i}. {m.nome} — Mat.: {m.matricula} — Função: {func}")
    return "\n".join(lines)


def _lines_objetos(detail: AcbaDetail) -> str:
    if not detail.objetos_arrecadados:
        return "—"
    lines = []
    for i, o in enumerate(detail.objetos_arrecadados, start=1):
        desc = str(o.get("descricao", ""))
        qtd = str(o.get("quantidade", ""))
        ac = str(o.get("acondicionamento", ""))
        obs = str(o.get("observacao", "") or "")
        lines.append(f"{i}. {desc} — Qtd: {qtd} — Acond.: {ac} — Obs.: {obs or '—'}")
    return "\n".join(lines)


def _lines_testemunhas(detail: AcbaDetail) -> str:
    if not detail.testemunhas:
        return "—"
    lines = []
    for i, t in enumerate(detail.testemunhas, start=1):
        lines.append(
            f"{i}. {t.get('nome','')} — Doc.: {t.get('documento','')} — "
            f"Contato: {t.get('contato','')}"
        )
    return "\n".join(lines)


def build_placeholder_map(detail: AcbaDetail) -> dict[str, str]:
    dt = detail.data_lavratura.strftime("%d/%m/%Y")
    hr = detail.hora_lavratura.strftime("%H:%M")
    delegado_mat = detail.delegado_matricula or "—"
    equipe_label = f"Equipe {detail.equipe_numero}"
    if detail.equipe_nome:
        equipe_label = f"{equipe_label} — {detail.equipe_nome}"
    return {
        "numero_auto": detail.numero_auto,
        "unidade": detail.unidade_nome,
        "delegacia": detail.delegacia_nome,
        "cidade": detail.cidade_nome,
        "uf_sigla": detail.uf_sigla,
        "uf_nome": detail.uf_nome,
        "data_lavratura": dt,
        "hora_lavratura": hr,
        "autoridade": detail.delegado_nome,
        "autoridade_matricula": delegado_mat,
        "delegado": detail.delegado_nome,
        "delegado_matricula": delegado_mat,
        "escrivao": detail.escrivao_nome,
        "tipo_procedimento": detail.tipo_procedimento_nome,
        "procedimento_numero": detail.procedimento_numero,
        "fundamento_legal": detail.fundamento_legal,
        "endereco_busca": detail.endereco_busca,
        "alvo_busca": detail.alvo_busca,
        "assinatura_responsavel": detail.assinatura_responsavel,
        "observacoes": detail.observacoes or "—",
        "equipe_numero": detail.equipe_numero,
        "equipe_nome": detail.equipe_nome or "—",
        "equipe_identificacao": equipe_label,
        "equipe_texto": _lines_agentes(detail),
        "objetos_texto": _lines_objetos(detail),
        "testemunhas_texto": _lines_testemunhas(detail),
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

    mapping = build_placeholder_map(detail)
    doc = Document(template_path)
    _replace_in_document(doc, mapping)

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
