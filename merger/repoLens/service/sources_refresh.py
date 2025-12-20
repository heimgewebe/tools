import json
import logging
import subprocess
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "fleet.snapshot.v1"
TTL_HOURS = 24

def _get_commit(repo_path: Path) -> str:
    """Get current git commit hash of the repo."""
    if not (repo_path / ".git").exists():
        return "unknown"
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_path, text=True
        ).strip()
    except Exception:
        return "unknown"

def _parse_repo_matrix(md_path: Path) -> Dict[str, Any]:
    """
    Parses repo-matrix.md to extract fleet roles and expectations.
    Expected Markdown Table columns: Repo | Role | WGX Profile Expected | ...
    """
    if not md_path.exists():
        raise FileNotFoundError(f"{md_path} not found")

    content = md_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    data = {}

    in_table = False
    col_map = {} # name -> index

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue

        # Parse pipes: | A | B | -> ['', 'A', 'B', '']
        parts = [p.strip() for p in line.split("|")]
        # Remove empty start/end if they exist (common in MD tables)
        if len(parts) > 1 and parts[0] == "":
            parts.pop(0)
        if len(parts) > 0 and parts[-1] == "":
            parts.pop(-1)

        if not in_table:
            # Check if header
            lower_parts = [p.lower() for p in parts]
            if "repo" in lower_parts or "repository" in lower_parts:
                in_table = True
                # Map headers
                for i, h in enumerate(lower_parts):
                    if "repo" in h: col_map["repo"] = i
                    elif "role" in h or "rolle" in h: col_map["role"] = i
                    elif "wgx" in h or "profile" in h: col_map["wgx"] = i
                continue
        else:
            if "---" in line:
                continue

            repo_idx = col_map.get("repo")
            if repo_idx is not None and repo_idx < len(parts):
                repo_name = parts[repo_idx]

                # Extract clean name (remove links if any: [name](...))
                m = re.match(r"\[(.*?)\]", repo_name)
                if m:
                    repo_name = m.group(1)

                # Skip if empty
                if not repo_name:
                    continue

                entry = {"repo": repo_name}

                # Role
                role_idx = col_map.get("role")
                if role_idx is not None and role_idx < len(parts):
                    entry["role"] = parts[role_idx]
                else:
                    entry["role"] = "unknown"

                # WGX Expected
                wgx_idx = col_map.get("wgx")
                if wgx_idx is not None and wgx_idx < len(parts):
                    val = parts[wgx_idx].lower()
                    if val in ("yes", "ja", "true", "required", "y", "1"):
                        entry["profile_expected"] = True
                    elif val in ("no", "nein", "false", "optional", "n", "0", "-"):
                        entry["profile_expected"] = False
                    else:
                        entry["profile_expected"] = None # unknown
                else:
                    # Default if column missing? Or unknown?
                    entry["profile_expected"] = None

                data[repo_name] = entry

    return data

def _normalize_repo_entry(raw: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Normalize a single repo entry from metarepo/fleet/repos.yml into the canonical snapshot shape.
    Supports:
      - new nested keys: wgx: { profile_expected: bool|null }
      - legacy dot key:  "wgx.profile_expected": bool|null
    """
    repo = raw.get("repo") or raw.get("name")
    if not repo:
        raise ValueError("fleet entry missing repo/name")

    wgx_obj = raw.get("wgx") if isinstance(raw.get("wgx"), dict) else {}
    if "profile_expected" not in wgx_obj and "wgx.profile_expected" in raw:
        wgx_obj = { **wgx_obj, "profile_expected": raw.get("wgx.profile_expected") }

    norm = {
        "repo": repo,
        "fleet_member": bool(raw.get("fleet_member")) if raw.get("fleet_member") is not None else None,
        "role": raw.get("role", "unknown"),
        "policy_tier": raw.get("policy_tier", "standard"),
        "wgx": {
            "profile_expected": wgx_obj.get("profile_expected", None)
        }
    }
    # Fix: omit null fields to satisfy schema
    if norm["fleet_member"] is None:
        del norm["fleet_member"]
    return repo, norm

def refresh(hub_path: Path):
    """
    Reads Metarepo sources and updates snapshots in .gewebe/cache/.
    """
    gewebe_dir = hub_path / ".gewebe"
    cache_dir = gewebe_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    metarepo_path = hub_path / "metarepo"

    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # 1. Fleet Snapshot
    fleet_out = cache_dir / "fleet.snapshot.json"
    repo_matrix = metarepo_path / "docs" / "repo-matrix.md"

    # Prepare base objects
    metarepo_commit = _get_commit(metarepo_path)

    # P1: Check for repos.yml first
    repos_yml = metarepo_path / "fleet" / "repos.yml"

    fleet_snapshot = None

    if repos_yml.exists() and yaml is not None:
        try:
            raw_data = yaml.safe_load(repos_yml.read_text(encoding="utf-8"))
            data: Dict[str, Any] = {}
            if isinstance(raw_data, list):
                for item in raw_data:
                    if not isinstance(item, dict):
                        continue
                    repo, norm = _normalize_repo_entry(item)
                    data[repo] = norm
            elif isinstance(raw_data, dict):
                # Accept dict-of-dicts, normalize values
                for k, v in raw_data.items():
                    if not isinstance(v, dict):
                        continue
                    # allow key to be repo name if missing inside
                    v2 = dict(v)
                    v2.setdefault("repo", k)
                    repo, norm = _normalize_repo_entry(v2)
                    data[repo] = norm

            fleet_snapshot = {
                "schema_version": SCHEMA_VERSION,
                "status": "ok",
                "generated_at": ts,
                "validity": { "ttl_hours": TTL_HOURS, "outdated": False },
                "sources": {
                    "metarepo": {"path": str(repos_yml.relative_to(hub_path)), "commit": metarepo_commit}
                },
                "data": {"repos": data}
            }
        except Exception as e:
            logger.warning(f"Failed to parse repos.yml: {e}")
            # Fallback to MD if YAML fails
            pass

    # Fallback to repo-matrix.md if YAML not used/failed
    if not fleet_snapshot:
        if not repo_matrix.exists():
            fleet_snapshot = {
                "schema_version": SCHEMA_VERSION,
                "status": "error",
                "generated_at": ts,
                "validity": { "ttl_hours": TTL_HOURS, "outdated": False },
                "sources": {
                    "metarepo": {"path": str(repo_matrix.relative_to(hub_path)) if repo_matrix.is_relative_to(hub_path) else "metarepo/docs/repo-matrix.md", "commit": metarepo_commit}
                },
                "data": {},
                "error": "Source file docs/repo-matrix.md not found in metarepo"
            }
        else:
            try:
                data = _parse_repo_matrix(repo_matrix)
                # MD fallback yields profile_expected at top-level; normalize to nested
                normed = {}
                for repo, entry in data.items():
                    # Fix: omit null fields to satisfy schema
                    # fleet_member is unknown in MD fallback, so we omit it.
                    normed[repo] = {
                        "repo": repo,
                        "role": entry.get("role", "unknown"),
                        "policy_tier": "standard",
                        "wgx": { "profile_expected": entry.get("profile_expected", None) }
                    }
                fleet_snapshot = {
                    "schema_version": SCHEMA_VERSION,
                    "status": "ok",
                    "generated_at": ts,
                    "validity": { "ttl_hours": TTL_HOURS, "outdated": False },
                    "sources": {
                        "metarepo": {"path": str(repo_matrix.relative_to(hub_path)), "commit": metarepo_commit}
                    },
                    "data": {"repos": normed}
                }
            except Exception as e:
                logger.exception("Failed to parse repo-matrix.md")
                fleet_snapshot = {
                    "schema_version": SCHEMA_VERSION,
                    "status": "error",
                    "generated_at": ts,
                    "validity": { "ttl_hours": TTL_HOURS, "outdated": False },
                    "sources": {
                        "metarepo": {"path": str(repo_matrix.relative_to(hub_path)), "commit": metarepo_commit}
                    },
                    "data": {},
                    "error": str(e)
                }

    with open(fleet_out, "w", encoding="utf-8") as f:
        json.dump(fleet_snapshot, f, indent=2)

    # 2. Organism Index Snapshot
    # Heuristic: check for docs/organism-index.md or similar.
    # Since not explicitly defined, we check exact file.
    # If missing, we report error as requested "sonst status=error".

    org_index_out = cache_dir / "organism.index.snapshot.json"
    org_source = metarepo_path / "docs" / "organism-index.md"

    if org_source.exists():
         # Placeholder parsing for now
         org_snapshot = {
            "status": "ok",
            "generated_at": ts,
             "sources": {
                "metarepo": {"path": str(org_source.relative_to(hub_path)), "commit": metarepo_commit}
            },
            "data": {"available": True}
         }
    else:
         org_snapshot = {
            "status": "error",
            "generated_at": ts,
             "sources": {
                "metarepo": {"path": "metarepo/docs/organism-index.md", "commit": metarepo_commit}
            },
            "data": {},
            "error": "Source file docs/organism-index.md not found in metarepo"
         }

    with open(org_index_out, "w", encoding="utf-8") as f:
        json.dump(org_snapshot, f, indent=2)

    return {
        "status": "ok",
        "snapshots": {
            "fleet": fleet_snapshot.get("status"),
            "organism_index": org_snapshot.get("status")
        }
    }
