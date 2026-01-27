import yaml
from pathlib import Path
from unittest import mock
from merger.lenskit.adapters.metarepo import sync_from_metarepo, sync_repo, MANIFEST_REL_PATH

def test_metarepo_sync_parallel(tmp_path: Path):
    """
    Test that sync_from_metarepo correctly synchronizes files across multiple repositories
    using the optimized parallel implementation.
    """
    hub_path = tmp_path / "hub"
    hub_path.mkdir()

    # Create metarepo
    metarepo = hub_path / "metarepo"
    metarepo.mkdir()
    (metarepo / "sync").mkdir()

    # Create a source file
    source_content = '{"foo": "bar"}' * 100
    source_file = metarepo / "shared_config.json"
    source_file.write_text(source_content, encoding='utf-8')

    # Create manifest
    manifest = {
        "version": 1,
        "entries": [
            {
                "id": "config",
                "source": "shared_config.json",
                "targets": ["config.json"],
                "mode": "copy"
            }
        ]
    }

    with (metarepo / MANIFEST_REL_PATH).open("w") as f:
        yaml.dump(manifest, f)

    # Create repos
    num_repos = 20
    for i in range(num_repos):
        repo_name = f"repo_{i}"
        repo_path = hub_path / repo_name
        repo_path.mkdir()
        (repo_path / ".git").mkdir() # Mark as repo

    # Run sync
    report = sync_from_metarepo(hub_path, mode="apply")

    assert report["status"] == "ok"
    assert report["aggregate_summary"]["add"] == num_repos
    assert report["aggregate_summary"]["error"] == 0

    # Verify files
    for i in range(num_repos):
        repo_path = hub_path / f"repo_{i}"
        target_file = repo_path / "config.json"
        assert target_file.exists()
        assert target_file.read_text(encoding='utf-8') == source_content

def test_metarepo_sync_update_flow(tmp_path: Path):
    """
    Test that updates work correctly with hash checks.
    """
    hub_path = tmp_path / "hub"
    hub_path.mkdir()

    # Create metarepo
    metarepo = hub_path / "metarepo"
    metarepo.mkdir()
    (metarepo / "sync").mkdir()

    source_content = "v1\n# managed-by: metarepo-sync"
    source_file = metarepo / "v1.txt"
    source_file.write_text(source_content)

    manifest = {
        "version": 1,
        "entries": [
            {
                "id": "v1",
                "source": "v1.txt",
                "targets": ["v1.txt"],
                "mode": "copy"
            }
        ]
    }
    with (metarepo / MANIFEST_REL_PATH).open("w") as f:
        yaml.dump(manifest, f)

    repo_path = hub_path / "repo1"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    # First sync (ADD)
    report = sync_from_metarepo(hub_path, mode="apply")
    assert report["aggregate_summary"]["add"] == 1
    assert (repo_path / "v1.txt").read_text() == source_content

    # Second sync (SKIP)
    report = sync_from_metarepo(hub_path, mode="apply")
    assert report["aggregate_summary"]["skip"] == 1

    # Update source file
    source_content_v2 = "v2\n# managed-by: metarepo-sync"
    source_file.write_text(source_content_v2)

    # Sync (UPDATE)
    report = sync_from_metarepo(hub_path, mode="apply")
    assert report["aggregate_summary"]["update"] == 1
    assert (repo_path / "v1.txt").read_text() == source_content_v2

def test_metarepo_sync_error_handling(tmp_path: Path):
    """
    Test that errors during parallel sync are properly handled and aggregated.
    """
    hub_path = tmp_path / "hub"
    hub_path.mkdir()

    # Create metarepo with valid manifest
    metarepo = hub_path / "metarepo"
    metarepo.mkdir()
    (metarepo / "sync").mkdir()

    source_content = "test content"
    source_file = metarepo / "test.txt"
    source_file.write_text(source_content)

    manifest = {
        "version": 1,
        "entries": [
            {
                "id": "test",
                "source": "test.txt",
                "targets": ["test.txt"],
                "mode": "copy"
            }
        ]
    }
    with (metarepo / MANIFEST_REL_PATH).open("w") as f:
        yaml.dump(manifest, f)

    # Create two normal repos
    repo1_path = hub_path / "repo1"
    repo1_path.mkdir()
    (repo1_path / ".git").mkdir()

    repo2_path = hub_path / "repo2"
    repo2_path.mkdir()
    (repo2_path / ".git").mkdir()

    # Mock sync_repo to raise an exception for repo2
    def mock_sync_repo(repo_root, *args, **kwargs):
        if repo_root.name == "repo2":
            raise RuntimeError("Simulated sync failure for repo2")
        return sync_repo(repo_root, *args, **kwargs)
    
    with mock.patch('merger.lenskit.adapters.metarepo.sync_repo', side_effect=mock_sync_repo):
        # Run sync - should handle the error gracefully
        report = sync_from_metarepo(hub_path, mode="apply")

        # Verify error was captured
        assert report["status"] == "error", "Overall status should be error when any repo fails"
        assert report["aggregate_summary"]["error"] >= 1, "Error count should be at least 1"

        # Verify the successful repo was processed
        assert "repo1" in report["repos"]
        assert report["repos"]["repo1"]["status"] == "ok"
        
        # Verify the failed repo has error status
        assert "repo2" in report["repos"]
        assert report["repos"]["repo2"]["status"] == "error"
