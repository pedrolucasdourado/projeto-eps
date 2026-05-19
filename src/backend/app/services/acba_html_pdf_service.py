"""Renderiza o ACBA em HTML (Jinja2) e converte em PDF com WeasyPrint."""

from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.acba_schemas import AcbaDetail
from app.config import settings
from app.services.acba_pdf_context import _format_senha_html, build_context


def _template_dir() -> Path:
    return Path(settings.acba_html_template_path).parent


def _render_html(detail: AcbaDetail) -> str:
    template_dir = _template_dir()
    template_name = Path(settings.acba_html_template_path).name
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)
    context = build_context(detail, senha_formatter=_format_senha_html)
    return template.render(**context)


def render_acba_pdf_bytes(detail: AcbaDetail) -> bytes:
    template_path = settings.acba_html_template_path
    if not os.path.isfile(template_path):
        raise FileNotFoundError(
            f"Template HTML não encontrado em {template_path}."
        )

    html = _render_html(detail)
    base_url = str(_template_dir())
    return HTML(string=html, base_url=base_url).write_pdf()
