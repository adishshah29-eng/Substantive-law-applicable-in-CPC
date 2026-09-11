"""
Hybrid retrieval: fuses BM25 and dense retrieval rankings across one or
more collections using Reciprocal Rank Fusion (RRF).
"""
from __future__ import annotations

from backend.retrieval import bm25_retriever, dense_retriever
from backend.models.schemas import RetrievalResult

DEFAULT_RRF_K = 60


def _rrf_scores(ranked_results: list[RetrievalResult], k: int) -> dict[str, float]:
    """Map chunk_id -> RRF contribution (1 / (k + rank)) for one ranked list."""
    return {
        result.chunk.chunk_id: 1.0 / (k + rank)
        for rank, result in enumerate(ranked_results, start=1)
    }


def hybrid_search(
    query: str,
    top_k: int = 10,
    collections: list[str] = ["statutes", "judgments"],
    rrf_k: int = DEFAULT_RRF_K,
    per_retriever_k: int = 20,
) -> list[RetrievalResult]:
    """Run BM25 and dense retrieval independently over each collection,
    fuse all rankings with Reciprocal Rank Fusion, and return the top_k
    RetrievalResults sorted by fused score (descending)."""
    by_chunk_id: dict[str, RetrievalResult] = {}
    fused_scores: dict[str, float] = {}
    bm25_ranks: dict[str, int] = {}
    dense_ranks: dict[str, int] = {}

    for collection in collections:
        bm25_results = bm25_retriever.retrieve(query, top_k=per_retriever_k, collection=collection)
        dense_results = dense_retriever.retrieve(query, top_k=per_retriever_k, collection=collection)

        for result in bm25_results:
            cid = result.chunk.chunk_id
            by_chunk_id[cid] = result
            bm25_ranks[cid] = result.bm25_rank

        for result in dense_results:
            cid = result.chunk.chunk_id
            by_chunk_id.setdefault(cid, result)
            dense_ranks[cid] = result.dense_rank

        for cid, score in _rrf_scores(bm25_results, rrf_k).items():
            fused_scores[cid] = fused_scores.get(cid, 0.0) + score
        for cid, score in _rrf_scores(dense_results, rrf_k).items():
            fused_scores[cid] = fused_scores.get(cid, 0.0) + score

    ranked_ids = sorted(fused_scores, key=lambda cid: fused_scores[cid], reverse=True)[:top_k]

    fused_results = []
    for cid in ranked_ids:
        base = by_chunk_id[cid]
        fused_results.append(
            RetrievalResult(
                chunk=base.chunk,
                score=fused_scores[cid],
                bm25_rank=bm25_ranks.get(cid),
                dense_rank=dense_ranks.get(cid),
                retrieval_method="hybrid",
            )
        )
    return fused_results
