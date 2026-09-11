"""
Smoke-tests the full pipeline through the actual HTTP API (POST /verify,
poll GET /report/{job_id}) using the demo PDF, and prints the resulting
integrity score.
"""
from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_PDF = REPO_ROOT / "data" / "demo" / "rajesh_sharma_v_priya_enterprises.pdf"

POLL_INTERVAL_SECONDS = 2
MAX_POLLS = 60


def main() -> None:
    if not DEMO_PDF.exists():
        raise SystemExit(
            f"{DEMO_PDF} not found -- run scripts/04_generate_demo_doc.py first."
        )

    client = TestClient(app)

    with DEMO_PDF.open("rb") as f:
        response = client.post(
            "/verify",
            files={"file": (DEMO_PDF.name, f, "application/pdf")},
        )
    response.raise_for_status()
    job_id = response.json()["job_id"]
    print(f"job_id: {job_id}")

    report = None
    for _ in range(MAX_POLLS):
        poll = client.get(f"/report/{job_id}")
        poll.raise_for_status()
        body = poll.json()
        status = body.get("status")
        if status == "completed" or "integrity_score" in body:
            report = body
            break
        if status == "failed":
            raise SystemExit(f"pipeline failed: {body.get('error')}")
        print(f"  status: {status or 'processing'} ...")
        time.sleep(POLL_INTERVAL_SECONDS)

    if report is None:
        raise SystemExit("timed out waiting for report")

    print()
    print(f"Integrity score: {report['integrity_score']:.1f}")
    print(f"Procedural risk flag: {report['procedural_risk_flag']}")
    if report.get("procedural_risk_summary"):
        print(f"  {report['procedural_risk_summary']}")
    print(f"Total claims analyzed: {report['total_claims_analyzed']}")
    print(f"Category breakdown: {report['category_breakdown']}")
    print(f"Citation verdicts: {len(report['citation_verdicts'])}")
    for cv in report["citation_verdicts"]:
        print(f"  verified={cv['verified']} | {cv['citation']['raw_text']} | {cv['reason']}")


if __name__ == "__main__":
    main()
