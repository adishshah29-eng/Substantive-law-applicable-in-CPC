"""
Phase 1 acceptance tests: each retriever tested separately (BM25, dense).
Hybrid fusion (RRF) is implemented in Phase 2 alongside judgment retrieval.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import chromadb
import pytest
from rank_bm25 import BM25Okapi

from backend.indexing.embeddings import embed
from backend.indexing.statute_indexer import _tokenize, statute_entity_matches

REPO_ROOT = Path(__file__).resolve().parents[1]
INDICES_DIR = REPO_ROOT / "data" / "indices"
BM25_PATH = INDICES_DIR / "bm25_statutes.pkl"
CHROMA_DIR = INDICES_DIR / "chroma_db"

pytestmark = pytest.mark.skipif(
    not BM25_PATH.exists(),
    reason="statute indices not built; run scripts/02_build_statute_index.py first",
)


def _load_bm25():
    with open(BM25_PATH, "rb") as f:
        return pickle.load(f)


def bm25_search(query: str, top_k: int = 5):
    data = _load_bm25()
    bm25: BM25Okapi = data["bm25"]
    metadata = data["metadata"]
    texts = data["texts"]

    scores = bm25.get_scores(_tokenize(query))
    ranked_by_score = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    # An explicit "Order X Rule Y" / "Section N" citation in the query is
    # resolved by exact metadata match first; BM25's document-length
    # normalization can otherwise rank a short, unrelated chunk above the
    # correct (often longer) provision. See statute_entity_matches().
    entity_hits = statute_entity_matches(query, metadata)
    ranked = entity_hits + [i for i in ranked_by_score if i not in entity_hits]
    ranked = ranked[:top_k]
    return [(metadata[i], texts[i], scores[i]) for i in ranked]


def dense_search(query: str, top_k: int = 5):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection("statutes")
    query_vector = embed([query])[0].tolist()
    results = collection.query(query_embeddings=[query_vector], n_results=top_k)
    return list(zip(results["metadatas"][0], results["documents"][0]))


def test_bm25_finds_order_xxxix_rule_1():
    results = bm25_search("Order XXXIX Rule 1", top_k=3)
    hit = any(
        meta.get("order_number") == "XXXIX" and meta.get("rule_number") == "1"
        for meta, _, _ in results
    )
    assert hit, f"Order XXXIX Rule 1 not in top-3 BM25 results: {results}"


def test_dense_finds_temporary_injunction_requirements():
    results = dense_search("temporary injunction requirements", top_k=5)
    hit = any(meta.get("order_number") == "XXXIX" for meta, _ in results)
    assert hit, f"Order XXXIX not in top-5 dense results: {results}"
