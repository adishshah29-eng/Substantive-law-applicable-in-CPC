# VERITAS

Civil Litigation Verification Engine — verifies substantive legal propositions and CPC procedural claims in AI-generated Indian legal documents.

Full specification: [`VERITAS_SPEC.md`](./VERITAS_SPEC.md). Demo script: [`docs/DEMO_SCRIPT.md`](./docs/DEMO_SCRIPT.md). Expected results for the seeded demo: [`docs/SEEDED_DOCUMENT_KEY.md`](./docs/SEEDED_DOCUMENT_KEY.md).

## Run it

Backend (FastAPI):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m spacy download en_core_web_sm

cp .env.example .env   # fill in GEMINI_API_KEY

# Build the statute + judgment indices (one-time, or after editing data/):
python scripts/01_download_statutes.py
python scripts/02_build_statute_index.py
python scripts/03_ingest_golden_judgments.py

uvicorn backend.main:app --reload
```

`GET http://localhost:8000/health` should return `{"status": "ok"}`.

Frontend (Next.js):

```bash
cd frontend
npm install
npm run dev
```

`http://localhost:3000` should be reachable.

### Try the demo end to end

```bash
python scripts/04_generate_demo_doc.py     # regenerates data/demo/*.pdf if needed
python scripts/05_smoke_test_pipeline.py   # drives the real API with the demo PDF, prints the integrity score
```

Or upload `data/demo/rajesh_sharma_v_priya_enterprises.pdf` at `http://localhost:3000/verify`.

## Status

All phases in `VERITAS_SPEC.md` Part 6 are implemented and tested end-to-end against the real demo document:

- **Phase 1** — statute ingestion (CPC sections + hand-curated Order/Rule provisions, Contract Act, Specific Relief Act) with a hybrid BM25 + dense index.
- **Phase 2** — 30-judgment golden-set corpus, hybrid retrieval with Reciprocal Rank Fusion across statutes and judgments.
- **Phase 3** — PDF/DOCX ingestion, sentence splitting, citation regex extraction, LLM claim classifier.
- **Phase 4** — citation verifier (exact + fuzzy match), statute/case routers, the verdict engine.
- **Phase 5** — risk scoring, report assembly, and the FastAPI orchestration (`POST /verify`, `GET /report/{id}`, `GET /source/{id}`).
- **Phase 6** — the Next.js dashboard (landing, upload/progress, report view with drilldown), redesigned onto a navy/gold legal-tech visual system.
- **Phase 7** — the seeded demo document, its answer key, and the demo script are in place; `docs/SEEDED_DOCUMENT_KEY.md` includes a comparison of the spec's illustrative expectations against what the built pipeline actually produces.

**LLM provider note:** the spec's primary choice was Claude/Anthropic tool-use; this build runs on a Gemini API key instead (`GEMINI_API_KEY` in `.env`), via `backend/verification/llm_client.py`, which adapts the same `prompts.py` schemas to Gemini's structured-output API. Default model is `gemini-3.5-flash-lite`.

Run the test suite with:

```bash
PYTHONPATH=. pytest tests/
```

(Tests that call the LLM are skipped automatically if `GEMINI_API_KEY` is not set.)
