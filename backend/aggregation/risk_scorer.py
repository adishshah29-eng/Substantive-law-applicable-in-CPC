"""
Aggregates per-claim Verdicts and per-citation CitationVerdicts into the
document-level integrity score, category rollup, and procedural risk flag.
"""
from __future__ import annotations

from backend.models.schemas import (
    CategoryBreakdown,
    CitationVerdict,
    ClaimType,
    ClassifiedClaim,
    Verdict,
    VerdictStatus,
)

VERDICT_WEIGHTS = {
    VerdictStatus.SUPPORTED: 1.0,
    VerdictStatus.PARTIALLY_SUPPORTED: 0.7,
    VerdictStatus.OVERSTATED: 0.4,
    VerdictStatus.UNVERIFIABLE: 0.3,
    VerdictStatus.CONTRADICTED: 0.0,
}

FABRICATED_CITATION_PENALTY = 15.0

_UNSUPPORTED_STATUSES = {
    VerdictStatus.OVERSTATED,
    VerdictStatus.PARTIALLY_SUPPORTED,
    VerdictStatus.UNVERIFIABLE,
}
_PROCEDURAL_ISSUE_STATUSES = {
    VerdictStatus.OVERSTATED,
    VerdictStatus.CONTRADICTED,
    VerdictStatus.PARTIALLY_SUPPORTED,
    VerdictStatus.UNVERIFIABLE,
}


def compute_integrity_score(
    verdicts: list[Verdict], citation_verdicts: list[CitationVerdict]
) -> float:
    if verdicts:
        raw_score = 100.0 * sum(VERDICT_WEIGHTS[v.status] for v in verdicts) / len(verdicts)
    else:
        raw_score = 100.0

    fabricated_count = sum(1 for c in citation_verdicts if not c.verified)
    score = raw_score - FABRICATED_CITATION_PENALTY * fabricated_count
    return max(0.0, min(100.0, score))


def category_breakdown(
    claims: list[ClassifiedClaim],
    verdicts: list[Verdict],
    citation_verdicts: list[CitationVerdict],
) -> CategoryBreakdown:
    verdict_by_claim_id = {v.claim_id: v for v in verdicts}

    substantive_verified = 0
    cpc_verified = 0
    unsupported_propositions = 0
    procedural_issues = 0
    conflicting_authorities = 0

    for claim in claims:
        verdict = verdict_by_claim_id.get(claim.id)
        if verdict is None:
            continue

        if verdict.status == VerdictStatus.SUPPORTED:
            if claim.claim_type == ClaimType.SUBSTANTIVE_PROPOSITION:
                substantive_verified += 1
            elif claim.claim_type == ClaimType.PROCEDURAL_PROPOSITION:
                cpc_verified += 1

        if verdict.status in _UNSUPPORTED_STATUSES:
            unsupported_propositions += 1

        if claim.claim_type == ClaimType.PROCEDURAL_PROPOSITION and verdict.status in _PROCEDURAL_ISSUE_STATUSES:
            procedural_issues += 1

        if verdict.status == VerdictStatus.CONTRADICTED:
            conflicting_authorities += 1

    citations_verified = sum(1 for c in citation_verdicts if c.verified)
    fabricated_citations = sum(1 for c in citation_verdicts if not c.verified)

    return CategoryBreakdown(
        substantive_verified=substantive_verified,
        cpc_verified=cpc_verified,
        citations_verified=citations_verified,
        unsupported_propositions=unsupported_propositions,
        procedural_issues=procedural_issues,
        conflicting_authorities=conflicting_authorities,
        fabricated_citations=fabricated_citations,
    )


def compute_procedural_risk_flag(
    verdicts: list[Verdict], claims: list[ClassifiedClaim]
) -> tuple[bool, str | None]:
    verdict_by_claim_id = {v.claim_id: v for v in verdicts}

    flagged: list[str] = []
    for claim in claims:
        if claim.claim_type != ClaimType.PROCEDURAL_PROPOSITION:
            continue
        verdict = verdict_by_claim_id.get(claim.id)
        if verdict is None or verdict.status not in (VerdictStatus.OVERSTATED, VerdictStatus.CONTRADICTED):
            continue
        snippet = claim.sentence.text.strip()
        if len(snippet) > 60:
            snippet = snippet[:57].rstrip() + "..."
        flagged.append(snippet)

    if not flagged:
        return False, None

    descriptions = "; ".join(flagged)
    count = len(flagged)
    plural = "claims" if count != 1 else "claim"
    summary = (
        f"{count} procedural {plural} ({descriptions}) are overstated or "
        f"contradicted and require review before filing."
    )
    return True, summary
