"""
Parses golden-set judgment .txt files (YAML frontmatter + body) and chunks
each judgment's body into SourceChunks of ~500 tokens with a 100-token
overlap, using a recursive splitter that prefers paragraph boundaries.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import yaml

from backend.models.schemas import CourtLevel, SourceChunk, SourceType

CHUNK_TOKENS = 500
OVERLAP_TOKENS = 100

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n\n?(.*)", re.S)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def parse_judgment_file(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path} has no YAML frontmatter block")
    metadata = yaml.safe_load(match.group(1))
    body = match.group(2).strip()
    return metadata, body


def _split_paragraphs(body: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]


def chunk_body(body: str, max_tokens: int = CHUNK_TOKENS, overlap_tokens: int = OVERLAP_TOKENS) -> list[str]:
    """Greedily pack paragraphs into chunks up to max_tokens, carrying the
    tail ~overlap_tokens words of each chunk into the start of the next."""
    paragraphs = _split_paragraphs(body)
    if not paragraphs:
        return []

    chunks: list[str] = []
    current_words: list[str] = []

    for para in paragraphs:
        para_words = para.split()
        if current_words and len(current_words) + len(para_words) > max_tokens:
            chunks.append(" ".join(current_words))
            overlap = current_words[-overlap_tokens:] if overlap_tokens else []
            current_words = overlap + para_words
        else:
            current_words.extend(para_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def _map_court(value: str | None) -> CourtLevel | None:
    if not value:
        return None
    try:
        return CourtLevel(value)
    except ValueError:
        return CourtLevel.OTHER


def normalize_judgment_file(path: Path) -> Iterator[SourceChunk]:
    metadata, body = parse_judgment_file(path)
    case_name = metadata["case_name"]
    slug = slugify(case_name)
    pieces = chunk_body(body)

    for i, piece in enumerate(pieces):
        yield SourceChunk(
            chunk_id=f"judgment-{slug}-{i}",
            source_type=SourceType.JUDGMENT,
            text=piece,
            case_name=case_name,
            citation_string=metadata.get("citation"),
            court=_map_court(metadata.get("court")),
            year=metadata.get("year"),
            judges=metadata.get("judges"),
            source_url=metadata.get("source_url"),
            chunk_index=i,
        )


def normalize_all_judgments(golden_set_dir: Path) -> list[SourceChunk]:
    chunks: list[SourceChunk] = []
    for path in sorted(golden_set_dir.glob("*.txt")):
        chunks.extend(normalize_judgment_file(path))
    return chunks
