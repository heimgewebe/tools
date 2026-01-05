import concurrent.futures
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import List

from .models import Artifact
from .jobstore import JobStore
from ..adapters.security import validate_source_dir

# Import core logic.
# Since this file is in merger/repoLens/service/runner.py,
# and merger/repoLens is usually in sys.path when running repolens.py.
# We can try absolute import first.

try:
    from lenskit.core.merge import (
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        SKIP_ROOTS,
        MERGES_DIR_NAME,
        parse_human_size,
    )
except ImportError:
    # Fallback to relative import if running as package
    from ...core.merge import (
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        SKIP_ROOTS,
        MERGES_DIR_NAME,
        parse_human_size,
    )

def _find_repos(hub: Path) -> List[str]:
    from ..adapters.security import validate_source_dir
    hub = validate_source_dir(hub)
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

def _parse_extras_csv(extras_csv: str) -> ExtrasConfig:
    config = ExtrasConfig()
    items = [x.strip().lower() for x in (extras_csv or "").split(",") if x.strip()]
    for item in items:
        if item == "ai_heatmap":
            print("[Warning] Deprecated: 'ai_heatmap' is now 'heatmap'. Please update your config.", file=sys.stderr)
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

        if job.status in ("canceled", "canceling"):
            job.status = "canceled"
            job.finished_at = datetime.utcnow().isoformat()
            self.job_store.update_job(job)
            return

        # Update status to running
        job.status = "running"
        job.started_at = datetime.utcnow().isoformat()
        self.job_store.update_job(job)

        def log(msg: str):
            ts = datetime.utcnow().strftime("%H:%M:%S")
            line = f"[{ts}] {msg}"
            self.job_store.append_log_line(job.id, line)
            # Keep a small in-memory tail for API convenience (optional)
            job.logs.append(line)
            if len(job.logs) > 200:
                job.logs = job.logs[-200:]
            # Save job state less aggressively: only on status changes or every N lines
            # For simplicity, we update job here to keep 'logs' tail sync, but strictly we could skip it.
            # self.job_store.update_job(job)
            # To avoid excessive writes, we DON'T call update_job for every log line anymore.
            pass

        try:
            req = job.request

            # 1. Use resolved Hub from job
            if not job.hub_resolved:
                raise ValueError("Internal: hub_resolved missing on job")
            hub = Path(job.hub_resolved)
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
                if p.exists() and p.is_dir():
                    validate_source_dir(p)
                    sources.append(p)
                else:
                    log(f"Warning: Repo {name} not found at {p}")

            if not sources:
                raise ValueError("No valid repository sources found.")

            # 3. Scan Repos
            max_bytes = parse_human_size(req.max_bytes or "0")
            ext_list = _normalize_ext_list(",".join(req.extensions)) if req.extensions else None
            path_filter = req.path_filter
            include_paths = req.include_paths

            summaries = []
            total_sources = len(sources)
            for i, src in enumerate(sources, 1):
                # Refresh job status from store to detect external cancel
                current_job = self.job_store.get_job(job_id)
                if current_job and current_job.status in ("canceled", "canceling"):
                    log("Job canceled by user during scan.")
                    current_job.status = "canceled"
                    current_job.finished_at = datetime.utcnow().isoformat()
                    self.job_store.update_job(current_job)
                    return

                # Defense in depth: validate each src before scanning
                validate_source_dir(src)

                # Determine include_paths for this specific repo
                # Priority: include_paths_by_repo (if key exists) > include_paths (global)
                current_include_paths = include_paths
                if req.include_paths_by_repo is not None:
                    if src.name in req.include_paths_by_repo:
                        current_include_paths = req.include_paths_by_repo[src.name]
                    else:
                        # Critical: Missing key implies configuration drift.
                        # We must NOT fall back to global/full scan, as that risks exposing unintended data.

                        # Diagnostic: check if normalization would have helped (before failing)
                        norm_key = src.name.lower().strip("./").strip("/")
                        available_norm = [k.lower().strip("./").strip("/") for k in req.include_paths_by_repo.keys()]
                        if norm_key in available_norm:
                            log(f"INFO key would match after normalization (diagnostic only)")

                        err_msg = f"Strict Mode Violation: include_paths_by_repo is active but missing key for repo '{src.name}'. Available: {list(req.include_paths_by_repo.keys())}"
                        log(f"ERROR {err_msg}")
                        raise ValueError(err_msg)

                log(f"Scanning {i}/{total_sources}: {src.name} ...")
                # Note: scan_repo can be slow.
                summary = scan_repo(src, ext_list, path_filter, max_bytes, include_paths=current_include_paths)
                summaries.append(summary)

            # 4. Write Reports
            log("Generating reports...")
            if req.merges_dir:
                merges_dir = Path(req.merges_dir)
                merges_dir.mkdir(parents=True, exist_ok=True)
                # Ensure security/validation for custom merges_dir if needed
                # For now assuming if user can specify it, they have access.
            else:
                merges_dir = get_merges_dir(hub)

            # Re-check cancel status before write (expensive operation)
            job = self.job_store.get_job(job_id)
            if job.status in ("canceled", "canceling"):
                log("Job canceled by user before write.")
                job.status = "canceled"
                job.finished_at = datetime.utcnow().isoformat()
                self.job_store.update_job(job)
                return

            split_size = parse_human_size(req.split_size or "25MB")
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
