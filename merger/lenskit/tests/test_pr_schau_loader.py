import json
import tempfile
from pathlib import Path

import pytest

from merger.lenskit.core.extractor import generate_review_bundle
from merger.lenskit.core.pr_schau_bundle import load_pr_schau_bundle, PRSchauBundleError


def test_loader_accepts_generated_bundle_basic():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        hub = tmp / "hub"
        hub.mkdir()

        old_repo = tmp / "old"
        old_repo.mkdir()
        (old_repo / "README.md").write_text("Old", encoding="utf-8")

        new_repo = tmp / "new"
        new_repo.mkdir()
        (new_repo / "README.md").write_text("New", encoding="utf-8")
        (new_repo / "contracts" / "x").mkdir(parents=True, exist_ok=True)
        (new_repo / "contracts" / "x" / "c.schema.json").write_text('{"a":1}', encoding="utf-8")

        generate_review_bundle(old_repo, new_repo, "repo1", hub)

        prdir = hub / ".repolens" / "pr-schau" / "repo1"
        # Find the timestamp folder
        ts_folders = list(prdir.iterdir())
        assert len(ts_folders) == 1
        bundle_dir = ts_folders[0]

        data, base = load_pr_schau_bundle(bundle_dir, verify_level="basic")
        assert base == bundle_dir
        assert data["kind"] == "repolens.pr_schau.bundle"
        assert data["version"] == "1.0"


def test_loader_accepts_generated_bundle_full():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        hub = tmp / "hub"
        hub.mkdir()

        old_repo = tmp / "old"
        old_repo.mkdir()
        (old_repo / "a.txt").write_text("A", encoding="utf-8")

        new_repo = tmp / "new"
        new_repo.mkdir()
        (new_repo / "a.txt").write_text("B", encoding="utf-8")

        generate_review_bundle(old_repo, new_repo, "repo2", hub)

        prdir = hub / ".repolens" / "pr-schau" / "repo2"
        # Find the timestamp folder
        ts_folders = list(prdir.iterdir())
        assert len(ts_folders) == 1
        bundle_dir = ts_folders[0]

        data, _ = load_pr_schau_bundle(bundle_dir, verify_level="full")
        assert data["completeness"]["primary_part"] == "review.md"


def test_loader_rejects_legacy_flat_bundle():
    with tempfile.TemporaryDirectory() as tmp_dir:
        d = Path(tmp_dir)
        # Craft a legacy-like flat bundle.json
        legacy = {
            "kind": "repolens.pr_schau.bundle",
            "version": 1,
            "repo": "x",
            "created_at": "2023-01-01T00:00:00Z",
            "generator": {"name": "old"},
        }
        (d / "bundle.json").write_text(json.dumps(legacy), encoding="utf-8")

        with pytest.raises(PRSchauBundleError):
            load_pr_schau_bundle(d, strict=True, verify_level="none")


def test_loader_rejects_missing_parts():
    with tempfile.TemporaryDirectory() as tmp_dir:
        d = Path(tmp_dir)
        bad = {
            "kind": "repolens.pr_schau.bundle",
            "version": "1.0",
            "meta": {"repo": "x", "generated_at": "2023-01-01T00:00:00Z", "generator": {"name": "x"}},
            "completeness": {"is_complete": True, "policy": "split", "parts": ["review.md"], "primary_part": "review.md"},
            "artifacts": [{"role": "canonical_md", "basename": "review.md", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "mime": "text/markdown"}],
        }
        (d / "bundle.json").write_text(json.dumps(bad), encoding="utf-8")

        with pytest.raises(PRSchauBundleError):
            load_pr_schau_bundle(d, verify_level="basic")
