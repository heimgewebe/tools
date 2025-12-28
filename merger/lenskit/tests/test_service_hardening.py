import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import time
from merger.lenskit.service.app import app, init_service, state
from merger.lenskit.service.models import JobRequest, Job

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

def test_idempotency(client_and_hub):
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

    # Second create
    resp2 = client.post("/api/jobs", json=req, headers=headers)
    assert resp2.status_code == 200, resp2.text
    job2 = resp2.json()

    assert job1["id"] == job2["id"]
    assert job1["content_hash"] == job2["content_hash"]

    # Change params -> new job
    req["level"] = "summary"
    resp3 = client.post("/api/jobs", json=req, headers=headers)
    job3 = resp3.json()
    assert job3["id"] != job1["id"]

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

    # Cancel
    resp_cancel = client.post(f"/api/jobs/{job_id}/cancel", headers=headers)
    assert resp_cancel.status_code == 200, resp_cancel.text
    assert resp_cancel.json()["status"] == "canceling"

    # Verify status
    resp_get = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert resp_get.json()["status"] == "canceling"

def test_log_resume(client_and_hub):
    client, hub_path = client_and_hub
    # Manually inject a job and logs
    req = {
        "hub": hub_path,
        "repos": ["repo3"]
    }
    headers = {"Authorization": "Bearer test-token"}
    resp = client.post("/api/jobs", json=req, headers=headers)
    assert resp.status_code == 200, resp.text
    job_id = resp.json()["id"]

    # Inject logs
    state.job_store.append_log_line(job_id, "Line 1")
    state.job_store.append_log_line(job_id, "Line 2")
    state.job_store.append_log_line(job_id, "Line 3")

    # Mark job as finished so stream stops
    job = state.job_store.get_job(job_id)
    job.status = "succeeded"
    state.job_store.update_job(job)

    # Test stream with last_id=1 (should skip index 0)
    resp_stream = client.get(f"/api/jobs/{job_id}/logs?last_id=1", headers=headers)
    assert resp_stream.status_code == 200
    content = resp_stream.content.decode("utf-8")

    assert "Line 1" not in content
    assert "Line 2" in content
    assert "Line 3" in content
    assert "id: 2" in content
    assert "id: 3" in content
