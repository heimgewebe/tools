from typing import Protocol, List
from pathlib import Path
from .jobstore import JobStore

class LogProvider(Protocol):
    def read_log_lines(self, job_id: str) -> List[str]:
        ...

class FileLogProvider:
    def __init__(self, job_store: JobStore):
        self.job_store = job_store

    def read_log_lines(self, job_id: str) -> List[str]:
        return self.job_store.read_log_lines(job_id)

class MockLogProvider:
    def __init__(self, logs_map: dict):
        self.logs_map = logs_map

    def read_log_lines(self, job_id: str) -> List[str]:
        return self.logs_map.get(job_id, [])
