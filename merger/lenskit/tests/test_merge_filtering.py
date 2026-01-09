
import pytest
from pathlib import Path
from merger.lenskit.core import merge
from merger.lenskit.core.merge import FileInfo

def create_file_info(rel_path, category="other", tags=None, content="content"):
    return FileInfo(
        root_label="test-repo",
        abs_path=Path("/tmp") / rel_path,
        rel_path=Path(rel_path),
        size=len(content),
        is_text=True,
        md5="md5sum",
        category=category,
        tags=tags or [],
        ext=Path(rel_path).suffix,
        content=content,
        inclusion_reason="normal"
    )

def test_path_filter_hard_include():
    """
    Task A: path_filter matches explicitly. Critical files (README) must be excluded
    if they don't match the filter.
    """
    files = [
        create_file_info("docs/adr/001-decision.md", category="doc", tags=["adr"]),
        create_file_info("README.md", category="doc", tags=["ai-context"]), # Critical file
        create_file_info(".github/workflows/main.yml", category="config", tags=["ci"]), # Critical
    ]

    # Simulate force_include logic from scan_repo (usually handled there, but we test the iter logic here)
    # The iter_report_blocks receives the list *after* scan_repo.
    # scan_repo includes critical files even if filter doesn't match.
    # So we pass them all in, and expect iter_report_blocks to filter them OUT.

    gen = merge.iter_report_blocks(
        files=files,
        level="max",
        max_file_bytes=0,
        sources=[Path("/tmp/test-repo")],
        plan_only=False,
        path_filter="docs/adr",
        meta_density="standard"
    )
    report = "".join(gen)

    assert "docs/adr/001-decision.md" in report
    # README.md is mentioned in "Reading Plan", so we check for Manifest/Content specific markers
    # We use the generated anchor (file-test-repo-readme-md) to verify exclusion
    # because the static header mentions "README.md".
    # Note: anchor format uses "file-<repo>-<path>" slugified.
    assert "file-test-repo-readme-md" not in report
    assert ".github/workflows/main.yml" not in report
    assert "001-decision.md" in report # Content should be there

def test_meta_density_min_no_hotspots_anywhere():
    """
    Task B: meta_density='min' must disable Hotspots in Plan and Reading Lenses.
    """
    files = [
        # main.py in src/ will get 'entrypoint' role automatically via compute_file_roles
        # if filename matches heuristics (main.py matches).
        create_file_info("src/main.py", category="source", tags=["entrypoint"]),
        create_file_info("docs/readme.md", category="doc"),
    ]

    gen = merge.iter_report_blocks(
        files=files,
        level="max",
        max_file_bytes=0,
        sources=[Path("/tmp/test-repo")],
        plan_only=False,
        meta_density="min"
    )
    report = "".join(gen)

    assert "Hotspots (Einstiegspunkte)" not in report
    assert "Reading Lenses" not in report
    # "## 📄 Content" is not strictly required to check here (layout fragile),
    # but confirming the report isn't empty is good.
    assert "file-test-repo-src-main-py" in report

def test_hotspots_present_in_standard():
    """
    Control test: Hotspots should be present in standard/full.
    """
    files = [
        create_file_info("src/main.py", category="source", tags=["entrypoint"]),
    ]

    gen = merge.iter_report_blocks(
        files=files,
        level="max",
        max_file_bytes=0,
        sources=[Path("/tmp/test-repo")],
        plan_only=False,
        meta_density="standard"
    )
    report = "".join(gen)

    assert "Hotspots (Einstiegspunkte)" in report

def test_auto_warning_only_on_actual_auto_downgrade():
    """
    Task C:
    1. auto + filter -> warning
    2. standard + filter -> NO warning
    """
    files = [create_file_info("test.txt")]

    # Case 1: Auto + Filter -> Warning
    gen1 = merge.iter_report_blocks(
        files=files, level="max", max_file_bytes=0, sources=[], plan_only=False,
        path_filter="test", meta_density="auto"
    )
    report1 = "".join(gen1)
    assert "⚠️ **Auto-Drosselung:**" in report1

    # Case 2: Standard + Filter -> No Warning
    gen2 = merge.iter_report_blocks(
        files=files, level="max", max_file_bytes=0, sources=[], plan_only=False,
        path_filter="test", meta_density="standard"
    )
    report2 = "".join(gen2)
    assert "⚠️ **Auto-Drosselung:**" not in report2
