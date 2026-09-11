"""
Phase 4 acceptance tests: three golden cases from the seeded demo document
(VERITAS_SPEC.md Part 8/9) run through the real routing + verdict pipeline.

Prop 4 ("unrestricted right to amend ... under Order VI Rule 17") is
tested against OVERSTATED rather than the spec's suggested CONTRADICTED.
Empirically, and per VERDICT_ENGINE_SYSTEM's own definitions, the sources
do not say the opposite of the claim (the defendant does have a right to
amend); they establish a narrower, conditional version of it (subject to
the trial-commencement proviso), which is squarely OVERSTATED's
definition ("states a conditional rule as absolute"), not CONTRADICTED's
("sources directly say the opposite"). VERITAS_SPEC.md Part 9 itself
authorizes this: "Correct any drift between what the propositions say and
what the golden judgments actually hold." Forcing CONTRADICTED here would
mean steering the verdict engine to a predetermined answer rather than
letting it reason from the sources, which is the opposite of what VERITAS
is for.
"""
from __future__ import annotations

import os

import pytest

from backend.models.schemas import ClaimType, ClassifiedClaim, Sentence, VerdictStatus
from backend.verification.case_router import route_case
from backend.verification.statute_router import route_statute
from backend.verification.verdict_engine import render_verdict

pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set; verdict engine needs a live LLM call",
)


def _make_claim(text: str, claim_type: ClaimType) -> ClassifiedClaim:
    sentence = Sentence(paragraph_index=0, sentence_index=0, text=text, char_start=0, char_end=len(text))
    return ClassifiedClaim(sentence=sentence, paragraph_index=0, sentence_index=0, claim_type=claim_type)


def _route_and_verify(claim: ClassifiedClaim):
    sources = route_statute(claim.sentence.text) + route_case(claim.sentence.text)
    return render_verdict(claim, sources)


def test_prop1_section_10_contract_act_is_supported():
    claim = _make_claim(
        "Under Section 10 of the Indian Contract Act, 1872, all agreements are contracts "
        "if they are made by the free consent of parties competent to contract, for a "
        "lawful consideration and with a lawful object, and are not expressly declared "
        "to be void.",
        ClaimType.SUBSTANTIVE_PROPOSITION,
    )
    verdict = _route_and_verify(claim)
    assert verdict.status == VerdictStatus.SUPPORTED, verdict.reasoning


def test_prop3_prima_facie_alone_is_overstated():
    claim = _make_claim(
        "The plaintiff is entitled to an interim injunction under Order XXXIX Rules 1 "
        "and 2 CPC upon establishing a prima facie case. Once a prima facie case is "
        "shown, the injunction must follow as a matter of course.",
        ClaimType.PROCEDURAL_PROPOSITION,
    )
    verdict = _route_and_verify(claim)
    assert verdict.status == VerdictStatus.OVERSTATED, verdict.reasoning
    missing_lower = " ".join(verdict.missing_elements).lower()
    assert "balance of convenience" in missing_lower
    assert "irreparable" in missing_lower


def test_prop4_unrestricted_amendment_right_is_overstated():
    claim = _make_claim(
        "The defendant, if he seeks to bring on record any additional pleadings or "
        "fresh grounds of defence, has an unrestricted right to amend the written "
        "statement at any stage of the proceeding under Order VI Rule 17 CPC.",
        ClaimType.PROCEDURAL_PROPOSITION,
    )
    verdict = _route_and_verify(claim)
    assert verdict.status == VerdictStatus.OVERSTATED, verdict.reasoning
