import pytest
from pathlib import Path
from merger.lenskit.adapters.atlas import AtlasScanner

def test_atlas_merge_single_folder(tmp_path):
    target_dir = tmp_path / "myfolder"
    target_dir.mkdir()

    (target_dir / "a.txt").write_text("Content A", encoding="utf-8")
    (target_dir / "b.md").write_text("Content B", encoding="utf-8")
    (target_dir / "c.bin").write_bytes(b"\x00\x01\x02") # Binary
    (target_dir / "sub").mkdir() # Subdir should be ignored
    (target_dir / "sub" / "d.txt").write_text("Content D", encoding="utf-8")

    output_file = tmp_path / "merged.txt"

    scanner = AtlasScanner(tmp_path)
    result = scanner.merge_folder("myfolder", output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")

    # Check structure
    assert "===== FILE: myfolder/a.txt =====" in content
    assert "Content A" in content
    assert "===== FILE: myfolder/b.md =====" in content
    assert "Content B" in content

    # Check binary skip
    assert "===== SKIPPED FILES =====" in content
    assert "myfolder/c.bin (binary/non-text)" in content

    # Check non-recursive (subdir ignored)
    assert "myfolder/sub/d.txt" not in content

    # Result dict
    assert "myfolder/a.txt" in result["merged"]
    assert "myfolder/b.md" in result["merged"]
    assert "myfolder/c.bin" not in [x['path'] for x in result["merged"] if isinstance(x, dict)]
    # merged is list of strings (paths)
    assert "myfolder/c.bin" not in result["merged"]
