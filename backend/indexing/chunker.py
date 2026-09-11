"""
Chunks statute SourceChunks to ~200 tokens each. If a section/rule's text is
under the limit, it is kept as one chunk; otherwise it is split by
subsection (paragraphs that look like "(1)", "(2)", ... or lettered clauses),
and each piece carries the full parent metadata plus a chunk_index.

Token count is approximated as whitespace-split word count, which is
adequate for the ~200-token target used here and avoids adding a tokenizer
dependency to the indexing step.
"""
from __future__ import annotations

import re
from typing import Iterable

from backend.models.schemas import SourceChunk

MAX_TOKENS = 200

# Matches the start of a numbered subsection like "(1)" or a lettered
# clause like "(a)" at the beginning of a line, used as split points.
_SUBSECTION_SPLIT_RE = re.compile(r"\n(?=\(\d+[A-Za-z]?\)|\([a-z]{1,3}\)|Provided that|Explanation)")


def _token_count(text: str) -> int:
    return len(text.split())


def _split_by_subsection(text: str) -> list[str]:
    parts = [p.strip() for p in _SUBSECTION_SPLIT_RE.split(text) if p.strip()]
    return parts if len(parts) > 1 else [text]


def chunk_source(chunk: SourceChunk) -> list[SourceChunk]:
    """Split a single SourceChunk into one or more sub-chunks under MAX_TOKENS."""
    if _token_count(chunk.text) <= MAX_TOKENS:
        return [chunk]

    pieces = _split_by_subsection(chunk.text)
    if len(pieces) == 1:
        # No subsection markers found; fall back to a single oversized chunk
        # rather than splitting mid-sentence.
        return [chunk]

    header, *body_pieces = pieces
    sub_chunks: list[SourceChunk] = []
    for i, piece in enumerate(body_pieces):
        text = piece if i == 0 else f"{header}\n{piece}"
        sub_chunks.append(
            chunk.model_copy(
                update={
                    "chunk_id": f"{chunk.chunk_id}-{i}",
                    "text": text,
                    "chunk_index": i,
                }
            )
        )
    return sub_chunks


def chunk_all(chunks: Iterable[SourceChunk]) -> list[SourceChunk]:
    result: list[SourceChunk] = []
    for chunk in chunks:
        result.extend(chunk_source(chunk))
    return result
