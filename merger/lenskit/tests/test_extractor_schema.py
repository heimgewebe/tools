import json
import shutil
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timezone
from merger.lenskit.core.extractor import generate_review_bundle, _compute_sha256

# Path to the schema file
SCHEMA_PATH = Path(__file__).parents[1] / "contracts" / "pr-schau.v1.schema.json"

@pytest.fixture
def schema():
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

def test_generate_review_bundle_output_schema(schema):
    """
    Test that generate_review_bundle produces a bundle.json that complies with pr-schau.v1.schema.json.
    """
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        hub_dir = tmp_path / "hub"
        hub_dir.mkdir()

        # Create dummy old and new repos
        old_repo = tmp_path / "old_repo"
        old_repo.mkdir()
        (old_repo / "file1.txt").write_text("content1")

        new_repo = tmp_path / "new_repo"
        new_repo.mkdir()
        (new_repo / "file1.txt").write_text("content1_modified")
        (new_repo / "file2.txt").write_text("content2")

        repo_name = "test-repo"

        # Run generator
        generate_review_bundle(old_repo, new_repo, repo_name, hub_dir)

        # Check output structure
        pr_schau_dir = hub_dir / ".repolens" / "pr-schau" / repo_name
        assert pr_schau_dir.exists()

        # Find the timestamp folder (should be only one)
        ts_folders = list(pr_schau_dir.iterdir())
        assert len(ts_folders) == 1
        bundle_dir = ts_folders[0]

        bundle_json_path = bundle_dir / "bundle.json"
        assert bundle_json_path.exists()

        with open(bundle_json_path, "r") as f:
            bundle_data = json.load(f)

        # Validate against schema
        jsonschema.validate(instance=bundle_data, schema=schema)

        # Additional checks for values
        assert bundle_data["kind"] == "repolens.pr_schau.bundle"
        assert bundle_data["version"] == "1.0"
        assert bundle_data["meta"]["repo"] == repo_name
        assert bundle_data["completeness"]["is_complete"] is True
        assert bundle_data["completeness"]["primary_part"] == "review.md"
        assert "review.md" in bundle_data["completeness"]["parts"]

        # Verify SHA256 matches
        artifacts = bundle_data["artifacts"]
        review_md_artifact = next(a for a in artifacts if a["role"] == "canonical_md")
        expected_sha = _compute_sha256(bundle_dir / "review.md")
        assert review_md_artifact["sha256"] == expected_sha

if __name__ == "__main__":
    pytest.main([__file__])
