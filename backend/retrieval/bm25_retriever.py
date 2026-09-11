"""
BM25 retrieval over a named collection ("statutes" or "judgments"), backed
by the pickled indices built in backend/indexing/statute_indexer.py.
"""
from __future__ import annotations

import pickle
from pathlib import Path

from backend.indexing.statute_indexer import _tokenize, statute_entity_matches
from backend.models.schemas import RetrievalResult, SourceChunk

REPO_ROOT = Path(__file__).resolve().parents[2]
INDICES_DIR = REPO_ROOT / "data" / "indices"

_bm25_cache: dict[str, dict] = {}


def _load(collection: str) -> dict:
    if collection not in _bm25_cache:
        path = INDICES_DIR / f"bm25_{collection}.pkl"
        with open(path, "rb") as f:
            _bm25_cache[collection] = pickle.load(f)
    return _bm25_cache[collection]


def retrieve(query: str, top_k: int = 10, collection: str = "statutes") -> list[RetrievalResult]:
    data = _load(collection)
    bm25 = data["bm25"]
    metadata = data["metadata"]
    texts = data["texts"]

    scores = bm25.get_scores(_tokenize(query))
    ranked_by_score = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    # For the statute corpus, an explicit "Order X Rule Y" / "Section N"
    # citation is resolved by exact metadata match first; see
    # statute_entity_matches() for why plain BM25 alone is not reliable here.
    entity_hits = statute_entity_matches(query, metadata) if collection == "statutes" else []
    ranked = entity_hits + [i for i in ranked_by_score if i not in entity_hits]
    ranked = ranked[:top_k]

    results = []
    for rank, i in enumerate(ranked, start=1):
        chunk = SourceChunk(**{**metadata[i], "text": texts[i]})
        results.append(
            RetrievalResult(
                chunk=chunk,
                score=float(scores[i]),
                bm25_rank=rank,
                retrieval_method="bm25_only",
            )
        )
    return results
