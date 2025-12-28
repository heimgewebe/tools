import json
import shutil
import tempfile
import pytest
import subprocess
import sys
from pathlib import Path
from merger.lenskit.core.extractor import generate_review_bundle

# Path to the verifier script
VERIFIER_SCRIPT = Path(__file__).parents[1] / "cli" / "pr_schau_verify.py"

def test_pr_schau_verify_tool():
    """
    Test that the pr-schau-verify CLI tool correctly validates a generated bundle.
    """
    if not VERIFIER_SCRIPT.exists():
        pytest.skip(f"Verifier script not found at {VERIFIER_SCRIPT}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        hub_dir = tmp_path / "hub"
        hub_dir.mkdir()

        # Create dummy repos
        old_repo = tmp_path / "old_repo"
        old_repo.mkdir()
        (old_repo / "README.md").write_text("Old Content")

        new_repo = tmp_path / "new_repo"
        new_repo.mkdir()
        (new_repo / "README.md").write_text("New Content")
        (new_repo / "extra.md").write_text("Extra Content")

        repo_name = "verify-test-repo"

        # 1. Generate a valid bundle
        generate_review_bundle(old_repo, new_repo, repo_name, hub_dir)

        pr_schau_dir = hub_dir / ".repolens" / "pr-schau" / repo_name
        assert pr_schau_dir.exists()
        bundle_dir = list(pr_schau_dir.iterdir())[0]
        bundle_json = bundle_dir / "bundle.json"

        # 2. Run Verifier (Basic)
        cmd_basic = [sys.executable, str(VERIFIER_SCRIPT), str(bundle_json), "--level", "basic"]
        result_basic = subprocess.run(cmd_basic, capture_output=True, text=True)
        print("Basic Output:", result_basic.stdout)
        print("Basic Error:", result_basic.stderr)
        assert result_basic.returncode == 0, "Basic verification failed"

        # 3. Run Verifier (Full)
        cmd_full = [sys.executable, str(VERIFIER_SCRIPT), str(bundle_json), "--level", "full"]
        result_full = subprocess.run(cmd_full, capture_output=True, text=True)
        print("Full Output:", result_full.stdout)
        print("Full Error:", result_full.stderr)
        assert result_full.returncode == 0, "Full verification failed"

        # 4. Tamper with the bundle (invalidate hash)
        review_md = bundle_dir / "review.md"
        original_content = review_md.read_text()
        review_md.write_text(original_content + "\nTAMPERED")

        cmd_tamper = [sys.executable, str(VERIFIER_SCRIPT), str(bundle_json), "--level", "full"]
        result_tamper = subprocess.run(cmd_tamper, capture_output=True, text=True)
        assert result_tamper.returncode != 0, "Verifier should fail on tampered content"
        assert "SHA256 mismatch" in result_tamper.stderr or "SHA256 mismatch" in result_tamper.stdout

        # 5. Tamper with truncation (add forbidden text)
        # Restore content first to fix hash mismatch (though hash check runs before guard, so order matters)
        # We'll fix the hash in bundle.json to match the new tampered content, but include the forbidden string
        review_md.write_text("This Content truncated at 100 chars.")
        # Update hash in json to pass hash check, so we hit the Guard check
        import hashlib
        new_sha = hashlib.sha256(review_md.read_bytes()).hexdigest()

        with open(bundle_json, "r") as f:
            data = json.load(f)

        for art in data["artifacts"]:
            if art["basename"] == "review.md":
                art["sha256"] = new_sha

        with open(bundle_json, "w") as f:
            json.dump(data, f)

        cmd_guard = [sys.executable, str(VERIFIER_SCRIPT), str(bundle_json), "--level", "full"]
        result_guard = subprocess.run(cmd_guard, capture_output=True, text=True)

        # Note: The verifier logic:
        # verify_full calls checks sequentially.
        # It checks hashes first.
        # Then "No-Truncate" guard.
        # "content truncated at" (lowercase) matches "content truncated at" in my text.

        assert result_guard.returncode != 0, "Verifier should fail on forbidden truncation text"
        assert "Found truncation marker" in result_guard.stderr

if __name__ == "__main__":
    pytest.main([__file__])
