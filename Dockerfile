# VERITAS backend image. Builds the statute + judgment indices at image
# build time (the corpus is static, so no persistent disk is needed at
# runtime) and serves the FastAPI app.
FROM python:3.11-slim

# git: scripts/01_download_statutes.py clones civictech-India's repo for cpc.json.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY backend ./backend
COPY scripts ./scripts
COPY data ./data

RUN pip install --no-cache-dir -e . \
    && python -m spacy download en_core_web_sm

# Bake the indices into the image: the corpus (statutes, golden-set
# judgments) is static, so building it once at image-build time avoids
# needing a persistent disk at runtime.
RUN python scripts/01_download_statutes.py \
    && python scripts/02_build_statute_index.py \
    && python scripts/03_ingest_golden_judgments.py

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
