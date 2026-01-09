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

    content_full = artifacts_full.canonical_md.read_text(encoding="utf-8")

    # Should NOT have Meta-Density header if full (default)
    assert "MD5: abc" in content_full

def test_file_meta_safety_in_min_mode(tmp_path):
    """
    Test that meta=min hides file_meta for full files,
    but SHOWS it for truncated/omitted files (Safety Rule).
    """
    root = tmp_path / "repo"
    root.mkdir()
    f1 = root / "large.py"
    # Create large content
    f1.write_text("print('hello')\n" * 1000, encoding="utf-8")

    fi = FileInfo(
        root_label="repo",
        abs_path=f1,
        rel_path=Path("large.py"),
        size=15000,
        is_text=True,
        md5="abc",
        category="source",
        tags=[],
        ext=".py",
        content=None,
        inclusion_reason="normal"
    )

    merges_dir = tmp_path / "merges"
    merges_dir.mkdir()

    # Simulate truncation via max_bytes
    # Note: Currently logic sets status="full" if size <= max_bytes, else "omitted" or "truncated" if logic exists.
    # determine_inclusion_status logic:
    # if level==dev: source->full.
    # But max_bytes check: if size <= max_file_bytes -> full, else omitted?
    # Wait, the logic is: return "full" if fi.size <= max_file_bytes else "omitted"
    # To get "truncated", we might need to rely on `read_smart_content` (which doesn't truncate anymore in v2.3+).
    # However, the gating rule uses `status != "full"`.
    # Let's force status to be "omitted" or "meta-only" by using a small max_bytes.

    # Actually, we want to test "partial/truncated".
    # If determine_inclusion_status returns "omitted", the file block is skipped entirely?
    # Yes: "if status in ('omitted', 'meta-only'): continue" loop in `iter_report_blocks`.

    # So `file_meta` is only relevant if the file BLOCK is rendered.
    # The file block is rendered if status is "full" or "truncated".
    # In v2.4 logic, "truncated" is rare/disabled.
    # But let's check "meta-only" -> skipped.

    # Wait, if I want to verify the safety rule "file_meta mandatory if not full",
    # I need a case where the file IS included but NOT full.
    # Is there such a case?
    # "truncated" status is commented out in `iter_report_blocks`?
    # "Explicitly removed: automatic downgrade..."

    # So currently files are either full or omitted/meta-only.
    # If they are meta-only, they don't get a file block in Content.
    # They appear in Manifest.

    # So where does `file_meta` appear? Inside the file block in Content.
    # If the file block is skipped, `file_meta` is moot.

    # Conclusion: The safety rule applies if we *re-enable* truncation or have a "partial" status that renders a block.
    # If we manually force status to 'truncated' for the test, we can verify the gate.

    # Direct Unit Test of iter_report_blocks
    # We bypass scanning logic and provide manually constructed FileInfos
    # to simulate a "truncated" file.

    # Manually constructed file list
    files = [fi]
    # sources is List[Path]
    sources = [root]

    # We need to monkeypatch `read_smart_content` or `determine_inclusion_status`?
    # Actually, `iter_report_blocks` calls `determine_inclusion_status`.
    # And we want status="truncated".

    # Let's monkeypatch determine_inclusion_status to force 'truncated' for this file
    original_determine = merge.determine_inclusion_status
    def mock_determine(f, l, m):
        if f.rel_path.name == "large.py":
            return "truncated"
        return original_determine(f, l, m)

    merge.determine_inclusion_status = mock_determine

    try:
        # Run generator
        blocks = list(merge.iter_report_blocks(
            files=files,
            level="dev",
            max_file_bytes=100,
            sources=sources,
            plan_only=False,
            meta_density="min" # Requested minimal density
        ))

        full_text = "".join(blocks)

        # In 'min' mode, full files have NO file_meta.
        # But this file is 'truncated', so it MUST have file_meta.
        assert "file_meta:" in full_text
        assert "included: truncated" in full_text

    finally:
        # Restore
        merge.determine_inclusion_status = original_determine
