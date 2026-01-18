import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import time
import json

# Import app logic
from merger.lenskit.service.app import app, init_service, state
from merger.lenskit.adapters.security import get_security_config

client = TestClient(app)

@pytest.fixture
def service_env(tmp_path):
    hub = tmp_path / "hub"
    hub.mkdir()

    # Create a dummy repo
    repo = hub / "dummy-repo"
    repo.mkdir()
    (repo / "README.md").write_text("dummy content")
    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("print('hello')")

    custom_merges = tmp_path / "custom_merges"
    custom_merges.mkdir()

    # Initialize service with custom merges dir
    init_service(hub_path=hub, merges_dir=custom_merges)

    yield {
        "hub": hub,
        "repo": repo,
        "merges_dir": custom_merges
    }

    # Teardown
    state.hub = None
    state.merges_dir = None
    state.job_store = None
    state.runner = None
    state.log_provider = None
    sec = get_security_config()
    sec.allowlist_roots = []
    sec.token = None

def test_effective_merges_dir_populated(service_env):
    """
    Test that when the service is configured with a custom merges_dir,
    jobs submitted without explicit merges_dir result in artifacts
    that record the effective merges_dir, and downloads work.
    """
    # 1. Submit Job (via API to ensure default population logic runs)
    payload = {
        "repos": ["dummy-repo"],
        "merges_dir": None, # Explicitly None to trigger default
        "level": "max",
        "plan_only": False
    }

    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 200, f"Job creation failed: {response.text}"
    job_id = response.json()["id"]

    # 2. Wait for completion
    max_retries = 50
    for _ in range(max_retries):
        resp = client.get(f"/api/jobs/{job_id}")
        assert resp.status_code == 200
        job_data = resp.json()
        if job_data["status"] in ("succeeded", "failed"):
            break
        time.sleep(0.1)

    assert job_data["status"] == "succeeded", f"Job failed with error: {job_data.get('error')} logs: {job_data.get('logs')}"

    # 3. Get Artifact
    artifact_ids = job_data.get("artifact_ids", [])
    assert len(artifact_ids) > 0
    art_id = artifact_ids[0]

    resp = client.get(f"/api/artifacts/{art_id}")
    assert resp.status_code == 200
    artifact = resp.json()

    # 4. Verify merges_dir field (The fix)
    assert "merges_dir" in artifact
    recorded_merges_dir = artifact["merges_dir"]
    assert recorded_merges_dir is not None
    # Use resolve() to handle potential symlinks/abs path differences,
    # but service_env["merges_dir"] is a pytest tmp_path (pathlib)
    assert Path(recorded_merges_dir).resolve() == service_env["merges_dir"].resolve()

    # 5. Verify params.merges_dir (The existing behavior - populated by app.py)
    # app.py populates request.merges_dir from state.merges_dir
    assert artifact["params"]["merges_dir"] == str(service_env["merges_dir"])

    # 6. Verify Download Works
    dl_resp = client.get(f"/api/artifacts/{art_id}/download")
    assert dl_resp.status_code == 200
    # The report should contain reference to the dummy content or at least the header
    assert "# repoLens Report" in dl_resp.text

    # Verify logging (optional, but good to check if we log the path)
    logs = "".join(job_data["logs"])
    assert f"Writing reports to: {service_env['merges_dir'].resolve()}" in logs
