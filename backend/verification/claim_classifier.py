"""
Classifies each Sentence in a document into a ClaimType by batching
sentences 10 at a time and calling the LLM with CLASSIFY_BATCH_TOOL's
structured-output schema.

extracted_citations on the returned ClassifiedClaim come from the
deterministic regex citation_extractor, not the LLM: the LLM's own
extracted_citations field is useful for judging citation intent but
carries no character offsets, so it cannot drive UI highlighting or
downstream citation verification, and regex extraction carries no
hallucination risk. statutory_references and claim_type/confidence come
from the LLM, which is better placed to interpret context-dependent
statutory mentions.
"""
from __future__ import annotations

from backend.ingestion.citation_extractor import extract_citations
from backend.models.schemas import ClaimType, ClassifiedClaim, Sentence, StatutoryReference
from backend.verification.llm_client import call_structured
from backend.verification.prompts import (
    CLAIM_CLASSIFIER_SYSTEM,
    CLAIM_CLASSIFIER_USER_TEMPLATE,
    CLASSIFY_BATCH_TOOL,
)

BATCH_SIZE = 10


def _batches(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _classify_batch(batch: list[Sentence]) -> dict[int, dict]:
    numbered_sentences = "\n".join(f"{i}: {s.text}" for i, s in enumerate(batch))
    user_prompt = CLAIM_CLASSIFIER_USER_TEMPLATE.format(
        n=len(batch), numbered_sentences=numbered_sentences
    )
    result = call_structured(
        CLAIM_CLASSIFIER_SYSTEM, user_prompt, CLASSIFY_BATCH_TOOL["input_schema"]
    )
    return {c["sentence_index"]: c for c in result.get("classifications", [])}


def classify_claims(sentences: list[Sentence]) -> list[ClassifiedClaim]:
    claims: list[ClassifiedClaim] = []

    for batch in _batches(sentences, BATCH_SIZE):
        by_local_index = _classify_batch(batch)

        for local_index, sentence in enumerate(batch):
            classification = by_local_index.get(local_index)
            if classification is None:
                # LLM omitted this sentence from its response; fail safe to
                # narrative/low-confidence rather than guessing a claim type.
                classification = {
                    "claim_type": ClaimType.NARRATIVE.value,
                    "statutory_references": [],
                    "confidence": 0.0,
                }

            citations = extract_citations(sentence.text)
            for citation in citations:
                citation.char_start += sentence.char_start
                citation.char_end += sentence.char_start

            statutory_references = [
                StatutoryReference(**ref)
                for ref in classification.get("statutory_references", [])
            ]

            claims.append(
                ClassifiedClaim(
                    sentence=sentence,
                    paragraph_index=sentence.paragraph_index,
                    sentence_index=sentence.sentence_index,
                    claim_type=ClaimType(classification["claim_type"]),
                    extracted_citations=citations,
                    statutory_references=statutory_references,
                    classifier_confidence=classification.get("confidence", 0.0),
                )
            )

    return claims
