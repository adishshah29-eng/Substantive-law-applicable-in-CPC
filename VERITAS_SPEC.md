# VERITAS — Full Specification for Claude Code

**Project:** VERITAS — Civil Litigation Verification Engine (Substantive Law + CPC Procedural Law)
**Context:** Vibeathon / hackathon MVP, 24–72 hour build window
**Reader:** Claude Code, executing phase-by-phase against this spec

---

## HOW TO USE THIS DOCUMENT

This is the **single source of truth** for the VERITAS build. It contains, in order:

1. **Research summary** — the problem, quantified. Why we are building this and what makes it different.
2. **Scope lock** — exactly what we cover and what we do not.
3. **Data sources** — every URL, dataset, and fallback.
4. **Architecture** — system diagram, tech stack, design decisions with reasons.
5. **Repository layout** — the folder structure to create.
6. **Phased implementation plan** — Phase 0 through Phase 7, each with deliverables, acceptance criteria, and an executable prompt for you (Claude Code).
7. **Starter code** — full contents of `schemas.py`, `prompts.py`, and the seeded demo document, embedded inline. Copy them verbatim into the file paths shown.
8. **Demo script and risk mitigation** — how to win the pitch.

**Hard rule for the whole build:** Every claim VERITAS makes in its output must be traceable to a primary source in our corpus. If we cannot cite it, we do not say it.

---

## PART 1 — RESEARCH SUMMARY (WHY THIS MATTERS)

### 1.1 The hallucination problem is real, measured, and worsening

- **Stanford RegLab (2024, peer-reviewed 2025):** Purpose-built legal AI tools from LexisNexis and Thomson Reuters (Westlaw Precision, Lexis+ AI) hallucinate **17%–33% of the time**. General-purpose LLMs hallucinate on legal queries **up to 88% of the time**. Vendor claims of "hallucination-free" AI were found to be overstated.
- **Damien Charlotin (HEC Paris)** now maintains a live database of **1,000+ court cases worldwide** where lawyers were caught filing AI-hallucinated citations. It grows weekly.
- **Indian courts in 2024–2026** have started sanctioning lawyers for AI-fabricated citations. This is no longer a US-only phenomenon.
- **OpenAI's own data:** GPT-o3 hallucinates 33% of the time, GPT-o4-mini 48% — hallucination rates are *going up* with newer reasoning models.

**Why this creates VERITAS's opening:** Lawyers know they cannot trust AI drafts, but they cannot stop juniors, opposing counsel, or clients from using AI. They need a **verification layer**, not another drafting tool.

### 1.2 The Indian legal AI landscape (competitors)

| Tool | Type | Function | Verification-first? |
|---|---|---|---|
| BharatLaw AI | Indian, RAG-based | Research + drafting | No — drafts, then cites |
| SCC Online AI Pro | Established publisher | Case-law research | Partial — hyperlinked citations |
| Manupatra AI | Established publisher | Similar to SCC | Partial |
| CaseMine (AMICUS AI) | Precedent mapping | Related judgments | No — retrieval only |
| VIDUR AI | Vertical (tax/corp) | Specialist drafting | No |
| Draft Bot Pro / Law Bot Pro | Consumer | AI drafting + research | No |
| NyayGuru | Free consumer | IPC/CPC/BNS chatbot | No |
| Jhana | Startup | AI research | Cited answers, "automated citation accuracy" (vendor-stated) |
| Lexlegis.ai (MIRA) | Startup | Research | Partial |
| KanoonGPT | Data infra + tools | Open Indian legal data | Data, not verification |
| Advocase.ai / JuniorLawyer | Practice mgmt + AI | Drafting bail apps | No |
| Jurisphere.ai | Startup | RBI/SEBI/law firm sources | Retrieval-based |
| **RealityCheck (BriefCatch, US)** | **Verification-first** | **Scans filed briefs for hallucinated citations** | **YES — closest analog** |

**The gap:** Every Indian tool above is a **generator with citations bolted on**. The only pure verifier (RealityCheck) is US-focused, Bluebook-formatted, and does not touch CPC.

**VERITAS positioning:** *"AI drafts. VERITAS verifies. The lawyer decides."* — the only Indian-law verification-first engine, with a dedicated CPC procedural layer.

### 1.3 Pain points from lawyers (Reddit + Legally India + reviews)

1. **Hallucinated case law is the number-one complaint.** Lawyers now fear opposing counsel's filings, not just their own.
2. **"It adds a step instead of removing one."** If checking AI output takes as long as doing the work, the tool is theatre. Lawyers quietly abandon such tools within two weeks.
3. **Price versus substance.** Four-figure-per-seat tools called "comedy" when the engine underneath is a general model with a legal label.
4. **Give me one-click citation verification.** Most-requested feature across every legal-tech thread.
5. Real user complaints on Legally India: "Casemine is slow and has given incorrect answers multiple times." "Jurisphere's culmination of multiple sources seldom gives a reliable answer."

**Translation to VERITAS design:**
- Must **remove** a step, not add one. Upload once, get a verdict.
- Must be **cheap or free** to demo.
- Must have **one-click drilldown** on every flagged claim.
- Must be **fast**. Under 60 seconds per document.

### 1.4 Technical challenges from academic literature

From NyayaRAG (IIT Kanpur, AACL 2025), LegalRAG, Metadata-Enriched RAG, and the Digital Applied 50-year archive case study:

1. **Pure vector search fails on proper nouns.** Case names and party identifiers get semantically smeared. **Hybrid retrieval (BM25 + dense embeddings)** is mandatory. Reciprocal Rank Fusion of both is called "the single largest quality lever."
2. **Naive chunking destroys citations.** Case citations and cross-references straddle chunk boundaries and lose their anchor. Fix: **citation-aware chunking** that preserves citations with surrounding context.
3. **Statute retrieval needs section-level exact-match keys.** BM25 or an entity index — "Section 11 CPC" must retrieve Section 11, not something semantically similar.
4. **Metadata filters matter.** Chunks need `act`, `section`, `order`, `rule`, `year` metadata for filterable retrieval.
5. **LLM context length forces judgment condensation.** Standard trick: structured ~400-token summary per judgment, so ~10 fit in context.

---

## PART 2 — SCOPE LOCK

**Do not expand this scope during the hackathon. Depth beats breadth.**

### 2.1 Substantive law (2 acts, MVP)

- **Indian Contract Act, 1872** — formation, void/voidable, breach, damages
- **Specific Relief Act, 1963** — injunctions, specific performance

Stretch: Transfer of Property Act, 1882.

### 2.2 CPC procedural law (5 focused areas, MVP)

1. **Institution of suits** — Sections 9, 15–20, 26; Order IV, Order VII
2. **Pleadings** — Order VI (amendment of pleadings is a favourite AI trap)
3. **Written Statement** — Order VIII (timelines, extensions)
4. **Interim Injunctions** — Order XXXIX + Section 11 tests from case law
5. **Res Judicata** — Section 11 (6-element decomposition)

Stretch: Appeals/Review/Revision (Sections 96, 100, 114, 115), Execution (Order XXI).

### 2.3 Case authority verification

- Supreme Court + all 25 High Courts citations
- Verify (a) the case exists, (b) the citation is correct, (c) the proposition attributed to it is supported by the judgment

### 2.4 Four verdict types

- 🟢 **SUPPORTED** — proposition matches sources
- 🟠 **PARTIALLY_SUPPORTED / OVERSTATED** — real authority exists but claim over-generalizes
- 🔴 **CONTRADICTED** — sources say the opposite
- ⚫ **UNVERIFIABLE** — no sources found, or sources don't address the claim

### 2.5 Explicit non-goals for MVP

- No criminal law, tax, IP, family law, arbitration.
- No drafting — VERITAS never writes a legal argument. It only verifies one.
- No full CPC coverage.
- No final legal advice. Every red/orange flag says *"human review required."*

---

## PART 3 — DATA SOURCES

### 3.1 Statutes — bare acts (free, immediately usable)

**Primary: `civictech-India/Indian-Law-Penal-Code-Json` on GitHub**
- Has `cpc.json` (Civil Procedure Code, 1908) as structured JSON — **exactly what we need**
- Also `iea.json`, `nia.json`, full SQLite DB `indialaw.db`
- Clone this Day 1, Hour 1

**Secondary: India Code** (https://www.indiacode.nic.in/)
- Government-authoritative, HTML-scrape or PDF-parse
- Use as verification source if primary is incomplete for Contract/Specific Relief Acts

**Tertiary: Vaquill AI public API** (https://api.vaquill.ai)
- Free tier available, 22,265 enactments, 1M+ addressable provisions
- Backup only

### 3.2 Case law — judgments

**Primary: Indian Kanoon**
- Free public HTML at https://indiankanoon.org/
- Paid API at https://api.indiankanoon.org (apply for key; may not arrive in time)
- **Fallback for hackathon:** curated ~30 landmark judgments pre-downloaded to `data/judgments/golden_set/`

**Secondary: KanoonGPT HuggingFace** — `KanoonGPT/indian-case-laws` structured metadata for SC + 25 HCs, sample variant available immediately.

**Reference implementations to study (architecture, not copy code):**
- `ShubhamKumarNigam/NyayaRAG` — RAG for Indian judgment prediction (AACL 2025)
- `DanielDeshmukh/Hector` — "zero-hallucination Hard-RAG" for IPC-BNS mapping
- `goyashek/bns-legal-rag` — statute-aware retrieval + deterministic citation check
- `upalbhattacharya/indian-legal-dataset-preparation` — preprocessing scripts

### 3.3 Curated demo corpus (golden set)

Hand-curate ~30 judgments covering:
- 5 landmark Contract Act cases (Mohori Bibee v Dharmodas Ghose is essential)
- 5 Specific Relief Act cases
- 5 Order XXXIX interim injunction cases (Dalpat Kumar v Prahlad Singh is essential)
- 5 Order VI amendment cases (Revajeetu Builders, Rajesh Kumar Aggarwal)
- 5 Section 11 res judicata cases (Satyadhyan Ghosal, Sulochana Amma)
- 5 Order VIII written statement cases (Salem Advocate Bar Association, Kailash v Nanhku)

**These are the cases the demo document cites. We control what needs to be verifiable.**

### 3.4 Demo document

A fictional civil suit ("Rajesh Sharma v Priya Enterprises") with 10 numbered propositions embedded in Part 8 of this document. It contains intentionally-seeded errors so the verifier has something to catch on stage.

---

## PART 4 — TECHNICAL ARCHITECTURE

### 4.1 System diagram

```
                    ┌─────────────────────────────────┐
                    │  User uploads legal document    │
                    │  (PDF / DOCX / TXT)             │
                    └────────────────┬────────────────┘
                                     ▼
                    ┌─────────────────────────────────┐
                    │  1. INGESTION LAYER             │
                    │  PDF/DOCX -> text               │
                    │  Sentence + paragraph split     │
                    │  Citation regex extraction      │
                    └────────────────┬────────────────┘
                                     ▼
                    ┌─────────────────────────────────┐
                    │  2. CLAIM CLASSIFIER (LLM)      │
                    │  Each sentence -> one of:       │
                    │  substantive / procedural /     │
                    │  citation / statutory_ref /     │
                    │  remedy / factual / narrative   │
                    └────────────────┬────────────────┘
                                     ▼
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
┌──────────────────┐      ┌──────────────────┐        ┌──────────────────┐
│ 3a. STATUTE      │      │ 3b. CASE LAW     │        │ 3c. CITATION     │
│ ROUTER           │      │ ROUTER           │        │ VERIFIER         │
│ - Identify Act   │      │ - Identify issue │        │ - Regex match    │
│ - Fetch §/Order/ │      │ - Hybrid search  │        │ - Party+year     │
│   Rule text      │      │   (BM25 + dense) │        │   lookup         │
│                  │      │ - Rerank         │        │                  │
└────────┬─────────┘      └────────┬─────────┘        └────────┬─────────┘
         │                         │                           │
         └─────────────────────────┼───────────────────────────┘
                                   ▼
                    ┌─────────────────────────────────┐
                    │  4. VERIFICATION ENGINE (LLM)   │
                    │  Prompt: "Given claim X and     │
                    │  these primary sources, is it   │
                    │  SUPPORTED / OVERSTATED /       │
                    │  CONTRADICTED / UNVERIFIABLE?"  │
                    │  Returns verdict + evidence     │
                    └────────────────┬────────────────┘
                                     ▼
                    ┌─────────────────────────────────┐
                    │  5. RISK AGGREGATOR             │
                    │  - Per-claim verdict            │
                    │  - Category rollup              │
                    │  - Overall integrity score      │
                    │  - Procedural risk flag         │
                    └────────────────┬────────────────┘
                                     ▼
                    ┌─────────────────────────────────┐
                    │  6. REPORT UI                   │
                    │  - Dashboard summary            │
                    │  - Clickable red/orange flags   │
                    │  - Side-by-side: claim vs       │
                    │    primary source               │
                    │  - Export report                │
                    └─────────────────────────────────┘
```

### 4.2 Tech stack (choices with reasons)

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Standard for ML/RAG, fast, async |
| Frontend | Next.js 14 (App Router) + TailwindCSS + shadcn/ui | Matches your web-dev stack, premium look |
| LLM (primary) | Claude 3.5 Sonnet via Anthropic API | Best long-context legal reasoning, refuses fabrication |
| LLM (fallback) | GPT-4o-mini or Gemini 2.0 Flash | Cheaper for the classifier step |
| Embeddings | BAAI/bge-large-en-v1.5 (free) or OpenAI text-embedding-3-large | Kanon 2 is gated; bge-large is best free |
| Vector DB | ChromaDB (in-process, simple) → Qdrant if time | Chroma is faster to set up; Qdrant if we need heavy filtering |
| Lexical search | rank-bm25 | Needed for hybrid — do not skip |
| Reranker (stretch) | BAAI/bge-reranker-base | +10% quality, adds latency |
| PDF parsing | pdfplumber + pypdf fallback | Handles tables |
| DOCX parsing | python-docx | Standard |
| Citation regex | Custom Python patterns for Indian formats | `(YYYY) N SCC PAGE`, `AIR YYYY SC NNNN`, etc. |
| Deployment | Vercel (Next.js) + Render/Railway (FastAPI) + ngrok fallback | Free tiers |
| Auth | None — single-page demo | Skip |

### 4.3 Key design decisions

1. **Hybrid retrieval is not optional.** Chunk once, index twice (BM25 + dense), fuse with Reciprocal Rank Fusion.
2. **Citation-aware chunking.** Parse citations before chunking, tag each chunk with the citations it contains.
3. **Section-level metadata on statute chunks.** `act_name`, `section_number`, `order_number`, `rule_number`, `subsection`.
4. **LLM output must be structured JSON.** Use Anthropic's tool-use for schema-enforced output. Never accept free-form.
5. **The verification LLM has no world knowledge as an allowed source.** Prompt says: *"Only answer using the provided sources. If sources are silent, return UNVERIFIABLE."* This is the anti-hallucination lever.
6. **Every UI verdict links to a highlighted primary-source span.** No verdict without a quotable evidence excerpt.

---

## PART 5 — REPOSITORY STRUCTURE

```
veritas/
├── README.md
├── VERITAS_SPEC.md                    # this file
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── data/
│   ├── statutes/
│   │   ├── cpc.json                   # from civictech-India
│   │   ├── contract_act.json
│   │   └── specific_relief_act.json
│   ├── judgments/
│   │   └── golden_set/                # ~30 curated .txt files with YAML frontmatter
│   ├── demo/
│   │   ├── rajesh_sharma_v_priya_enterprises.md    # source
│   │   └── rajesh_sharma_v_priya_enterprises.pdf   # generated
│   └── indices/
│       ├── bm25_index.pkl
│       └── chroma_db/
│
├── backend/
│   ├── main.py                        # FastAPI entrypoint
│   ├── config.py                      # env, model names, paths
│   ├── pipeline.py                    # orchestrator
│   ├── models/
│   │   └── schemas.py                 # all Pydantic models
│   ├── ingestion/
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── sentence_splitter.py       # spaCy
│   │   └── citation_extractor.py      # regex
│   ├── indexing/
│   │   ├── statute_normalizer.py
│   │   ├── chunker.py                 # citation-aware
│   │   ├── embeddings.py              # bge-large wrapper
│   │   ├── statute_indexer.py
│   │   └── judgment_indexer.py
│   ├── retrieval/
│   │   ├── bm25_retriever.py
│   │   ├── dense_retriever.py
│   │   ├── hybrid.py                  # RRF
│   │   └── reranker.py                # optional
│   ├── verification/
│   │   ├── prompts.py                 # all LLM prompts
│   │   ├── claim_classifier.py
│   │   ├── statute_router.py
│   │   ├── case_router.py
│   │   ├── citation_verifier.py
│   │   └── verdict_engine.py
│   ├── aggregation/
│   │   ├── risk_scorer.py
│   │   └── report_builder.py
│   └── api/
│       ├── routes.py
│       └── dependencies.py
│
├── frontend/                          # Next.js 14
│   ├── app/
│   │   ├── page.tsx
│   │   ├── verify/page.tsx
│   │   └── report/[id]/page.tsx
│   ├── components/
│   │   ├── UploadDropzone.tsx
│   │   ├── IntegrityDashboard.tsx
│   │   ├── CategoryRollup.tsx
│   │   ├── ClaimCard.tsx
│   │   ├── EvidencePanel.tsx
│   │   └── ExportReportButton.tsx
│   └── lib/api.ts
│
├── scripts/
│   ├── 01_download_statutes.py
│   ├── 02_build_statute_index.py
│   ├── 03_ingest_golden_judgments.py
│   ├── 04_generate_demo_doc.py
│   └── 05_smoke_test_pipeline.py
│
├── tests/
│   ├── test_citation_extractor.py
│   ├── test_claim_classifier.py
│   ├── test_hybrid_retriever.py
│   └── test_verdict_engine.py
│
└── docs/
    ├── SEEDED_DOCUMENT_KEY.md
    └── DEMO_SCRIPT.md
```

---

## PART 6 — PHASED IMPLEMENTATION PLAN

Each phase: **goal → deliverables → acceptance → Claude Code prompt**.

Total: 40–50 focused hours for solo builder, 24–35 for a team of 2–3.

---

### PHASE 0 — Setup (2 hours)

**Goal:** Repo scaffolded, dependencies installed, reproducible env.

**Deliverables:** Folder structure from Part 5. `pyproject.toml` with pinned deps. `.env.example`. Minimal `backend/main.py` with `/health`. Bootstrapped `frontend/` with Next.js + shadcn.

**Acceptance:** `uvicorn backend.main:app --reload` returns 200 on `GET /health`. `npm run dev` shows a hello-world.

**Prompt for Claude Code:**
> Scaffold the VERITAS project per Part 5 of the spec. Create `pyproject.toml` with: fastapi, uvicorn, python-multipart, pydantic, pdfplumber, pypdf, python-docx, spacy, rank-bm25, chromadb, sentence-transformers, anthropic, python-dotenv, numpy, rapidfuzz, weasyprint, markdown. Create minimal `backend/main.py` with a `/health` endpoint returning `{"status": "ok"}`. Bootstrap `frontend/` with `npx create-next-app@latest frontend --typescript --tailwind --app --eslint --no-src-dir`. Install shadcn/ui default style. Write README.md with a one-command run instruction. Do not write any business logic yet.

---

### PHASE 1 — Statute ingestion + hybrid statute index (6 hours)

**Goal:** All statute text loaded, chunked, indexed with BM25 and dense vectors, filterable by section/order/rule.

**Deliverables:**
- `scripts/01_download_statutes.py` — clones `civictech-India/Indian-Law-Penal-Code-Json`, copies `cpc.json` to `data/statutes/`.
- Placeholder `contract_act.json` and `specific_relief_act.json` with top-15 sections each.
- `backend/indexing/chunker.py` — chunks each section to ~200 tokens, preserves metadata.
- `backend/indexing/embeddings.py` — wraps `bge-large-en-v1.5`.
- `backend/indexing/statute_indexer.py` — builds BM25 (pickled) and ChromaDB collection.
- `scripts/02_build_statute_index.py` — one command builds both indices.

**Acceptance:** Querying "Order XXXIX Rule 1" returns the correct provision in top-3 BM25 results. Querying "temporary injunction requirements" returns Order XXXIX in top-5 dense results. Every chunk has metadata: `{act, section, order, rule, subsection, chunk_id, source_url}`.

**Prompt for Claude Code:**
> Implement Phase 1 of VERITAS.
> 1. Copy the schemas from Part 7 of the spec into `backend/models/schemas.py`.
> 2. Write `scripts/01_download_statutes.py` that git-clones `https://github.com/civictech-India/Indian-Law-Penal-Code-Json` into a temp dir and copies `cpc.json` into `data/statutes/`.
> 3. Inspect `cpc.json` structure and write `backend/indexing/statute_normalizer.py` that yields `SourceChunk` objects with the metadata schema (act_name, section_number, order_number, rule_number, subsection).
> 4. Create minimal `contract_act.json` and `specific_relief_act.json` in `data/statutes/` — hard-code the top 15 most-cited sections of each in the same schema.
> 5. Write `backend/indexing/chunker.py` — for each section, if under 200 tokens keep as one chunk, else split by subsection. Every chunk carries full metadata.
> 6. Write `backend/indexing/embeddings.py` wrapping `BAAI/bge-large-en-v1.5` via sentence-transformers, with a batched `embed(texts: list[str]) -> np.ndarray` method.
> 7. Write `backend/indexing/statute_indexer.py` that builds (a) a BM25Okapi index pickled to `data/indices/bm25_statutes.pkl` with parallel chunk-metadata list, and (b) a ChromaDB persistent collection at `data/indices/chroma_db/` (collection name: `statutes`) with embeddings and metadata attached.
> 8. Write `scripts/02_build_statute_index.py` running the full indexing pipeline.
> 9. Write `tests/test_hybrid_retriever.py` with the two acceptance queries above; skip the hybrid part for now, test each retriever separately.

---

### PHASE 2 — Judgment ingestion + hybrid retrieval (6 hours)

**Goal:** ~30 curated judgments ingested, indexed. Hybrid retriever (BM25 + dense + RRF) working across statutes and judgments.

**Deliverables:**
- `data/judgments/golden_set/` populated with 30 `.txt` files. Each file has YAML frontmatter: `case_name`, `citation`, `court`, `year`, `judges`, `source_url`, followed by the judgment body.
- `backend/indexing/judgment_indexer.py` — chunks judgments at 500 tokens with 100-token overlap.
- `backend/retrieval/bm25_retriever.py`, `dense_retriever.py`, `hybrid.py` (RRF).

**Acceptance:** Query "prima facie case interim injunction" returns Dalpat Kumar v Prahlad Singh in top-3 hybrid results. Query "Order VI Rule 17 amendment after trial commencement" returns Revajeetu Builders in top-5.

**Prompt for Claude Code:**
> Implement Phase 2. I will supply 30 judgment `.txt` files in `data/judgments/golden_set/` with YAML frontmatter containing case_name, citation, court, year, judges, source_url.
> 1. Write `backend/indexing/judgment_indexer.py` reading each `.txt`, parsing frontmatter, chunking body at 500 tokens with 100-token overlap using a recursive character splitter respecting paragraph boundaries. Tag each chunk with frontmatter metadata + `chunk_id` and `chunk_index`.
> 2. Extend ChromaDB from Phase 1 with a `judgments` collection; extend BM25 with a parallel judgments index at `data/indices/bm25_judgments.pkl`.
> 3. Write `backend/retrieval/bm25_retriever.py` and `dense_retriever.py`, each with `retrieve(query: str, top_k: int, collection: str) -> list[RetrievalResult]`.
> 4. Write `backend/retrieval/hybrid.py` implementing Reciprocal Rank Fusion (k=60 default) over both retrievers. Signature: `hybrid_search(query: str, top_k: int = 10, collections: list[str] = ["statutes", "judgments"]) -> list[RetrievalResult]`.
> 5. Add the two acceptance queries to `tests/test_hybrid_retriever.py`.

---

### PHASE 3 — Document ingestion + claim classifier (5 hours)

**Goal:** User uploads PDF/DOCX, sentences extracted, each classified as substantive/procedural/citation/factual, and citations extracted with regex.

**Deliverables:**
- `backend/ingestion/pdf_parser.py`, `docx_parser.py`, `sentence_splitter.py`.
- `backend/ingestion/citation_extractor.py` — regex for Indian citation formats.
- `backend/verification/claim_classifier.py` — Claude API call in batches of 10 sentences, structured output.
- `backend/verification/prompts.py` — copy from Part 7 of this spec.

**Acceptance:** Given the demo document, ~30–50 sentences extracted, ~8–12 flagged as claims, rest as narrative. Every fabricated citation in the demo document is picked up by regex.

**Prompt for Claude Code:**
> Implement Phase 3.
> 1. Copy the prompts from Part 7 of the spec into `backend/verification/prompts.py` verbatim.
> 2. Write `backend/ingestion/pdf_parser.py` using pdfplumber with pypdf fallback; returns list of `Paragraph` objects.
> 3. Write `backend/ingestion/docx_parser.py` using python-docx; same interface.
> 4. Write `backend/ingestion/sentence_splitter.py` using spaCy `en_core_web_sm`. Preserves paragraph and sentence indices, char offsets.
> 5. Write `backend/ingestion/citation_extractor.py` with a regex bank for Indian formats: `(YYYY) N SCC PAGE`, `AIR YYYY SC NNNN`, `[YYYY] N Reporter PAGE`, and neutral citations. Extract into structured `Citation` objects with char offsets.
> 6. Write `backend/verification/claim_classifier.py`:
>    - Batches sentences 10 at a time.
>    - Calls Anthropic Claude 3.5 Sonnet with `CLAIM_CLASSIFIER_SYSTEM` from prompts.py.
>    - Uses the `CLASSIFY_BATCH_TOOL` schema (also in prompts.py) for tool-use structured output.
>    - Returns `list[ClassifiedClaim]`.
> 7. Write `tests/test_claim_classifier.py` with 5 example sentences and expected classifications.

---

### PHASE 4 — Verdict engine + citation verifier (8 hours) — **CORE OF VERITAS**

**Goal:** For each classified claim, retrieve relevant primary sources, get a verdict with evidence from Claude, and detect fabricated citations.

**Deliverables:**
- `backend/verification/citation_verifier.py` — exact-match then fuzzy match (rapidfuzz threshold 85) against judgment metadata index.
- `backend/verification/statute_router.py` — LLM call to extract Act/Section/Order/Rule references from a procedural claim.
- `backend/verification/case_router.py` — hybrid retrieval for substantive claims.
- `backend/verification/verdict_engine.py` — the core LLM call. Returns `Verdict`.

**Acceptance:**
- The fabricated citation in the demo (`ABC Developers Pvt Ltd v State of Maharashtra, (2021) 4 SCC 321`) returns `CitationVerdict(verified=False, reason="No case matching this citation was found...")`.
- The overstated "prima facie case alone is sufficient" claim returns `OVERSTATED` with missing elements `["balance of convenience", "irreparable injury"]`.
- Correct claims return `SUPPORTED`.

**Prompt for Claude Code:**
> Implement Phase 4 — the verdict engine.
> 1. Write `backend/verification/citation_verifier.py`:
>    - Normalise case name (strip `vs`/`v.`/`versus`, lowercase, remove punctuation).
>    - Exact match against judgment metadata (case_name substring match + year exact + reporter+volume+page match).
>    - Fuzzy match via rapidfuzz WRatio, threshold 85, secondary.
>    - Returns `CitationVerdict`.
> 2. Write `backend/verification/statute_router.py`:
>    - Uses Claude Sonnet with `STATUTE_ROUTER_SYSTEM` and `EXTRACT_STATUTORY_REFS_TOOL` from prompts.py.
>    - Fetches matching statute chunks from the index.
> 3. Write `backend/verification/case_router.py`:
>    - Runs hybrid retrieval on the claim text.
>    - Returns top-5 judgment chunks + top-3 statute chunks.
> 4. Write `backend/verification/verdict_engine.py`:
>    - `render_verdict(claim: ClassifiedClaim, sources: list[RetrievalResult]) -> Verdict`.
>    - Formats sources using `format_sources_block` from prompts.py.
>    - Calls Claude Sonnet with `VERDICT_ENGINE_SYSTEM` and `RENDER_VERDICT_TOOL`.
>    - Validates the response against the Verdict schema; retries once on invalid JSON.
> 5. Write `tests/test_verdict_engine.py` with three golden test cases from the seeded demo (see Part 9 answer key): one SUPPORTED (Prop 1 — Section 10 Contract Act), one OVERSTATED (Prop 3 — prima facie only), one CONTRADICTED (Prop 4 — unrestricted amendment right).

---

### PHASE 5 — Aggregation, API, orchestration (4 hours)

**Goal:** Full pipeline exposed as `POST /verify` returning a complete `Report`.

**Deliverables:**
- `backend/aggregation/risk_scorer.py` — integrity score and category breakdown.
- `backend/aggregation/report_builder.py` — assembles `Report`.
- `backend/api/routes.py` — `POST /verify`, `GET /report/{id}`, `GET /source/{id}`.
- `backend/pipeline.py` — orchestrator.

**Acceptance:** `curl -F 'file=@demo.pdf' http://localhost:8000/verify` returns a job ID. Within 60 seconds, `GET /report/{id}` returns a report matching the seeded answer key.

**Prompt for Claude Code:**
> Implement Phase 5.
> 1. Write `backend/aggregation/risk_scorer.py`:
>    - `compute_integrity_score(verdicts, citation_verdicts) -> float`. Weights: SUPPORTED=1.0, PARTIALLY_SUPPORTED=0.7, OVERSTATED=0.4, UNVERIFIABLE=0.3, CONTRADICTED=0.0. Each fabricated citation subtracts 15 points from the raw score. Clamp 0–100.
>    - `category_breakdown(verdicts, citation_verdicts) -> CategoryBreakdown` counting the six buckets.
>    - `compute_procedural_risk_flag(verdicts, claims) -> tuple[bool, str]` — true if any procedural_proposition claim has status CONTRADICTED or OVERSTATED, with a one-line summary.
> 2. Write `backend/aggregation/report_builder.py` assembling `Report` from all pipeline outputs.
> 3. Write `backend/pipeline.py`:
>    ```python
>    async def verify_document(file_path: str, job_id: str) -> Report:
>        text = parse(file_path)
>        sentences = split(text)
>        claims = classify_claims(sentences)
>        verdicts = []
>        for claim in claims:
>            if claim.claim_type in (SUBSTANTIVE, PROCEDURAL, REMEDY):
>                sources = route_and_retrieve(claim)
>                verdicts.append(render_verdict(claim, sources))
>        citation_verdicts = verify_all_citations(claims)
>        return build_report(job_id, claims, verdicts, citation_verdicts)
>    ```
> 4. Write `backend/api/routes.py`:
>    - `POST /verify` — multipart file upload. Saves file, kicks off pipeline in a background task, returns `{"job_id": <uuid>, "status": "processing"}`.
>    - `GET /report/{job_id}` — returns report JSON or `{"status": "processing"}`.
>    - `GET /source/{source_id}` — returns full chunk text and metadata.
>    - In-memory dict for MVP job store.
> 5. Wire up in `backend/main.py`, enable CORS for `http://localhost:3000`.
> 6. Write `scripts/05_smoke_test_pipeline.py` that hits the API with the demo PDF and prints integrity score.

---

### PHASE 6 — Frontend dashboard (8 hours) — **60% OF DEMO SCORE**

**Goal:** Premium dashboard that makes the verdicts tangible. This is what the judges see.

**Deliverables:**
- `app/page.tsx` — landing with tagline "AI drafts. VERITAS verifies. The lawyer decides." + upload CTA.
- `app/verify/page.tsx` — drag-and-drop upload, 4-step progress.
- `app/report/[id]/page.tsx` — the money page:
  - Large circular integrity score (color-coded).
  - Category rollup card.
  - Procedural risk callout in red if triggered.
  - Filterable claim list (All / Critical / Review / Verified).
  - Click a claim → slide-over drawer with side-by-side detail.
  - Export PDF button.
- shadcn components: `card badge sheet progress tabs alert button`.
- Dark mode, Inter for UI, JetBrains Mono for citations, deep indigo accent.

**Acceptance:** Demo PDF uploaded, report loads in under 5 seconds after backend finishes. Fabricated-citation red flag shows "not found" reason. Overstated interim injunction flag shows missing elements as bullets next to the actual case excerpt.

**Prompt for Claude Code:**
> Implement Phase 6 — the frontend.
> 1. Install shadcn components: `npx shadcn-ui@latest add card badge sheet progress tabs alert button`.
> 2. `frontend/lib/api.ts` — fetch wrapper with `NEXT_PUBLIC_API_URL`.
> 3. `frontend/app/page.tsx` — landing. Hero with tagline "AI drafts. VERITAS verifies. The lawyer decides." One-line pitch: "The only Indian-law verification engine that reads AI-generated legal drafts and tells you what's real, what's overstated, and what's fabricated." CTA button to `/verify`. Dark bg, deep indigo accent.
> 4. `frontend/app/verify/page.tsx` — dropzone (react-dropzone) accepting `.pdf` and `.docx`. On drop, POST to `/verify`, then poll `GET /report/{job_id}` every 2s until report ready, then redirect to `/report/{job_id}`. Show 4-step progress: Parsing → Classifying → Verifying → Aggregating.
> 5. `frontend/app/report/[id]/page.tsx`:
>    - Header: filename, timestamp, integrity score as a large animated ring (0–100, gradient from red at 0 to green at 100).
>    - Category rollup card: 6 rows with icons, counts, labels.
>    - Alert component: procedural risk callout in red if `procedural_risk_flag` is true.
>    - Tabs: All / Critical / Review / Verified. Count in each tab label.
>    - Claim list: each `ClaimCard` shows the sentence, a verdict badge (color-coded), and the primary source citation (mono font). Clicking opens a `Sheet` (right slide-over).
>    - `Sheet` content: two columns. Left = claim text (highlighted), verdict, reasoning, missing_elements as bullets. Right = evidence — quoted_text with the highlighted span, source metadata (case_name, citation_string, court, year), "View full source" button that fetches `/source/{id}` and opens a modal.
>    - Bottom: "Export PDF" button using html2pdf.js.
> 6. Style: Tailwind dark mode default. Inter (UI) + JetBrains Mono (citations). Primary color `indigo-600`.
> 7. Loading skeletons and error states throughout.

---

### PHASE 7 — Demo document + rehearsal (4 hours)

**Goal:** The killer demo is preloaded and rehearsed.

**Deliverables:**
- `data/demo/rajesh_sharma_v_priya_enterprises.md` — copy from Part 8 of this spec.
- `data/demo/rajesh_sharma_v_priya_enterprises.pdf` — generated via `weasyprint` or `markdown-pdf`.
- `docs/SEEDED_DOCUMENT_KEY.md` — copy from Part 9 of this spec.
- `docs/DEMO_SCRIPT.md` — copy from Part 10 of this spec.

**Acceptance:** Full demo runs end-to-end in under 3 minutes with no dev tools open. Every seeded error triggers its intended verdict. Presenter can explain any verdict in one sentence.

**Prompt for Claude Code:**
> Implement Phase 7.
> 1. Copy Part 8 of the spec verbatim into `data/demo/rajesh_sharma_v_priya_enterprises.md`.
> 2. Write `scripts/04_generate_demo_doc.py` that converts the markdown to PDF using weasyprint. Save to `data/demo/rajesh_sharma_v_priya_enterprises.pdf`.
> 3. Copy Part 9 verbatim into `docs/SEEDED_DOCUMENT_KEY.md`.
> 4. Copy Part 10 verbatim into `docs/DEMO_SCRIPT.md`.
> 5. Run the full pipeline end-to-end on the demo PDF, print the integrity score and per-claim verdicts, and compare against the answer key. Report any mismatches.

---

## PART 7 — STARTER CODE (COPY VERBATIM)

### 7.1 `backend/models/schemas.py`

```python
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
```

### 7.2 `backend/verification/prompts.py`

```python
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
```

---

## PART 8 — SEEDED DEMO DOCUMENT

Save as `data/demo/rajesh_sharma_v_priya_enterprises.md`, then convert to PDF.

```markdown
# LEGAL RESEARCH MEMO

**Matter:** Rajesh Sharma v Priya Enterprises Pvt Ltd
**Court:** Bombay High Court (Ordinary Original Civil Jurisdiction)
**Suit No.:** 1234 of 2026
**Prepared for:** Senior Counsel
**Prepared by:** Associate (AI-assisted draft)
**Date:** 3 September 2026

---

## 1. FACTS

The plaintiff, Rajesh Sharma, entered into an agreement to sell dated 12 January 2025 with the defendant, Priya Enterprises Pvt Ltd, for the purchase of a commercial premises at Andheri (West), Mumbai, for a consideration of Rs. 3.75 crore. The plaintiff paid Rs. 75 lakh as earnest money at the time of execution. The balance of Rs. 3 crore was to be paid on or before 30 June 2025, against which the defendant was to execute a sale deed and hand over vacant possession.

The plaintiff tendered the balance consideration on 25 June 2025 by way of a banker's cheque. The defendant refused the tender and, by a letter dated 2 July 2025, purported to terminate the agreement on the ground that the plaintiff had defaulted on an earlier instalment. On 15 July 2025, the plaintiff learned that the defendant had entered into a fresh agreement to sell the same premises to a third party for Rs. 4.2 crore.

The plaintiff has filed the present suit seeking specific performance of the agreement to sell and, in the alternative, damages. An application for interim injunction restraining the defendant from alienating, encumbering, or parting with possession of the suit premises has been filed under Order XXXIX Rules 1 and 2 CPC.

---

## 2. LEGAL ANALYSIS

### Proposition 1 — Essential elements of a valid contract

Under Section 10 of the Indian Contract Act, 1872, all agreements are contracts if they are made by the free consent of parties competent to contract, for a lawful consideration and with a lawful object, and are not expressly declared to be void. The agreement to sell dated 12 January 2025 satisfies each of these requirements.

### Proposition 2 — Grant of specific performance

Section 10 of the Specific Relief Act, 1963 (as amended in 2018) provides that specific performance of a contract shall be enforced by the court, subject to the provisions contained in sub-section (2) of section 11, section 14 and section 16. Following the 2018 amendment, specific performance is now the rule and not the exception.

### Proposition 3 — Standard for interim injunction under Order XXXIX

The plaintiff is entitled to an interim injunction under Order XXXIX Rules 1 and 2 CPC upon establishing a prima facie case. Once a prima facie case is shown, the injunction must follow as a matter of course.

### Proposition 4 — Amendment of the written statement

The defendant, if he seeks to bring on record any additional pleadings or fresh grounds of defence, has an unrestricted right to amend the written statement at any stage of the proceeding under Order VI Rule 17 CPC.

### Proposition 5 — Applicability of the doctrine of lis pendens

The pendency of the present suit operates as a caveat on the property. As held in ABC Developers Pvt Ltd v State of Maharashtra, (2021) 4 SCC 321, any transfer of the suit premises by the defendant during the pendency of the suit shall be void ab initio.

### Proposition 6 — Bar of res judicata

The defendant has raised a plea that an earlier suit (SC No. 456/2023) between the same parties bars the present proceedings. However, a subsequent suit is barred by res judicata under Section 11 CPC whenever the parties have previously litigated the same subject matter. Since the earlier suit related to a lease dispute and not to the present agreement to sell, the bar does not apply.

### Proposition 7 — Rejection of plaint

The defendant has moved an application under Order VII Rule 11 CPC seeking rejection of the plaint on the ground that it is barred by limitation. Order VII Rule 11(d) permits rejection where the suit appears from the statement in the plaint to be barred by any law. The present plaint discloses that the cause of action arose on 2 July 2025, and the suit was filed on 20 August 2025, well within limitation. The application must fail.

### Proposition 8 — Place of suing

Section 20 CPC provides that every suit shall be instituted in a court within the local limits of whose jurisdiction the defendant actually and voluntarily resides, or carries on business, or personally works for gain, or where the cause of action, wholly or in part, arises. The defendant carries on business at Andheri (West), and the cause of action arose in Mumbai. This Hon'ble Court has jurisdiction.

### Proposition 9 — Availability of revision

Should the trial court decide the interim injunction application against the plaintiff, revision under Section 115 CPC lies as a matter of right to this Hon'ble Court. The plaintiff will accordingly have a further remedy available.

### Proposition 10 — Amendment of pleadings before trial

The plaintiff may amend the plaint at any time before the commencement of the trial, subject to the discretion of the court, and such amendments as are necessary for the purpose of determining the real question in controversy between the parties shall be allowed. This is provided under Order VI Rule 17 CPC.

---

## 3. PRAYER

In view of the foregoing, it is respectfully submitted that the plaintiff has established a prima facie case for the grant of interim injunction, and that the suit is maintainable both on jurisdictional and limitation grounds. The plaintiff prays that this Hon'ble Court be pleased to:

1. Restrain the defendant, its agents, servants, and assigns from alienating, encumbering, transferring, or parting with possession of the suit premises pending the disposal of the suit;
2. Decree specific performance of the agreement to sell dated 12 January 2025;
3. In the alternative, grant damages of Rs. 2 crore with interest;
4. Grant such further and other reliefs as this Hon'ble Court may deem fit.

*[Draft ends. To be reviewed by Senior Counsel before filing.]*
```

---

## PART 9 — SEEDED DOCUMENT ANSWER KEY

Save as `docs/SEEDED_DOCUMENT_KEY.md`.

> **Important:** The seeded document is fictional. The propositions below are the *expected* verdicts VERITAS should produce, verified against the golden-set corpus. Before demo day, have a law student or lawyer friend cross-check each expected verdict — VERITAS's demo credibility depends on the answer key being accurate. Correct any drift between what the propositions say and what the golden judgments actually hold.

| # | Proposition summary | Expected verdict | Rationale | Primary source in golden set |
|---|---|---|---|---|
| 1 | Section 10 Contract Act essential elements | 🟢 **SUPPORTED** | Standard uncontroversial recitation of Section 10 | Contract Act §10 (statute chunk) |
| 2 | Section 10 SRA 1963 (as amended 2018), SP now the rule | 🟢 **SUPPORTED** | Post-2018 SRA amendment does make SP mandatory subject to §11(2), §14, §16 | Specific Relief Act §10 chunk + explanatory case |
| 3 | Prima facie case alone sufficient for Order XXXIX injunction | 🟠 **OVERSTATED** | Missing elements: **balance of convenience**, **irreparable injury**. Landmark: Dalpat Kumar v Prahlad Singh, (1993) 1 SCC 719, holds all three tests must be satisfied. | Dalpat Kumar v Prahlad Singh judgment chunk |
| 4 | Defendant has unrestricted right to amend WS under Order VI Rule 17 | 🔴 **CONTRADICTED** | Order VI Rule 17 has a *proviso* barring amendment after commencement of trial except where the court concludes that in spite of due diligence the party could not have raised the matter earlier. Absolute claim is directly contradicted. | Order VI Rule 17 CPC statute chunk (with proviso) + Revajeetu Builders v Narayanaswamy, (2009) 10 SCC 84 |
| 5 | Citation: ABC Developers Pvt Ltd v State of Maharashtra, (2021) 4 SCC 321 | 🔴 **CITATION FABRICATED** | This citation does not exist in the golden set or in any Indian legal database. Expected `CitationVerdict(verified=False, reason="No case matching this citation was found in the searched databases.")` | (n/a — not found) |
| 6 | Res judicata bars subsequent suit whenever same subject matter | 🟠 **OVERSTATED** | Section 11 CPC requires **six elements**: (i) same parties or those claiming under them, (ii) same title, (iii) matter directly and substantially in issue, (iv) previously heard and finally decided, (v) by a competent court, (vi) subsequent suit. Claim collapses all six into "same subject matter." | Section 11 CPC statute chunk + Satyadhyan Ghosal v Deorajin Debi, AIR 1960 SC 941 |
| 7 | Order VII Rule 11(d) grounds for rejection of plaint | 🟢 **SUPPORTED** | Faithful recitation of Rule 11(d) plus fact application; suit filed within 3-year contract limitation | Order VII Rule 11 CPC statute chunk |
| 8 | Section 20 CPC — place of suing | 🟢 **SUPPORTED** | Direct recitation of Section 20, faithful to the statute | Section 20 CPC statute chunk |
| 9 | Revision under Section 115 CPC lies as of right | 🟠 **OVERSTATED** | Revision is discretionary and constrained by the jurisdictional grounds in Section 115 itself (jurisdictional error, illegality). Not a matter of right. | Section 115 CPC statute chunk |
| 10 | Order VI Rule 17 amendment before commencement of trial | 🟢 **SUPPORTED** | Correctly captures the discretionary and "real question in controversy" standard from Rule 17 | Order VI Rule 17 CPC statute chunk |

**Expected overall integrity score:** ~55–65 (with the fabricated citation applying a 15-point penalty).

**Expected category breakdown:**
- Substantive verified: 3 (Props 1, 2, 8)
- CPC verified: 2 (Props 7, 10)
- Citations verified: 0 (only 1 citation in the memo, and it's fabricated)
- Unsupported / overstated: 3 (Props 3, 6, 9)
- Procedural issues: 2 (Props 3, 4 — both procedural)
- Fabricated citations: 1 (Prop 5)

**Expected procedural risk flag:** TRUE, summary: "2 procedural claims (interim injunction standard, written statement amendment) are overstated or contradicted and require review before filing."

---

## PART 10 — DEMO SCRIPT (3 MINUTES)

Save as `docs/DEMO_SCRIPT.md`. Time it. Rehearse three times before pitching.

### [0:00 — 0:20] Hook

> "Last year, Stanford published a study showing that the leading legal AI research tools — Westlaw, Lexis+ — hallucinate up to 33% of the time. Indian courts have started sanctioning lawyers for filing AI-generated fake citations. Over a thousand cases have been catalogued worldwide. The problem is not going away — hallucination rates in newer reasoning models are actually higher."

> "Every Indian legal AI tool today is a *drafting* tool that citations bolted on. VERITAS is the opposite. We don't write. We verify."

### [0:20 — 0:50] Problem framing

> "A junior associate in a Mumbai firm asks ChatGPT to draft a research memo on a property dispute. She gets back something polished, formal, footnoted. And she has to check every single line before it goes anywhere near a partner. That checking takes as long as writing it herself. So she does one of two things: she stops using AI, or she stops checking. Both are bad."

> "VERITAS is the seatbelt. Upload the AI-generated draft. In under a minute, you get every legal proposition classified, verified against Indian statute and case law, and flagged if the AI overstated, contradicted, or fabricated."

### [0:50 — 2:20] Live demo

*(Upload `rajesh_sharma_v_priya_enterprises.pdf`.)*

> "This is an AI-generated legal memo for a real-looking Bombay HC property dispute. Ten propositions. The associate has no idea which are trustworthy."

*(Wait for report. Land on dashboard.)*

> "Integrity score: 58. Two procedural issues flagged. One fabricated citation."

*(Click the fabricated citation flag.)*

> "The memo cites *ABC Developers Pvt Ltd v State of Maharashtra*, (2021) 4 SCC 321. VERITAS searched our corpus of Supreme Court and High Court judgments — no such case exists. In the current legal-AI wave, this is the single failure that has cost lawyers their careers. VERITAS caught it in three seconds."

*(Click the overstated interim injunction flag.)*

> "The memo says a prima facie case is enough for an interim injunction. VERITAS retrieved Order XXXIX and *Dalpat Kumar v Prahlad Singh*. The Supreme Court has held that all three elements are required: prima facie case, balance of convenience, and irreparable injury. The claim is overstated — here are the two missing elements the associate would have to add before filing."

*(Click the res judicata flag.)*

> "Section 11 CPC requires six elements. The memo collapses them to one. VERITAS lists exactly which elements the AI-generated draft dropped."

### [2:20 — 2:50] The CPC differentiator

> "The Indian legal AI market has a dozen drafting tools and one or two research tools. None of them do procedural verification on the CPC. Ask any Indian civil litigator whether procedural mistakes get more people in trouble than substantive ones and you'll get the same answer. VERITAS is the first tool where every procedural claim gets checked against the actual Section, Order, and Rule text — and against the case law interpreting them."

### [2:50 — 3:00] Close

> "AI drafts. VERITAS verifies. The lawyer decides."

---

## PART 11 — RISK MITIGATION

### 11.1 If time runs out — cut in this order

1. Reranker (Phase 2 stretch) — cut first.
2. Live Indian Kanoon HTTP fallback for citation verification (Phase 4) — cut, rely only on golden set.
3. Contract Act and Specific Relief Act — cut to top 5 sections each.
4. Async job queue in Phase 5 — cut, synchronous is fine.
5. PDF export in Phase 6 — cut, show on screen only.
6. Only cut Phase 6 UI polish if you've already cut everything above.

**Never cut:** the seeded demo document, the drilldown Sheet UI, or the citation verifier.

### 11.2 If a component fails on demo day

- **LLM API down:** Cache the demo report as static JSON. Serve from `/report/demo`.
- **Vector DB refuses to load:** BM25-only mode. Quality drops, system still works.
- **Frontend build breaks:** Pre-render the demo report as static HTML fallback.
- **Wifi dies:** Everything runs on localhost. Do not depend on cloud in the demo.

### 11.3 Legal accuracy risk

- Judges may include lawyers.
- Every seeded verdict must be checkable by a lawyer without embarrassing you. Ask a law student to read Parts 8 and 9 before demo day and confirm each expected verdict is defensible.
- The pitch always frames VERITAS as "a verification layer that flags claims for human review" — never "an authoritative legal opinion tool."

### 11.4 Common hackathon losing patterns to avoid

- Three features at 60% instead of one at 95%.
- Impressive tech, boring demo. Judges reward what they can see.
- Reading slides. Show the product. The product is the pitch.
- Fabricating results if the live pipeline fails. Own the failure. Do NOT fake it.

---

## PART 12 — STRETCH GOALS (only if MVP is stable by hour 30)

Ranked by demo impact per hour of effort:

1. **"Suggest a fix" button** on each 🟠 flag — LLM proposes a corrected version of the claim, adding missing elements. Judges love actionable output. Uses `SUGGESTION_SYSTEM` prompt (add to `prompts.py`).
2. **Comparison view:** upload two versions of a document, show which flags were resolved.
3. **Chrome extension:** highlight text in Google Docs, right-click → "Verify with VERITAS."
4. **Live Indian Kanoon integration** with the paid API — replace local lookup with live query.
5. **Case-law relationship graph:** cited cases + their citations as a small D3 network.

Do not attempt these until MVP is bulletproof.

---

## PART 13 — KICKOFF PROMPT FOR CLAUDE CODE

Paste this into Claude Code as the very first message, after `git init`:

> I am building **VERITAS**, a civil litigation verification engine for Indian law that verifies substantive legal propositions and CPC procedural claims in AI-generated legal documents. The full specification is in `VERITAS_SPEC.md` at the repo root — read it end-to-end before writing any code.
>
> Work through Phases 0 through 7 in order. After each phase, run the acceptance tests defined in the spec, commit with message `phase-N: <summary>`, and confirm with me before moving to the next phase.
>
> Start with Phase 0. Use the exact folder structure in Part 5. Pin all dependency versions. Prefer explicit over clever — this is a hackathon demo, readability matters more than elegance.
>
> Two hard rules for every LLM prompt you write:
> (1) The verification LLM may only reason from provided sources; it must return UNVERIFIABLE if the sources are silent.
> (2) All LLM outputs must be structured JSON via tool_use schemas; never accept free-form output.
>
> When implementing Phases 3, 4, and 7, copy the code and content in Parts 7, 8, 9, and 10 of the spec verbatim into the file paths shown. Do not rewrite them.
>
> Begin Phase 0.

---

## APPENDIX — QUICK REFERENCE

### Repos to clone / study Day 1

- `civictech-India/Indian-Law-Penal-Code-Json` — **clone for cpc.json**
- `ShubhamKumarNigam/NyayaRAG` — reference RAG architecture (AACL 2025)
- `DanielDeshmukh/Hector` — zero-hallucination hard-RAG reference
- `Vaquill-AI/awesome-legaltech` — full resource landscape
- `upalbhattacharya/indian-legal-dataset-preparation` — preprocessing patterns

### Papers to skim (one paragraph each)

- Stanford RegLab "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools" — cite this in the pitch.
- NyayaRAG (Nigam et al., AACL 2025) — validates RAG-for-Indian-law.
- LegalRAG — hybrid retrieval justification.
- Digital Applied "50-year archive, zero-tolerance brief" — hybrid retrieval as "single largest quality lever."

### Pitch one-liners bank

- "AI drafts. VERITAS verifies. The lawyer decides."
- "Stanford found leading legal AI tools hallucinate up to 33% of the time. VERITAS is the seatbelt."
- "Every Indian legal AI tool today is a generator with citations bolted on. VERITAS is the only verifier."
- "The CPC is procedural law. VERITAS is the only tool that checks whether a case can actually proceed the way the draft says it should."
- "We don't tell you what the law is. We tell you whether the draft got it right."

---

**End of specification.**

Total scope: ~15,000 words, one file, everything Claude Code needs.
Build budget: 40–50 focused hours solo, 24–35 hours for a team of 2–3.
Good luck at Vibeathon.
