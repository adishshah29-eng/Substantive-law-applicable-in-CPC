"""
Ingests the golden-set judgments: parses YAML frontmatter, chunks each
judgment body (~500 tokens / 100-token overlap), and builds the
"judgments" BM25 + Chroma indices alongside the "statutes" ones.
"""
from __future__ import annotations

from pathlib import Path

from backend.indexing.judgment_indexer import normalize_all_judgments
from backend.indexing.statute_indexer import build_indices

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_SET_DIR = REPO_ROOT / "data" / "judgments" / "golden_set"
INDICES_DIR = REPO_ROOT / "data" / "indices"


def main() -> None:
    print(f"Parsing judgments from {GOLDEN_SET_DIR} ...")
    chunks = normalize_all_judgments(GOLDEN_SET_DIR)
    print(f"  {len(chunks)} judgment chunks from {len(list(GOLDEN_SET_DIR.glob('*.txt')))} files")

    build_indices(chunks, INDICES_DIR, name="judgments")
    print("Done.")


if __name__ == "__main__":
    main()
