import json
import pytest
from pathlib import Path
from merger.lenskit.adapters.atlas import AtlasScanner

def test_atlas_inventory_includes_all_titles(tmp_path):
    # Setup: Create folder structure
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file1.txt").write_text("content", encoding="utf-8")
    # Use a binary file with null byte to ensure detection works
    (tmp_path / "subdir" / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
    (tmp_path / "root.md").write_text("# Root", encoding="utf-8")

    # .git should be excluded by default
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x", encoding="utf-8")

    inventory_file = tmp_path / "atlas.inventory.jsonl"

    scanner = AtlasScanner(tmp_path, inventory_strict=False)
    scanner.scan(inventory_file=inventory_file)

    assert inventory_file.exists()

    lines = inventory_file.read_text(encoding="utf-8").strip().splitlines()
    items = [json.loads(line) for line in lines]

    paths = {item["rel_path"] for item in items}

    # Check inclusions
    assert "subdir/file1.txt" in paths
    assert "subdir/image.png" in paths
    assert "root.md" in paths

    # Check exclusions
    assert ".git/config" not in paths

    # Check fields
    file1 = next(i for i in items if i["rel_path"] == "subdir/file1.txt")
    assert file1["name"] == "file1.txt"
    assert file1["ext"] == ".txt"
    assert file1["is_text"] is True
    assert "size_bytes" in file1
    assert "mtime" in file1

    img = next(i for i in items if i["rel_path"] == "subdir/image.png")
    assert img["is_text"] is False

def test_atlas_inventory_strict_mode(tmp_path):
    # Test strict mode (minimal excludes)
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.json").write_text("{}", encoding="utf-8")

    inventory_file = tmp_path / "atlas.inventory_strict.jsonl"

    # With inventory_strict=True, node_modules should be included
    # (Default strict excludes are only .git and .venv)
    scanner = AtlasScanner(tmp_path, inventory_strict=True)
    scanner.scan(inventory_file=inventory_file)

    lines = inventory_file.read_text(encoding="utf-8").strip().splitlines()
    items = [json.loads(line) for line in lines]
    paths = {item["rel_path"] for item in items}

    assert "node_modules/pkg.json" in paths
