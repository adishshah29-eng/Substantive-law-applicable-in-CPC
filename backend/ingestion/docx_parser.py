"""
Parses a DOCX file into Paragraph objects, using python-docx. DOCX has no
native concept of a "page," so Paragraph.page is left None.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document

from backend.models.schemas import Paragraph


def parse_docx(path: str | Path) -> list[Paragraph]:
    document = Document(str(path))

    paragraphs: list[Paragraph] = []
    index = 0
    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        paragraphs.append(Paragraph(index=index, text=text, page=None))
        index += 1

    return paragraphs
