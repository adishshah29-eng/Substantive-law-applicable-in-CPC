"""
Verifies whether a citation extracted from a document actually exists in
the golden-set judgment corpus: exact match first (case name substring +
year exact + reporter/volume/page match), then fuzzy match via rapidfuzz
WRatio (threshold 85) as a secondary check for minor OCR/typo variation.
Never claims a case exists if it isn't in the candidates.
"""
from __future__ import annotations

import re
from pathlib import Path

from rapidfuzz import fuzz

from backend.ingestion.citation_extractor import extract_citations
from backend.indexing.judgment_indexer import normalize_all_judgments
from backend.models.schemas import Citation, CitationVerdict, SourceChunk

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_SET_DIR = REPO_ROOT / "data" / "judgments" / "golden_set"

FUZZY_MATCH_THRESHOLD = 85

_VERSUS_RE = re.compile(r"\b(vs\.?|versus|v\.?)\b", re.I)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9 ]")

_candidates_cache: list[SourceChunk] | None = None


def normalize_case_name(name: str) -> str:
    """Strip vs/v./versus, lowercase, remove punctuation, collapse whitespace."""
    name = name.lower()
    name = _VERSUS_RE.sub(" v ", name)
    name = _NON_ALNUM_RE.sub(" ", name)
    return re.sub(r"\s+", " ", name).strip()


def _load_candidates() -> list[SourceChunk]:
    global _candidates_cache
    if _candidates_cache is None:
        chunks = normalize_all_judgments(GOLDEN_SET_DIR)
        by_case_name: dict[str, SourceChunk] = {}
        for chunk in chunks:
            by_case_name.setdefault(chunk.case_name, chunk)
        _candidates_cache = list(by_case_name.values())
    return _candidates_cache


def _parse_citation_string(citation_string: str | None) -> dict:
    """Re-run the citation regex bank on a stored citation_string (e.g.
    "(1993) 1 SCC 719") to get comparable year/reporter/volume/page fields."""
    if not citation_string:
        return {}
    matches = extract_citations(citation_string)
    if not matches:
        return {}
    match = matches[0]
    return {
        "year": match.year,
        "reporter": (match.reporter or "").upper(),
        "volume": match.volume,
        "page": match.page,
    }


def _is_exact_match(citation: Citation, norm_claimed: str, candidate: SourceChunk) -> bool:
    if not norm_claimed:
        return False
    norm_candidate = normalize_case_name(candidate.case_name or "")
    name_match = norm_claimed in norm_candidate or norm_candidate in norm_claimed

    parsed = _parse_citation_string(candidate.citation_string)
    year_match = citation.year is not None and parsed.get("year") == citation.year
    page_match = citation.page is not None and parsed.get("page") == citation.page
    reporter_match = (
        citation.reporter is not None
        and parsed.get("reporter") == citation.reporter.upper()
    )

    return name_match and year_match and page_match and reporter_match


def verify_citation(citation: Citation) -> CitationVerdict:
    candidates = _load_candidates()
    norm_claimed = normalize_case_name(citation.case_name or "")

    for candidate in candidates:
        if _is_exact_match(citation, norm_claimed, candidate):
            return CitationVerdict(
                citation=citation,
                verified=True,
                matched_case_id=candidate.chunk_id,
                matched_case_name=candidate.case_name,
                match_confidence=1.0,
                reason=(
                    f"Exact match on case name, year, and citation "
                    f"({candidate.citation_string}) against the golden-set corpus."
                ),
            )

    if norm_claimed:
        best_candidate, best_score = None, 0.0
        for candidate in candidates:
            score = fuzz.WRatio(norm_claimed, normalize_case_name(candidate.case_name or ""))
            if score > best_score:
                best_candidate, best_score = candidate, score

        if best_candidate is not None and best_score >= FUZZY_MATCH_THRESHOLD:
            parsed = _parse_citation_string(best_candidate.citation_string)
            if citation.year is not None and parsed.get("year") == citation.year:
                return CitationVerdict(
                    citation=citation,
                    verified=True,
                    matched_case_id=best_candidate.chunk_id,
                    matched_case_name=best_candidate.case_name,
                    match_confidence=best_score / 100.0,
                    reason=(
                        f"Fuzzy case-name match ({best_score:.0f}/100) with matching "
                        f"year against {best_candidate.case_name}, "
                        f"{best_candidate.citation_string}."
                    ),
                )

    return CitationVerdict(
        citation=citation,
        verified=False,
        match_confidence=0.0,
        reason="No case matching this citation was found in the searched databases.",
    )


def verify_all_citations(citations: list[Citation]) -> list[CitationVerdict]:
    return [verify_citation(c) for c in citations]
