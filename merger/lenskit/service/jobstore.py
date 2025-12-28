import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
from .models import Job, Artifact

try:
    from ..core.merge import MERGES_DIR_NAME
except ImportError:
    from merger.lenskit.core.merge import MERGES_DIR_NAME

class JobStore:
    def __init__(self, hub_path: Path):
        self.hub_path = hub_path
        self.storage_dir = self.hub_path / MERGES_DIR_NAME / ".rlens-service"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_file = self.storage_dir / "jobs.json"
        self.artifacts_file = self.storage_dir / "artifacts.json"
        self.logs_dir = self.storage_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self._jobs_cache: Dict[str, Job] = {}
        self._artifacts_cache: Dict[str, Artifact] = {}

        self._load()

    def _load(self):
        with self._lock:
            if self.jobs_file.exists():
                try:
                    data = json.loads(self.jobs_file.read_text(encoding="utf-8"))
                    for j in data:
                        job = Job(**j)
                        self._jobs_cache[job.id] = job
                except Exception as e:
                    print(f"Error loading jobs: {e}")

            if self.artifacts_file.exists():
                try:
                    data = json.loads(self.artifacts_file.read_text(encoding="utf-8"))
                    for a in data:
                        art = Artifact(**a)
                        self._artifacts_cache[art.id] = art
                except Exception as e:
                    print(f"Error loading artifacts: {e}")

    def _save_jobs(self):
        # Must be called under lock
        tmp_file = self.jobs_file.with_suffix(".tmp")
        data = [j.model_dump() for j in self._jobs_cache.values()]
        tmp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp_file.rename(self.jobs_file)

    def _save_artifacts(self):
        # Must be called under lock
        tmp_file = self.artifacts_file.with_suffix(".tmp")
        data = [a.model_dump() for a in self._artifacts_cache.values()]
        tmp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp_file.rename(self.artifacts_file)

    def add_job(self, job: Job):
        with self._lock:
            self._jobs_cache[job.id] = job
            self._save_jobs()

    def update_job(self, job: Job):
        with self._lock:
            self._jobs_cache[job.id] = job
            self._save_jobs()

    def append_log_line(self, job_id: str, line: str):
        with self._lock:
            p = self.logs_dir / f"{job_id}.log"
            with p.open("a", encoding="utf-8", errors="replace") as f:
                f.write(line + "\n")

    def read_log_lines(self, job_id: str) -> List[str]:
        with self._lock:
            p = self.logs_dir / f"{job_id}.log"
            if not p.exists():
                return []
            return p.read_text(encoding="utf-8", errors="replace").splitlines()

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs_cache.get(job_id)

    def get_all_jobs(self) -> List[Job]:
        with self._lock:
            # Sort by created_at desc
            return sorted(self._jobs_cache.values(), key=lambda x: x.created_at, reverse=True)

    def find_job_by_hash(self, content_hash: str) -> Optional[Job]:
        with self._lock:
            candidates = [j for j in self._jobs_cache.values() if j.content_hash == content_hash]
            if not candidates:
                return None

            # Priority: running/queued/canceling > succeeded/failed/canceled
            # Within priority: newest created_at

            active = [j for j in candidates if j.status in ("queued", "running", "canceling")]
            if active:
                return sorted(active, key=lambda x: x.created_at, reverse=True)[0]

            return sorted(candidates, key=lambda x: x.created_at, reverse=True)[0]

    def cleanup_jobs(self, max_jobs: int = 100, max_age_hours: int = 24):
        now = datetime.utcnow()
        limit_time = now - timedelta(hours=max_age_hours)

        with self._lock:
            to_remove = set()
            all_jobs = sorted(self._jobs_cache.values(), key=lambda x: x.created_at, reverse=True)

            # 1. Age check
            for job in all_jobs:
                try:
                    dt = datetime.fromisoformat(job.created_at)
                    if dt < limit_time:
                        if job.status not in ("queued", "running", "canceling"):
                             to_remove.add(job.id)
                except Exception:
                    pass

            # 2. Count check
            remaining = [j for j in all_jobs if j.id not in to_remove]

            finished = [j for j in remaining if j.status not in ("queued", "running", "canceling")]
            active = [j for j in remaining if j.status in ("queued", "running", "canceling")]

            capacity = max(0, max_jobs - len(active))

            if len(finished) > capacity:
                for j in finished[capacity:]:
                    to_remove.add(j.id)

            if not to_remove:
                return

            for job_id in to_remove:
                if job_id in self._jobs_cache:
                    del self._jobs_cache[job_id]

                # remove log file
                log_p = self.logs_dir / f"{job_id}.log"
                if log_p.exists():
                    try:
                        log_p.unlink()
                    except Exception:
                        pass

            self._save_jobs()

    def add_artifact(self, artifact: Artifact):
        with self._lock:
            self._artifacts_cache[artifact.id] = artifact
            self._save_artifacts()

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        with self._lock:
            return self._artifacts_cache.get(artifact_id)

    def get_all_artifacts(self) -> List[Artifact]:
        with self._lock:
            return sorted(self._artifacts_cache.values(), key=lambda x: x.created_at, reverse=True)
