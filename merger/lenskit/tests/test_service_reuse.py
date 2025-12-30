from fastapi.testclient import TestClient
from merger.lenskit.service.app import app, init_service, state
from merger.lenskit.service.models import JobRequest
import pytest
from unittest.mock import MagicMock
from pathlib import Path

# Setup fixture
@pytest.fixture
def client(tmp_path):
    # Initialize service with a temp hub
    hub = tmp_path / "hub"
    hub.mkdir()
    merges = tmp_path / "merges"
    merges.mkdir()
    init_service(hub_path=hub, merges_dir=merges, token="secret")

    # Mock runner to prevent job execution/failure during test
    # This keeps the job in 'queued' state, ensuring reuse logic triggers.
    # We use a context manager or explicit restore to avoid global state pollution.
    original_submit = state.runner.submit_job
    state.runner.submit_job = MagicMock()

    yield TestClient(app)

    # Restore original method (though init_service replaces runner, this is cleaner)
    state.runner.submit_job = original_submit

def test_create_job_idempotency(client):
    """
    Test that creating the same job twice returns the same job object (reused),
    and that the new job_key is being used/persisted.
    """
    # Create a job
    payload = {
        "repos": ["repo1"],
        "extras": "json_sidecar",
        "force_new": False
    }
    headers = {"Authorization": "Bearer secret"}

    resp1 = client.post("/api/jobs", json=payload, headers=headers)
    assert resp1.status_code == 200
    job1 = resp1.json()
    assert "job_key" in job1
    assert job1["job_key"] is not None

    # Create same job again
    resp2 = client.post("/api/jobs", json=payload, headers=headers)
    assert resp2.status_code == 200
    job2 = resp2.json()

    # Should be same ID (reuse)
    assert job1["id"] == job2["id"]
    assert job1["job_key"] == job2["job_key"]

def test_force_new_job(client):
    """Test that force_new=True creates a new job even if inputs are same."""
    payload = {
        "repos": ["repo1"],
        "extras": "json_sidecar",
        "force_new": False
    }
    headers = {"Authorization": "Bearer secret"}

    resp1 = client.post("/api/jobs", json=payload, headers=headers)
    assert resp1.status_code == 200
    job1 = resp1.json()

    # Force new
    payload["force_new"] = True
    resp2 = client.post("/api/jobs", json=payload, headers=headers)
    assert resp2.status_code == 200
    job2 = resp2.json()

    assert job1["id"] != job2["id"]
    # Keys should be identical though
    assert job1["job_key"] == job2["job_key"]

def test_job_key_variance_integration(client):
    """Test that different parameters result in different job keys via API."""
    headers = {"Authorization": "Bearer secret"}

    resp1 = client.post("/api/jobs", json={"repos": ["r1"]}, headers=headers)
    job1 = resp1.json()

    resp2 = client.post("/api/jobs", json={"repos": ["r2"]}, headers=headers)
    job2 = resp2.json()

    assert job1["job_key"] != job2["job_key"]
