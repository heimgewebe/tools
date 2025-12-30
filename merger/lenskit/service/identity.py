import json
import hashlib
from .models import JobRequest

def compute_job_key(req: JobRequest, hub_resolved: str, version: str) -> str:
    """
    Computes a canonical job key (hash) for idempotency.
    Wraps/Replaces calculate_job_hash with stricter canonicalization if needed,
    but currently reuses the logic to ensure consistency.
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

    # Construct signature dict
    sig = {
        "lenskit_version": version,
        "hub": hub_resolved,
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
        "json_sidecar": req.json_sidecar
    }

    # Serialize and hash
    sig_str = json.dumps(sig, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(sig_str.encode("utf-8")).hexdigest()
