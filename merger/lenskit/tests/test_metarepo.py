import yaml
from unittest.mock import patch
from merger.lenskit.adapters.metarepo import sync_from_metarepo

def test_sync_from_metarepo_success(tmp_path):
    hub = tmp_path / "hub"
    hub.mkdir()
    metarepo = hub / "metarepo"
    metarepo.mkdir()
    (metarepo / "sync").mkdir()

    manifest = {
        "version": 1,
        "entries": [
            {"id": "test", "source": "src.txt", "targets": ["tgt.txt"]}
        ]
    }
    with (metarepo / "sync/metarepo-sync.yml").open("w") as f:
        yaml.dump(manifest, f)

    (metarepo / "src.txt").write_text("hello")

    repo1 = hub / "repo1"
    repo1.mkdir()
    (repo1 / ".git").mkdir()

    report = sync_from_metarepo(hub, mode="apply")

    assert report["status"] == "ok"
    assert report["aggregate_summary"]["add"] == 1
    assert (repo1 / "tgt.txt").read_text() == "hello"

def test_sync_from_metarepo_parallel_failure_aggregation(tmp_path):
    """
    Test that sync_from_metarepo correctly aggregates errors when one repo fails.
    """
    # Setup Hub
    hub = tmp_path / "hub"
    hub.mkdir()

    # Setup Metarepo
    metarepo = hub / "metarepo"
    metarepo.mkdir()
    (metarepo / "sync").mkdir()

    # Manifest
    manifest = {
        "version": 1,
        "managed_marker": "managed-by: metarepo-sync",
        "entries": [
            {
                "id": "file1",
                "source": "files/source.txt",
                "targets": ["dest.txt"]
            }
        ]
    }
    with (metarepo / "sync/metarepo-sync.yml").open("w") as f:
        yaml.dump(manifest, f)

    # Source file
    (metarepo / "files").mkdir()
    (metarepo / "files/source.txt").write_text("content")

    # Setup Repos
    repo1 = hub / "repo1"
    repo1.mkdir()
    (repo1 / ".git").mkdir()

    repo2 = hub / "repo2"
    repo2.mkdir()
    (repo2 / ".git").mkdir()

    # We patch sync_repo to fail for repo2
    with patch('merger.lenskit.adapters.metarepo.sync_repo') as mock_sync:
        def side_effect(repo_root, *args, **kwargs):
            if repo_root.name == "repo2":
                raise RuntimeError("Simulated Sync Failure")
            # For repo1, return a success report
            return {
                "status": "ok",
                "summary": {"add": 1, "update": 0, "skip": 0, "blocked": 0, "error": 0},
                "details": []
            }

        mock_sync.side_effect = side_effect

        report = sync_from_metarepo(hub, mode="apply")

        # Verification
        assert report["status"] == "error"
        assert report["aggregate_summary"]["error"] >= 1
        assert "repo2" in report["repos"]
        assert report["repos"]["repo2"]["status"] == "error"
        # repo1 should be fine (mocked response)
        assert report["repos"]["repo1"]["status"] == "ok"

        # Verify deterministic ordering
        repo_keys = list(report["repos"].keys())
        assert repo_keys == sorted(repo_keys)
