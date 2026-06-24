from __future__ import annotations

import os

import pytest

from app.services import acba_docx_pdf_service, acba_html_pdf_service
from app.acba_schemas import AcbaDetail
from tests.helpers.sample_data import acba_detail_dict


pytestmark = pytest.mark.unit


def test_html_pdf_missing_template(monkeypatch):
    monkeypatch.setattr(acba_html_pdf_service.settings, "acba_html_template_path", "/nope.html")
    detail = AcbaDetail.model_validate(acba_detail_dict())
    with pytest.raises(FileNotFoundError):
        acba_html_pdf_service.render_acba_pdf_bytes(detail)


def test_html_pdf_renders_with_mock_weasyprint(monkeypatch, tmp_path):
    template = tmp_path / "acba_template.html"
    template.write_text("<html><body>{{ processo_numero }}</body></html>", encoding="utf-8")
    monkeypatch.setattr(
        acba_html_pdf_service.settings,
        "acba_html_template_path",
        str(template),
    )

    class FakeHTML:
        def __init__(self, string, base_url):
            self.string = string

        def write_pdf(self):
            return b"%PDF-mock"

    monkeypatch.setattr(acba_html_pdf_service, "HTML", FakeHTML)
    detail = AcbaDetail.model_validate(acba_detail_dict())
    pdf = acba_html_pdf_service.render_acba_pdf_bytes(detail)
    assert pdf.startswith(b"%PDF")


def test_docx_pdf_missing_template(monkeypatch):
    monkeypatch.setattr(
        acba_docx_pdf_service.settings,
        "acba_docx_template_path",
        "/missing.docx",
    )
    detail = AcbaDetail.model_validate(acba_detail_dict())
    with pytest.raises(FileNotFoundError):
        acba_docx_pdf_service.render_acba_pdf_bytes(detail)


def test_docx_pdf_success_with_mocks(monkeypatch, tmp_path):
    template = tmp_path / "model.docx"
    template.write_bytes(b"PK\x03\x04fake-docx")
    monkeypatch.setattr(
        acba_docx_pdf_service.settings,
        "acba_docx_template_path",
        str(template),
    )
    monkeypatch.setattr(
        acba_docx_pdf_service,
        "_find_libreoffice",
        lambda: "/usr/bin/soffice",
    )

    class FakeDoc:
        def render(self, context):
            self.context = context

        def save(self, path):
            with open(path, "wb") as handle:
                handle.write(b"docx")

    monkeypatch.setattr(acba_docx_pdf_service, "DocxTemplate", lambda path: FakeDoc())

    pdf_path_holder = {}

    def fake_run(args, **kwargs):
        outdir = args[args.index("--outdir") + 1]
        docx_path = args[-1]
        base = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(outdir, f"{base}.pdf")
        with open(pdf_path, "wb") as handle:
            handle.write(b"%PDF-docx")
        pdf_path_holder["path"] = pdf_path

    monkeypatch.setattr(acba_docx_pdf_service.subprocess, "run", fake_run)
    detail = AcbaDetail.model_validate(acba_detail_dict())
    pdf = acba_docx_pdf_service.render_acba_pdf_bytes(detail)
    assert pdf.startswith(b"%PDF")


def test_find_libreoffice_from_settings(monkeypatch, tmp_path):
    fake_bin = tmp_path / "soffice"
    fake_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_bin.chmod(0o755)
    monkeypatch.setattr(acba_docx_pdf_service.settings, "libreoffice_cmd", str(fake_bin))
    assert acba_docx_pdf_service._find_libreoffice() == str(fake_bin)

    monkeypatch.setattr(acba_docx_pdf_service.settings, "libreoffice_cmd", "")
    monkeypatch.setattr(acba_docx_pdf_service.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="LibreOffice"):
        acba_docx_pdf_service._find_libreoffice()
