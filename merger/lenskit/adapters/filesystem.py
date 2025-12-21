from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException
from dataclasses import dataclass
from .security import get_security_config, resolve_any_path
import os
import time
import json
import base64
import hmac
import hashlib

@dataclass(frozen=True)
class TrustedPath:
    """
    Marker type: Path has been validated by SecurityConfig.validate_path.
    Use this to make the trust boundary explicit and to reduce CodeQL taint noise.
    """
    path: Path

def list_allowed_roots(hub: Optional[Path], merges_dir: Optional[Path]) -> List[Dict[str, Any]]:
    sec = get_security_config()
    roots: List[Dict[str, Any]] = []
    # stable ids for clients/agents
    if hub:
        roots.append({"id": "hub", "path": str(hub.resolve())})
    if merges_dir:
        roots.append({"id": "merges", "path": str(merges_dir.resolve())})
    # system root only if explicitly allowlisted
    try:
        sec.validate_path(Path("/"))
        roots.append({"id": "system", "path": "/"})
    except HTTPException:
        pass
    return roots

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))

def _token_secret() -> bytes:
    # Explicit secret; if missing, fall back to RLENS_TOKEN for local setups.
    # (This is NOT a legacy alias; it's the same token material already required to call the API.)
    s = os.getenv("RLENS_FS_TOKEN_SECRET") or os.getenv("RLENS_TOKEN") or ""
    if not s:
        # Fallback for dev/test if no token set? No, secure by default.
        # But for tests we might need to mock this.
        # If no token is set, we can't sign.
        raise HTTPException(status_code=500, detail="FS token secret not configured")
    return s.encode("utf-8")

def issue_fs_token(abs_path: Path, ttl_seconds: int = 1200) -> str:
    """
    Create an HMAC-signed token that encodes an absolute path.
    The server will re-validate the decoded path against SecurityConfig at use-time.
    """
    payload = {
        "p": str(abs_path),
        "exp": int(time.time()) + int(ttl_seconds),
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(_token_secret(), body, hashlib.sha256).digest()
    return f"{_b64url(body)}.{_b64url(sig)}"

def _parse_fs_token(token: str) -> Tuple[Path, int]:
    try:
        body_b64, sig_b64 = token.split(".", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")

    body = _b64url_decode(body_b64)
    sig = _b64url_decode(sig_b64)
    expected = hmac.new(_token_secret(), body, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=403, detail="Invalid token signature")

    try:
        payload = json.loads(body.decode("utf-8"))
        p = Path(payload["p"])
        exp = int(payload["exp"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    if int(time.time()) > exp:
        raise HTTPException(status_code=403, detail="Token expired")

    if "\x00" in str(p):
        raise HTTPException(status_code=400, detail="Invalid path request")

    return p, exp

def resolve_fs_token(token: str) -> Path:
    """
    Resolve a token to an allowed absolute path.
    IMPORTANT: final authority is SecurityConfig.validate_path.
    """
    sec = get_security_config()
    p, _exp = _parse_fs_token(token)
    # validate_path must enforce allowlisted roots (hub/merges/system opt-in)
    return sec.validate_path(p)

def resolve_fs_path(hub: Optional[Path], merges_dir: Optional[Path], root_id: Optional[str] = None, rel_path: Optional[str] = None, token: Optional[str] = None) -> TrustedPath:
    """
    Resolve a filesystem request into an allowed absolute Path.
    Canonical mode: token-based navigation (no user path segments).
    Transitional mode: root_id+rel_path (base only).
    """
    sec = get_security_config()

    # Canonical: token
    if token is not None:
        return TrustedPath(resolve_fs_token(token))

    # Preferred protocol: root_id + rel_path (Legacy/Transitional)
    if root_id is not None:
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
        base_resolved = sec.validate_path(base.resolve())

        # Instead of joining user rel_path here (CodeQL magnet),
        # we issue/expect tokens for navigation. Keep root_id+rel_path only for UI migration.
        # Minimal behavior: treat empty rel as base.
        rel = (rel_path or "").strip()
        if rel in ("", ".", "/"):
            return TrustedPath(base_resolved)

        # Subpaths require token navigation for security.
        # Legacy absolute path resolution logic (if any) should use resolve_any_path in explicit callers.
        raise HTTPException(status_code=400, detail="Use token navigation for subpaths")

    # If neither token nor root_id is provided, reject (strict).
    raise HTTPException(status_code=400, detail="Invalid fs request")
