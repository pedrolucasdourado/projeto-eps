#!/usr/bin/env python3
"""Gera src/backend/templates/acba_template.docx com marcadores {{...}} para preenchimento via API.

Substitua o arquivo gerado pelo DOCX oficial da PCDF, mantendo os mesmos marcadores
onde couber, ou ajuste build_placeholder_map em app/services/acba_docx_pdf_service.py.
"""

from pathlib import Path

from docx import Document


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "templates" / "acba_template.docx"
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    doc.add_heading("AUTO CIRCUNSTANCIADO DE BUSCA E ARRECADACAO", level=0)
    doc.add_paragraph(
        "SUBSTITUIR ESTE DOCUMENTO PELO MODELO OFICIAL DA PCDF, "
        "PRESERVANDO OS MARCADORES {{...}} ABAIXO NOS PONTOS CORRESPONDENTES."
    )

    pairs = [
        ("Numero do processo", "{{processo_numero}}"),
        ("Numero do protocolo", "{{protocolo_numero}}"),
        ("Descricao do processo", "{{processo_descricao}}"),
        ("Unidade responsavel", "{{unidade}}"),
        ("Delegacia", "{{delegacia}}"),
        ("Cidade / UF", "{{cidade}} — {{uf_sigla}} / {{uf_nome}}"),
        ("Data / hora lavratura", "{{data_lavratura}} {{hora_lavratura}}"),
        ("Autoridade policial", "{{autoridade}} (Mat. {{autoridade_matricula}})"),
        ("Escrivao", "{{escrivao}}"),
        ("Tipo e numero do procedimento", "{{tipo_procedimento}} — {{procedimento_numero}}"),
        ("Fundamento legal", "{{fundamento_legal}}"),
        ("Endereco da busca", "{{endereco_busca}}"),
        ("Alvo", "{{alvo_busca}}"),
        ("Equipe operacional", "{{equipe_texto}}"),
        ("Objetos arrecadados", "{{objetos_texto}}"),
        ("Testemunhas", "{{testemunhas_texto}}"),
        ("Observacoes", "{{observacoes}}"),
        ("Responsavel pela assinatura", "{{assinatura_responsavel}}"),
    ]
    for label, ph in pairs:
        doc.add_heading(label, level=2)
        doc.add_paragraph(ph)

    doc.add_paragraph("")
    doc.add_paragraph("____________________________________")
    doc.add_paragraph("{{assinatura_responsavel}}")

    doc.save(out)
    print(f"Gerado: {out}")


if __name__ == "__main__":
    main()
