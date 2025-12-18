from typing import List, Optional, Literal, Dict
from pydantic import BaseModel
import uuid
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
    extras: Optional[str] = "health,augment_sidecar,organism_index,fleet_panorama,json_sidecar,heatmap"
    json_sidecar: bool = True  # Default true for service

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
    status: Literal["queued", "running", "succeeded", "failed", "canceled"]
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    request: JobRequest
    hub_resolved: Optional[str] = None
    logs: List[str] = []
    artifact_ids: List[str] = []
    error: Optional[str] = None

    @classmethod
    def create(cls, request: JobRequest) -> "Job":
        now = datetime.utcnow().isoformat()
        return cls(
            id=str(uuid.uuid4()),
            status="queued",
            created_at=now,
            request=request,
            logs=[],
            artifact_ids=[]
        )
