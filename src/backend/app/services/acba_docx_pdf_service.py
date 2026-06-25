"""Renderiza o ACBA em DOCX (via docxtpl) e converte em PDF com LibreOffice."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - usado apenas com comando fixo do LibreOffice, sem shell
import tempfile

from docxtpl import DocxTemplate

from app.acba_schemas import AcbaDetail
from app.config import settings
from app.services.acba_pdf_context import _format_senha_docx, build_context


def _find_libreoffice() -> str:
    cmd = (settings.libreoffice_cmd or "").strip()
    if cmd:
        resolved = shutil.which(cmd) or (cmd if os.path.isabs(cmd) else None)
    else:
        resolved = shutil.which("soffice") or shutil.which("libreoffice")
    if not resolved or not os.path.isfile(resolved):
        raise RuntimeError(
            "Binário do LibreOffice (soffice/libreoffice) não encontrado no PATH "
            "nem em LIBREOFFICE_CMD. Instale o LibreOffice ou ajuste a configuração."
        )
    return resolved


def render_acba_pdf_bytes(detail: AcbaDetail) -> bytes:
    template_path = settings.acba_docx_template_path
    if not os.path.isfile(template_path):
        raise FileNotFoundError(
            f"Template DOCX não encontrado em {template_path}. "
            "Coloque o modelo oficial (com placeholders) ou gere o template padrão."
        )

    doc = DocxTemplate(template_path)
    context = build_context(
        detail,
        senha_formatter=lambda m: _format_senha_docx(m, doc),
    )
    doc.render(context)

    tmpdir = tempfile.mkdtemp(prefix="acba_pdf_")
    try:
        docx_path = os.path.join(tmpdir, "acba_preenchido.docx")
        doc.save(docx_path)

        soffice = _find_libreoffice()
        env = {**os.environ, "HOME": tmpdir}
        subprocess.run(  # nosec B603 - args fixos e binário resolvido; sem shell e sem entrada do usuário
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
