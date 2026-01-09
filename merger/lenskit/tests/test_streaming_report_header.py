
import pytest
from pathlib import Path
from merger.lenskit.core import merge

def create_dummy_file_info(tmp_path, name="file.txt", content="content"):
    """Robust helper to create a FileInfo with a real file backing it."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(exist_ok=True)
    fpath = repo_dir / name
    fpath.write_text(content, encoding="utf-8")

    # Instantiate FileInfo with all fields matching current signature
    return merge.FileInfo(
        root_label="repo",
        abs_path=fpath,
        rel_path=Path(name),
        size=len(content.encode('utf-8')),
        is_text=True,
        md5="abc", # Dummy MD5
        category="source",
        tags=[],
        ext=fpath.suffix,
        skipped=False,
        reason=None,
        content=None,
        inclusion_reason="normal"
    ), repo_dir

def test_iter_report_blocks_first_block_contains_report_title(tmp_path):
    """Ensure the first block yielded by iter_report_blocks contains the report title."""
    fi, repo_dir = create_dummy_file_info(tmp_path)

    # Call iter_report_blocks with explicit keyword arguments matching signature
    iterator = merge.iter_report_blocks(
        files=[fi],
        level="max",
        max_file_bytes=0,
        sources=[repo_dir],
        plan_only=False
    )

    # Get the first block
    first_block = next(iterator)

    # Check for title
    assert "# repoLens Report" in first_block

def test_write_reports_v2_single_file_enforces_part_1_1_header(tmp_path):
    """Ensure write_reports_v2 in single-file mode enforces 'Part 1/1' header."""
    # Setup directories
    merges_dir = tmp_path / "merges"
    merges_dir.mkdir()
    hub = tmp_path / "hub"
    hub.mkdir()

    repo_dir = hub / "test-repo"
    repo_dir.mkdir()

    # Create dummy file info using helper
    fi, _ = create_dummy_file_info(tmp_path, name="README.md", content="# Hi")

    repo_summary = {
        "name": "test-repo",
        "root": repo_dir,
        "files": [fi]
    }

    # We use plan_only=True to focus on header generation
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
