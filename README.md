# VERITAS

Civil Litigation Verification Engine — verifies substantive legal propositions and CPC procedural claims in AI-generated Indian legal documents.

Full specification: [`VERITAS_SPEC.md`](./VERITAS_SPEC.md).

## Run it

Backend (FastAPI):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in ANTHROPIC_API_KEY
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

## Status

Phase 0 (scaffold) complete. See `VERITAS_SPEC.md` Part 6 for the phased build plan (Phase 1: statute ingestion, Phase 2: judgment retrieval, Phase 3: document ingestion + claim classifier, Phase 4: verdict engine, Phase 5: API orchestration, Phase 6: frontend dashboard, Phase 7: demo).
