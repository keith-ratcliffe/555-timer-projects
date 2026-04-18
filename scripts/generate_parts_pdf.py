#!/usr/bin/env python3
"""Generate a single-page PDF from PARTS.md.

Usage:
    python3 scripts/generate_parts_pdf.py

The PDF is written to docs/Parts.pdf.
"""

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

_IMG_SPACING = 8  # points between images


def _parse_image_paths(md_text):
    return re.findall(r'!\[.*?\]\((.+?)\)', md_text)


def generate_pdf():
    md_text = PARTS_MD.read_text(encoding='utf-8')
    rel_paths = _parse_image_paths(md_text)
    if not rel_paths:
        sys.exit("Error: no images found in PARTS.md")

    # Resolve paths and read native pixel dimensions.
    images = []
    for rel in rel_paths:
        img_path = (REPO_ROOT / rel).resolve()
        if not img_path.exists():
            sys.exit(f"Error: image not found: {img_path}")
        pil = ImageOps.exif_transpose(PILImage.open(img_path))
        pw, ph = pil.size
        # Scale down only if the image is wider than the usable area.
        draw_w = float(pw)
        draw_h = float(ph)
        if draw_w > USABLE_W:
            draw_h = draw_h * (USABLE_W / draw_w)
            draw_w = USABLE_W
        images.append((img_path, draw_w, draw_h))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT_PATH), pagesize=letter)

    # Draw images from top to bottom. Canvas origin is bottom-left.
    y = PAGE_H - MARGIN_V
    for i, (img_path, draw_w, draw_h) in enumerate(images):
        y -= draw_h
        c.drawImage(ImageReader(str(img_path)), x=MARGIN_H, y=y,
                    width=draw_w, height=draw_h)
        if i < len(images) - 1:
            y -= _IMG_SPACING

    c.showPage()
    c.save()
    print(f"PDF written to: {OUT_PATH}")


if __name__ == '__main__':
    generate_pdf()
