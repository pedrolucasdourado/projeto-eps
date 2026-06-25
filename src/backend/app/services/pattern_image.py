"""Gera a imagem do padrão de bloqueio (senha-padrão) no formato esperado pelo
ACBA: 9 pontos numerados em grade 3x3, linhas conectando-os na ordem, seta
indicando a direção e marcação especial no ponto inicial.

Tudo é desenhado em memória com Pillow — não toca disco.
"""

from __future__ import annotations

import math
from io import BytesIO
from typing import cast

from PIL import Image, ImageDraw, ImageFont


def _grid_xy(point: int, padding: int, spacing: int) -> tuple[int, int]:
    """Converte ponto 1..9 (grade 3x3, top-left=1, bottom-right=9) em pixel (x,y)."""
    if not 1 <= point <= 9:
        raise ValueError(f"Ponto fora do intervalo 1..9: {point}")
    idx = point - 1
    col = idx % 3
    row = idx // 3
    return (padding + col * spacing, padding + row * spacing)


def render_pattern_png(
    pontos: list[int],
    size: int = 360,
    *,
    background: tuple[int, int, int] = (255, 255, 255),
    dot_color: tuple[int, int, int] = (110, 110, 120),
    line_color: tuple[int, int, int] = (10, 10, 10),
    arrow_color: tuple[int, int, int] = (0, 90, 200),
    start_color: tuple[int, int, int] = (40, 160, 60),
    label_color: tuple[int, int, int] = (30, 30, 30),
) -> bytes:
    """Renderiza o padrão e devolve PNG em bytes."""
    if not pontos:
        raise ValueError("Sequência de pontos vazia.")

    padding = int(size * 0.16)
    spacing = (size - 2 * padding) // 2
    dot_r = max(6, size // 30)

    img = Image.new("RGB", (size, size), background)
    draw = ImageDraw.Draw(img)

    font: ImageFont.ImageFont
    try:
        font = cast(
            ImageFont.ImageFont,
            ImageFont.truetype("DejaVuSans.ttf", size // 22),
        )
    except OSError:
        font = cast(ImageFont.ImageFont, ImageFont.load_default())

    for n in range(1, 10):
        cx, cy = _grid_xy(n, padding, spacing)
        draw.ellipse(
            (cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r),
            outline=dot_color,
            width=2,
        )
        draw.text(
            (cx - dot_r * 1.6, cy + dot_r + 2),
            str(n),
            fill=label_color,
            font=font,
        )

    coords = [_grid_xy(p, padding, spacing) for p in pontos]
    for (x1, y1), (x2, y2) in zip(coords[:-1], coords[1:]):
        draw.line((x1, y1, x2, y2), fill=line_color, width=4)
        _arrow_head(draw, (x1, y1), (x2, y2), arrow_color, length=max(12, dot_r * 1.6))

    sx, sy = coords[0]
    draw.ellipse(
        (sx - dot_r * 1.6, sy - dot_r * 1.6, sx + dot_r * 1.6, sy + dot_r * 1.6),
        outline=start_color,
        width=3,
    )
    draw.text(
        (sx - dot_r * 1.6, sy - dot_r * 3.2),
        "início",
        fill=start_color,
        font=font,
    )

    for ordem, (x, y) in enumerate(coords, start=1):
        draw.text(
            (x + dot_r + 2, y - dot_r * 1.8),
            f"{ordem}º",
            fill=label_color,
            font=font,
        )

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _arrow_head(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: tuple[int, int, int],
    length: float = 14,
    width: int = 3,
) -> None:
    """Desenha uma seta na metade do segmento end-start, apontando para `end`."""
    x1, y1 = start
    x2, y2 = end
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    angle = math.atan2(y2 - y1, x2 - x1)
    ax = mx + math.cos(angle) * (length * 0.5)
    ay = my + math.sin(angle) * (length * 0.5)
    bx = mx - math.cos(angle + 2.6) * length
    by = my - math.sin(angle + 2.6) * length
    cx = mx - math.cos(angle - 2.6) * length
    cy = my - math.sin(angle - 2.6) * length
    draw.line((bx, by, ax, ay), fill=color, width=width)
    draw.line((cx, cy, ax, ay), fill=color, width=width)
