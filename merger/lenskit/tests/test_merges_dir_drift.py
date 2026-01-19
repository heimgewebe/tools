import pytest
from unittest.mock import MagicMock, patch
from merger.lenskit.service.runner import JobRunner
from merger.lenskit.service.jobstore import JobStore
from merger.lenskit.service.models import JobRequest, Job, Artifact
from merger.lenskit.service.app import download_artifact
from fastapi import HTTPException
from pathlib import Path
import tempfile

# Backward Compatibility Note:
# Artifacts created before the 'merges_dir' field was added (or where it is None)
# are handled by the 'else' branch in download_artifact, which defaults to
# get_merges_dir(hub). This ensures legacy artifacts remain accessible.

@pytest.fixture
def mock_job_store():
    store = MagicMock(spec=JobStore)
    store.get_job = MagicMock()
    store.update_job = MagicMock()
    store.append_log_line = MagicMock()
    store.add_artifact = MagicMock()
    store.get_artifact = MagicMock()
    return store

@pytest.fixture
def temp_hub():
    with tempfile.TemporaryDirectory() as tmp:
        hub = Path(tmp)
        (hub / "repoA").mkdir()
        yield hub

def test_runner_resolves_relative_merges_dir(mock_job_store, temp_hub):
    """
    Test that relative merges_dir in request is resolved relative to HUB, not CWD.
    """
    runner = JobRunner(mock_job_store)

    # Setup: relative path
    rel_path = "my_merges"
    req = JobRequest(
        hub=str(temp_hub),
        repos=["repoA"],
        merges_dir=rel_path
    )
    job = Job.create(req)
    job.hub_resolved = str(temp_hub)
    mock_job_store.get_job.return_value = job

    # Expected absolute path
    expected_merges_dir = temp_hub / rel_path

    with patch("merger.lenskit.service.runner.scan_repo") as mock_scan, \
         patch("merger.lenskit.service.runner.write_reports_v2") as mock_write, \
         patch("merger.lenskit.service.runner.validate_source_dir"):

        # Mock artifacts to return some paths
        mock_artifacts = MagicMock()
        mock_artifacts.get_all_paths.return_value = [expected_merges_dir / "report.md"]
        mock_artifacts.index_json = None
        mock_artifacts.canonical_md = None
        mock_artifacts.md_parts = []

        mock_write.return_value = mock_artifacts

        runner._run_job(job.id)

        # check that write_reports_v2 was called with absolute path
        assert mock_write.call_count == 1
        args, _ = mock_write.call_args
        merges_dir_arg = args[0]

        assert merges_dir_arg == expected_merges_dir
        assert merges_dir_arg.is_absolute()

        # check that Artifact record contains absolute path (updated in req)
        assert mock_job_store.add_artifact.call_count == 1
        art = mock_job_store.add_artifact.call_args[0][0]

        # The runner should update req.merges_dir to absolute path
        assert art.params.merges_dir == str(expected_merges_dir)

def test_runner_logs_output_paths(mock_job_store, temp_hub):
    """
    Test that the runner logs the generated file paths.
    """
    runner = JobRunner(mock_job_store)

    req = JobRequest(hub=str(temp_hub), repos=["repoA"])
    job = Job.create(req)
    job.hub_resolved = str(temp_hub)
    mock_job_store.get_job.return_value = job

    with patch("merger.lenskit.service.runner.scan_repo"), \
         patch("merger.lenskit.service.runner.write_reports_v2") as mock_write, \
         patch("merger.lenskit.service.runner.validate_source_dir"):

        mock_artifacts = MagicMock()
        # Set attributes to None to avoid 'Mock' being truthy and accessing .name
        mock_artifacts.index_json = None
        mock_artifacts.canonical_md = None
        mock_artifacts.md_parts = []

        mock_artifacts.get_all_paths.return_value = [Path("/tmp/foo.md"), Path("/tmp/bar.json")]
        mock_write.return_value = mock_artifacts

        runner._run_job(job.id)

        # Check logs
        logs = mock_job_store.append_log_line.call_args_list
        log_messages = [call[0][1] for call in logs]

        # Should contain list of paths
        found_paths = any("/tmp/foo.md" in msg and "/tmp/bar.json" in msg for msg in log_messages)

        assert found_paths, f"Log messages did not contain output paths. Logs: {log_messages}"

def test_download_resolves_relative_paths(mock_job_store, temp_hub):
    """
    Test that download_artifact resolves relative merges_dir against the Hub.
    """
    # Create an artifact with a relative merges_dir
    rel_path = "custom_out"
    abs_path = temp_hub / rel_path
    abs_path.mkdir()

    # Create the file
    (abs_path / "test.md").write_text("content")

    art = Artifact(
        id="art1",
        job_id="job1",
        hub=str(temp_hub),
        repos=["repoA"],
        created_at="2024-01-01T00:00:00",
        paths={"md": "test.md"},
        params=JobRequest(
            hub=str(temp_hub),
            repos=["repoA"],
            merges_dir=rel_path # Relative!
        )
    )

    mock_job_store.get_artifact.return_value = art

    # We need to mock 'state' in app.py or 'get_security_config'
    # app.py uses global state. We must patch it.

    with patch("merger.lenskit.service.app.state") as mock_state, \
         patch("merger.lenskit.service.app.get_security_config") as mock_get_sec:

        mock_state.job_store = mock_job_store

        # Mock security to allow everything for this test (focus on path logic)
        mock_sec = MagicMock()
        # validate_path just returns the path if valid
        mock_sec.validate_path.side_effect = lambda p: p
        mock_get_sec.return_value = mock_sec

        # Call download_artifact
        response = download_artifact("art1", "md")

        # Verify the file path used in response
        assert str(response.path) == str(abs_path / "test.md")

        # Verify that validate_path was called with the absolute path
        # (It should resolve rel_path to temp_hub / rel_path)
        # We expect validate_path to be called for merges_dir
        # Check call args
        calls = mock_sec.validate_path.call_args_list

        # There should be at least one call with the absolute directory
        # The implementation first resolves/validates merges_dir, then file_path

        # Verify that at least one call matches expected_dir
        resolved_dir_calls = [c[0][0] for c in calls if c[0][0] == abs_path]
        assert len(resolved_dir_calls) > 0, f"Security config not called with resolved absolute path {abs_path}"
