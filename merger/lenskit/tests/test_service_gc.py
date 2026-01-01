
import uuid
from merger.lenskit.service.models import Job, Artifact, JobRequest

def test_gc_deletes_real_artifacts(service_client):
    ctx = service_client

    # 1. Create a dummy physical file inside merges_dir
    dummy_file = ctx.merges_dir / "dummy-artifact.md"
    dummy_file.write_text("content", encoding="utf-8")
    assert dummy_file.exists()

    # 2. Create Job and Artifact
    # Construct Job cleanly
    req = JobRequest()
    job = Job.create(req)
    # Override ID to match our test setup if needed, but create() gives random UUID.
    # We can just use the returned object.

    job.status = "succeeded"
    ctx.store.add_job(job)

    art_id = str(uuid.uuid4())

    art = Artifact(
        id=art_id,
        job_id=job.id,
        hub=str(ctx.hub_path),
        repos=[],
        created_at=job.created_at,
        paths={"md": dummy_file.name}, # relative filename
        params=req
    )
    ctx.store.add_artifact(art)

    job.artifact_ids.append(art_id)
    ctx.store.update_job(job)

    # 3. Call remove_job
    ctx.store.remove_job(job.id)

    # 4. Assert Job gone
    assert ctx.store.get_job(job.id) is None

    # 5. Assert Artifact gone from DB
    assert ctx.store.get_artifact(art_id) is None

    # 6. Assert Physical File gone
    assert not dummy_file.exists()

def test_gc_safe_unlink(service_client):
    """Ensure GC doesn't delete files outside merges dir"""
    ctx = service_client

    # Create sensitive file outside merges (in parent temp dir)
    # ctx.merges_dir is inside temp/hub/merges
    # We go up to temp root
    sensitive_file = ctx.merges_dir.parent.parent / "sensitive.txt"
    sensitive_file.write_text("secret")

    # Create Job/Artifact pointing to it via traversal
    req = JobRequest()
    job = Job.create(req)
    ctx.store.add_job(job)

    art_id = str(uuid.uuid4())
    # Try to traverse up: ../../sensitive.txt
    # merges_dir is usually absolute.
    # Artifact.paths are joined with merges_dir.
    # We simulate a path that tries to escape.

    # Note: The service logic usually does: (base / rel).resolve().relative_to(base)
    # We rely on that check in _safe_unlink or similar.

    rel_path = f"../../{sensitive_file.name}"

    art = Artifact(
        id=art_id,
        job_id=job.id,
        hub=str(ctx.hub_path),
        repos=[],
        created_at=job.created_at,
        paths={"secret": rel_path},
        params=req
    )
    ctx.store.add_artifact(art)
    job.artifact_ids.append(art_id)
    ctx.store.update_job(job)

    ctx.store.remove_job(job.id)

    # Verify sensitive file still exists
    assert sensitive_file.exists()
    assert sensitive_file.read_text() == "secret"
