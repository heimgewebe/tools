
import pytest
import uuid
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from merger.lenskit.service.app import app, init_service, state
from merger.lenskit.service.models import JobRequest
from merger.lenskit.service.jobstore import JobStore
from merger.lenskit.service.runner import JobRunner
from fastapi.testclient import TestClient

@pytest.fixture
def test_env():
    # Setup temporary hub and merges dir
    temp_dir = tempfile.mkdtemp()
    hub_path = Path(temp_dir) / "hub"
    hub_path.mkdir()
    merges_dir = hub_path / "merges"
    merges_dir.mkdir()

    # Create dummy repo
    (hub_path / "repo1").mkdir()
    (hub_path / "repo1" / "file1.txt").write_text("content1")

    # Init service
    init_service(hub_path, merges_dir=merges_dir)

    # Mock runner submit to avoid actual thread execution if desired,
    # but for full integration we might want it.
    # For this test we just check job creation logic (IDs), so runner execution is secondary.
    # However, runner needs to 'succeed' the job for reuse test.

    # We'll use a real runner but maybe we don't need to wait for it
    # if we manually manipulate state for the test setup?
    # Let's mock runner.submit_job to do nothing, and manually set job status for testing reuse.

    original_submit = state.runner.submit_job
    state.runner.submit_job = MagicMock()

    yield

    # Teardown
    state.runner.submit_job = original_submit
    shutil.rmtree(temp_dir)

def test_explicit_reuse_policy(test_env):
    client = TestClient(app)

    # 1. Create initial job
    req_payload = {
        "repos": ["repo1"],
        "level": "overview",
        "plan_only": True
    }
    resp1 = client.post("/api/jobs", json=req_payload)
    assert resp1.status_code == 200
    job1 = resp1.json()
    job1_id = job1["id"]

    # Mark job1 as succeeded in store so it becomes candidate for reuse
    job1_obj = state.job_store.get_job(job1_id)
    job1_obj.status = "succeeded"
    state.job_store.update_job(job1_obj)

    # 2. Create identical job (expect reuse by default)
    resp2 = client.post("/api/jobs", json=req_payload)
    assert resp2.status_code == 200
    job2 = resp2.json()
    assert job2["id"] == job1_id

    # 3. Create identical job with force_new=True (expect NEW job)
    req_payload_forced = req_payload.copy()
    req_payload_forced["force_new"] = True

    resp3 = client.post("/api/jobs", json=req_payload_forced)
    assert resp3.status_code == 200
    job3 = resp3.json()

    assert job3["id"] != job1_id

    # Verify job3 is actually in store
    assert state.job_store.get_job(job3["id"]) is not None

def test_force_new_ignored_if_no_existing(test_env):
    client = TestClient(app)

    # Create job with force_new=True but no prior job exists
    req_payload = {
        "repos": ["repo1"],
        "level": "max", # different param to ensure no collision with previous test
        "plan_only": True,
        "force_new": True
    }
    resp = client.post("/api/jobs", json=req_payload)
    assert resp.status_code == 200
    job = resp.json()
    assert state.job_store.get_job(job["id"]) is not None
