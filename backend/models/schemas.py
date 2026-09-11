"""
VERITAS data model. Every object that flows through the pipeline is defined here.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class ClaimType(str, Enum):
    SUBSTANTIVE_PROPOSITION = "substantive_proposition"
    PROCEDURAL_PROPOSITION = "procedural_proposition"
    CITATION = "citation"
    STATUTORY_REFERENCE = "statutory_reference"
    REMEDY_PROCEDURE = "remedy_procedure"
    FACTUAL_ASSERTION = "factual_assertion"
    NARRATIVE = "narrative"


class VerdictStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    OVERSTATED = "overstated"
    CONTRADICTED = "contradicted"
    UNVERIFIABLE = "unverifiable"


class SourceType(str, Enum):
    STATUTE = "statute"
    JUDGMENT = "judgment"


class CourtLevel(str, Enum):
    SUPREME_COURT = "supreme_court"
    HIGH_COURT = "high_court"
    DISTRICT_COURT = "district_court"
    TRIBUNAL = "tribunal"
    OTHER = "other"


class Paragraph(BaseModel):
    index: int
    text: str
    page: Optional[int] = None


class Sentence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    paragraph_index: int
    sentence_index: int
    text: str
    char_start: int
    char_end: int


class Citation(BaseModel):
    raw_text: str
    case_name: Optional[str] = None
    reporter: Optional[str] = None
    volume: Optional[str] = None
    page: Optional[str] = None
    year: Optional[int] = None
    court: Optional[CourtLevel] = None
    char_start: int
    char_end: int


class CitationVerdict(BaseModel):
    citation: Citation
    verified: bool
    matched_case_id: Optional[str] = None
    matched_case_name: Optional[str] = None
    match_confidence: float = 0.0
    reason: str


class StatutoryReference(BaseModel):
    act: str
    section: Optional[str] = None
    order: Optional[str] = None
    rule: Optional[str] = None
    subsection: Optional[str] = None


class Claim(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    sentence: Sentence
    paragraph_index: int
    sentence_index: int


class ClassifiedClaim(Claim):
    claim_type: ClaimType
    extracted_citations: list[Citation] = Field(default_factory=list)
    statutory_references: list[StatutoryReference] = Field(default_factory=list)
    classifier_confidence: float = 0.0
    classifier_reasoning: Optional[str] = None


class SourceChunk(BaseModel):
    chunk_id: str
    source_type: SourceType
    text: str
    act_name: Optional[str] = None
    section_number: Optional[str] = None
    order_number: Optional[str] = None
    rule_number: Optional[str] = None
    subsection: Optional[str] = None
    case_name: Optional[str] = None
    citation_string: Optional[str] = None
    court: Optional[CourtLevel] = None
    year: Optional[int] = None
    judges: Optional[list[str]] = None
    source_url: Optional[str] = None
    chunk_index: Optional[int] = None


class RetrievalResult(BaseModel):
    chunk: SourceChunk
    score: float
    bm25_rank: Optional[int] = None
    dense_rank: Optional[int] = None
    retrieval_method: Literal["hybrid", "bm25_only", "dense_only", "exact"] = "hybrid"


class EvidenceSpan(BaseModel):
    source_type: SourceType
    source_id: str
    source_citation: str
    quoted_text: str
    relation: Literal["supports", "contradicts", "partial", "context"]


class Verdict(BaseModel):
    claim_id: str
    status: VerdictStatus
    reasoning: str
    evidence: list[EvidenceSpan] = Field(default_factory=list)
    missing_elements: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    verified_at: datetime = Field(default_factory=datetime.utcnow)


class ClaimWithVerdict(BaseModel):
    claim: ClassifiedClaim
    verdict: Verdict
    retrieved_sources: list[RetrievalResult] = Field(default_factory=list)


class CategoryBreakdown(BaseModel):
    substantive_verified: int = 0
    cpc_verified: int = 0
    citations_verified: int = 0
    unsupported_propositions: int = 0
    procedural_issues: int = 0
    conflicting_authorities: int = 0
    fabricated_citations: int = 0


class Report(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    job_id: str
    document_id: str
    filename: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    integrity_score: float
    procedural_risk_flag: bool
    procedural_risk_summary: Optional[str] = None
    category_breakdown: CategoryBreakdown
    claims: list[ClaimWithVerdict]
    citation_verdicts: list[CitationVerdict]
    total_claims_analyzed: int
    total_sentences_ingested: int
    processing_time_seconds: float


class VerifyResponse(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: float = 0.0
    current_step: Optional[str] = None
    error: Optional[str] = None
    report: Optional[Report] = None
