from fastapi.testclient import TestClient
from merger.lenskit.service.app import app, state, init_service
from pathlib import Path
import pytest
import shutil

# Setup temporary hub for tests
@pytest.fixture
def client(tmp_path):
    hub = tmp_path / "hub"
    hub.mkdir()
    (hub / "repoA").mkdir()

    # Initialize service state
    init_service(hub_path=hub, token="test-token")

    return TestClient(app)

def test_create_job_blocks_dirty_repo_keys(client):
    """
    Backend Hardening: Ensure that sending a dirty repo key (e.g. traversal attempt)
    results in a 400 Bad Request, even if the frontend check is bypassed.
    """
    headers = {"Authorization": "Bearer test-token"}
    payload = {
        "repos": ["repoA", "../dirty"],
        "hub": str(state.hub),
        "level": "max",
        "mode": "gesamt"
    }

    response = client.post("/api/jobs", json=payload, headers=headers)

    assert response.status_code == 400
    # The validation happens in `validate_repo_name` called early in `create_job`
    assert "Invalid repo name" in response.json()["detail"]

def test_create_job_blocks_absolute_path_repo(client):
    """
    Backend Hardening: Ensure absolute paths are rejected as repo names.
    """
    headers = {"Authorization": "Bearer test-token"}
    payload = {
        "repos": ["/etc/passwd"],
        "hub": str(state.hub),
        "level": "max",
        "mode": "gesamt"
    }

    response = client.post("/api/jobs", json=payload, headers=headers)
    assert response.status_code == 400
