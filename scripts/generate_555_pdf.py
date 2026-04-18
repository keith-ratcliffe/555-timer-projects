#!/usr/bin/env python3
"""Generate a PDF from 555.md.

Usage:
    python3 scripts/generate_555_pdf.py

The PDF is written to docs/555.pdf.

Margins are set to 0.25 in on all sides to maximise the usable page area
and minimise the amount of scaling required for each image.
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
SOURCE_MD = REPO_ROOT / '555.md'
OUT_PATH = REPO_ROOT / 'docs' / '555.pdf'

PAGE_W, PAGE_H = letter
MARGIN = 0.25 * inch          # applied to all four sides
USABLE_W = PAGE_W - 2 * MARGIN
USABLE_H = PAGE_H - 2 * MARGIN

_IMG_SPACING = 8              # points of vertical gap between images on the same page


def _parse_image_paths(md_text):
    return re.findall(r'!\[.*?\]\((.+?)\)', md_text)


def generate_pdf():
    md_text = SOURCE_MD.read_text(encoding='utf-8')
    rel_paths = _parse_image_paths(md_text)
    if not rel_paths:
        sys.exit('Error: no images found in 555.md')

    # Resolve each image and calculate its draw size.
    # Scale down only if the image is wider than the usable area; never scale up.
    images = []
    for rel in rel_paths:
        img_path = (REPO_ROOT / rel).resolve()
        if not img_path.exists():
            sys.exit(f'Error: image not found: {img_path}')
        pil = ImageOps.exif_transpose(PILImage.open(img_path))
        pw, ph = pil.size
        draw_w = float(pw)
        draw_h = float(ph)
        if draw_w > USABLE_W:
            draw_h *= USABLE_W / draw_w
            draw_w = USABLE_W
        images.append((img_path, draw_w, draw_h))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT_PATH), pagesize=letter)

    # Draw images top-to-bottom, starting a new page whenever the next image
    # would overflow the bottom margin.
    y = PAGE_H - MARGIN
    for i, (img_path, draw_w, draw_h) in enumerate(images):
        if y - draw_h < MARGIN:
            c.showPage()
            y = PAGE_H - MARGIN
        y -= draw_h
        c.drawImage(ImageReader(str(img_path)), x=MARGIN, y=y,
                    width=draw_w, height=draw_h)
        if i < len(images) - 1:
            y -= _IMG_SPACING

    c.showPage()
    c.save()
    print(f'PDF written to: {OUT_PATH}')


if __name__ == '__main__':
    generate_pdf()
