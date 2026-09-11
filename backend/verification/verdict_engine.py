"""
The core VERITAS verification call: given a claim and its retrieved
sources, render a strict verdict via VERDICT_ENGINE_SYSTEM +
RENDER_VERDICT_TOOL. Validates the LLM's response against the Verdict
schema and retries once on invalid JSON.
"""
from __future__ import annotations

from backend.models.schemas import ClassifiedClaim, EvidenceSpan, RetrievalResult, Verdict, VerdictStatus
from backend.verification.llm_client import call_structured
from backend.verification.prompts import (
    RENDER_VERDICT_TOOL,
    VERDICT_ENGINE_SYSTEM,
    VERDICT_ENGINE_USER_TEMPLATE,
    format_sources_block,
)

MAX_RETRIES = 1


def _format_statutory_refs(claim: ClassifiedClaim) -> str:
    if not claim.statutory_references:
        return "(none)"
    return ", ".join(
        f"{ref.act}"
        + (f" Section {ref.section}" if ref.section else "")
        + (f" Order {ref.order} Rule {ref.rule}" if ref.order and ref.rule else "")
        for ref in claim.statutory_references
    )


def _format_claimed_citations(claim: ClassifiedClaim) -> str:
    if not claim.extracted_citations:
        return "(none)"
    return ", ".join(c.raw_text for c in claim.extracted_citations)


def _call_verdict_llm(claim: ClassifiedClaim, sources: list[RetrievalResult]) -> dict:
    chunks = [r.chunk for r in sources]
    user_prompt = VERDICT_ENGINE_USER_TEMPLATE.format(
        claim_text=claim.sentence.text,
        claim_type=claim.claim_type.value,
        statutory_refs=_format_statutory_refs(claim),
        claimed_citations=_format_claimed_citations(claim),
        numbered_sources=format_sources_block(chunks),
    )

    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        try:
            return call_structured(
                VERDICT_ENGINE_SYSTEM, user_prompt, RENDER_VERDICT_TOOL["input_schema"]
            )
        except Exception as exc:  # invalid/unparseable JSON from the LLM
            last_error = exc
    raise RuntimeError(f"verdict engine failed after retry: {last_error}") from last_error


def render_verdict(claim: ClassifiedClaim, sources: list[RetrievalResult]) -> Verdict:
    result = _call_verdict_llm(claim, sources)
    chunks = [r.chunk for r in sources]

    evidence = []
    for item in result.get("evidence", []):
        source_number = item["source_number"]
        if not (1 <= source_number <= len(chunks)):
            continue
        chunk = chunks[source_number - 1]
        evidence.append(
            EvidenceSpan(
                source_type=chunk.source_type,
                source_id=chunk.chunk_id,
                source_citation=chunk.citation_string
                or f"{chunk.act_name} "
                + (f"Section {chunk.section_number}" if chunk.section_number else f"Order {chunk.order_number} Rule {chunk.rule_number}"),
                quoted_text=item["quoted_text"],
                relation=item["relation"],
            )
        )

    return Verdict(
        claim_id=claim.id,
        status=VerdictStatus(result["status"]),
        reasoning=result["reasoning"],
        evidence=evidence,
        missing_elements=result.get("missing_elements", []),
        confidence=result.get("confidence", 0.0),
    )
