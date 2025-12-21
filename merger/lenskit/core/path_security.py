import os
from pathlib import Path

def resolve_secure_path(root: Path, relpath: str) -> Path:
    if not isinstance(relpath, str):
        raise ValueError("relpath must be a string")
    if os.path.isabs(relpath) or "\0" in relpath:
        raise ValueError("Absolute paths and null bytes are forbidden")
    if ".." in relpath.split("/"):
        raise ValueError("Directory traversal ('..') is forbidden")
    try:
        root_abs = root.resolve()
        candidate = root_abs / relpath
        resolved = candidate.resolve()
        resolved.relative_to(root_abs)
        return resolved
    except (ValueError, RuntimeError, OSError) as e:
        raise ValueError(f"Path resolution failed: {e}")
