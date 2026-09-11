"""
Parses a PDF file into Paragraph objects, using pdfplumber (handles tables
and layout better) with a pypdf fallback if pdfplumber fails to extract
any text (e.g. certain malformed or image-heavy PDFs).
"""
from __future__ import annotations

import re
from pathlib import Path

from backend.models.schemas import Paragraph

_BLANK_LINE_RE = re.compile(r"\n\s*\n+")


def _split_into_paragraphs(page_texts: list[str]) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    index = 0
    for page_num, page_text in enumerate(page_texts, start=1):
        for block in _BLANK_LINE_RE.split(page_text):
            block = block.strip()
            if not block:
                continue
            paragraphs.append(Paragraph(index=index, text=block, page=page_num))
            index += 1
    return paragraphs


def _parse_with_pdfplumber(path: Path) -> list[str]:
    import pdfplumber

    page_texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_texts.append(page.extract_text() or "")
    return page_texts


def _parse_with_pypdf(path: Path) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]


def parse_pdf(path: str | Path) -> list[Paragraph]:
    path = Path(path)

    page_texts = _parse_with_pdfplumber(path)
    if not any(text.strip() for text in page_texts):
        page_texts = _parse_with_pypdf(path)

    return _split_into_paragraphs(page_texts)
