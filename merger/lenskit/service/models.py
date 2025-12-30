from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel
import uuid
import hashlib
import json
from datetime import datetime

class JobRequest(BaseModel):
    hub: Optional[str] = None
    merges_dir: Optional[str] = None # Output directory override
    repos: Optional[List[str]] = None  # None/empty = all
    level: Literal["overview", "summary", "dev", "max"] = "dev"
    mode: Literal["gesamt", "pro-repo"] = "gesamt"
    max_bytes: Optional[str] = "0"  # human size string or "0"
    split_size: Optional[str] = "25MB"
    plan_only: bool = False
    code_only: bool = False
    extensions: Optional[List[str]] = None
    path_filter: Optional[str] = None
    # Default: Minimal (Agent-fokussiert). Nur Sidecars.
    # Aligning with repolens.py logic to prevent drift.
    extras: Optional[str] = "json_sidecar,augment_sidecar"
    json_sidecar: bool = True  # Default true for service
    force_new: bool = False

class AtlasRequest(BaseModel):
    # Canonical: token from FS picker (opaque, HMAC-signed by server).
    # This avoids user-controlled path expressions and satisfies CodeQL.
    root_token: Optional[str] = None

    # Transitional: allow selecting a known root id ("hub" | "merges" | "system").
    # NOTE: Do NOT accept arbitrary paths here; use root_token instead.
    root_id: Optional[str] = None

    root: Optional[str] = None  # Deprecated.
    max_depth: int = 6
    max_entries: int = 200000
    exclude_globs: Optional[List[str]] = None
    sample_files: bool = False

class AtlasArtifact(BaseModel):
    id: str
    created_at: str
    hub: str
    root_scanned: str
    paths: Dict[str, str] # {"json": "...", "md": "..."}
    stats: Dict[str, Any] # Summary stats

class Artifact(BaseModel):
    id: str
    job_id: str
    hub: str
    repos: List[str]
    created_at: str
    paths: Dict[str, str]  # e.g. {"md": "...", "json": "...", "part2": "..."}
    params: JobRequest

class Job(BaseModel):
    id: str
    # 'canceling' = user requested cancel, runner hasn't stopped yet
    # 'canceled' = final state
    status: Literal["queued", "running", "succeeded", "failed", "canceling", "canceled"]
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    request: JobRequest
    hub_resolved: Optional[str] = None
    # content_hash is deprecated, aliased to job_key for backward compatibility
    content_hash: Optional[str] = None
    job_key: Optional[str] = None
    logs: List[str] = []
    artifact_ids: List[str] = []
    error: Optional[str] = None

    @classmethod
    def create(cls, request: JobRequest, content_hash: Optional[str] = None, job_key: Optional[str] = None) -> "Job":
        now = datetime.utcnow().isoformat()
        return cls(
            id=str(uuid.uuid4()),
            status="queued",
            created_at=now,
            request=request,
            content_hash=content_hash,
            job_key=job_key,
            logs=[],
            artifact_ids=[]
        )
