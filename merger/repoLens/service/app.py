from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import asyncio
import json
import time
import ipaddress
import logging
import re
from datetime import datetime

from .models import JobRequest, Job, Artifact, AtlasRequest, AtlasArtifact
from .jobstore import JobStore
from .runner import JobRunner
from .security import verify_token, get_security_config, validate_hub_path, validate_repo_name, resolve_relative_path
from .fs_resolver import resolve_fs_path, list_allowed_roots, issue_fs_token, TrustedPath
from .atlas import AtlasScanner, render_atlas_md
from .metarepo_sync import sync_from_metarepo

try:
    from merge_core import detect_hub_dir, get_merges_dir, MERGES_DIR_NAME, SPEC_VERSION
except ImportError:
    from ...merge_core import detect_hub_dir, get_merges_dir, MERGES_DIR_NAME, SPEC_VERSION

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="rLens", version="1.0.0")

# Security: Root Jail for File System Browsing
# Set to system root to allow full access, but preventing traversal above it (which is impossible anyway).
# Can be overridden if needed via Env or Config in future.
FS_ROOT = Path("/").resolve()

def _is_loopback_host(host: str) -> bool:
    h = (host or "").strip().lower()
    if h in ("127.0.0.1", "localhost", "::1"):
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except Exception:
        return False

# Global State
class ServiceState:
    hub: Path = None
    merges_dir: Path = None
    job_store: JobStore = None
    runner: JobRunner = None

state = ServiceState()

def init_service(hub_path: Path, token: Optional[str] = None, host: str = "127.0.0.1", merges_dir: Optional[Path] = None):
    state.hub = hub_path
    state.merges_dir = merges_dir
    state.job_store = JobStore(hub_path)
    state.runner = JobRunner(state.job_store)

    # Configure Security
    sec = get_security_config()
    sec.set_token(token)
    # Allowlist the Hub
    sec.add_allowlist_root(hub_path)
    # Allowlist Merges Dir if separate
    if merges_dir:
        sec.add_allowlist_root(merges_dir)

    # DANGEROUS CAPABILITY:
    # Allows rLens to browse the entire filesystem ("/") via API.
    # Must be explicitly enabled.
    if os.getenv("RLENS_ALLOW_FS_ROOT", "0") == "1":
        sec.add_allowlist_root(Path("/"))

    # Apply CORS based on host
    # Prevent middleware duplication (if init called multiple times in tests)
    has_cors = any(m.cls == CORSMiddleware for m in app.user_middleware)
    if not has_cors:
        if _is_loopback_host(host):
            # Regex for localhost/127.0.0.1 with any port
            allow_origin_regex = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"
            allow_origins = []
        else:
            allow_origin_regex = None
            allow_origins = [] # Strict for non-loopback by default

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_origin_regex=allow_origin_regex,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type", "x-rlens-token"],
        )

def _list_dir(candidate: Path) -> Dict[str, Any]:
    # Defense-in-depth: always re-validate before touching the filesystem.
    sec = get_security_config()
    resolved = sec.validate_path(candidate)

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    if not resolved.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")

    dirs: List[str] = []
    files: List[str] = []
    entries: List[Dict[str, Any]] = []

    try:
        for child in sorted(resolved.iterdir(), key=lambda x: x.name.lower()):
            if child.is_dir():
                dirs.append(child.name)
                entries.append({"name": child.name, "type": "dir", "token": issue_fs_token(child.resolve())})
            else:
                files.append(child.name)
                entries.append({"name": child.name, "type": "file"})
    except OSError as e:
        logger.error(f"Error listing {resolved}: {e}")
        raise HTTPException(status_code=500, detail="Error listing directory")

    return {"abs": str(resolved), "dirs": dirs, "files": files, "entries": entries}

@app.get("/api/fs/roots", dependencies=[Depends(verify_token)])
def api_fs_roots():
    """
    Return a stable list of allowed roots for the picker & agents.
    The client should prefer token navigation.
    """
    roots = list_allowed_roots(state.hub, getattr(state, "merges_dir", None))
    # Add tokens for each root
    out = []
    for r in roots:
        p = Path(r["path"]).resolve()
        out.append({**r, "token": issue_fs_token(p)})
    return {"roots": out}

@app.get("/api/fs", dependencies=[Depends(verify_token)])
@app.get("/api/fs/list", dependencies=[Depends(verify_token)])
def api_fs_list(token: Optional[str] = None, root: Optional[str] = None, rel: Optional[str] = None):
    """
    FS listing endpoint.
    Canonical: ?token=<opaque>
    Transitional: ?root=<root_id>&rel=   (base only; subpaths require tokens)
    """
    hub = state.hub
    merges_dir = getattr(state, "merges_dir", None)
    trusted = resolve_fs_path(hub=hub, merges_dir=merges_dir, root_id=root, rel_path=rel, token=token)
    payload = _list_dir(trusted.path)
    # Add parent token for upward navigation if possible
    try:
        # Only offer parent if parent itself is allowed (avoid broken Up + reduce taint)
        sec = get_security_config()
        p = trusted.path
        if p.parent and p.parent != p:
            parent_resolved = sec.validate_path(p.parent)
            payload["parent_token"] = issue_fs_token(parent_resolved)
    except Exception:
        pass
    return {"root": root, "rel": rel, "token": token, **payload}

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": SPEC_VERSION,
        "hub": str(state.hub),
        "merges_dir": str(state.merges_dir) if state.merges_dir else None,
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

    # Apply default merges dir if not specified
    if not request.merges_dir and state.merges_dir:
        request.merges_dir = str(state.merges_dir)

    # Validate repo names early (API must be strict)
    if request.repos:
        request.repos = [validate_repo_name(r) for r in request.repos]

    job = Job.create(request)
    job.hub_resolved = str(req_hub)
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
            # Read logs from file
            # Optimized to read full file then slice. In production, seek() would be better.
            logs = state.job_store.read_log_lines(job_id)

            if len(logs) > last_idx:
                for line in logs[last_idx:]:
                    yield f"data: {line}\n\n"
                last_idx = len(logs)

            # Check status for completion
            current_job = state.job_store.get_job(job_id)
            if not current_job:
                break

            if current_job.status in ["succeeded", "failed", "canceled"]:
                # Ensure we sent everything
                logs = state.job_store.read_log_lines(job_id)
                if len(logs) > last_idx:
                    for line in logs[last_idx:]:
                        yield f"data: {line}\n\n"

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

# Atlas API

@app.post("/api/atlas", response_model=AtlasArtifact, dependencies=[Depends(verify_token)])
async def create_atlas(request: AtlasRequest, background_tasks: BackgroundTasks):
    # Determine root to scan
    hub = state.hub
    if not hub:
        raise HTTPException(status_code=400, detail="Hub not configured")

    # Resolve scan root
    try:
        # Canonical: token-based root selection (no user path expressions)
        if request.root_token:
            trusted = resolve_fs_path(
                hub=hub,
                merges_dir=state.merges_dir,
                token=request.root_token,
            )
            scan_root = trusted.path
        else:
            # Transitional: root_id only (known ids)
            root_id = request.root_id or "hub"
            if root_id not in ("hub", "merges", "system"):
                # Strict rejection of raw paths for Atlas to satisfy CodeQL
                raise HTTPException(status_code=400, detail="Invalid Atlas root_id or missing token")

            trusted = resolve_fs_path(
                hub=hub,
                merges_dir=state.merges_dir,
                root_id=root_id,
                rel_path="",
            )
            scan_root = trusted.path

    except HTTPException as e:
         raise e

    # Generate ID
    scan_id = f"atlas-{int(time.time())}"

    # Define output paths
    merges_dir = state.merges_dir or get_merges_dir(hub)
    if not merges_dir.exists():
        merges_dir.mkdir(parents=True, exist_ok=True)

    json_filename = f"{scan_id}.json"
    md_filename = f"{scan_id}.md"

    # Helper to run scan and save
    def run_scan_and_save():
        try:
            scanner = AtlasScanner(
                root=scan_root,
                max_depth=request.max_depth,
                max_entries=request.max_entries,
                exclude_globs=request.exclude_globs
            )
            result = scanner.scan()

            # Save JSON
            with open(merges_dir / json_filename, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            # Render and Save MD
            md_content = render_atlas_md(result)
            with open(merges_dir / md_filename, "w", encoding="utf-8") as f:
                f.write(md_content)

            logger.info(f"Atlas scan completed: {scan_id}")

        except Exception as e:
            logger.exception(f"Atlas scan failed: {e}")
            # Could save an error file?

    background_tasks.add_task(run_scan_and_save)

    # Return "pending" artifact response immediately (optimistic)
    # Or should we store it in a store?
    # For now, we return the paths where it WILL be.
    return AtlasArtifact(
        id=scan_id,
        created_at=datetime.utcnow().isoformat(),
        hub=str(hub),
        root_scanned=str(scan_root),
        paths={"json": json_filename, "md": md_filename},
        stats={} # Empty initially
    )

@app.post("/api/sync/metarepo", dependencies=[Depends(verify_token)])
def api_sync_metarepo(payload: Dict[str, Any]):
    """
    Trigger a metarepo synchronization (Manifest -> Fleet).
    Payload: { "mode": "dry_run"|"apply", "targets": ["wgx", "ci", ...] }
    """
    mode = payload.get("mode", "dry_run")
    targets = payload.get("targets")

    hub_path = state.hub
    if not hub_path:
        raise HTTPException(status_code=400, detail="Hub not configured")

    try:
        report = sync_from_metarepo(hub_path=hub_path, mode=mode, targets=targets)
        return report
    except Exception as e:
        logger.exception(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/atlas/latest", dependencies=[Depends(verify_token)])
def get_latest_atlas():
    merges_dir = state.merges_dir
    if not merges_dir and state.hub:
        merges_dir = get_merges_dir(state.hub)

    if not merges_dir or not merges_dir.exists():
        raise HTTPException(status_code=404, detail="No atlas artifacts found (no merges dir)")

    # Find atlas files
    # Pattern: atlas-{timestamp}.json
    files = list(merges_dir.glob("atlas-*.json"))
    if not files:
         raise HTTPException(status_code=404, detail="No atlas artifacts found")

    # Sort by name (timestamp) desc
    latest_file = sorted(files, key=lambda f: f.name, reverse=True)[0]

    # Load content for stats?
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            stats = data.get("stats", {})
            scan_root = data.get("root", "?")
    except Exception:
        stats = {}
        scan_root = "?"

    scan_id = latest_file.stem # atlas-123456

    return AtlasArtifact(
        id=scan_id,
        created_at=datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
        hub=str(state.hub),
        root_scanned=scan_root,
        paths={"json": latest_file.name, "md": latest_file.with_suffix(".md").name},
        stats=stats
    )

@app.get("/api/atlas/{id}/download", dependencies=[Depends(verify_token)])
def download_atlas(id: str, key: str = "md"):
    # Hard allowlist: atlas ids are generated as "atlas-<unix_ts>"
    if not re.fullmatch(r"atlas-\d+", (id or "").strip()):
        raise HTTPException(status_code=400, detail="Invalid atlas id format")

    if key not in ("json", "md"):
        raise HTTPException(status_code=400, detail="Invalid key. Use 'json' or 'md'.")

    if not state.hub:
        raise HTTPException(status_code=400, detail="Hub not configured")

    merges_dir = (state.merges_dir or get_merges_dir(state.hub)).resolve()
    if not merges_dir.exists():
        raise HTTPException(status_code=404, detail="Merges directory not found")

    # IMPORTANT: do NOT build a path from user input.
    # Enumerate allowed files and then select by id.
    candidates = {}
    for p in merges_dir.glob(f"atlas-*.{key}"):
        try:
            rp = p.resolve()
            rp.relative_to(merges_dir)  # containment even under symlinks
        except Exception:
            continue
        candidates[p.stem] = rp

    file_path = candidates.get(id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    # Final belt-and-suspenders containment check
    try:
        file_path.relative_to(merges_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(file_path, filename=file_path.name)

@app.post("/api/export/webmaschine", dependencies=[Depends(verify_token)])
def export_webmaschine():
    """
    Prepares an export directory for 'webmaschine'.
    """
    hub = state.hub
    if not hub:
        raise HTTPException(status_code=400, detail="Hub not configured")

    export_root = hub.parent / "exports" / "webmaschine" # Place next to hub or inside?
    # User said: "Erzeugt Verzeichnis exports/webmaschine/"
    # Where? Usually relative to where repolens is running or the repo root?
    # Or inside the Hub? "hub/exports"?
    # "innerhalb des Repos" context suggests inside the tooling repo?
    # But repolensd runs on the user's machine on a "Hub".
    # Let's put it in `merges_dir/../exports/webmaschine` to be near output?
    # Or just `hub/exports`?
    # Let's try `hub/exports/webmaschine` if hub is writable.

    target_dir = hub / "exports" / "webmaschine"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "atlas").mkdir(exist_ok=True)
        (target_dir / "repos").mkdir(exist_ok=True)

        # 1. Copy latest Atlas
        # Reuse get_latest_atlas logic
        try:
            latest = get_latest_atlas()
            merges_dir = state.merges_dir or get_merges_dir(hub)

            import shutil
            shutil.copy2(merges_dir / latest.paths["json"], target_dir / "atlas" / "latest.json")
            shutil.copy2(merges_dir / latest.paths["md"], target_dir / "atlas" / "latest.md")
        except HTTPException:
            logger.warning("No atlas found to export")

        # 2. Export Repos Index
        # We can just dump _find_repos result
        from .runner import _find_repos
        repos = _find_repos(hub)
        with open(target_dir / "repos" / "index.json", "w", encoding="utf-8") as f:
            json.dump(repos, f, indent=2)

        # 3. README
        readme_content = """# Webmaschine Export

This directory contains the latest atlas and repository index from RepoLens.

## Update
Run `POST /api/export/webmaschine` to update these files.
"""
        with open(target_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

        return {"status": "ok", "path": str(target_dir)}

    except Exception as e:
        logger.exception(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

# Serve static UI
# We assume webui folder is next to this file
current_dir = Path(__file__).parent
webui_dir = current_dir / "webui"
if webui_dir.exists():
    app.mount("/", StaticFiles(directory=str(webui_dir), html=True), name="webui")
