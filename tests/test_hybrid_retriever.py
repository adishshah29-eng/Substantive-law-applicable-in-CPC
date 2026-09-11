"""
Phase 1 acceptance tests: each retriever tested separately (BM25, dense)
over the statute corpus.
Phase 2 acceptance tests: hybrid RRF fusion across statutes + judgments.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.retrieval import bm25_retriever, dense_retriever
from backend.retrieval.hybrid import hybrid_search

REPO_ROOT = Path(__file__).resolve().parents[1]
INDICES_DIR = REPO_ROOT / "data" / "indices"

pytestmark = pytest.mark.skipif(
    not (INDICES_DIR / "bm25_statutes.pkl").exists(),
    reason="statute indices not built; run scripts/02_build_statute_index.py first",
)

judgments_built = pytest.mark.skipif(
    not (INDICES_DIR / "bm25_judgments.pkl").exists(),
    reason="judgment indices not built; run scripts/03_ingest_golden_judgments.py first",
)


def test_bm25_finds_order_xxxix_rule_1():
    results = bm25_retriever.retrieve("Order XXXIX Rule 1", top_k=3, collection="statutes")
    hit = any(
        r.chunk.order_number == "XXXIX" and r.chunk.rule_number == "1" for r in results
    )
    assert hit, f"Order XXXIX Rule 1 not in top-3 BM25 results: {[r.chunk.chunk_id for r in results]}"


def test_dense_finds_temporary_injunction_requirements():
    results = dense_retriever.retrieve("temporary injunction requirements", top_k=5, collection="statutes")
    hit = any(r.chunk.order_number == "XXXIX" for r in results)
    assert hit, f"Order XXXIX not in top-5 dense results: {[r.chunk.chunk_id for r in results]}"


@judgments_built
def test_hybrid_finds_dalpat_kumar_for_prima_facie_injunction():
    results = hybrid_search("prima facie case interim injunction", top_k=3)
    hit = any(r.chunk.case_name == "Dalpat Kumar v Prahlad Singh" for r in results)
    assert hit, f"Dalpat Kumar v Prahlad Singh not in top-3 hybrid results: {[r.chunk.chunk_id for r in results]}"


@judgments_built
def test_hybrid_finds_revajeetu_builders_for_amendment_after_trial():
    results = hybrid_search("Order VI Rule 17 amendment after trial commencement", top_k=5)
    hit = any(
        r.chunk.case_name == "Revajeetu Builders and Developers v Narayanaswamy and Sons"
        for r in results
    )
    assert hit, f"Revajeetu Builders not in top-5 hybrid results: {[r.chunk.chunk_id for r in results]}"
