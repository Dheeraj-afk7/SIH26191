#!/usr/bin/env python3
"""
SIH26191 -- Dynamic Pipeline Recompute API
==========================================

Provides a POST /api/pipeline/recompute endpoint that triggers
an operator-initiated pipeline recomputation across all pipeline modules.

LABEL: Operator-Triggered Recompute Workflow
Dynamically refreshes active in-memory datasets on completion.
"""

import uuid
import subprocess
import threading
import datetime
import time
import pathlib
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.data_loader import data_store

logger = logging.getLogger(__name__)
router = APIRouter()

_jobs: dict = {}
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent

VALID_STEPS = {
    "priority": {
        "script": "processing/priority/build_village_priority.py",
        "label": "Village Priority Classification (Step 10B + 10C)",
        "estimated_seconds": 5,
    },
    "capacity": {
        "script": "processing/capacity/build_candidate_context.py",
        "label": "Candidate Area Capacity Enrichment (Step 10D)",
        "estimated_seconds": 5,
    },
    "infrastructure": {
        "script": "processing/infrastructure/ingest_critical_infrastructure.py",
        "label": "Critical Infrastructure Ingestion & Routing (Phase 4)",
        "estimated_seconds": 10,
    },
    "decision_summary": {
        "script": "processing/priority/generate_decision_summary.py",
        "label": "Decision Summary & Metadata Generation (Step 10E)",
        "estimated_seconds": 3,
    },
}


class RecomputeRequest(BaseModel):
    steps: List[str] = ["priority", "capacity", "decision_summary"]
    operator_note: Optional[str] = None


def _run_job(job_id: str, steps: List[str], operator_note: Optional[str]):
    """Background thread: run requested pipeline steps sequentially and reload data_store."""
    job = _jobs[job_id]
    job["status"] = "RUNNING"
    job["started_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    results = []
    all_ok = True

    for step in steps:
        if step not in VALID_STEPS:
            results.append({
                "step": step,
                "status": "SKIPPED",
                "reason": f"Unknown step '{step}'. Valid steps: {list(VALID_STEPS.keys())}",
            })
            continue

        step_cfg = VALID_STEPS[step]
        script = str(_ROOT / step_cfg["script"])
        t0 = time.time()

        try:
            proc = subprocess.run(
                ["python", script],
                cwd=str(_ROOT),
                capture_output=True,
                text=True,
                timeout=300,
            )
            elapsed = round(time.time() - t0, 1)
            ok = proc.returncode == 0
            results.append({
                "step": step,
                "label": step_cfg["label"],
                "status": "COMPLETE" if ok else "FAILED",
                "elapsed_seconds": elapsed,
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-500:] if proc.stdout else "",
                "stderr_tail": proc.stderr[-200:] if proc.stderr else "",
            })
            if not ok:
                all_ok = False
        except subprocess.TimeoutExpired:
            results.append({
                "step": step,
                "label": step_cfg["label"],
                "status": "TIMEOUT",
                "elapsed_seconds": 300,
            })
            all_ok = False
        except Exception as exc:
            results.append({
                "step": step,
                "label": step_cfg["label"],
                "status": "ERROR",
                "error": str(exc),
            })
            all_ok = False

    # Dynamically reload active in-memory datasets
    try:
        logger.info("Pipeline recompute finished. Dynamically reloading in-memory data_store...")
        data_store.load_all()
        reload_status = "SUCCESS"
    except Exception as e:
        logger.error(f"Failed to reload data_store: {e}")
        reload_status = f"FAILED: {e}"

    job["status"] = "COMPLETE" if all_ok else "PARTIAL_FAILURE"
    job["completed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    job["step_results"] = results
    job["data_store_reload"] = reload_status
    job["note"] = "Pipeline recomputation complete and in-memory datasets dynamically refreshed."
    if operator_note:
        job["operator_note"] = operator_note

    logger.info(f"Pipeline job {job_id} finished: {job['status']}")


@router.post("/pipeline/recompute")
def trigger_recompute(request: RecomputeRequest):
    """
    Trigger an operator-initiated pipeline recompute.
    """
    unknown = [s for s in request.steps if s not in VALID_STEPS]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown steps: {unknown}. Valid steps: {list(VALID_STEPS.keys())}",
        )

    job_id = str(uuid.uuid4())[:8]
    estimated = sum(
        VALID_STEPS[s]["estimated_seconds"] for s in request.steps if s in VALID_STEPS
    )

    _jobs[job_id] = {
        "job_id": job_id,
        "status": "QUEUED",
        "steps": request.steps,
        "operator_note": request.operator_note,
        "queued_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "started_at": None,
        "completed_at": None,
        "estimated_seconds": estimated,
        "step_results": [],
        "disclaimer": (
            "Operator-Triggered Recompute Workflow -- Not autonomous real-time monitoring. "
            "Results reflect configured thresholds in configs/priority_thresholds.yaml."
        ),
    }

    thread = threading.Thread(
        target=_run_job,
        args=(job_id, request.steps, request.operator_note),
        daemon=True,
    )
    thread.start()

    return {
        "job_id": job_id,
        "status": "QUEUED",
        "steps": request.steps,
        "estimated_seconds": estimated,
        "poll_url": f"/api/pipeline/status/{job_id}",
        "label": "Operator-Triggered Recompute Workflow",
        "disclaimer": _jobs[job_id]["disclaimer"],
    }


@router.get("/pipeline/status/{job_id}")
def get_pipeline_status(job_id: str):
    """Poll the status of a pipeline recompute job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return _jobs[job_id]


@router.get("/pipeline/steps")
def list_pipeline_steps():
    """List available pipeline recompute steps."""
    return {
        "available_steps": [
            {
                "step": k,
                "label": v["label"],
                "estimated_seconds": v["estimated_seconds"],
            }
            for k, v in VALID_STEPS.items()
        ],
        "usage": "POST /api/pipeline/recompute with {\"steps\": [\"priority\", \"capacity\", \"infrastructure\"]}",
    }
