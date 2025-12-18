import os
from pathlib import Path
from typing import Optional
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
             # Fallback if no roots added yet (should be added at init)
             return

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
    return p
