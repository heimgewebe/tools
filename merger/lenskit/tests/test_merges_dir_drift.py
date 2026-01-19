import pytest
from unittest.mock import MagicMock, patch
from merger.lenskit.service.runner import JobRunner
from merger.lenskit.service.jobstore import JobStore
from merger.lenskit.service.models import JobRequest, Job, Artifact
from merger.lenskit.service.app import download_artifact
from merger.lenskit.adapters.security import get_security_config
from pathlib import Path
import tempfile

@pytest.fixture
def temp_hub():
    with tempfile.TemporaryDirectory() as tmp:
        hub = Path(tmp).resolve()
        (hub / "repoA").mkdir()
        (hub / "repoA" / "README.md").write_text("content")

        # Initialize Security Config
        sec = get_security_config()
        # Reset allowlist to avoid pollution
        sec.allowlist_roots = []
        sec.add_allowlist_root(hub)

        yield hub

        # Teardown
        sec.allowlist_roots = []

def test_runner_resolves_and_creates_relative_merges_dir(temp_hub):
    """
    Integration test: Runner should resolve relative merges_dir against HUB,
    create the directory, and persist absolute path in Artifact.
    """
    # 1. Setup Real JobStore
    store = JobStore(temp_hub)
    runner = JobRunner(store)

    # 2. Setup Job with relative merges_dir
    rel_path = "output/merges"
    req = JobRequest(
        hub=str(temp_hub),
        repos=["repoA"],
        merges_dir=rel_path
    )
    job = Job.create(req)
    job.hub_resolved = str(temp_hub)
    store.add_job(job)

    # 3. Run Job (Synchronously via private method)
    # We mock write_reports_v2 to return a dummy artifact object but let directory creation happen
    # scan_repo can also be mocked to avoid dependency on actual repo content logic if desired,
    # but since we created a dummy repo, it might run fine. Let's mock scan_repo for speed/isolation.
    with patch("merger.lenskit.service.runner.write_reports_v2") as mock_write, \
         patch("merger.lenskit.service.runner.scan_repo") as mock_scan:

        mock_artifacts = MagicMock()
        mock_artifacts.get_all_paths.return_value = [Path("dummy.md")]
        mock_artifacts.index_json = None
        mock_artifacts.canonical_md = None
        mock_artifacts.md_parts = []
        mock_write.return_value = mock_artifacts

        mock_scan.return_value = {} # Dummy summary

        runner._run_job(job.id)

    # 4. Verification

    # A. Check Directory Exists at Absolute Path
    expected_abs_path = (temp_hub / rel_path).resolve()
    assert expected_abs_path.exists(), f"Directory {expected_abs_path} was not created"
    assert expected_abs_path.is_dir()

    # B. Check Job Status
    updated_job = store.get_job(job.id)
    assert updated_job.status == "succeeded", f"Job failed with error: {updated_job.error}"

    # C. Check Artifact Persistence
    assert len(updated_job.artifact_ids) == 1
    art = store.get_artifact(updated_job.artifact_ids[0])
    assert art is not None

    # D. Check Artifact.merges_dir is absolute and correct
    assert art.merges_dir == str(expected_abs_path)
    assert Path(art.merges_dir).is_absolute()

    # E. Check Artifact.params.merges_dir (Request object was updated in memory)
    # Note: JobStore saves the updated request object
    assert art.params.merges_dir == str(expected_abs_path)


def test_download_artifact_uses_persisted_merges_dir(temp_hub):
    """
    Test that download_artifact uses the persisted absolute merges_dir.
    """
    # Setup manual artifact
    abs_merges_dir = temp_hub / "custom_output"
    abs_merges_dir.mkdir()
    (abs_merges_dir / "test.md").write_text("secret content")

    store = JobStore(temp_hub)

    art = Artifact(
        id="art_dl_test",
        job_id="job_dl_test",
        hub=str(temp_hub),
        repos=["repoA"],
        created_at="2024-01-01",
        paths={"md": "test.md"},
        params=JobRequest(hub=str(temp_hub), repos=["repoA"]),
        merges_dir=str(abs_merges_dir) # Persisted absolute path
    )
    store.add_artifact(art)

    # Patch global state for app.py
    # We need to ensure get_security_config allows the path

    with patch("merger.lenskit.service.app.state") as mock_state, \
         patch("merger.lenskit.service.app.get_security_config") as mock_get_sec:

        mock_state.job_store = store

        # Mock security to be permissive (we are testing path logic here)
        mock_sec = MagicMock()
        mock_sec.validate_path.side_effect = lambda p: p
        mock_get_sec.return_value = mock_sec

        response = download_artifact("art_dl_test", "md")

        assert str(response.path) == str(abs_merges_dir / "test.md")


def test_download_artifact_resolves_legacy_relative_path(temp_hub):
    """
    Test backward compatibility: if merges_dir is missing in Artifact,
    it uses params.merges_dir and resolves it against Hub.
    """
    rel_path = "legacy_output"
    abs_merges_dir = temp_hub / rel_path
    abs_merges_dir.mkdir()
    (abs_merges_dir / "legacy.md").write_text("legacy content")

    store = JobStore(temp_hub)

    art = Artifact(
        id="art_legacy",
        job_id="job_legacy",
        hub=str(temp_hub),
        repos=["repoA"],
        created_at="2024-01-01",
        paths={"md": "legacy.md"},
        params=JobRequest(
            hub=str(temp_hub),
            repos=["repoA"],
            merges_dir=rel_path # Relative in params
        ),
        merges_dir=None # Simulate legacy artifact
    )
    store.add_artifact(art)

    with patch("merger.lenskit.service.app.state") as mock_state, \
         patch("merger.lenskit.service.app.get_security_config") as mock_get_sec:

        mock_state.job_store = store

        mock_sec = MagicMock()
        mock_sec.validate_path.side_effect = lambda p: p
        mock_get_sec.return_value = mock_sec

        response = download_artifact("art_legacy", "md")

        # It should have resolved rel_path against temp_hub
        expected_path = abs_merges_dir / "legacy.md"
        assert str(response.path) == str(expected_path)
