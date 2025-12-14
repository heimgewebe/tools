# -*- coding: utf-8 -*-
import unittest
from pathlib import Path
import sys

# Ensure imports work
sys.path.append(str(Path(__file__).resolve().parent))

from core import build_merge_filename, safe_relpath, FileInfo, write_reports_v2, ExtrasConfig, scan_repo

class TestPortability(unittest.TestCase):

    def test_no_root_in_filename(self):
        """PATCH 2: Verify 'root' placeholder is stripped from filename."""
        name = build_merge_filename(
            repo_block="root", # Should be ignored
            mode="gesamt",
            detail="dev",
            filters=[],
            timestamp="TS"
        )
        self.assertNotIn("root", name)
        self.assertEqual(name, "gesamt-dev-TS_merge.md")

        name2 = build_merge_filename(
            repo_block="myrepo",
            mode="gesamt",
            detail="dev",
            filters=["docs"],
            timestamp="TS"
        )
        self.assertEqual(name2, "myrepo-gesamt-docs-dev-TS_merge.md")

    def test_safe_relpath(self):
        """PATCH 3: Verify path sanitization."""
        # Valid cases
        self.assertEqual(safe_relpath("src/main.py"), Path("src/main.py"))

        # Absolute path
        with self.assertRaises(ValueError):
            safe_relpath("/etc/passwd")

        # Traversal
        with self.assertRaises(ValueError):
            safe_relpath("../secret.txt")

        # Null byte
        with self.assertRaises(ValueError):
            safe_relpath("image.png\x00.exe")

    def test_deterministic_filename_parts(self):
        """PATCH 2: Verify filename structure."""
        name = build_merge_filename(
            repo_block="repo",
            mode="mode",
            detail="detail",
            filters=["filter1", "filter2"],
            timestamp="2023",
            part=(1, 3)
        )
        # Expected: repo-mode-filter1-filter2-detail-2023_part1of3_merge.md
        expected = "repo-mode-filter1-filter2-detail-2023_part1of3_merge.md"
        self.assertEqual(name, expected)

if __name__ == '__main__':
    unittest.main()
