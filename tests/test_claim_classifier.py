"""
Phase 3 acceptance test: 5 example sentences (the worked examples from
CLAIM_CLASSIFIER_SYSTEM itself, in backend/verification/prompts.py) with
their expected claim_type classifications.
"""
from __future__ import annotations

import os

import pytest

from backend.models.schemas import ClaimType, Sentence
from backend.verification.claim_classifier import classify_claims

pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set; claim classifier needs a live LLM call",
)

EXAMPLES = [
    ("A contract is void when its object is unlawful under Section 23.", ClaimType.SUBSTANTIVE_PROPOSITION),
    ("The written statement must be filed within thirty days.", ClaimType.PROCEDURAL_PROPOSITION),
    ("See Dalpat Kumar v Prahlad Singh, (1993) 1 SCC 719.", ClaimType.CITATION),
    ("This application is filed under Order XXXIX Rule 1 CPC.", ClaimType.STATUTORY_REFERENCE),
    ("The plaintiff paid Rs. 10 lakh on 15 March 2024.", ClaimType.FACTUAL_ASSERTION),
]


def _make_sentence(index: int, text: str) -> Sentence:
    return Sentence(
        paragraph_index=0,
        sentence_index=index,
        text=text,
        char_start=0,
        char_end=len(text),
    )


def test_classifier_matches_expected_claim_types():
    sentences = [_make_sentence(i, text) for i, (text, _) in enumerate(EXAMPLES)]
    claims = classify_claims(sentences)

    assert len(claims) == len(EXAMPLES)
    mismatches = [
        (text, expected, claim.claim_type)
        for claim, (text, expected) in zip(claims, EXAMPLES)
        if claim.claim_type != expected
    ]
    assert not mismatches, f"classification mismatches: {mismatches}"
