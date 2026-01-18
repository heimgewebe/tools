import pytest
from unittest.mock import MagicMock, patch
from merger.lenskit.service.runner import JobRunner
from merger.lenskit.service.jobstore import JobStore
from merger.lenskit.service.models import JobRequest, Job
from pathlib import Path
import tempfile
import os

@pytest.fixture
def mock_job_store():
    store = MagicMock(spec=JobStore)
    store.get_job = MagicMock()
    store.update_job = MagicMock()
    store.append_log_line = MagicMock()
    store.add_artifact = MagicMock()
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
