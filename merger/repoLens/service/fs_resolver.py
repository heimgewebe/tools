from pathlib import Path
from typing import Optional, List
from fastapi import HTTPException
from .security import get_security_config

def resolve_fs_path(raw: str, hub: Optional[Path], merges_dir: Optional[Path]) -> Path:
    """
    Resolve `raw` to an absolute path and ensure it stays within allowed roots.
    Allowed roots: hub (if set), merges_dir (if set), and any roots in SecurityConfig.
    If `raw` is relative and hub exists, it is resolved relative to hub for backward compatibility.
    """
    raw = (raw or "").strip()
    if "\x00" in raw:
        raise HTTPException(status_code=400, detail="Invalid path request")

    # Add Hub and Merges Dir if available
    roots: List[Path] = []
    if hub:
        roots.append(hub.resolve())
    if merges_dir:
        roots.append(merges_dir.resolve())

    # Add SecurityConfig allowed roots (which might include system root /)
    sec_config = get_security_config()

    if raw in ("", "/"):
        # Special case: root request
        # If "/" is allowed (system root allowed), return "/"
        system_root = Path("/").resolve()
        try:
            sec_config.validate_path(system_root)
            return system_root
        except HTTPException:
            pass # / not allowed

        # Fallback logic: prefer Hub
        if hub: return hub.resolve()

        # Fallback to first allowed root if available
        if sec_config.allowlist_roots:
            return sec_config.allowlist_roots[0]

        raise HTTPException(status_code=400, detail="No allowed roots configured")

    p = Path(raw)

    # Helper: resolve safely by binding to a known root
    def _bind_under_root(root: Path, rel: Path) -> Path:
        # reject traversal in rel explicitly
        if rel.is_absolute() or ".." in rel.parts:
            raise HTTPException(status_code=400, detail="Invalid path request")
        return (root / rel).resolve()

    # Absolute path: delegate validation to SecurityConfig
    if p.is_absolute():
        return sec_config.validate_path(p)
    else:
        # Relative: resolve within hub (legacy default) or fail if no Hub
        if hub:
            candidate = _bind_under_root(hub.resolve(), p)
            # Final check: ensure the resolved path is actually allowed
            # (e.g., if hub itself is not in allowed roots, which shouldn't happen but good for safety)
            return sec_config.validate_path(candidate)
        else:
            raise HTTPException(status_code=400, detail="Relative path requires Hub configuration")
