import os
from pathlib import Path
from typing import Optional
import re
from fastapi import Header, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)

class SecurityConfig:
    token: Optional[str] = None
    allowlist_roots: list[Path] = []

    def set_token(self, token: Optional[str]):
        self.token = token

    def add_allowlist_root(self, path: Path):
        self.allowlist_roots.append(path.resolve())

    def validate_path(self, path: Path):
        resolved = path.resolve()
        # If no roots configured, allow nothing? Or allow everything?
        # Requirement: "Default allowlist: nur hub und Subdirs"
        if not self.allowlist_roots:
             # If no roots configured, default to deny for safety
             raise HTTPException(status_code=403, detail="No allowed roots configured (SecurityConfig not initialized)")

        is_allowed = False
        for root in self.allowlist_roots:
            # Check if path is inside root
            try:
                resolved.relative_to(root)
                is_allowed = True
                break
            except ValueError:
                continue

        if not is_allowed:
            raise HTTPException(status_code=403, detail=f"Path '{path}' is not allowed. Allowed roots: {[str(r) for r in self.allowlist_roots]}")

        return resolved

_security_config = SecurityConfig()

def get_security_config() -> SecurityConfig:
    return _security_config

def verify_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    token: Optional[str] = Query(None) # Allow query param for SSE
):
    config = get_security_config()
    if not config.token:
        return # Auth disabled

    # Check header first
    if creds and creds.credentials == config.token:
        return

    # Check query param (for SSE or simple links)
    if token and token == config.token:
        return

    raise HTTPException(status_code=401, detail="Missing or invalid authentication token")

def validate_hub_path(path_str: str):
    p = Path(path_str)
    get_security_config().validate_path(p)
    # Also require a real directory
    if not p.exists():
        raise HTTPException(status_code=400, detail=f"Hub does not exist: {path_str}")
    if not p.is_dir():
        raise HTTPException(status_code=400, detail=f"Hub is not a directory: {path_str}")
    return p

_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+$")

def validate_repo_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        raise HTTPException(status_code=400, detail="Invalid repo name: empty")
    if "/" in n or "\\" in n:
        raise HTTPException(status_code=400, detail="Invalid repo name: path separators not allowed")
    if ".." in n:
        raise HTTPException(status_code=400, detail="Invalid repo name: '..' not allowed")
    if not _REPO_RE.match(n):
        raise HTTPException(status_code=400, detail="Invalid repo name: only A-Za-z0-9._- allowed")
    return n

def validate_source_dir(path: Path) -> Path:
    # Ensure source is within allowlist roots (hub)
    get_security_config().validate_path(path)
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=400, detail=f"Invalid repo path: {path}")
    return path
