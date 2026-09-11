"""
One-command statute indexing pipeline: normalize raw statute JSON -> chunk ->
embed -> build BM25 + Chroma indices.
"""
from __future__ import annotations

from pathlib import Path

from backend.indexing.chunker import chunk_all
from backend.indexing.statute_indexer import build_statute_indices
from backend.indexing.statute_normalizer import normalize_all_statutes

REPO_ROOT = Path(__file__).resolve().parents[1]
STATUTES_DIR = REPO_ROOT / "data" / "statutes"
INDICES_DIR = REPO_ROOT / "data" / "indices"


def main() -> None:
    print(f"Normalizing statutes from {STATUTES_DIR} ...")
    raw_chunks = normalize_all_statutes(STATUTES_DIR)
    print(f"  {len(raw_chunks)} section/rule-level chunks")

    chunks = chunk_all(raw_chunks)
    print(f"  {len(chunks)} chunks after ~200-token splitting")

    build_statute_indices(chunks, INDICES_DIR)
    print("Done.")


if __name__ == "__main__":
    main()
