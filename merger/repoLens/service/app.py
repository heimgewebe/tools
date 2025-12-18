from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
import asyncio
import json
import time

from .models import JobRequest, Job, Artifact
from .jobstore import JobStore
from .runner import JobRunner
from .security import verify_token, get_security_config, validate_hub_path

try:
    from merge_core import detect_hub_dir, get_merges_dir, MERGES_DIR_NAME, SPEC_VERSION
except ImportError:
    from ...merge_core import detect_hub_dir, get_merges_dir, MERGES_DIR_NAME, SPEC_VERSION


app = FastAPI(title="repoLens Service", version="1.0.0")

# CORS
# Tighten CORS: If token is used, we can be stricter.
# But for local tool, usually we want to allow localhost access.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Still useful for local dev, but Security layer protects actions
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
class ServiceState:
    hub: Path = None
    job_store: JobStore = None
    runner: JobRunner = None

state = ServiceState()

def init_service(hub_path: Path, token: Optional[str] = None):
    state.hub = hub_path
    state.job_store = JobStore(hub_path)
    state.runner = JobRunner(state.job_store)

    # Configure Security
    sec = get_security_config()
    sec.set_token(token)
    # Allowlist the Hub
    sec.add_allowlist_root(hub_path)
    # Also allow current dir if different? No, start with Hub.

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": SPEC_VERSION,
        "hub": str(state.hub),
        "auth_enabled": bool(get_security_config().token),
        "running_jobs": len(state.runner.futures) if state.runner else 0
    }

@app.get("/api/repos", dependencies=[Depends(verify_token)])
def list_repos(hub: Optional[str] = None):
    # If hub provided, validate it first
    target_hub = state.hub
    if hub:
        target_hub = validate_hub_path(hub)

    # Use runner's helper or core helper
    from .runner import _find_repos
    return _find_repos(target_hub)

@app.post("/api/jobs", response_model=Job, dependencies=[Depends(verify_token)])
def create_job(request: JobRequest):
    # Validate Hub in request
    req_hub = state.hub
    if request.hub:
         req_hub = validate_hub_path(request.hub)

    # Also implicit security check: find_repos logic usually stays within hub,
    # but verify paths in job runner?
    # The Runner will use the Hub. If Hub is validated, we are good.

    job = Job.create(request)
    state.job_store.add_job(job)
    state.runner.submit_job(job.id)
    return job

@app.get("/api/jobs", response_model=List[Job], dependencies=[Depends(verify_token)])
def get_jobs(status: Optional[str] = None, limit: int = 20):
    jobs = state.job_store.get_all_jobs()
    if status:
        jobs = [j for j in jobs if j.status == status]
    return jobs[:limit]

@app.get("/api/jobs/{job_id}", response_model=Job, dependencies=[Depends(verify_token)])
def get_job(job_id: str):
    job = state.job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/jobs/{job_id}/cancel", dependencies=[Depends(verify_token)])
def cancel_job(job_id: str):
    job = state.job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ["queued", "running"]:
        job.status = "canceled"
        state.job_store.update_job(job)
    return {"status": "canceled"}

@app.get("/api/jobs/{job_id}/logs", dependencies=[Depends(verify_token)])
def stream_logs(job_id: str):
    # SSE Stream
    job = state.job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def log_generator():
        last_idx = 0
        while True:
            # Refresh job
            current_job = state.job_store.get_job(job_id)
            if not current_job:
                break

            logs = current_job.logs
            if len(logs) > last_idx:
                for line in logs[last_idx:]:
                    yield f"data: {line}\n\n"
                last_idx = len(logs)

            if current_job.status in ["succeeded", "failed", "canceled"]:
                yield "event: end\ndata: end\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.get("/api/artifacts", response_model=List[Artifact], dependencies=[Depends(verify_token)])
def list_artifacts(repo: Optional[str] = None):
    arts = state.job_store.get_all_artifacts()
    if repo:
        arts = [a for a in arts if repo in a.repos]
    return arts

@app.get("/api/artifacts/latest", dependencies=[Depends(verify_token)])
def get_latest_artifact(repo: str, level: str = "max", mode: str = "gesamt"):
    # "Heimgewebe-Hebel" - Return the single latest matching artifact
    arts = state.job_store.get_all_artifacts()
    matches = []

    for a in arts:
        # Filter by params
        if a.params.level != level:
            continue
        if a.params.mode != mode:
            continue

        # Filter by repo
        # If artifact covers specific repos, 'repo' must be in that list.
        # If artifact covers all (empty list/None), it counts as a match for any repo query?
        # Or does 'latest?repo=X' imply "Snapshot of X"?
        # Usually "Snapshot of X" means X is in the list.
        if a.repos:
            if repo in a.repos:
                matches.append(a)
        else:
            # Artifact is for ALL repos.
            # Does this count as "latest artifact for repo X"?
            # Yes, if X is in the hub. We assume it is.
            matches.append(a)

    if not matches:
        raise HTTPException(status_code=404, detail="No matching artifact found")

    # Sort by created_at desc (lexicographical ISO string sort works)
    # The JobStore already returns sorted list (desc), but to be safe/explicit:
    latest = max(matches, key=lambda x: x.created_at)
    return latest

@app.get("/api/artifacts/{id}", dependencies=[Depends(verify_token)])
def get_artifact(id: str):
    art = state.job_store.get_artifact(id)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return art

@app.get("/api/artifacts/{id}/download", dependencies=[Depends(verify_token)])
def download_artifact(id: str, key: str = "md"):
    art = state.job_store.get_artifact(id)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")

    filename = art.paths.get(key)
    if not filename:
        # Try finding part
        if key == "md" and "canonical_md" in art.paths:
            filename = art.paths["canonical_md"]
        elif key == "json" and "index_json" in art.paths:
             filename = art.paths["index_json"]
        else:
             raise HTTPException(status_code=404, detail=f"File key '{key}' not found in artifact")

    merges_dir = get_merges_dir(Path(art.hub))
    file_path = merges_dir / filename

    # Explicitly check if file is inside merges_dir (Directory Traversal Protection)
    try:
        file_path.resolve().relative_to(merges_dir.resolve())
    except ValueError:
         raise HTTPException(status_code=403, detail="Access denied: File outside of merges directory")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File on disk missing")

    return FileResponse(file_path, filename=filename)

# Serve static UI
# We assume webui folder is next to this file
current_dir = Path(__file__).parent
webui_dir = current_dir / "webui"
if webui_dir.exists():
    app.mount("/", StaticFiles(directory=str(webui_dir), html=True), name="webui")
