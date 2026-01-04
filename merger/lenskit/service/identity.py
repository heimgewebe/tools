from __future__ import annotations
from typing import TYPE_CHECKING
import hashlib
import json

if TYPE_CHECKING:
    from .models import JobRequest

def compute_job_key(req: "JobRequest", hub_resolved: str, version: str) -> str:
    """
    Calculates a deterministic hash for the job parameters to ensure idempotency.
    Identity Canon: This is the Single Source of Truth for Job Identity.
    """
    # Normalize extras
    extras_list = sorted([x.strip().lower() for x in (req.extras or "").split(",") if x.strip()])
    extras_str = ",".join(extras_list)

    # Normalize path_filter (None vs "")
    path_filter = req.path_filter.strip() if isinstance(req.path_filter, str) else None
    if path_filter == "":
        path_filter = None

    # Normalize repos
    repos_list = sorted(req.repos) if req.repos else ["__ALL__"]

    # Normalize extensions
    ext_list = sorted(req.extensions) if req.extensions else []

    # Normalize include_paths (Tri-State Semantics)
    # None = All (no whitelist)
    # [] = None (empty whitelist -> include nothing except forced)
    # ["."] / [""] = All (normalized to None)

    inc_paths = None
    if req.include_paths is not None:
        # Check for explicit "all" markers (match scan_repo logic)
        if any(p in (".", "") for p in req.include_paths):
            inc_paths = None
        else:
            inc_paths = sorted(req.include_paths)

    # Construct signature dict
    sig = {
        "lenskit_version": version,
        "hub": hub_resolved, # Use resolved hub path!
        "repos": repos_list,
        "level": req.level,
        "mode": req.mode,
        "max_bytes": req.max_bytes,
        "split_size": req.split_size,
        "plan_only": req.plan_only,
        "code_only": req.code_only,
        "extensions": ext_list,
        "path_filter": path_filter,
        "extras": extras_str,
        "json_sidecar": req.json_sidecar,
        "include_paths": inc_paths
        # Merges dir excluded from content hash:
        # Same content, different output path = same logical job.
    }

    # Serialize and hash
    sig_str = json.dumps(sig, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(sig_str.encode("utf-8")).hexdigest()
