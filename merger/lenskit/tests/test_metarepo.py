import yaml
from pathlib import Path
from unittest.mock import patch

from merger.lenskit.adapters.metarepo import sync_from_metarepo, MANIFEST_REL_PATH


def test_metarepo_sync_parallel(tmp_path: Path) -> None:
    """
    Test that sync_from_metarepo correctly synchronizes files across multiple repositories
    using the parallel implementation.
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
    source_file.write_text(source_content, encoding="utf-8")

    # Create manifest
    manifest = {
        "version": 1,
        "entries": [
            {
                "id": "config",
                "source": "shared_config.json",
                "targets": ["config.json"],
                "mode": "copy",
            }
        ],
    }

    with (metarepo / MANIFEST_REL_PATH).open("w", encoding="utf-8") as f:
        yaml.dump(manifest, f)

    # Create repos
    num_repos = 20
    for i in range(num_repos):
        repo_path = hub_path / f"repo_{i}"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()  # Mark as repo

    # Run sync
    report = sync_from_metarepo(hub_path, mode="apply")

    assert report["status"] == "ok"
    assert report["aggregate_summary"]["add"] == num_repos
    assert report["aggregate_summary"]["error"] == 0

    # Verify deterministic ordering
    repo_keys = list(report["repos"].keys())
    assert repo_keys == sorted(repo_keys)

    # Verify files
    for i in range(num_repos):
        repo_path = hub_path / f"repo_{i}"
        target_file = repo_path / "config.json"
        assert target_file.exists()
        assert target_file.read_text(encoding="utf-8") == source_content


def test_metarepo_sync_update_flow(tmp_path: Path) -> None:
    """
    Test that updates work correctly with hash checks.
    """
    hub_path = tmp_path / "hub"
    hub_path.mkdir()

    # Create metarepo
    metarepo = hub_path / "metarepo"
    metarepo.mkdir()
    (metarepo / "sync").mkdir()

    source_file = metarepo / "v1.txt"
    source_content_v1 = "v1\n# managed-by: metarepo-sync"
    source_file.write_text(source_content_v1, encoding="utf-8")

    manifest = {
        "version": 1,
        "entries": [
            {
                "id": "v1",
                "source": "v1.txt",
                "targets": ["v1.txt"],
                "mode": "copy",
            }
        ],
    }

    with (metarepo / MANIFEST_REL_PATH).open("w", encoding="utf-8") as f:
        yaml.dump(manifest, f)

    repo_path = hub_path / "repo1"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    # First sync (ADD)
    report = sync_from_metarepo(hub_path, mode="apply")
    assert report["status"] == "ok"
    assert report["aggregate_summary"]["add"] == 1
    assert (repo_path / "v1.txt").read_text(encoding="utf-8") == source_content_v1

    # Second sync (SKIP)
    report = sync_from_metarepo(hub_path, mode="apply")
    assert report["status"] == "ok"
    assert report["aggregate_summary"]["skip"] == 1

    # Update source file
    source_content_v2 = "v2\n# managed-by: metarepo-sync"
    source_file.write_text(source_content_v2, encoding="utf-8")

    # Sync (UPDATE)
    report = sync_from_metarepo(hub_path, mode="apply")
    assert report["status"] == "ok"
    assert report["aggregate_summary"]["update"] == 1
    assert (repo_path / "v1.txt").read_text(encoding="utf-8") == source_content_v2


def test_metarepo_sync_error_handling(tmp_path: Path) -> None:
    """
    Test that sync errors in individual repositories are correctly aggregated
    and result in an overall error status, while still producing deterministic output.
    """
    hub_path = tmp_path / "hub"
    hub_path.mkdir()

    # Create metarepo
    metarepo = hub_path / "metarepo"
    metarepo.mkdir()
    (metarepo / "sync").mkdir()

    # Minimal manifest; content doesn't matter because we patch sync_repo below
    manifest = {"version": 1, "entries": []}
    with (metarepo / MANIFEST_REL_PATH).open("w", encoding="utf-8") as f:
        yaml.dump(manifest, f)

    # Create two repos
    repo1 = hub_path / "repo1"
    repo1.mkdir()
    (repo1 / ".git").mkdir()

    repo2 = hub_path / "repo2"
    repo2.mkdir()
    (repo2 / ".git").mkdir()

    # Mock sync_repo to fail for repo1 and succeed for repo2
    def side_effect(repo_root: Path, *args: Any, **kwargs: Any) -> dict:
        if repo_root.name == "repo1":
            raise RuntimeError("Simulated sync failure")
        return {
            "status": "ok",
            "summary": {"add": 0, "update": 0, "skip": 1, "blocked": 0, "error": 0},
            "details": [],
        }

    with patch("merger.lenskit.adapters.metarepo.sync_repo", side_effect=side_effect):
        report = sync_from_metarepo(hub_path, mode="apply")

    assert report["status"] == "error"
    assert report["aggregate_summary"]["error"] == 1

    assert report["repos"]["repo1"]["status"] == "error"
    assert "Simulated sync failure" in report["repos"]["repo1"]["details"][0]["reason"]

    assert report["repos"]["repo2"]["status"] == "ok"

    # Deterministic ordering
    repo_keys = list(report["repos"].keys())
    assert repo_keys == sorted(repo_keys)
