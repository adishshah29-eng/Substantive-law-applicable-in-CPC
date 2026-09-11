"""
Dense (embedding) retrieval over a named Chroma collection ("statutes" or
"judgments").
"""
from __future__ import annotations

from pathlib import Path

import chromadb

from backend.indexing.embeddings import embed
from backend.models.schemas import RetrievalResult, SourceChunk

REPO_ROOT = Path(__file__).resolve().parents[2]
CHROMA_DIR = REPO_ROOT / "data" / "indices" / "chroma_db"

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
    return _client


def retrieve(query: str, top_k: int = 10, collection: str = "statutes") -> list[RetrievalResult]:
    client = _get_client()
    coll = client.get_collection(collection)

    query_vector = embed([query])[0].tolist()
    results = coll.query(query_embeddings=[query_vector], n_results=top_k)

    out = []
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]
    distances = results["distances"][0]
    for rank, (meta, doc, dist) in enumerate(zip(metadatas, documents, distances), start=1):
        chunk_data = dict(meta)
        judges = chunk_data.get("judges")
        if isinstance(judges, str):
            chunk_data["judges"] = judges.split("; ")
        chunk = SourceChunk(**{**chunk_data, "text": doc})
        out.append(
            RetrievalResult(
                chunk=chunk,
                score=1.0 - float(dist),
                dense_rank=rank,
                retrieval_method="dense_only",
            )
        )
    return out
