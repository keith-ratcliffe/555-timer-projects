#!/usr/bin/env python3
"""Generate a standalone PDF from a 555 timer project's README.md.

Usage:
    python3 scripts/generate_pdf.py <project-number>

Examples:
    python3 scripts/generate_pdf.py 01
    python3 scripts/generate_pdf.py 03

The PDF is written to docs/<project-number>/<project-dir-name>.pdf.
"""

import io
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import markdown
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPO_ROOT = Path(__file__).parent.parent

PAGE_W = letter[0] - 2 * inch   # usable text width
PAGE_H = letter[1] - 2 * inch   # usable page height
# Leave ~2 inches for the step heading + bullet text above the image.
_IMG_MAX_DRAW_H = PAGE_H - 2 * inch


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _build_styles():
    base = getSampleStyleSheet()
    return {
        'h1': ParagraphStyle(
            'h1', parent=base['Heading1'], fontSize=20, spaceAfter=10, spaceBefore=14),
        'h2': ParagraphStyle(
            'h2', parent=base['Heading2'], fontSize=15, spaceAfter=8, spaceBefore=10),
        'h3': ParagraphStyle(
            'h3', parent=base['Heading3'], fontSize=12, spaceAfter=6, spaceBefore=8),
        'normal': ParagraphStyle(
            'normal', parent=base['Normal'], fontSize=10, spaceAfter=6, leading=14),
        'code_block': ParagraphStyle(
            'code_block', parent=base['Code'], fontSize=8, fontName='Courier',
            spaceAfter=4, leftIndent=12, backColor=colors.HexColor('#f5f5f5')),
        'list_item': ParagraphStyle(
            'list_item', parent=base['Normal'], fontSize=10, leading=14,
            spaceAfter=3, leftIndent=18, bulletIndent=6),
        'list_item_l2': ParagraphStyle(
            'list_item_l2', parent=base['Normal'], fontSize=10, leading=14,
            spaceAfter=2, leftIndent=36, bulletIndent=24),
        'th': ParagraphStyle(
            'th', parent=base['Normal'], fontSize=9, fontName='Helvetica-Bold'),
        'td': ParagraphStyle(
            'td', parent=base['Normal'], fontSize=9),
    }


# ---------------------------------------------------------------------------
# Inline markup helpers
# ---------------------------------------------------------------------------

def _escape_para(text):
    """Escape characters that would break a ReportLab Paragraph."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _inline_text(el):
    """Collect inline text from an element, converting inline tags to
    ReportLab Paragraph markup (<b>, <i>, <font name="Courier">)."""
    parts = []

    def _collect(node, tags):
        tag = node.tag if hasattr(node, 'tag') else None

        if tag in ('strong', 'b'):
            parts.append('<b>')
            _gather(node, tags + [tag])
            parts.append('</b>')
        elif tag in ('em', 'i'):
            parts.append('<i>')
            _gather(node, tags + [tag])
            parts.append('</i>')
        elif tag == 'code':
            parts.append('<font name="Courier" size="8">')
            _gather(node, tags + [tag])
            parts.append('</font>')
        elif tag == 'a':
            # Render link text; ignore href
            _gather(node, tags + [tag])
        elif tag == 'br':
            parts.append('<br/>')
            if node.tail:
                parts.append(_escape_para(node.tail))
        elif tag == 'img':
            # Inline images: use alt text
            alt = node.get('alt', '')
            if alt:
                parts.append(_escape_para(f'[{alt}]'))
            if node.tail:
                parts.append(_escape_para(node.tail))
        elif tag is not None:
            # Unknown inline tag — just render contents
            _gather(node, tags + [tag])
        else:
            # Plain text node (shouldn't happen, but safety)
            parts.append(_escape_para(str(node)))

    def _gather(node, tags):
        if node.text:
            parts.append(_escape_para(node.text))
        for child in node:
            _collect(child, tags)
            # tail text belongs to parent context
            if child.tail:
                parts.append(_escape_para(child.tail))

    if el.text:
        parts.append(_escape_para(el.text))
    for child in el:
        _collect(child, [])
        if child.tail:
            parts.append(_escape_para(child.tail))

    return ''.join(parts)


# ---------------------------------------------------------------------------
# Element processors
# ---------------------------------------------------------------------------

def _process_table(el, styles):
    """Convert a <table> element into a ReportLab Table flowable."""
    rows = []
    has_header = False

    for section in el:  # thead / tbody / tr
        if section.tag in ('thead', 'tbody'):
            for tr in section:
                row = _process_tr(tr, section.tag == 'thead', styles)
                rows.append(row)
                if section.tag == 'thead':
                    has_header = True
        elif section.tag == 'tr':
            row = _process_tr(section, False, styles)
            rows.append(row)

    if not rows:
        return []

    col_count = max(len(r) for r in rows)
    col_w = PAGE_W / col_count

    tbl = Table(rows, colWidths=[col_w] * col_count, repeatRows=1 if has_header else 0)
    style_cmds = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    if has_header:
        style_cmds.append(('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dce6f1')))
    tbl.setStyle(TableStyle(style_cmds))
    return [tbl, Spacer(1, 8)]


def _process_tr(tr, is_header, styles):
    row = []
    for cell in tr:
        text = _inline_text(cell)
        style = styles['th'] if (is_header or cell.tag == 'th') else styles['td']
        row.append(Paragraph(text or ' ', style))
    return row


def _process_list(el, styles, depth=0):
    """Convert a <ul> or <ol> element into a list of Paragraph flowables."""
    flowables = []
    list_type = el.tag  # 'ul' or 'ol'
    item_style = styles['list_item'] if depth == 0 else styles['list_item_l2']

    for i, li in enumerate(el):
        if li.tag != 'li':
            continue

        # Collect direct text and inline children (skip nested lists).
        # "Loose" lists (blank lines between items in Markdown) wrap each
        # item's content in a <p> element; "tight" lists have inline content
        # directly inside <li>.  Handle both cases.
        direct_parts = []
        if li.text:
            direct_parts.append(_escape_para(li.text))
        nested = []
        for child in li:
            if child.tag in ('ul', 'ol'):
                nested.append(child)
            elif child.tag == 'p':
                # Loose-list paragraph — use _inline_text to capture the full
                # content including any nested <strong>, <em>, <code>, etc.
                direct_parts.append(_inline_text(child))
                if child.tail:
                    direct_parts.append(_escape_para(child.tail))
            else:
                # Tight-list: inline element directly inside <li>
                if child.tag in ('strong', 'b'):
                    direct_parts.append('<b>')
                    if child.text:
                        direct_parts.append(_escape_para(child.text))
                    direct_parts.append('</b>')
                elif child.tag in ('em', 'i'):
                    direct_parts.append('<i>')
                    if child.text:
                        direct_parts.append(_escape_para(child.text))
                    direct_parts.append('</i>')
                elif child.tag == 'code':
                    direct_parts.append('<font name="Courier" size="8">')
                    if child.text:
                        direct_parts.append(_escape_para(child.text))
                    direct_parts.append('</font>')
                else:
                    if child.text:
                        direct_parts.append(_escape_para(child.text))
                if child.tail:
                    direct_parts.append(_escape_para(child.tail))

        bullet = '•' if list_type == 'ul' else f'{i + 1}.'
        item_text = f'<b>{bullet}</b> ' + ''.join(direct_parts).strip()
        flowables.append(Paragraph(item_text, item_style))

        for nested_list in nested:
            flowables.extend(_process_list(nested_list, styles, depth + 1))

    return flowables


_IMG_MAX_PX = 1200   # max pixel width when resampling source images
_IMG_JPEG_Q = 85     # JPEG quality for embedded images


def _render_img(img_el, project_dir, styles):
    """Return flowables for an <img> element, or [] if it cannot be rendered.

    Large source images are downsampled to _IMG_MAX_PX wide and re-encoded as
    JPEG before embedding, which keeps PDF file size manageable.
    """
    src = img_el.get('src', '')
    if src:
        img_path = (project_dir / src).resolve()
        if img_path.exists():
            try:
                pil = PILImage.open(img_path)
                pil_w, pil_h = pil.size

                # Downsample if wider than the threshold
                if pil_w > _IMG_MAX_PX:
                    new_h = int(pil_h * _IMG_MAX_PX / pil_w)
                    pil = pil.resize((_IMG_MAX_PX, new_h), PILImage.LANCZOS)
                    pil_w, pil_h = pil.size

                # Re-encode as JPEG into an in-memory buffer
                buf = io.BytesIO()
                rgb = pil.convert('RGB')
                rgb.save(buf, format='JPEG', quality=_IMG_JPEG_Q, optimize=True)
                buf.seek(0)

                img = Image(buf)
                # Scale draw dimensions to fit within page width and max height.
                draw_w = float(min(pil_w, PAGE_W))
                draw_h = pil_h * (draw_w / pil_w)
                if draw_h > _IMG_MAX_DRAW_H:
                    draw_w = draw_w * (_IMG_MAX_DRAW_H / draw_h)
                    draw_h = _IMG_MAX_DRAW_H
                img.drawWidth = draw_w
                img.drawHeight = draw_h
                img.hAlign = 'LEFT'
                return [img, Spacer(1, 8)]
            except Exception:
                pass
    alt = img_el.get('alt', '')
    return [Paragraph(f'[Image: {alt}]', styles['normal'])] if alt else []


def _element_is_img_only(el):
    """Return the sole <img> child if the element contains only an image."""
    children = list(el)
    if len(children) == 1 and children[0].tag == 'img' and not (el.text or '').strip():
        return children[0]
    return None


def _process_element(el, styles, project_dir):
    """Convert one top-level HTML element to a list of ReportLab flowables."""
    tag = el.tag

    if tag in ('h1', 'h2', 'h3'):
        # The markdown parser turns   ![alt](src)\n---   into <h2><img/></h2>.
        # Detect this and render as an image instead of a heading.
        img_el = _element_is_img_only(el)
        if img_el is not None:
            return _render_img(img_el, project_dir, styles)
        text = _inline_text(el)
        return [Paragraph(text, styles[tag])]

    if tag == 'p':
        img_el = _element_is_img_only(el)
        if img_el is not None:
            return _render_img(img_el, project_dir, styles)

        text = _inline_text(el)
        if text.strip():
            return [Paragraph(text, styles['normal'])]
        return []

    if tag in ('ul', 'ol'):
        items = _process_list(el, styles)
        return items + [Spacer(1, 4)]

    if tag == 'table':
        return _process_table(el, styles)

    if tag == 'pre':
        code_el = el.find('code')
        raw = (code_el.text if code_el is not None else el.text) or ''
        flowables = []
        for line in raw.split('\n'):
            safe = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            safe = safe.replace(' ', '&nbsp;') or '&nbsp;'
            flowables.append(Paragraph(safe, styles['code_block']))
        return flowables + [Spacer(1, 4)]

    if tag == 'hr':
        return [
            Spacer(1, 4),
            HRFlowable(width='100%', thickness=0.75, color=colors.HexColor('#999999')),
            Spacer(1, 4),
        ]

    if tag == 'blockquote':
        text = _inline_text(el)
        if text.strip():
            style = ParagraphStyle(
                'bq', parent=styles['normal'],
                leftIndent=24, textColor=colors.HexColor('#555555'))
            return [Paragraph(text, style)]
        return []

    # Fallback: try to render as paragraph
    text = _inline_text(el)
    if text.strip():
        return [Paragraph(text, styles['normal'])]
    return []


# ---------------------------------------------------------------------------
# Step grouping helpers
# ---------------------------------------------------------------------------

_STEP_RE = re.compile(r'^\s*Step\s+\d+', re.IGNORECASE)


def _is_step_heading(el):
    """True if el is a non-image heading whose text starts with 'Step N'."""
    if el.tag not in ('h2', 'h3'):
        return False
    if _element_is_img_only(el) is not None:
        return False
    return bool(_STEP_RE.match(''.join(el.itertext())))


def _group_elements(all_elements):
    """Split top-level HTML elements into three buckets:

    Returns (preamble, steps, trailing) where:
      - preamble: list of elements before the first numbered step
      - steps:    list of lists, one inner list per step (heading → … → image)
      - trailing: list of elements after the last step's closing image
    """
    preamble = []
    steps = []
    trailing = []
    current_step = None   # None = not inside a step
    past_steps = False    # True once we have started the first step

    for el in all_elements:
        if _is_step_heading(el):
            # Close any open step (shouldn't normally happen, but be safe)
            if current_step is not None:
                steps.append(current_step)
            current_step = [el]
            past_steps = True
        elif current_step is not None:
            current_step.append(el)
            # An image-only element closes the current step
            if _element_is_img_only(el) is not None:
                steps.append(current_step)
                current_step = None
        elif past_steps:
            trailing.append(el)
        else:
            preamble.append(el)

    # Flush any step that had no closing image
    if current_step is not None:
        steps.append(current_step)

    return preamble, steps, trailing


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def generate_pdf(project_num):
    # Locate the project directory
    matches = sorted(REPO_ROOT.glob(f'{project_num}-*'))
    if not matches:
        sys.exit(f"Error: no project directory found matching '{project_num}-*'")
    project_dir = matches[0]

    readme_path = project_dir / 'README.md'
    if not readme_path.exists():
        sys.exit(f"Error: README.md not found in {project_dir}")

    # Prepare output directory and path
    out_dir = REPO_ROOT / 'docs' / project_num
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f'{project_dir.name}.pdf'

    # Convert Markdown → HTML → XML tree
    md_text = readme_path.read_text(encoding='utf-8')
    html_str = markdown.markdown(
        md_text,
        extensions=['tables', 'fenced_code'],
        output_format='xhtml',
    )
    try:
        root = ET.fromstring(f'<root>{html_str}</root>')
    except ET.ParseError as exc:
        sys.exit(f"Error parsing generated HTML: {exc}")

    styles = _build_styles()

    def els_to_flowables(elements):
        result = []
        for el in elements:
            result.extend(_process_element(el, styles, project_dir))
        return result

    preamble_els, step_groups, trailing_els = _group_elements(list(root))

    # --- Assemble final flowable list ---
    flowables = els_to_flowables(preamble_els)

    for step_els in step_groups:
        # Each step starts on a fresh page and is kept together.
        flowables.append(PageBreak())
        flowables.append(KeepTogether(els_to_flowables(step_els)))

    if trailing_els:
        flowables.append(PageBreak())
        flowables.extend(els_to_flowables(trailing_els))

    if not flowables:
        flowables = [Paragraph('(empty document)', styles['normal'])]

    # Render PDF
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
        title=project_dir.name,
    )
    doc.build(flowables)
    print(f"PDF written to: {pdf_path}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 generate_pdf.py <project-number>  (e.g., 01)')
    generate_pdf(sys.argv[1])
