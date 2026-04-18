#!/usr/bin/env python3
"""Generate a single-page PDF from 555-HISTORY.md and 555-APPLICATIONS.md.

Usage:
    python3 scripts/generate_history_applications_pdf.py

The PDF is written to docs/555-History-Applications.pdf.

Margins are set to 0.75 in on all sides. If the combined content does not fit
on one page at the starting font size, the font size is reduced in small steps
until everything fits.
"""

import io
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import markdown
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

REPO_ROOT = Path(__file__).parent.parent
SOURCES = [
    REPO_ROOT / '555-HISTORY.md',
    REPO_ROOT / '555-APPLICATIONS.md',
]
OUT_PATH = REPO_ROOT / 'docs' / '555-History-Applications.pdf'

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch

# Starting body font size; reduced automatically if content overflows one page.
FONT_SIZE_START = 10.0
FONT_SIZE_STEP  = 0.25   # points to reduce per iteration
FONT_SIZE_MIN   = 5.0    # safety floor


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _build_styles(fs):
    """Build a style dictionary scaled to body font size *fs*."""
    base = getSampleStyleSheet()
    leading = fs * 1.35
    return {
        'h1': ParagraphStyle('h1', parent=base['Heading1'],
                             fontSize=fs * 1.6, leading=fs * 2.0,
                             spaceAfter=fs * 0.5, spaceBefore=fs * 0.9),
        'h2': ParagraphStyle('h2', parent=base['Heading2'],
                             fontSize=fs * 1.3, leading=fs * 1.7,
                             spaceAfter=fs * 0.4, spaceBefore=fs * 0.7),
        'h3': ParagraphStyle('h3', parent=base['Heading3'],
                             fontSize=fs * 1.1, leading=fs * 1.5,
                             spaceAfter=fs * 0.3, spaceBefore=fs * 0.6),
        'normal': ParagraphStyle('normal', parent=base['Normal'],
                                 fontSize=fs, leading=leading,
                                 spaceAfter=fs * 0.5),
        'li': ParagraphStyle('li', parent=base['Normal'],
                             fontSize=fs, leading=leading,
                             spaceAfter=fs * 0.2, leftIndent=fs * 1.5,
                             bulletIndent=fs * 0.5),
    }


# ---------------------------------------------------------------------------
# Inline markup
# ---------------------------------------------------------------------------

def _escape(text):
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def _inline_text(el):
    """Collect inline text from an element, converting bold/italic to RL markup."""
    parts = []

    def _collect(node):
        tag = getattr(node, 'tag', None)
        if tag in ('strong', 'b'):
            parts.append('<b>')
            _gather(node)
            parts.append('</b>')
        elif tag in ('em', 'i'):
            parts.append('<i>')
            _gather(node)
            parts.append('</i>')
        elif tag == 'code':
            parts.append('<font name="Courier">')
            _gather(node)
            parts.append('</font>')
        elif tag == 'a':
            href = node.get('href', '')
            if href:
                parts.append(f'<a href="{href}" color="blue">')
                _gather(node)
                parts.append('</a>')
            else:
                _gather(node)
        elif tag is not None:
            _gather(node)
        else:
            parts.append(_escape(str(node)))

    def _gather(node):
        if node.text:
            parts.append(_escape(node.text))
        for child in node:
            _collect(child)
            if child.tail:
                parts.append(_escape(child.tail))

    if el.text:
        parts.append(_escape(el.text))
    for child in el:
        _collect(child)
        if child.tail:
            parts.append(_escape(child.tail))

    return ''.join(parts)


# ---------------------------------------------------------------------------
# Element → flowables
# ---------------------------------------------------------------------------

def _el_to_flowables(el, styles):
    tag = el.tag

    if tag in ('h1', 'h2', 'h3'):
        text = _inline_text(el)
        return [Paragraph(text, styles[tag])] if text.strip() else []

    if tag == 'p':
        text = _inline_text(el)
        return [Paragraph(text, styles['normal'])] if text.strip() else []

    if tag in ('ul', 'ol'):
        items = []
        for i, li in enumerate(el):
            if li.tag != 'li':
                continue
            # Handle both loose lists (li > p) and tight lists (inline content).
            parts = []
            if li.text:
                parts.append(_escape(li.text))
            for child in li:
                if child.tag == 'p':
                    parts.append(_inline_text(child))
                elif child.tag not in ('ul', 'ol'):
                    parts.append(_inline_text(child))
                if child.tail:
                    parts.append(_escape(child.tail))
            bullet = '•' if tag == 'ul' else f'{i + 1}.'
            item_text = f'<b>{bullet}</b> ' + ''.join(parts).strip()
            items.append(Paragraph(item_text, styles['li']))
        return items

    if tag == 'hr':
        return [Spacer(1, styles['normal'].fontSize)]

    # Fallback
    text = _inline_text(el)
    return [Paragraph(text, styles['normal'])] if text.strip() else []


def _md_to_flowables(md_text, styles):
    html = markdown.markdown(md_text, extensions=['tables', 'fenced_code'],
                             output_format='xhtml')
    try:
        root = ET.fromstring(f'<root>{html}</root>')
    except ET.ParseError as exc:
        sys.exit(f'Error parsing HTML: {exc}')
    result = []
    for el in root:
        result.extend(_el_to_flowables(el, styles))
    return result


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------

def _count_pages(flowables, styles, font_size):
    """Render to a BytesIO buffer and return the number of pages produced."""
    pages = []

    def _on_page(canvas, doc):
        pages.append(1)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    doc.build(flowables, onFirstPage=_on_page, onLaterPages=_on_page)
    return len(pages)


def _build_flowables(font_size):
    styles = _build_styles(font_size)
    flowables = []
    for i, path in enumerate(SOURCES):
        if not path.exists():
            sys.exit(f'Error: file not found: {path}')
        md_text = path.read_text(encoding='utf-8')
        flowables.extend(_md_to_flowables(md_text, styles))
        # Small gap between the two documents (not a page break).
        if i < len(SOURCES) - 1:
            flowables.append(Spacer(1, font_size))
    return flowables, styles


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_pdf():
    font_size = FONT_SIZE_START

    while font_size >= FONT_SIZE_MIN:
        flowables, styles = _build_flowables(font_size)
        pages = _count_pages(flowables, styles, font_size)
        if pages <= 1:
            break
        font_size -= FONT_SIZE_STEP
    else:
        sys.exit(f'Error: content still exceeds one page at minimum font size '
                 f'({FONT_SIZE_MIN}pt). Cannot fit on a single page.')

    print(f'Using font size: {font_size:.2f}pt')

    # Final render to the output file.
    flowables, _ = _build_flowables(font_size)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT_PATH), pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title='555 Timer — History and Applications',
    )
    doc.build(flowables)
    print(f'PDF written to: {OUT_PATH}')


if __name__ == '__main__':
    generate_pdf()
