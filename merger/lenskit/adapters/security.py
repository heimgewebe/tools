from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os
import re

from fastapi import HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)

@dataclass
class SecurityConfig:
    # Absolute, normalized roots only. Anything else is rejected at registration.
    allowlist_roots: List[Path] = field(default_factory=list)
    token: str | None = None

    def set_token(self, token: Optional[str]):
        self.token = token

    def add_allowlist_root(self, path: Path) -> None:
        """
        Register a trusted root directory for filesystem access.
        This must NOT accept tainted/relative inputs, otherwise it can widen the jail.
        """
        s = str(path)
        if not s.strip():
            raise ValueError("Invalid root (empty)")
        if "\x00" in s:
            raise ValueError("Invalid root (NUL byte)")
        try:
            root = path.expanduser().resolve()
        except Exception:
            raise ValueError("Invalid root resolution")
        if not root.is_absolute():
            raise ValueError("Invalid root (not absolute)")
        if root not in self.allowlist_roots:
            self.allowlist_roots.append(root)

    def validate_path(self, path: Path) -> Path:
        """
        Central trust boundary for filesystem paths.
        Any user-influenced path must be normalized + constrained to allowlist_roots here,
        and callers must use ONLY the returned Path for filesystem operations.
        """
        s = str(path)
        if not s.strip():
            raise HTTPException(status_code=400, detail="Invalid path (empty)")
        if "\x00" in s:
            raise HTTPException(status_code=400, detail="Invalid path (NUL byte)")

        try:
            # normalize before checking roots (prevents traversal and oddities)
            resolved = path.expanduser().resolve()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid path resolution")

        if not resolved.is_absolute():
            raise HTTPException(status_code=400, detail="Invalid path (not absolute)")

        if not self.allowlist_roots:
            raise HTTPException(
                status_code=403,
                detail="No allowed roots configured (SecurityConfig not initialized)",
            )

        # Enforce containment within at least one root
        for root in self.allowlist_roots:
            try:
                # Optional drive guard (mostly relevant on Windows)
                if hasattr(root, "drive") and hasattr(resolved, "drive"):
                    if root.drive and resolved.drive and root.drive != resolved.drive:
                        continue
                resolved.relative_to(root)
                return resolved
            except ValueError:
                continue

        # Avoid leaking full filesystem layout in the error by default
        raise HTTPException(status_code=403, detail="Access denied: Path is not allowed")


_security_config = SecurityConfig()

def get_security_config() -> SecurityConfig:
    return _security_config


def verify_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    token: Optional[str] = Query(None)
):
    config = get_security_config()
    if not config.token:
        return

    if creds and creds.credentials == config.token:
        return

    if token and token == config.token:
        return

    raise HTTPException(status_code=401, detail="Missing or invalid authentication token")


def validate_hub_path(path_str: str) -> Path:
    """
    Validate a user-supplied hub path against the allowlist and ensure it exists/is a directory.
    Returns a canonical Path that is safe to use for filesystem operations.
    """
    if "\0" in path_str:
        raise HTTPException(status_code=400, detail="Invalid path (NUL byte)")

    p = Path(path_str)
    resolved = get_security_config().validate_path(p)
    # Also require a real directory
    if not resolved.exists():
        raise HTTPException(status_code=400, detail="Hub does not exist")
    if not resolved.is_dir():
        raise HTTPException(status_code=400, detail="Hub is not a directory")
    return resolved


def validate_source_dir(path: Path) -> Path:
    # Ensure source is within allowlist roots (hub) and use ONLY the validated path.
    resolved = get_security_config().validate_path(path)
    if not resolved.exists() or not resolved.is_dir():
        raise HTTPException(status_code=400, detail="Invalid repo path")
    return resolved

def validate_repo_name(name: str) -> str:
    _REPO_RE = re.compile(r"^[A-Za-z0-9._-]+$")
    n = (name or "").strip()
    if not n:
        raise HTTPException(status_code=400, detail="Invalid repo name: empty")
    if "/" in n or "\\" in n or ".." in n:
        raise HTTPException(status_code=400, detail="Invalid repo name")
    if not _REPO_RE.match(n):
        raise HTTPException(status_code=400, detail="Invalid repo name")
    return n

def resolve_any_path(root: Path, requested: Optional[str]) -> Path:
    if not requested or requested.strip() == "":
        return root.resolve()

    # If absolute, validate against roots
    if os.path.isabs(requested):
        return get_security_config().validate_path(Path(requested))

    # If relative, join and validate
    joined = root / requested
    return get_security_config().validate_path(joined)
