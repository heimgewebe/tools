
import pytest
from unittest.mock import MagicMock
from merger.lenskit.service.models import Job, JobRequest

def test_sse_contract(service_client, monkeypatch):
    ctx = service_client

    # 1. Create a job manually in store
    # Use proper Pydantic construction
    job_id = "test-job-sse"
    req = JobRequest(repos=["repo-test"])

    # Manually construct Job to control state perfectly
    # Note: Job.create() sets status='queued'. We want 'succeeded' for deterministic end.
    job = Job(
        id=job_id,
        status="succeeded", # Important: ensures stream ends immediately after logs
        created_at="2024-01-01T00:00:00+00:00",
        request=req,
        hub_resolved=str(ctx.hub_path),
        logs=["line1", "line2", "line3"]
    )

    # Mock store retrieval.
    # We use monkeypatch to avoid global side effects.
    # Must mock 'get_job' and 'read_log_lines'.

    def fake_get_job(jid):
        if jid == job_id:
            return job
        return None

    def fake_read_log_lines(jid):
        if jid == job_id:
            return job.logs
        return []

    monkeypatch.setattr(ctx.store, "get_job", fake_get_job)
    monkeypatch.setattr(ctx.store, "read_log_lines", fake_read_log_lines)

    url = f"/api/jobs/{job_id}/logs"

    # CASE 1: No last-id, start from 0
    with ctx.client.stream("GET", url, headers=ctx.headers) as response:
        lines = list(response.iter_lines())
        decoded = [l for l in lines if l]

        # Verify IDs and Data
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
    headers_resume = ctx.headers.copy()
    headers_resume["Last-Event-ID"] = "2"

    with ctx.client.stream("GET", url, headers=headers_resume) as response:
        lines = list(response.iter_lines())
        decoded = [l for l in lines if l]

        # Should start after ID 2
        assert "id: 1" not in decoded
        assert "id: 2" not in decoded

        assert "id: 3" in decoded
        assert "data: line3" in decoded
        assert "event: end" in decoded

    # CASE 3: Resume with query param
    with ctx.client.stream("GET", f"{url}?last_id=1", headers=ctx.headers) as response:
        lines = list(response.iter_lines())
        decoded = [l for l in lines if l]

        assert "id: 2" in decoded
        assert "id: 3" in decoded

    # CASE 4: Header overrides Query
    headers_resume["Last-Event-ID"] = "2"
    with ctx.client.stream("GET", f"{url}?last_id=0", headers=headers_resume) as response:
        lines = list(response.iter_lines())
        decoded = [l for l in lines if l]

        assert "id: 1" not in decoded
        assert "id: 2" not in decoded
        assert "id: 3" in decoded
