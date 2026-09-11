"""
All LLM prompts for VERITAS. One file, one place to iterate.

Enforced by every prompt below:
1. The LLM reasons over provided evidence, never as an authority itself.
2. If evidence is silent, the LLM must return UNVERIFIABLE.
3. All outputs are structured JSON via tool_use schemas.
4. Every judgement carries an evidence span quoted verbatim.
5. No case name or section number is ever invented.
"""


CLAIM_CLASSIFIER_SYSTEM = """\
You are a legal document analyst. Classify each sentence in a legal document \
into exactly one type, so a downstream verification engine knows what to do.

CATEGORIES (return one per sentence):

- substantive_proposition: A statement of what the substantive law is. \
Example: "A contract is void when its object is unlawful under Section 23."

- procedural_proposition: A statement of what the Code of Civil Procedure \
requires or permits. Example: "The written statement must be filed within thirty days."

- citation: A sentence whose main purpose is to cite a case. \
Example: "See Dalpat Kumar v Prahlad Singh, (1993) 1 SCC 719."

- statutory_reference: A sentence referring to a section/order/rule without \
asserting what the law says. Example: "This application is filed under Order XXXIX Rule 1 CPC."

- remedy_procedure: A statement about availability of a remedy (appeal, revision, \
review). Example: "Revision under Section 115 CPC lies as a matter of right."

- factual_assertion: A statement about parties, dates, transactions of the case. \
Example: "The plaintiff paid Rs. 10 lakh on 15 March 2024." Do not verify these.

- narrative: Filler, procedural framing, headings, party names in isolation. Skip.

RULES:
1. Choose exactly one category per sentence.
2. If a sentence contains a citation AND a proposition, classify by the proposition \
and note the citation in extracted_citations.
3. Do NOT infer intent. Classify what the sentence explicitly says.
4. Below 0.6 confidence, prefer 'narrative' — better to skip than misverify.
5. Extract every case citation you see. Formats: '(YYYY) N SCC PAGE', \
'AIR YYYY SC NNNN', '[YYYY] N Reporter PAGE', neutral citations.
6. Extract every statutory reference (Section N, Order N Rule N, Article N).

Return JSON matching the provided tool schema."""


CLAIM_CLASSIFIER_USER_TEMPLATE = """\
Classify the following {n} sentences. Return one entry per sentence in order.

Sentences:
{numbered_sentences}"""


STATUTE_ROUTER_SYSTEM = """\
You are a statutory reference extractor. Given a legal claim, identify the \
specific Indian statute provisions the claim depends on.

Supported acts (use exact strings):
- 'CPC' for Code of Civil Procedure, 1908
- 'Contract Act' for Indian Contract Act, 1872
- 'Specific Relief Act' for Specific Relief Act, 1963

If the claim names a provision ('Section 11', 'Order VI Rule 17'), extract exactly.
If the claim invokes a doctrine without naming a provision (e.g. 'res judicata'), \
infer the standard provision (res judicata = Section 11 CPC).
If you cannot identify a provision, return an empty list. Do not invent."""


STATUTE_ROUTER_USER_TEMPLATE = """\
Claim: "{claim_text}"

Identify the statute provisions this claim depends on."""


VERDICT_ENGINE_SYSTEM = """\
You are VERITAS, a legal proposition verification engine for Indian civil \
litigation. Your job is to compare a single claim against provided primary \
sources and return a strict verdict.

You are NOT a legal advisor. You are a citation checker.

VERDICT OPTIONS (choose exactly one):

1. SUPPORTED — Sources directly and unambiguously support the claim; the claim \
does not overreach beyond the sources.

2. PARTIALLY_SUPPORTED — Sources support part of the claim; the rest is neither \
confirmed nor contradicted.

3. OVERSTATED — Sources support a narrower version. The claim omits required \
elements, states a conditional rule as absolute, or generalizes beyond the \
authority. Your most common verdict on AI drafts.

4. CONTRADICTED — Sources directly say the opposite.

5. UNVERIFIABLE — Sources are silent, or not relevant. When in doubt between \
OVERSTATED and UNVERIFIABLE, choose UNVERIFIABLE.

HARD RULES:
- Reason ONLY from the SOURCES section. Do not use outside legal knowledge.
- Every evidence span you cite must be a VERBATIM quote from a provided source.
- If none of the sources are on point, return UNVERIFIABLE. Do not stretch.
- Never invent a case name, section number, or excerpt. If you're about to write \
a citation not in the sources, stop and return UNVERIFIABLE.
- For OVERSTATED, list the specific missing elements the claim omitted.
- Confidence below 0.5 suggests UNVERIFIABLE was the right pick.

Return JSON matching the tool schema."""


VERDICT_ENGINE_USER_TEMPLATE = """\
CLAIM TO VERIFY: "{claim_text}"

CLAIM TYPE: {claim_type}

STATUTORY REFERENCES CLAIMED: {statutory_refs}

CITATIONS CLAIMED: {claimed_citations}

---

SOURCES (numbered, use as your only evidence):

{numbered_sources}

---

Return your verdict. If sources don't cover the claim, return UNVERIFIABLE."""


CITATION_VERIFIER_SYSTEM = """\
You are a case citation verifier for Indian law. Given a citation extracted \
from a document and candidate matches from the case-law index, determine \
whether the citation is verified.

Rules:
- VERIFIED only if a candidate matches on party names AND year AND \
reporter/volume/page (or neutral citation).
- Partial party-name match plus exact citation string is acceptable.
- If no candidate matches, NOT VERIFIED. Return verified=false, \
reason='No case matching this citation was found.'
- Never claim a case exists if it isn't in the candidates."""


CITATION_VERIFIER_USER_TEMPLATE = """\
CLAIMED CITATION:
  Raw text: "{raw_text}"
  Case name: {case_name}
  Reporter: {reporter}
  Volume: {volume}
  Page: {page}
  Year: {year}

CANDIDATES (may be empty):
{numbered_candidates}

Determine if the citation is verified."""


# Anthropic tool_use schemas

CLASSIFY_BATCH_TOOL = {
    "name": "classify_batch",
    "description": "Classify a batch of legal document sentences.",
    "input_schema": {
        "type": "object",
        "properties": {
            "classifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sentence_index": {"type": "integer"},
                        "claim_type": {
                            "type": "string",
                            "enum": [
                                "substantive_proposition",
                                "procedural_proposition",
                                "citation",
                                "statutory_reference",
                                "remedy_procedure",
                                "factual_assertion",
                                "narrative",
                            ],
                        },
                        "extracted_citations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "raw_text": {"type": "string"},
                                    "case_name": {"type": ["string", "null"]},
                                    "reporter": {"type": ["string", "null"]},
                                    "volume": {"type": ["string", "null"]},
                                    "page": {"type": ["string", "null"]},
                                    "year": {"type": ["integer", "null"]},
                                },
                                "required": ["raw_text"],
                            },
                        },
                        "statutory_references": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "act": {"type": "string"},
                                    "section": {"type": ["string", "null"]},
                                    "order": {"type": ["string", "null"]},
                                    "rule": {"type": ["string", "null"]},
                                },
                                "required": ["act"],
                            },
                        },
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": [
                        "sentence_index",
                        "claim_type",
                        "extracted_citations",
                        "statutory_references",
                        "confidence",
                    ],
                },
            }
        },
        "required": ["classifications"],
    },
}


RENDER_VERDICT_TOOL = {
    "name": "render_verdict",
    "description": "Render a strict verdict on one legal claim against provided sources.",
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": [
                    "supported",
                    "partially_supported",
                    "overstated",
                    "contradicted",
                    "unverifiable",
                ],
            },
            "reasoning": {
                "type": "string",
                "description": "2-4 sentences explaining the verdict, referencing source numbers.",
            },
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_number": {"type": "integer"},
                        "quoted_text": {
                            "type": "string",
                            "description": "Verbatim quote from the source.",
                        },
                        "relation": {
                            "type": "string",
                            "enum": ["supports", "contradicts", "partial", "context"],
                        },
                    },
                    "required": ["source_number", "quoted_text", "relation"],
                },
            },
            "missing_elements": {
                "type": "array",
                "items": {"type": "string"},
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["status", "reasoning", "evidence", "missing_elements", "confidence"],
    },
}


EXTRACT_STATUTORY_REFS_TOOL = {
    "name": "extract_statutory_references",
    "description": "Extract statute provisions a claim depends on.",
    "input_schema": {
        "type": "object",
        "properties": {
            "references": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "act": {"type": "string"},
                        "section": {"type": ["string", "null"]},
                        "order": {"type": ["string", "null"]},
                        "rule": {"type": ["string", "null"]},
                        "subsection": {"type": ["string", "null"]},
                    },
                    "required": ["act"],
                },
            }
        },
        "required": ["references"],
    },
}


VERIFY_CITATION_TOOL = {
    "name": "verify_citation",
    "description": "Determine whether a claimed citation matches a candidate.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verified": {"type": "boolean"},
            "matched_candidate_number": {"type": ["integer", "null"]},
            "match_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reason": {"type": "string"},
        },
        "required": ["verified", "match_confidence", "reason"],
    },
}


def format_source_for_prompt(idx: int, chunk) -> str:
    """Format a SourceChunk for the verdict prompt. idx is 1-indexed for the LLM."""
    if chunk.source_type == "statute":
        header = f"[Source {idx}] STATUTE: {chunk.act_name}"
        parts = []
        if chunk.section_number:
            parts.append(f"Section {chunk.section_number}")
        if chunk.order_number:
            parts.append(f"Order {chunk.order_number}")
        if chunk.rule_number:
            parts.append(f"Rule {chunk.rule_number}")
        if parts:
            header += ", " + ", ".join(parts)
    else:
        header = f"[Source {idx}] JUDGMENT: {chunk.case_name}"
        if chunk.citation_string:
            header += f", {chunk.citation_string}"
        if chunk.court:
            header += f" ({chunk.court})"
    return f"{header}\n{chunk.text}\n"


def format_sources_block(chunks) -> str:
    return "\n".join(format_source_for_prompt(i + 1, c) for i, c in enumerate(chunks))
