
import pytest
from merger.lenskit.service.models import JobRequest

def test_explicit_reuse_policy(service_client):
    ctx = service_client

    # 1. Create initial job
    # We use a unique payload to ensure no collisions with other tests
    req_payload = {
        "repos": ["repo-test"],
        "level": "summary",
        "plan_only": True
    }

    resp1 = ctx.client.post("/api/jobs", json=req_payload, headers=ctx.headers)
    assert resp1.status_code == 200
    job1 = resp1.json()
    job1_id = job1["id"]

    # Simulate job completion to allow reuse
    # We access the store directly to update status
    job_obj = ctx.store.get_job(job1_id)
    assert job_obj is not None
    job_obj.status = "succeeded"
    ctx.store.update_job(job_obj)

    # 2. Create identical job (expect REUSE)
    resp2 = ctx.client.post("/api/jobs", json=req_payload, headers=ctx.headers)
    assert resp2.status_code == 200
    job2 = resp2.json()
    assert job2["id"] == job1_id

    # 3. Create identical job with force_new=True (expect NEW)
    req_payload_forced = req_payload.copy()
    req_payload_forced["force_new"] = True

    resp3 = ctx.client.post("/api/jobs", json=req_payload_forced, headers=ctx.headers)
    assert resp3.status_code == 200
    job3 = resp3.json()

    assert job3["id"] != job1_id

    # Verify job3 exists
    assert ctx.store.get_job(job3["id"]) is not None

def test_force_new_ignored_if_no_existing(service_client):
    ctx = service_client

    # Create job with force_new=True but no prior job exists
    req_payload = {
        "repos": ["repo-test"],
        "level": "max",
        "plan_only": True,
        "force_new": True
    }
    resp = ctx.client.post("/api/jobs", json=req_payload, headers=ctx.headers)
    assert resp.status_code == 200
    job = resp.json()

    assert ctx.store.get_job(job["id"]) is not None

def test_include_paths_reuse_semantics(service_client):
    """
    Verify tri-state logic at the API/Reuse level.
    None (All) vs [] (Nothing) should NOT reuse each other.
    None (All) vs ["."] (All) SHOULD reuse each other.
    """
    ctx = service_client
    base_payload = {
        "repos": ["repo-test"],
        "level": "summary",
        "plan_only": True
    }

    # 1. Create job with include_paths=None (implicit)
    resp1 = ctx.client.post("/api/jobs", json=base_payload, headers=ctx.headers)
    assert resp1.status_code == 200
    job1_id = resp1.json()["id"]

    # Mark as succeeded to allow reuse
    job_obj = ctx.store.get_job(job1_id)
    job_obj.status = "succeeded"
    ctx.store.update_job(job_obj)

    # 2. Request with include_paths=[] (explicit empty) -> Should be NEW
    payload_empty = base_payload.copy()
    payload_empty["include_paths"] = []

    resp2 = ctx.client.post("/api/jobs", json=payload_empty, headers=ctx.headers)
    assert resp2.status_code == 200
    job2_id = resp2.json()["id"]

    assert job2_id != job1_id, "Job with [] reused job with None! (Hash Collision)"

    # Mark 2 as succeeded
    job_obj2 = ctx.store.get_job(job2_id)
    job_obj2.status = "succeeded"
    ctx.store.update_job(job_obj2)

    # 3. Request with include_paths=["."] -> Should reuse job1 (None)
    payload_dot = base_payload.copy()
    payload_dot["include_paths"] = ["."]

    resp3 = ctx.client.post("/api/jobs", json=payload_dot, headers=ctx.headers)
    assert resp3.status_code == 200
    job3_id = resp3.json()["id"]

    assert job3_id == job1_id, "Job with ['.'] failed to reuse job with None"
