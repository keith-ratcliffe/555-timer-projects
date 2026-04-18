#!/usr/bin/env python3
"""Generate a single-page PDF from PARTS.md.

Usage:
    python3 scripts/generate_parts_pdf.py

The PDF is written to docs/Parts.pdf.
"""

import io
import re
import sys
from pathlib import Path

from PIL import Image as PILImage, ImageOps
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

REPO_ROOT = Path(__file__).parent.parent
PARTS_MD = REPO_ROOT / 'PARTS.md'
OUT_PATH = REPO_ROOT / 'docs' / 'Parts.pdf'

PAGE_W, PAGE_H = letter
MARGIN_H = 0.5 * inch
MARGIN_V = inch
USABLE_W = PAGE_W - 2 * MARGIN_H
USABLE_H = PAGE_H - 2 * MARGIN_V

_IMG_MAX_PX = 1200
_IMG_JPEG_Q = 85
_IMG_SPACING = 8  # points between images


def _parse_image_paths(md_text):
    """Return a list of relative image paths found in the Markdown."""
    return re.findall(r'!\[.*?\]\((.+?)\)', md_text)


def _prepare_image(rel_path):
    """Load, EXIF-correct, downsample, and JPEG-encode a source image.

    Returns (BytesIO buffer, px_width, px_height).
    """
    img_path = (REPO_ROOT / rel_path).resolve()
    if not img_path.exists():
        sys.exit(f"Error: image not found: {img_path}")
    pil = ImageOps.exif_transpose(PILImage.open(img_path))
    w, h = pil.size
    if w > _IMG_MAX_PX:
        h = int(h * _IMG_MAX_PX / w)
        w = _IMG_MAX_PX
        pil = pil.resize((w, h), PILImage.LANCZOS)
    buf = io.BytesIO()
    pil.convert('RGB').save(buf, format='JPEG', quality=_IMG_JPEG_Q, optimize=True)
    buf.seek(0)
    return buf, w, h


def generate_pdf():
    md_text = PARTS_MD.read_text(encoding='utf-8')
    rel_paths = _parse_image_paths(md_text)
    if not rel_paths:
        sys.exit("Error: no images found in PARTS.md")

    n = len(rel_paths)
    images = [_prepare_image(p) for p in rel_paths]

    # Divide usable height evenly, leaving gaps between images.
    total_spacing = _IMG_SPACING * (n - 1)
    slot_h = (USABLE_H - total_spacing) / n

    # For each image, compute draw dimensions that fit within (USABLE_W, slot_h).
    draw_dims = []
    for _, px_w, px_h in images:
        draw_w = USABLE_W
        draw_h = px_h * (draw_w / px_w)
        if draw_h > slot_h:
            draw_h = slot_h
            draw_w = px_w * (draw_h / px_h)
        draw_dims.append((draw_w, draw_h))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT_PATH), pagesize=letter)

    # Draw from top to bottom. ReportLab canvas uses bottom-left origin.
    y = PAGE_H - MARGIN_V  # start at top margin
    for i, ((buf, px_w, px_h), (draw_w, draw_h)) in enumerate(zip(images, draw_dims)):
        y -= draw_h
        c.drawImage(
            ImageReader(buf),
            x=MARGIN_H,
            y=y,
            width=draw_w,
            height=draw_h,
            preserveAspectRatio=True,
        )
        if i < n - 1:
            y -= _IMG_SPACING

    c.showPage()
    c.save()
    print(f"PDF written to: {OUT_PATH}")


if __name__ == '__main__':
    generate_pdf()
