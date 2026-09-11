"""
In-memory job store and shared lookups for the API layer. MVP only: no
persistence, no multi-process safety -- fine for a single-process
hackathon demo (see VERITAS_SPEC.md Part 6 Phase 5).
"""
from __future__ import annotations

from backend.models.schemas import JobStatus, SourceChunk
from backend.retrieval import bm25_retriever

JOB_STORE: dict[str, JobStatus] = {}

_SOURCE_COLLECTIONS = ("statutes", "judgments")


def get_job(job_id: str) -> JobStatus | None:
    return JOB_STORE.get(job_id)


def set_job(job_status: JobStatus) -> None:
    JOB_STORE[job_status.job_id] = job_status


def find_source_chunk(source_id: str) -> SourceChunk | None:
    for collection in _SOURCE_COLLECTIONS:
        try:
            data = bm25_retriever._load(collection)
        except FileNotFoundError:
            continue
        for meta, text in zip(data["metadata"], data["texts"]):
            if meta.get("chunk_id") == source_id:
                return SourceChunk(**{**meta, "text": text})
    return None
