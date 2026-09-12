"""
The VERITAS pipeline orchestrator: parse -> split -> classify -> route +
verify each verifiable claim -> verify citations -> build the Report.

VERITAS_SPEC.md Part 6 Phase 5 sketches this as `async def
verify_document`, but every step here (LLM calls, BM25, Chroma) is
blocking I/O with no async client in use, so an async def would gain
nothing without also threading each call -- and Part 11's own risk
mitigation explicitly sanctions cutting the async job queue for a
synchronous pipeline. FastAPI's BackgroundTasks runs a sync callable in
a worker thread automatically, so this stays a plain function and the
API layer (backend/api/routes.py) is what makes it non-blocking for the
caller.
"""
from __future__ import annotations

import time
from pathlib import Path

from backend.aggregation.report_builder import build_report
from backend.ingestion.docx_parser import parse_docx
from backend.ingestion.pdf_parser import parse_pdf
from backend.ingestion.sentence_splitter import split_sentences
from backend.models.schemas import ClaimType, ClassifiedClaim, Report, RetrievalResult
from backend.verification.case_router import route_case
from backend.verification.citation_verifier import verify_all_citations
from backend.verification.claim_classifier import classify_claims
from backend.verification.statute_router import route_statute
from backend.verification.verdict_engine import render_verdict

VERDICT_ELIGIBLE_TYPES = {
    ClaimType.SUBSTANTIVE_PROPOSITION,
    ClaimType.PROCEDURAL_PROPOSITION,
    ClaimType.REMEDY_PROCEDURE,
}


def parse_document(file_path: str | Path):
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)
    if suffix == ".docx":
        return parse_docx(path)
    raise ValueError(f"Unsupported file type: {suffix!r} (expected .pdf or .docx)")


def route_and_retrieve(claim: ClassifiedClaim) -> list[RetrievalResult]:
    return route_statute(claim.sentence.text) + route_case(claim.sentence.text)


def verify_document(file_path: str | Path, job_id: str, original_filename: str | None = None) -> Report:
    start = time.monotonic()

    paragraphs = parse_document(file_path)
    sentences = split_sentences(paragraphs)
    claims = classify_claims(sentences)

    verdicts = []
    sources_by_claim_id: dict[str, list[RetrievalResult]] = {}
    for claim in claims:
        if claim.claim_type in VERDICT_ELIGIBLE_TYPES:
            sources = route_and_retrieve(claim)
            sources_by_claim_id[claim.id] = sources
            verdicts.append(render_verdict(claim, sources))

    all_citations = [c for claim in claims for c in claim.extracted_citations]
    citation_verdicts = verify_all_citations(all_citations)

    processing_time_seconds = time.monotonic() - start

    return build_report(
        job_id=job_id,
        filename=original_filename or Path(file_path).name,
        claims=claims,
        verdicts=verdicts,
        citation_verdicts=citation_verdicts,
        total_sentences_ingested=len(sentences),
        processing_time_seconds=processing_time_seconds,
        sources_by_claim_id=sources_by_claim_id,
    )
