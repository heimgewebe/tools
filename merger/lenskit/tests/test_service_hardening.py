import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import time
from merger.lenskit.service.app import app, init_service, state
from merger.lenskit.service.models import JobRequest, Job, Artifact
from datetime import datetime
import uuid

@pytest.fixture
def client_and_hub():
    with tempfile.TemporaryDirectory() as tmp:
        hub = Path(tmp) / "hub"
        hub.mkdir()
        init_service(hub, token="test-token")

        # Mock runner to avoid real execution
        original_submit = state.runner.submit_job
        state.runner.submit_job = lambda jid: None # Do nothing

        with TestClient(app) as c:
            yield c, str(hub.resolve())

        state.runner.submit_job = original_submit

def test_idempotency_and_decoupling(client_and_hub):
    client, hub_path = client_and_hub
    req = {
        "hub": hub_path,
        "repos": ["repo1"],
        "level": "max"
    }
    headers = {"Authorization": "Bearer test-token"}

    # First create
    resp1 = client.post("/api/jobs", json=req, headers=headers)
    assert resp1.status_code == 200, resp1.text
    job1 = resp1.json()

    # Different output dir -> Should be SAME job (hash decoupling)
    req["merges_dir"] = "/tmp/out_different"
    resp2 = client.post("/api/jobs", json=req, headers=headers)
    assert resp2.status_code == 200
    job2 = resp2.json()

    assert job1["id"] == job2["id"], "Hash should ignore merges_dir"

def test_cancel_flow(client_and_hub):
    client, hub_path = client_and_hub
    req = {
        "hub": hub_path,
        "repos": ["repo2"],
        "level": "max"
    }
    headers = {"Authorization": "Bearer test-token"}

    resp = client.post("/api/jobs", json=req, headers=headers)
    assert resp.status_code == 200, resp.text
    job_id = resp.json()["id"]

    # Cancel running
    resp_cancel = client.post(f"/api/jobs/{job_id}/cancel", headers=headers)
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["status"] == "canceling"

    # Force finish
    job = state.job_store.get_job(job_id)
    job.status = "succeeded"
    state.job_store.update_job(job)

    # Cancel finished
    resp_cancel_fin = client.post(f"/api/jobs/{job_id}/cancel", headers=headers)
    assert resp_cancel_fin.status_code == 200
    assert resp_cancel_fin.json()["status"] == "succeeded"
    assert resp_cancel_fin.json().get("message") == "Job already finished"

def test_log_resume(client_and_hub):
    client, hub_path = client_and_hub
    req = {"hub": hub_path, "repos": ["repo3"]}
    headers = {"Authorization": "Bearer test-token"}
    resp = client.post("/api/jobs", json=req, headers=headers)
    job_id = resp.json()["id"]

    state.job_store.append_log_line(job_id, "Line 1")
    state.job_store.append_log_line(job_id, "Line 2")

    # Mark job as finished so stream stops
    job = state.job_store.get_job(job_id)
    job.status = "succeeded"
    state.job_store.update_job(job)

    # Delete log file manually (simulate GC race)
    log_p = state.job_store.logs_dir / f"{job_id}.log"
    log_p.unlink()

    # Stream should just return empty/close, not 500
    resp_stream = client.get(f"/api/jobs/{job_id}/logs", headers=headers)
    assert resp_stream.status_code == 200

def test_gc_artifacts(client_and_hub):
    client, hub_path = client_and_hub
    req = {"hub": hub_path, "repos": ["repo1"]}
    headers = {"Authorization": "Bearer test-token"}
    resp = client.post("/api/jobs", json=req, headers=headers)
    job_id = resp.json()["id"]

    # Manually add artifact
    art_id = str(uuid.uuid4())
    req_obj = JobRequest(**req)
    art = Artifact(
        id=art_id, job_id=job_id, hub=hub_path, repos=["repo1"],
        created_at=datetime.utcnow().isoformat(), paths={}, params=req_obj
    )
    state.job_store.add_artifact(art)

    # Associate
    job = state.job_store.get_job(job_id)
    job.artifact_ids.append(art_id)
    state.job_store.update_job(job)

    # Remove
    state.job_store.remove_job(job_id)

    # Check consistency
    assert state.job_store.get_job(job_id) is None
    assert state.job_store.get_artifact(art_id) is None
