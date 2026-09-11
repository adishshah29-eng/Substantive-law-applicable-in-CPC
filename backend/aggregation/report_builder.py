"""
Assembles the final Report from a pipeline run's claims, verdicts, and
citation verdicts.
"""
from __future__ import annotations

from backend.aggregation.risk_scorer import (
    category_breakdown,
    compute_integrity_score,
    compute_procedural_risk_flag,
)
from backend.models.schemas import (
    CitationVerdict,
    ClaimWithVerdict,
    ClassifiedClaim,
    Report,
    RetrievalResult,
    Verdict,
)


def build_report(
    job_id: str,
    filename: str,
    claims: list[ClassifiedClaim],
    verdicts: list[Verdict],
    citation_verdicts: list[CitationVerdict],
    total_sentences_ingested: int,
    processing_time_seconds: float,
    sources_by_claim_id: dict[str, list[RetrievalResult]] | None = None,
) -> Report:
    sources_by_claim_id = sources_by_claim_id or {}
    verdict_by_claim_id = {v.claim_id: v for v in verdicts}

    claims_with_verdicts = [
        ClaimWithVerdict(
            claim=claim,
            verdict=verdict_by_claim_id[claim.id],
            retrieved_sources=sources_by_claim_id.get(claim.id, []),
        )
        for claim in claims
        if claim.id in verdict_by_claim_id
    ]

    integrity_score = compute_integrity_score(verdicts, citation_verdicts)
    breakdown = category_breakdown(claims, verdicts, citation_verdicts)
    procedural_risk_flag, procedural_risk_summary = compute_procedural_risk_flag(verdicts, claims)

    return Report(
        job_id=job_id,
        document_id=job_id,
        filename=filename,
        integrity_score=integrity_score,
        procedural_risk_flag=procedural_risk_flag,
        procedural_risk_summary=procedural_risk_summary,
        category_breakdown=breakdown,
        claims=claims_with_verdicts,
        citation_verdicts=citation_verdicts,
        total_claims_analyzed=len(verdicts),
        total_sentences_ingested=total_sentences_ingested,
        processing_time_seconds=processing_time_seconds,
    )
