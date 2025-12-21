import os
from pathlib import Path

def resolve_secure_path(root: Path, relpath: str) -> Path:
    """
    Safely join root and relpath, ensuring the result is within root.
    Raises ValueError if path traversal or other violations detected.

    Strict rules:
    - No absolute paths
    - No null bytes
    - No '..' segments (naive check)
    - Must verify containment after resolve
    """
    if not isinstance(relpath, str):
        raise ValueError("relpath must be a string")

    # 1. explicit check for absolute path or null byte
    if os.path.isabs(relpath) or "\0" in relpath:
        raise ValueError("Absolute paths and null bytes are forbidden")

    # 2. Check for ".." in parts (naive string check first for speed/safety)
    if ".." in relpath.split("/"):
        raise ValueError("Directory traversal ('..') is forbidden")

    try:
        # Resolve root to have a canonical base
        root_abs = root.resolve()

        # Join
        candidate = root_abs / relpath

        # Resolve candidate
        resolved = candidate.resolve()

        # Final containment check
        # Python < 3.9 compat: use relative_to inside try/except
        resolved.relative_to(root_abs)

        return resolved
    except (ValueError, RuntimeError, OSError) as e:
        raise ValueError(f"Path resolution failed or outside root: {e}")
