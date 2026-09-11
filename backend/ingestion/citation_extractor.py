"""
Regex-based extraction of Indian case citations from free text, covering
the formats named in VERITAS_SPEC.md Part 6 Phase 3:
  - "(YYYY) N SCC PAGE"            e.g. (1993) 1 SCC 719
  - "AIR YYYY SC NNNN"             e.g. AIR 1960 SC 941
  - "[YYYY] N Reporter PAGE"       e.g. [2021] 4 SCC 321
  - neutral citations              e.g. 2021 SCC OnLine SC 123 / 2006 INSC 162
"""
from __future__ import annotations

import re

from backend.models.schemas import Citation, CourtLevel

# A party name: starts with a capital letter, allows the usual punctuation
# found in Indian case names (initials, "&", "Pvt Ltd", possessives, hyphens),
# and \s rather than a literal space so a PDF-extracted line wrap inside a
# party name (e.g. "ABC Developers\nPvt Ltd") doesn't break the match.
_PARTY = r"[A-Z][A-Za-z0-9.&'’\-,\s]*?"
_CASE_NAME_RE = re.compile(
    rf"(?P<case_name>{_PARTY}\s+v\.?s?\.?\s+{_PARTY})\s*,?\s*$"
)

_COURT_ABBREV = {
    "SC": CourtLevel.SUPREME_COURT,
    "INSC": CourtLevel.SUPREME_COURT,
}

_CITATION_PATTERNS = [
    # (1993) 1 SCC 719
    re.compile(
        r"\((?P<year>\d{4})\)\s*(?P<volume>\d+)\s*(?P<reporter>SCC|SCR)\s*(?P<page>\d+)"
    ),
    # AIR 1960 SC 941
    re.compile(
        r"(?P<reporter>AIR)\s*(?P<year>\d{4})\s*(?P<court>[A-Za-z]{2,4})\s*(?P<page>\d+)"
    ),
    # [2021] 4 SCC 321
    re.compile(
        r"\[(?P<year>\d{4})\]\s*(?P<volume>\d+)\s*(?P<reporter>[A-Za-z]{2,10})\s*(?P<page>\d+)"
    ),
    # 2021 SCC OnLine SC 123 (neutral-style reporter citation)
    re.compile(
        r"(?P<year>\d{4})\s*(?P<reporter>SCC\s*OnLine)\s*(?P<court>[A-Za-z]{2,4})\s*(?P<page>\d+)"
    ),
    # 2006 INSC 162 (Supreme Court neutral citation)
    re.compile(r"(?P<year>\d{4})\s*(?P<reporter>INSC)\s*(?P<page>\d+)"),
]

_CASE_NAME_LOOKBACK_CHARS = 100

# Common lead-in phrases that can precede a case name in a sentence but are
# not part of it (e.g. "See Dalpat Kumar v Prahlad Singh" -> "Dalpat Kumar
# v Prahlad Singh"). The case-name regex is greedy from the leftmost
# capital letter in the lookback window, so these are stripped afterward.
_LEADING_FILLER_RE = re.compile(
    r"^(?:see|as\s+held\s+in|held\s+in|reference:?|per|citing|under|"
    r"according\s+to|in)\s+",
    re.I,
)


def _strip_leading_filler(case_name: str) -> str:
    while True:
        new_name = _LEADING_FILLER_RE.sub("", case_name)
        if new_name == case_name:
            return case_name
        case_name = new_name


def _resolve_court(match: re.Match) -> CourtLevel | None:
    groupdict = match.groupdict()
    court_token = groupdict.get("court")
    reporter = groupdict.get("reporter", "")
    if court_token:
        return _COURT_ABBREV.get(court_token.upper(), CourtLevel.OTHER)
    if reporter and "INSC" in reporter.upper():
        return CourtLevel.SUPREME_COURT
    return None


def _find_case_name(text: str, citation_start: int) -> tuple[str | None, int]:
    """Look backward from the citation's start for a "X v Y" case name
    immediately preceding it (allowing for a comma/space separator).
    Returns (case_name, span_start) where span_start extends the citation's
    overall span to include the case name when found."""
    window_start = max(0, citation_start - _CASE_NAME_LOOKBACK_CHARS)
    window = text[window_start:citation_start]
    match = _CASE_NAME_RE.search(window)
    if not match:
        return None, citation_start

    case_name = re.sub(r"\s+", " ", match.group("case_name")).strip()
    cleaned = _strip_leading_filler(case_name)
    # The case name's span within the window shrinks by however much filler
    # was stripped from the front, so the overall citation span (which
    # starts at the case name) must shift forward by the same amount.
    trimmed_chars = len(case_name) - len(cleaned)
    span_start = window_start + match.start() + trimmed_chars
    return cleaned, span_start


def extract_citations(text: str) -> list[Citation]:
    citations: list[Citation] = []
    seen_spans: set[tuple[int, int]] = set()

    for pattern in _CITATION_PATTERNS:
        for match in pattern.finditer(text):
            citation_start, citation_end = match.start(), match.end()
            case_name, span_start = _find_case_name(text, citation_start)
            span = (span_start, citation_end)
            if span in seen_spans:
                continue
            seen_spans.add(span)

            groupdict = match.groupdict()
            # char_start/char_end must stay accurate against the original
            # text for UI highlighting, but raw_text is for display, so its
            # whitespace (e.g. a PDF line wrap inside a party name) is
            # normalized to a single space.
            raw_text = re.sub(r"\s+", " ", text[span_start:citation_end]).strip()
            citations.append(
                Citation(
                    raw_text=raw_text,
                    case_name=case_name,
                    reporter=groupdict.get("reporter"),
                    volume=groupdict.get("volume"),
                    page=groupdict.get("page"),
                    year=int(groupdict["year"]) if groupdict.get("year") else None,
                    court=_resolve_court(match),
                    char_start=span_start,
                    char_end=citation_end,
                )
            )

    citations.sort(key=lambda c: c.char_start)
    return citations
