from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from .security import get_security_config

def list_allowed_roots(hub: Optional[Path], merges_dir: Optional[Path]) -> List[Dict[str, Any]]:
    sec = get_security_config()
    roots: List[Dict[str, Any]] = []
    # stable ids for clients/agents
    if hub:
        roots.append({"id": "hub", "path": str(hub.resolve())})
    if merges_dir:
        # Avoid duplicate if merges_dir is same as hub or inside?
        # For simplicity, just list it. Client can handle UI.
        roots.append({"id": "merges", "path": str(merges_dir.resolve())})
    # system root only if explicitly allowlisted
    try:
        sec.validate_path(Path("/"))
        roots.append({"id": "system", "path": "/"})
    except HTTPException:
        pass
    return roots

def resolve_fs_path(hub: Optional[Path], merges_dir: Optional[Path], root_id: str, rel_path: str) -> Path:
    """
    Resolve a filesystem request into an allowed absolute Path.
    Strictly uses (root_id + rel_path) to keep the security model explicit and scanner-friendly.
    """
    sec = get_security_config()

    if not root_id:
        raise HTTPException(status_code=400, detail="Missing root_id")

    # map root_id -> base path
    root_map: Dict[str, Optional[Path]] = {
        "hub": hub,
        "merges": merges_dir,
        "system": Path("/"),
    }

    base = root_map.get(root_id)
    if base is None:
        raise HTTPException(status_code=400, detail="Unknown root id")

    # ensure base itself is allowed (system only if allowlisted via env-gated init_service)
    # validate_path will raise 403 if not allowed
    base_resolved = sec.validate_path(base.resolve())

    rel = (rel_path or "").strip()
    if "\x00" in rel:
        raise HTTPException(status_code=400, detail="Invalid path request")

    # Root request for this base
    if rel in ("", ".", "/"):
        return base_resolved

    # Strict relative path only
    rel_p = Path(rel)
    if rel_p.is_absolute() or ".." in rel_p.parts:
        raise HTTPException(status_code=400, detail="Invalid path request (traversal or absolute)")

    # Bind under base and containment-check after normalization
    combined = (base_resolved / rel_p)
    resolved_path = combined.resolve()

    try:
        resolved_path.relative_to(base_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="Path escapes allowed root")

    # Final policy validation (allowlist roots, symlink policy, etc.)
    return sec.validate_path(resolved_path)
