#!/usr/bin/env python3
"""Gera src/backend/templates/acba_template.docx com a sintaxe Jinja do docxtpl.

Substitua o arquivo gerado pelo DOCX oficial da PCDF, mantendo os mesmos
marcadores e os blocos de loop em `{% for m in materiais_informatica %}` /
`{% for m in materiais_geral %}` nas tabelas correspondentes.
"""

from pathlib import Path

from docx import Document
from docx.shared import Pt


def _add_field_row(doc: Document, label: str, value: str) -> None:
    doc.add_paragraph(f"{label}: {value}")


def _add_table(doc: Document, headers: list[str], jinja_for: str, jinja_cells: list[str]) -> None:
    table = doc.add_table(rows=2, cols=len(headers))
    table.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    table.rows[1].cells[0].text = "{%tr " + jinja_for + " %}"
    for i, cell_expr in enumerate(jinja_cells):
        table.rows[1].cells[i].text = cell_expr
    extra = table.add_row()
    extra.cells[0].text = "{%tr endfor %}"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "templates" / "acba_template.docx"
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    doc.add_heading("AUTO CIRCUNSTANCIADO DE BUSCA E APREENSÃO", level=0)
    doc.add_paragraph(
        "SUBSTITUIR ESTE DOCUMENTO PELO MODELO OFICIAL DA PCDF, "
        "PRESERVANDO OS PLACEHOLDERS {{...}} E BLOCOS {% ... %} ABAIXO."
    )

    p = doc.add_paragraph()
    run = p.add_run("Processo: ")
    run.bold = True
    p.add_run("{{ processo_numero }} (Prot.: {{ protocolo_numero }})")

    pairs = [
        ("Unidade responsável", "{{ unidade }}"),
        ("Delegacia", "{{ delegacia }}"),
        ("Cidade/UF", "{{ cidade }} — {{ uf_sigla }}/{{ uf_nome }}"),
        ("Data / hora", "{{ data_lavratura }} {{ hora_lavratura }}"),
        ("Autoridade policial", "{{ delegado }} (Mat. {{ delegado_matricula }})"),
        ("Escrivão", "{{ escrivao }}"),
        ("Tipo / nº procedimento", "{{ tipo_procedimento }} — {{ procedimento_numero }}"),
        ("Fundamento legal", "{{ fundamento_legal }}"),
        ("Endereço da busca", "{{ endereco_busca }}"),
        ("Alvo", "{{ alvo_busca }}"),
        ("Equipe", "{{ equipe_numero }} — {{ equipe_nome }}"),
    ]
    for label, val in pairs:
        _add_field_row(doc, label, val)

    doc.add_heading("Equipe operacional", level=2)
    doc.add_paragraph("{{ equipe_texto }}")

    doc.add_heading(
        "DESCRIÇÃO DO MATERIAL DE INFORMÁTICA APREENDIDO E EXATA POSIÇÃO EM QUE SE DEU A LOCALIZAÇÃO",
        level=2,
    )
    _add_table(
        doc,
        headers=["ITEM", "DESCRIÇÃO + LOCALIZAÇÃO", "SENHA"],
        jinja_for="for m in materiais_informatica",
        jinja_cells=[
            "{{ m.item_num }}",
            "{{ m.descricao }}\n{% if m.localizacao %}Local: {{ m.localizacao }}{% endif %}",
            "{{ m.senha_render }}",
        ],
    )

    doc.add_heading(
        "DESCRIÇÃO DO MATERIAL APREENDIDO E EXATA POSIÇÃO EM QUE SE DEU A LOCALIZAÇÃO",
        level=2,
    )
    _add_table(
        doc,
        headers=["ITEM", "DESCRIÇÃO + LOCALIZAÇÃO"],
        jinja_for="for m in materiais_geral",
        jinja_cells=[
            "{{ m.item_num }}",
            "{{ m.descricao }}\n{% if m.localizacao %}Local: {{ m.localizacao }}{% endif %}",
        ],
    )

    doc.add_heading("Testemunhas", level=2)
    doc.add_paragraph("{{ testemunhas_texto }}")

    doc.add_heading("Observações", level=2)
    doc.add_paragraph("{{ observacoes }}")

    doc.add_paragraph("")
    doc.add_paragraph("____________________________________")
    doc.add_paragraph("{{ assinatura_responsavel }}")

    style = doc.styles["Normal"]
    style.font.size = Pt(11)
    doc.save(out)
    print(f"Gerado: {out}")


if __name__ == "__main__":
    main()
