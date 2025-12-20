import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

def rebuild(hub_path: Path) -> Dict[str, Any]:
    """
    Rebuilds diagnostics snapshot based on fleet.snapshot.json expectations.
    """
    gewebe_dir = hub_path / ".gewebe"
    cache_dir = gewebe_dir / "cache"
    # Ensure cache dir exists
    cache_dir.mkdir(parents=True, exist_ok=True)

    fleet_snap_path = cache_dir / "fleet.snapshot.json"
    diag_out_path = cache_dir / "diagnostics.snapshot.json"

    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # 1. Load Fleet Snapshot
    if not fleet_snap_path.exists():
        diag = {
            "status": "error",
            "generated_at": ts,
            "data": {},
            "error": "fleet.snapshot.json missing"
        }
        with open(diag_out_path, "w", encoding="utf-8") as f:
            json.dump(diag, f, indent=2)
        return {"status": "error", "message": "Fleet snapshot missing"}

    try:
        fleet_data = json.loads(fleet_snap_path.read_text(encoding="utf-8"))
    except Exception as e:
        diag = {
            "status": "error",
            "generated_at": ts,
            "data": {},
            "error": f"Invalid fleet snapshot: {e}"
        }
        with open(diag_out_path, "w", encoding="utf-8") as f:
            json.dump(diag, f, indent=2)
        return {"status": "error", "message": f"Invalid fleet snapshot: {e}"}

    if fleet_data.get("status") != "ok":
         diag = {
            "status": "error",
            "generated_at": ts,
            "data": {},
            "error": "Fleet snapshot is in error state"
        }
         with open(diag_out_path, "w", encoding="utf-8") as f:
            json.dump(diag, f, indent=2)
         return {"status": "error", "message": "Fleet snapshot is in error state"}

    repos = fleet_data.get("data", {}).get("repos", {})
    results = {}

    # 2. Iterate Fleet Repos and check local state
    for repo_name, meta in repos.items():
        repo_path = hub_path / repo_name

        # Check existence
        if not repo_path.is_dir():
            results[repo_name] = {
                "status": "missing",
                "checks": []
            }
            continue

        checks = []

        # Profile Expectation
        # "prüft lokal ... .wgx/profile.yml vorhanden, wenn snapshot sagt: profile_expected=true"
        expected = meta.get("profile_expected")
        if expected is True:
            profile_path = repo_path / ".wgx" / "profile.yml"
            if not profile_path.exists():
                checks.append({
                    "code": "missing_wgx_profile",
                    "severity": "warn",
                    "message": ".wgx/profile.yml expected but missing"
                })

        results[repo_name] = {
            "status": "ok" if not checks else "issue",
            "checks": checks,
            # Pass through role for convenience
            "role": meta.get("role", "unknown")
        }

    diag = {
        "status": "ok",
        "generated_at": ts,
        "source_snapshot_ts": fleet_data.get("generated_at"),
        "data": results
    }

    with open(diag_out_path, "w", encoding="utf-8") as f:
        json.dump(diag, f, indent=2)

    return {"status": "ok", "issues": sum(1 for r in results.values() if r["status"] == "issue")}
