"""
POST /verify (multipart upload, kicks off the pipeline in the background),
GET /report/{job_id} (poll for the result), GET /source/{source_id}
(full chunk text + metadata for the "View full source" UI drilldown).
"""
from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from backend.api.dependencies import find_source_chunk, get_job, set_job
from backend.models.schemas import JobStatus
from backend.pipeline import verify_document

router = APIRouter()

UPLOAD_DIR = Path(tempfile.gettempdir()) / "veritas_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_SUFFIXES = {".pdf", ".docx"}


def _run_pipeline(job_id: str, file_path: Path, original_filename: str) -> None:
    set_job(JobStatus(job_id=job_id, status="processing", current_step="verifying", progress=0.1))
    try:
        report = verify_document(file_path, job_id, original_filename=original_filename)
        set_job(JobStatus(job_id=job_id, status="completed", progress=1.0, report=report))
    except Exception as exc:
        set_job(JobStatus(job_id=job_id, status="failed", error=str(exc)))
    finally:
        file_path.unlink(missing_ok=True)


@router.post("/verify")
async def verify(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> dict:
    original_filename = file.filename or "document"
    suffix = Path(original_filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(400, f"Unsupported file type {suffix!r}; expected .pdf or .docx")

    job_id = str(uuid.uuid4())
    dest = UPLOAD_DIR / f"{job_id}{suffix}"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    set_job(JobStatus(job_id=job_id, status="queued"))
    background_tasks.add_task(_run_pipeline, job_id, dest, original_filename)

    return {"job_id": job_id, "status": "processing"}


@router.get("/report/{job_id}")
async def get_report(job_id: str) -> dict:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    if job.status != "completed":
        return {"status": job.status, "error": job.error}
    return job.report.model_dump(mode="json")


@router.get("/source/{source_id}")
async def get_source(source_id: str) -> dict:
    chunk = find_source_chunk(source_id)
    if chunk is None:
        raise HTTPException(404, "source not found")
    return chunk.model_dump(mode="json")
