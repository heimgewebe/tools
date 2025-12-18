import concurrent.futures
import time
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from .models import Job, JobRequest, Artifact
from .jobstore import JobStore

# Import core logic.
# Since this file is in merger/repoLens/service/runner.py,
# and merger/repoLens is usually in sys.path when running repolens.py.
# We can try absolute import first.

try:
    from merge_core import (
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        MergeArtifacts,
        SKIP_ROOTS,
        MERGES_DIR_NAME,
    )
except ImportError:
    # Fallback to relative import if running as package
    from ...merge_core import (
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        MergeArtifacts,
        SKIP_ROOTS,
        MERGES_DIR_NAME,
    )

def _find_repos(hub: Path) -> List[str]:
    repos = []
    if not hub.exists():
        return []
    for child in sorted(hub.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name in SKIP_ROOTS:
            continue
        if child.name == MERGES_DIR_NAME:
            continue
        if child.name.startswith("."):
            continue
        repos.append(child.name)
    return repos

# Helper to parse human size (duplicated from repolens.py to stay independent)
def _parse_human_size(text: str) -> int:
    text = str(text).upper().strip()
    if not text: return 0
    if text.isdigit(): return int(text)

    units = {"K": 1024, "M": 1024**2, "G": 1024**3}
    for u, m in units.items():
        if text.endswith(u) or text.endswith(u+"B"):
            val = text.rstrip(u+"B").rstrip(u)
            try:
                return int(float(val) * m)
            except ValueError:
                return 0
    return 0

def _parse_extras_csv(extras_csv: str) -> ExtrasConfig:
    config = ExtrasConfig()
    items = [x.strip().lower() for x in (extras_csv or "").split(",") if x.strip()]
    for item in items:
        if item == "ai_heatmap":
            item = "heatmap"
        if hasattr(config, item):
            setattr(config, item, True)
    return config

class JobRunner:
    def __init__(self, job_store: JobStore, max_workers: int = 1):
        self.job_store = job_store
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.futures = {}

    def submit_job(self, job_id: str):
        job = self.job_store.get_job(job_id)
        if not job or job.status != "queued":
            return

        future = self.executor.submit(self._run_job, job_id)
        self.futures[job_id] = future

    def _run_job(self, job_id: str):
        job = self.job_store.get_job(job_id)
        if not job:
            return

        # Update status to running
        job.status = "running"
        job.started_at = datetime.utcnow().isoformat()
        self.job_store.update_job(job)

        def log(msg: str):
            # Refresh job from store to get latest logs if needed, but we are single writer mostly
            # Actually for simple list append it's fine, but thread safety?
            # JobStore handles saving.
            # We add timestamp
            ts = datetime.utcnow().strftime("%H:%M:%S")
            job.logs.append(f"[{ts}] {msg}")
            self.job_store.update_job(job)

        try:
            req = job.request

            # 1. Detect Hub
            # We use the service's hub as base, but if request has override, try to use it?
            # The plan said: hub = detect_hub_dir(SCRIPT_PATH, req.hub)
            # SCRIPT_PATH needs to be safe.
            script_path = Path(__file__).resolve()
            # If JobStore has hub_path, prefer that as default
            base_hub = str(self.job_store.hub_path) if self.job_store.hub_path else str(script_path.parent)
            hub = detect_hub_dir(script_path, req.hub or base_hub)
            log(f"Using hub: {hub}")

            # 2. Determine Repos
            if req.repos:
                repo_names = req.repos
                log(f"Selected specific repos: {repo_names}")
            else:
                repo_names = _find_repos(hub)
                log(f"Auto-detected all repos: {repo_names}")

            if not repo_names:
                raise ValueError("No repositories found or selected.")

            sources = []
            for name in repo_names:
                p = hub / name
                if p.is_dir():
                    sources.append(p)
                else:
                    log(f"Warning: Repo {name} not found at {p}")

            if not sources:
                raise ValueError("No valid repository sources found.")

            # 3. Scan Repos
            max_bytes = _parse_human_size(req.max_bytes or "0")
            ext_list = _normalize_ext_list(",".join(req.extensions)) if req.extensions else None
            path_filter = req.path_filter

            summaries = []
            total_sources = len(sources)
            for i, src in enumerate(sources, 1):
                if job.status == "canceled":
                    log("Job canceled during scan.")
                    return

                log(f"Scanning {i}/{total_sources}: {src.name} ...")
                # Note: scan_repo can be slow.
                summary = scan_repo(src, ext_list, path_filter, max_bytes)
                summaries.append(summary)

            # 4. Write Reports
            log("Generating reports...")
            merges_dir = get_merges_dir(hub)

            split_size = _parse_human_size(req.split_size or "25MB")
            extras = _parse_extras_csv(req.extras)
            if req.json_sidecar:
                extras.json_sidecar = True

            artifacts_obj = write_reports_v2(
                merges_dir,
                hub,
                summaries,
                req.level,
                req.mode,
                max_bytes,
                req.plan_only,
                req.code_only,
                split_size,
                debug=False,
                path_filter=path_filter,
                ext_filter=ext_list,
                extras=extras
            )

            # 5. Register Artifacts
            out_paths = artifacts_obj.get_all_paths()
            log(f"Generated {len(out_paths)} files.")

            # Map outputs to Artifact record
            path_map = {}
            if artifacts_obj.index_json:
                path_map["json"] = artifacts_obj.index_json.name

            if artifacts_obj.canonical_md:
                path_map["md"] = artifacts_obj.canonical_md.name

            for i, p in enumerate(artifacts_obj.md_parts):
                path_map[f"md_part_{i+1}"] = p.name

            artifact_id = str(uuid.uuid4())

            art = Artifact(
                id=artifact_id,
                job_id=job_id,
                hub=str(hub),
                repos=repo_names,
                created_at=datetime.utcnow().isoformat(),
                paths=path_map,
                params=req
            )

            self.job_store.add_artifact(art)
            job.artifact_ids.append(artifact_id)

            job.status = "succeeded"
            job.finished_at = datetime.utcnow().isoformat()
            log("Job completed successfully.")
            self.job_store.update_job(job)

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.finished_at = datetime.utcnow().isoformat()
            log(f"Error: {e}")
            import traceback
            traceback.print_exc() # Print to server console too
            self.job_store.update_job(job)
