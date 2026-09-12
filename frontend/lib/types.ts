export type ClaimType =
  | "substantive_proposition"
  | "procedural_proposition"
  | "citation"
  | "statutory_reference"
  | "remedy_procedure"
  | "factual_assertion"
  | "narrative";

export type VerdictStatus =
  | "supported"
  | "partially_supported"
  | "overstated"
  | "contradicted"
  | "unverifiable";

export type SourceType = "statute" | "judgment";

export interface Sentence {
  id: string;
  paragraph_index: number;
  sentence_index: number;
  text: string;
  char_start: number;
  char_end: number;
}

export interface Citation {
  raw_text: string;
  case_name: string | null;
  reporter: string | null;
  volume: string | null;
  page: string | null;
  year: number | null;
  court: string | null;
  char_start: number;
  char_end: number;
}

export interface CitationVerdict {
  citation: Citation;
  verified: boolean;
  matched_case_id: string | null;
  matched_case_name: string | null;
  match_confidence: number;
  reason: string;
}

export interface StatutoryReference {
  act: string;
  section: string | null;
  order: string | null;
  rule: string | null;
  subsection: string | null;
}

export interface ClassifiedClaim {
  id: string;
  sentence: Sentence;
  paragraph_index: number;
  sentence_index: number;
  claim_type: ClaimType;
  extracted_citations: Citation[];
  statutory_references: StatutoryReference[];
  classifier_confidence: number;
  classifier_reasoning: string | null;
}

export interface SourceChunk {
  chunk_id: string;
  source_type: SourceType;
  text: string;
  act_name: string | null;
  section_number: string | null;
  order_number: string | null;
  rule_number: string | null;
  subsection: string | null;
  case_name: string | null;
  citation_string: string | null;
  court: string | null;
  year: number | null;
  judges: string[] | null;
  source_url: string | null;
  chunk_index: number | null;
}

export interface RetrievalResult {
  chunk: SourceChunk;
  score: number;
  bm25_rank: number | null;
  dense_rank: number | null;
  retrieval_method: "hybrid" | "bm25_only" | "dense_only" | "exact";
}

export interface EvidenceSpan {
  source_type: SourceType;
  source_id: string;
  source_citation: string;
  quoted_text: string;
  relation: "supports" | "contradicts" | "partial" | "context";
}

export interface Verdict {
  claim_id: string;
  status: VerdictStatus;
  reasoning: string;
  evidence: EvidenceSpan[];
  missing_elements: string[];
  confidence: number;
  verified_at: string;
}

export interface ClaimWithVerdict {
  claim: ClassifiedClaim;
  verdict: Verdict;
  retrieved_sources: RetrievalResult[];
}

export interface CategoryBreakdown {
  substantive_verified: number;
  cpc_verified: number;
  citations_verified: number;
  unsupported_propositions: number;
  procedural_issues: number;
  conflicting_authorities: number;
  fabricated_citations: number;
}

export interface Report {
  job_id: string;
  document_id: string;
  filename: string;
  generated_at: string;
  integrity_score: number;
  procedural_risk_flag: boolean;
  procedural_risk_summary: string | null;
  category_breakdown: CategoryBreakdown;
  claims: ClaimWithVerdict[];
  citation_verdicts: CitationVerdict[];
  total_claims_analyzed: number;
  total_sentences_ingested: number;
  processing_time_seconds: number;
}

export interface JobStatusResponse {
  status: "queued" | "processing" | "completed" | "failed";
  error?: string | null;
}

export type ReportPollResult = Report | JobStatusResponse;

export function isReport(value: ReportPollResult): value is Report {
  return "integrity_score" in value;
}
