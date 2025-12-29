
import pytest
import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock
from merger.lenskit.service.jobstore import JobStore
from merger.lenskit.service.models import Job, Artifact, JobRequest

@pytest.fixture
def job_store_env():
    temp_dir = tempfile.mkdtemp()
    hub_path = Path(temp_dir) / "hub"
    hub_path.mkdir()
    merges_dir = hub_path / "merges"
    merges_dir.mkdir()

    store = JobStore(hub_path)

    yield store, merges_dir, temp_dir

    shutil.rmtree(temp_dir)

def test_gc_deletes_real_artifacts(job_store_env):
    store, merges_dir, temp_dir = job_store_env

    # 1. Create a dummy physical file
    dummy_file = merges_dir / "dummy-artifact.md"
    dummy_file.write_text("content", encoding="utf-8")
    assert dummy_file.exists()

    # 2. Create Job and Artifact
    job_id = str(uuid.uuid4())
    req = JobRequest()
    job = Job.create(req)
    job.id = job_id
    job.status = "succeeded"
    store.add_job(job)

    art_id = str(uuid.uuid4())
    # Note: paths are relative to merges_dir usually
    # Artifact.paths values are just filenames usually.
    art = Artifact(
        id=art_id,
        job_id=job_id,
        hub=str(store.hub_path),
        repos=[],
        created_at=job.created_at,
        paths={"md": dummy_file.name},
        params=req
    )
    store.add_artifact(art)

    job.artifact_ids.append(art_id)
    store.update_job(job)

    # 3. Call remove_job
    store.remove_job(job_id)

    # 4. Assert Job gone
    assert store.get_job(job_id) is None

    # 5. Assert Artifact gone from DB
    assert store.get_artifact(art_id) is None

    # 6. Assert Physical File gone
    assert not dummy_file.exists()

def test_gc_safe_unlink(job_store_env):
    """Ensure GC doesn't delete files outside merges dir"""
    store, merges_dir, temp_dir = job_store_env

    # Create sensitive file outside merges
    sensitive_file = Path(temp_dir) / "sensitive.txt"
    sensitive_file.write_text("secret")

    # Create Job/Artifact pointing to it via traversal (should be caught)
    job_id = str(uuid.uuid4())
    req = JobRequest()
    job = Job.create(req)
    job.id = job_id
    store.add_job(job)

    art_id = str(uuid.uuid4())
    # Try to traverse up
    rel_path = f"../{sensitive_file.name}"

    art = Artifact(
        id=art_id,
        job_id=job_id,
        hub=str(store.hub_path),
        repos=[],
        created_at=job.created_at,
        paths={"secret": rel_path},
        params=req
    )
    store.add_artifact(art)
    job.artifact_ids.append(art_id)
    store.update_job(job)

    store.remove_job(job_id)

    # Verify sensitive file still exists
    assert sensitive_file.exists()
    assert sensitive_file.read_text() == "secret"
