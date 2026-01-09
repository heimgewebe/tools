
import pytest
from pathlib import Path
from merger.lenskit.core import merge

def test_iter_report_blocks_first_block_contains_report_title(tmp_path):
    """Ensure the first block yielded by iter_report_blocks contains the report title."""
    # Setup dummy source and file
    dummy_source = tmp_path / "repo"
    dummy_source.mkdir()
    dummy_file = dummy_source / "file.txt"
    dummy_file.write_text("content", encoding="utf-8")

    # Setup mock FileInfo
    fi = merge.FileInfo(
        root_label="repo",
        abs_path=dummy_file,
        rel_path=Path("file.txt"),
        size=10,
        is_text=True,
        md5="abc",
        category="source",
        tags=[],
        ext=".txt"
    )

    # Call iter_report_blocks
    iterator = merge.iter_report_blocks(
        files=[fi],
        level="max",
        max_file_bytes=0,
        sources=[dummy_source],
        plan_only=False
    )

    # Get the first block
    first_block = next(iterator)

    # Check for title
    assert "# repoLens Report" in first_block

def test_write_reports_v2_single_file_enforces_part_1_1_header(tmp_path):
    """Ensure write_reports_v2 in single-file mode enforces 'Part 1/1' header."""
    # Setup
    merges_dir = tmp_path / "merges"
    merges_dir.mkdir()
    hub = tmp_path / "hub"
    hub.mkdir()

    repo_dir = hub / "test-repo"
    repo_dir.mkdir()

    # Dummy file info
    # Use a dummy path that exists if possible, though plan_only bypasses reading
    dummy_abs = repo_dir / "README.md"
    # We don't necessarily need to create it for plan_only, but for robustness:
    dummy_abs.touch()

    fi = merge.FileInfo(
        root_label="test-repo",
        abs_path=dummy_abs,
        rel_path=Path("README.md"),
        size=100,
        is_text=True,
        md5="123",
        category="doc",
        tags=[],
        ext=".md"
    )

    repo_summary = {
        "name": "test-repo",
        "root": repo_dir,
        "files": [fi]
    }

    artifacts = merge.write_reports_v2(
        merges_dir=merges_dir,
        hub=hub,
        repo_summaries=[repo_summary],
        detail="summary",
        mode="single",
        max_bytes=0,
        plan_only=True,
        split_size=0, # Single file mode
        path_filter=None
    )

    # Find the markdown file
    md_path = artifacts.canonical_md
    assert md_path is not None
    assert md_path.exists()

    content = md_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Look for the header line
    header_found = False
    for line in lines:
        if line.strip() == "# repoLens Report (Part 1/1)":
            header_found = True
            break

    assert header_found, f"Header '# repoLens Report (Part 1/1)' not found in:\n{content[:500]}"
