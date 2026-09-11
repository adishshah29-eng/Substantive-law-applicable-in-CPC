"""
Routes a substantive/procedural claim to relevant case law: runs hybrid
(BM25 + dense, RRF-fused) retrieval on the claim text and returns the
top-5 judgment chunks plus the top-3 statute chunks.
"""
from __future__ import annotations

from backend.models.schemas import RetrievalResult
from backend.retrieval.hybrid import hybrid_search


def route_case(claim_text: str, top_k_judgments: int = 5, top_k_statutes: int = 3) -> list[RetrievalResult]:
    judgment_results = hybrid_search(claim_text, top_k=top_k_judgments, collections=["judgments"])
    statute_results = hybrid_search(claim_text, top_k=top_k_statutes, collections=["statutes"])
    return judgment_results + statute_results
