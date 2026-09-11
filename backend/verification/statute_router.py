"""
Extracts the statute provisions a claim depends on (via the LLM, per
STATUTE_ROUTER_SYSTEM / EXTRACT_STATUTORY_REFS_TOOL) and fetches the
matching statute chunks from the index -- exact metadata match on
act/section or order/rule first, falling back to BM25 search on the
claim text itself if the LLM found no explicit provision to route on.
"""
from __future__ import annotations

from backend.models.schemas import RetrievalResult, SourceChunk, StatutoryReference
from backend.retrieval import bm25_retriever
from backend.verification.llm_client import call_structured
from backend.verification.prompts import (
    EXTRACT_STATUTORY_REFS_TOOL,
    STATUTE_ROUTER_SYSTEM,
    STATUTE_ROUTER_USER_TEMPLATE,
)


def extract_statutory_references(claim_text: str) -> list[StatutoryReference]:
    user_prompt = STATUTE_ROUTER_USER_TEMPLATE.format(claim_text=claim_text)
    result = call_structured(
        STATUTE_ROUTER_SYSTEM, user_prompt, EXTRACT_STATUTORY_REFS_TOOL["input_schema"]
    )
    return [StatutoryReference(**ref) for ref in result.get("references", [])]


def _matches_reference(ref: StatutoryReference, meta: dict) -> bool:
    if ref.section and str(meta.get("section_number", "")).lower() == ref.section.lower():
        return True
    if (
        ref.order
        and ref.rule
        and str(meta.get("order_number", "")).upper() == ref.order.upper()
        and str(meta.get("rule_number", "")).lower() == ref.rule.lower()
    ):
        return True
    return False


def _lookup_exact(references: list[StatutoryReference]) -> list[RetrievalResult]:
    data = bm25_retriever._load("statutes")
    metadata, texts = data["metadata"], data["texts"]

    results = []
    for ref in references:
        for i, meta in enumerate(metadata):
            if _matches_reference(ref, meta):
                chunk = SourceChunk(**{**meta, "text": texts[i]})
                results.append(RetrievalResult(chunk=chunk, score=1.0, retrieval_method="exact"))
    return results


def route_statute(claim_text: str, top_k: int = 3) -> list[RetrievalResult]:
    references = extract_statutory_references(claim_text)

    exact_results = _lookup_exact(references)
    if exact_results:
        return exact_results[:top_k]

    return bm25_retriever.retrieve(claim_text, top_k=top_k, collection="statutes")
