
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from merger.lenskit.service.app import app, init_service, state
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil
from merger.lenskit.service.models import Job

@pytest.fixture
def test_env():
    temp_dir = tempfile.mkdtemp()
    hub_path = Path(temp_dir) / "hub"
    hub_path.mkdir()
    merges_dir = hub_path / "merges"
    merges_dir.mkdir()

    init_service(hub_path, merges_dir=merges_dir)

    yield

    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_sse_contract(test_env):
    client = TestClient(app)

    # 1. Create a job manually in store
    job_id = "test-job-sse"
    job = Job(
        id=job_id,
        status="running",
        created_at="2024-01-01T00:00:00Z",
        request={}
    )
    job.logs = ["line1", "line2", "line3"]

    # Mock read_log_lines to return fixed logs
    state.job_store.get_job = MagicMock(return_value=job)
    state.job_store.read_log_lines = MagicMock(return_value=job.logs)

    # CASE 1: No last-id, start from 0
    # We use stream=True but TestClient might not support SSE parsing natively easily.
    # We'll just read the lines.

    # Note: The generator has an asyncio.sleep(0.25) loop.
    # To test this synchronously/fast without waiting forever, we need to mock job status
    # to switch to 'succeeded' so the loop terminates.

    # We'll simulate a flow:
    # 1. Start stream.
    # 2. Generator yields existing logs.
    # 3. Check status (running) -> sleep
    # 4. Check status (succeeded) -> yield rest -> yield end -> break

    # To avoid the sleep delay in tests, we can patch SSE_POLL_SEC or app.state.
    # But SSE_POLL_SEC is a global constant in app.py.
    # Let's rely on the fact that if job is 'succeeded', it breaks immediately.

    job.status = "succeeded" # Force immediate finish for test speed

    with client.stream("GET", f"/api/jobs/{job_id}/logs") as response:
        lines = list(response.iter_lines())

        # Parse SSE lines
        # format:
        # id: 1
        # data: line1
        #
        # id: 2
        # data: line2
        # ...
        # event: end
        # data: end

        decoded = [l for l in lines if l]

        # Verify IDs start at 1 (index + 1)
        assert "id: 1" in decoded
        assert "data: line1" in decoded
        assert "id: 2" in decoded
        assert "data: line2" in decoded
        assert "id: 3" in decoded
        assert "data: line3" in decoded

        # Verify end event
        assert "event: end" in decoded
        assert "data: end" in decoded

    # CASE 2: Resume with Last-Event-ID header
    # If client saw id:2 (line2), it sends Last-Event-ID: 2.
    # Server should send logs[2:] -> line3 (id:3)

    headers = {"Last-Event-ID": "2"}
    with client.stream("GET", f"/api/jobs/{job_id}/logs", headers=headers) as response:
        lines = list(response.iter_lines())
        decoded = [l for l in lines if l]

        # Should NOT contain id: 1 or id: 2
        assert "id: 1" not in decoded
        assert "id: 2" not in decoded

        # Should contain id: 3
        assert "id: 3" in decoded
        assert "data: line3" in decoded

        assert "event: end" in decoded

    # CASE 3: Resume with query param (lower priority)
    # last_id=1 -> should send line2, line3
    with client.stream("GET", f"/api/jobs/{job_id}/logs?last_id=1") as response:
        lines = list(response.iter_lines())
        decoded = [l for l in lines if l]

        assert "id: 2" in decoded
        assert "id: 3" in decoded

    # CASE 4: Header overrides Query
    # Header=2, Query=0. Header wins -> start after 2 (send 3)
    headers = {"Last-Event-ID": "2"}
    with client.stream("GET", f"/api/jobs/{job_id}/logs?last_id=0", headers=headers) as response:
        lines = list(response.iter_lines())
        decoded = [l for l in lines if l]

        assert "id: 1" not in decoded
        assert "id: 2" not in decoded
        assert "id: 3" in decoded
