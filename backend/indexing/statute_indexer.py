"""
Builds the two statute indices used by hybrid retrieval:

1. A BM25Okapi index over chunk text, pickled to data/indices/bm25_statutes.pkl
   alongside a parallel list of chunk metadata (as plain dicts, in the same
   order as the BM25 corpus).
2. A ChromaDB persistent collection named "statutes" at data/indices/chroma_db/,
   with dense embeddings and metadata attached to each chunk.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

from backend.indexing.embeddings import embed
from backend.models.schemas import SourceChunk

BM25_STOPWORD_FREE_TOKENIZER = None  # simple whitespace tokenizer is used below


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def _chunk_metadata(chunk: SourceChunk) -> dict:
    """Flatten a SourceChunk into a Chroma-compatible metadata dict (no Nones)."""
    data = chunk.model_dump(exclude={"text"})
    return {k: v for k, v in data.items() if v is not None}


def build_bm25_index(chunks: list[SourceChunk], out_path: Path) -> None:
    corpus_tokens = [_tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(corpus_tokens)
    metadata = [_chunk_metadata(c) for c in chunks]
    texts = [c.text for c in chunks]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump({"bm25": bm25, "metadata": metadata, "texts": texts}, f)
    print(f"BM25 statute index: {len(chunks)} chunks -> {out_path}")


def build_chroma_index(chunks: list[SourceChunk], persist_dir: Path, collection_name: str = "statutes") -> None:
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(collection_name)

    texts = [c.text for c in chunks]
    ids = [c.chunk_id for c in chunks]
    metadatas = [_chunk_metadata(c) for c in chunks]
    vectors = embed(texts)

    collection.add(
        ids=ids,
        embeddings=vectors.tolist(),
        documents=texts,
        metadatas=metadatas,
    )
    print(f"Chroma '{collection_name}' collection: {len(chunks)} chunks -> {persist_dir}")


def build_statute_indices(chunks: list[SourceChunk], indices_dir: Path) -> None:
    build_bm25_index(chunks, indices_dir / "bm25_statutes.pkl")
    build_chroma_index(chunks, indices_dir / "chroma_db", collection_name="statutes")
