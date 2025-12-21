import json
import threading
from pathlib import Path
from typing import List, Optional, Dict
from .models import Job, Artifact

try:
    from lenskit.core.merge import MERGES_DIR_NAME
except ImportError:
    from ...core.merge import MERGES_DIR_NAME

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
