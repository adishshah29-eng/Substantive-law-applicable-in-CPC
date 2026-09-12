# Deploying VERITAS to Render

Vercel can host the Next.js frontend, but **not** the FastAPI backend: it
depends on `sentence-transformers`/`torch` (a ~1.5GB embedding model) and a
persistent Chroma/BM25 index, which don't fit Vercel's serverless function
size and execution-time limits. This repo deploys both halves to
**Render** instead, via the `render.yaml` blueprint at the repo root and
the `Dockerfile` for the backend.

## What's already set up

- **`Dockerfile`** — builds the backend image and bakes the statute +
  judgment indices into the image at *build* time (downloads `cpc.json`,
  embeds the corpus with `bge-large-en-v1.5`, builds BM25 + Chroma). The
  corpus is static, so no persistent disk is needed at runtime.
- **`render.yaml`** — defines two services: `veritas-backend` (Docker) and
  `veritas-frontend` (Node/Next.js).
- **`backend/main.py`** — CORS origins are read from `ALLOWED_ORIGINS`
  (comma-separated), defaulting to `http://localhost:3000` for local dev.
- **`frontend/lib/api.ts`** — reads the backend URL from
  `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000` for local dev.

## Steps

1. **Push this repo to GitHub** if it isn't already (Render deploys from a
   Git remote, not a local directory).

2. **In the Render dashboard:** New → Blueprint → connect this repository.
   Render will read `render.yaml` and propose both services
   (`veritas-backend`, `veritas-frontend`). Click **Apply**.

3. **Set the backend's secret before the first deploy finishes:**
   Dashboard → `veritas-backend` → Environment → add `GEMINI_API_KEY` with
   your key (from [Google AI Studio](https://aistudio.google.com/apikey)).
   `render.yaml` deliberately does not set this (`sync: false`) so it's
   never committed to the repo.

4. **Wait for both builds.** The backend build takes several minutes —
   it's downloading and embedding the full statute + judgment corpus, not
   just installing packages. Watch the backend's build logs; the last
   lines should look like:
   ```
   BM25 index: ... chunks -> data/indices/bm25_statutes.pkl
   Chroma 'judgments' collection: 30 chunks -> data/indices/chroma_db
   Done.
   ```

5. **Check the two URLs Render actually assigned.** `render.yaml` assumes
   `https://veritas-backend.onrender.com` and
   `https://veritas-frontend.onrender.com` — Render uses exactly that if
   the names are free, but appends a random suffix if someone else already
   has them. Open each service's page in the dashboard and check the URL
   shown at the top.

   If either differs from the assumed URL, update:
   - `veritas-frontend` → Environment → `NEXT_PUBLIC_API_URL` → the actual backend URL, then **manually redeploy the frontend** (Next.js bakes `NEXT_PUBLIC_*` vars in at build time, so just changing the env var isn't enough — trigger a new deploy after changing it).
   - `veritas-backend` → Environment → `ALLOWED_ORIGINS` → the actual frontend URL, then redeploy the backend (or Render will redeploy it automatically on env var change).

6. **Verify it's live:**
   - `https://<your-backend>.onrender.com/health` → `{"status": "ok"}`
   - Open `https://<your-frontend>.onrender.com`, go to Verify, upload
     `data/demo/rajesh_sharma_v_priya_enterprises.pdf`, and confirm the
     report renders with the fabricated citation flagged.

## Known constraints, honestly

- **RAM.** `render.yaml` pins the backend to Render's `standard` plan
  (2GB). The embedding model alone needs ~1.5GB resident; Render's
  free/starter tiers (512MB) will OOM. This is a real cost, not a free
  demo — check Render's current pricing before deploying.
- **Cold starts.** On Render's free/starter plans, idle services spin
  down and take 30–60s to wake on the next request. The `standard` plan
  the backend needs doesn't idle down, but if you downgrade it to save
  cost, expect the first request after a quiet period to be slow.
- **In-memory job store.** `backend/api/dependencies.py`'s `JOB_STORE` is
  a plain Python dict (explicitly an MVP simplification per
  `VERITAS_SPEC.md`). It resets whenever the backend restarts or
  redeploys, and won't work correctly if you ever scale the backend to
  more than one instance (each instance would have its own store). Fine
  for a single-instance demo; not production-grade job tracking.
- **Rebuilding the index.** Because the index is baked into the Docker
  image, changing anything under `data/statutes/`, `data/judgments/`, or
  the indexing code requires a new backend deploy (which Render triggers
  automatically on a push to the connected branch).
