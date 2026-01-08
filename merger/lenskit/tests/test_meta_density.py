import pytest
from pathlib import Path
from merger.lenskit.core import merge
from merger.lenskit.core.merge import FileInfo, ExtrasConfig

def test_meta_density_min_counts(tmp_path):
    """
    Test that meta_density='min' suppresses file headers and file_meta blocks.
    Counts blocks to ensure 'zero' visibility.
    """
    root = tmp_path / "repo"
    root.mkdir()
    f1 = root / "script.py"
    f1.write_text("print('hello')", encoding="utf-8")

    fi = FileInfo(
        root_label="repo",
        abs_path=f1,
        rel_path=Path("script.py"),
        size=100,
        is_text=True,
        md5="abc",
        category="source",
        tags=["script"],
        ext=".py",
        content=None,
        inclusion_reason="normal"
    )

    merges_dir = tmp_path / "merges"
    merges_dir.mkdir()

    artifacts = merge.write_reports_v2(
        merges_dir=merges_dir,
        hub=tmp_path,
        repo_summaries=[{"name": "repo", "files": [fi], "root": root}],
        detail="dev",
        mode="single",
        max_bytes=1000,
        plan_only=False,
        meta_density="min"
    )

    content = artifacts.canonical_md.read_text(encoding="utf-8")

    # Check that per-file headers are minimal (only path)
    assert "**Path:** `script.py`" in content
    assert "Category: source" not in content

    # Block counting: file_meta should appear 0 times
    assert content.count("file_meta:") == 0

    # Check for Index reduction note
    assert "_Index reduced (meta=min)_" in content

def test_meta_density_full_counts(tmp_path):
    """
    Test that meta_density='full' shows everything.
    """
    root = tmp_path / "repo"
    root.mkdir()
    f1 = root / "script.py"
    f1.write_text("print('hello')", encoding="utf-8")

    fi = FileInfo(
        root_label="repo",
        abs_path=f1,
        rel_path=Path("script.py"),
        size=100,
        is_text=True,
        md5="abc",
        category="source",
        tags=["script"],
        ext=".py",
        content=None,
        inclusion_reason="normal"
    )

    merges_dir = tmp_path / "merges"
    merges_dir.mkdir()

    artifacts = merge.write_reports_v2(
        merges_dir=merges_dir,
        hub=tmp_path,
        repo_summaries=[{"name": "repo", "files": [fi], "root": root}],
        detail="dev",
        mode="single",
        max_bytes=1000,
        plan_only=False,
        meta_density="full"
    )

    content = artifacts.canonical_md.read_text(encoding="utf-8")

    assert "**Path:** `script.py`" in content
    assert "Category: source" in content
    assert "MD5: abc" in content

    # file_meta should appear exactly once
    assert content.count("file_meta:") == 1

def test_meta_density_standard_counts(tmp_path):
    """
    Test meta_density='standard':
    - file_meta should be 0 for full files.
    """
    root = tmp_path / "repo"
    root.mkdir()
    f1 = root / "script.py"
    f1.write_text("print('hello')", encoding="utf-8")

    fi = FileInfo(
        root_label="repo",
        abs_path=f1,
        rel_path=Path("script.py"),
        size=100,
        is_text=True,
        md5="abc",
        category="source",
        tags=["script"],
        ext=".py",
        content=None,
        inclusion_reason="normal"
    )

    merges_dir = tmp_path / "merges"
    merges_dir.mkdir()

    artifacts = merge.write_reports_v2(
        merges_dir=merges_dir,
        hub=tmp_path,
        repo_summaries=[{"name": "repo", "files": [fi], "root": root}],
        detail="dev",
        mode="single",
        max_bytes=1000, # Fits fully
        plan_only=False,
        meta_density="standard"
    )

    content = artifacts.canonical_md.read_text(encoding="utf-8")

    assert "**Path:** `script.py`" in content
    assert "Category: source" in content
    assert "MD5: abc" not in content

    # file_meta should be hidden because file is fully included
    assert content.count("file_meta:") == 0

def test_auto_throttling_trigger(tmp_path):
    """
    Test that meta_density='auto' triggers 'standard' behavior when filters are active.
    """
    root = tmp_path / "repo"
    root.mkdir()
    f1 = root / "script.py"
    f1.write_text("print('hello')", encoding="utf-8")

    fi = FileInfo(
        root_label="repo",
        abs_path=f1,
        rel_path=Path("script.py"),
        size=100,
        is_text=True,
        md5="abc",
        category="source",
        tags=["script"],
        ext=".py",
        content=None,
        inclusion_reason="normal"
    )

    merges_dir = tmp_path / "merges"
    merges_dir.mkdir()

    # Case 1: Auto with filters -> Standard behavior (no MD5, no file_meta for full)
    artifacts = merge.write_reports_v2(
        merges_dir=merges_dir,
        hub=tmp_path,
        repo_summaries=[{"name": "repo", "files": [fi], "root": root}],
        detail="dev",
        mode="single",
        max_bytes=1000,
        plan_only=False,
        path_filter="script", # Filter active
        meta_density="auto"
    )

    content = artifacts.canonical_md.read_text(encoding="utf-8")
    assert "**Meta-Density:** `standard`" in content # Resolved value
    assert "Auto-Drosselung" in content
    assert "MD5: abc" not in content # Standard behavior

    # Case 2: Auto without filters -> Full behavior
    artifacts_full = merge.write_reports_v2(
        merges_dir=merges_dir,
        hub=tmp_path,
        repo_summaries=[{"name": "repo", "files": [fi], "root": root}],
        detail="dev",
        mode="single",
        max_bytes=1000,
        plan_only=False,
        meta_density="auto" # No filters
    )

    # Note: write_reports_v2 appends to list, so we get a new file.
    # But since we use deterministic naming and didn't change enough params to change the run_id except maybe...
    # run_id depends on path_filter. So filename will differ.

    # We need to find the correct file. write_reports_v2 returns the artifact object.
    content_full = artifacts_full.canonical_md.read_text(encoding="utf-8")

    # Should NOT have Meta-Density header if full (default)
    # The implementation:
    # if meta_density != "full": header.append(...)
    # If auto resolves to full, is meta_density variable updated to "full" in the scope?
    # In iter_report_blocks: if meta_density == "auto": ... meta_density = "full"
    # So yes, it should behave like full.

    assert "MD5: abc" in content_full
