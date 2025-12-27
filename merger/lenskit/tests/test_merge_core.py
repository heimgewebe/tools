# -*- coding: utf-8 -*-
import unittest
import sys
import os
from pathlib import Path

# Add merger/ to sys.path so lenskit is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lenskit.core.merge import (
    _slug_token,
    classify_file_v2,
    _generate_run_id,
    determine_inclusion_status,
    iter_report_blocks,
    FileInfo,
    DEBUG_CONFIG
)

class TestMergeCore(unittest.TestCase):

    def test_slug_token(self):
        self.assertEqual(_slug_token("Foo Bar"), "foo-bar")
        self.assertEqual(_slug_token("path/to/file.txt"), "path-to-file-txt")
        self.assertEqual(_slug_token("UPPERCASE"), "uppercase")
        self.assertEqual(_slug_token("mixed_CASE/123"), "mixed-case-123")

    def test_classify_file_v2(self):
        # Category: Source
        cat, tags = classify_file_v2(Path("src/main.py"), ".py")
        self.assertEqual(cat, "source")
        self.assertNotIn("script", tags)

        # Category: Config
        cat, tags = classify_file_v2(Path("package.json"), ".json")
        self.assertEqual(cat, "config")

        # Category: Doc
        cat, tags = classify_file_v2(Path("README.md"), ".md")
        self.assertEqual(cat, "doc")
        self.assertIn("ai-context", tags) # readme.md is strictly tagged as ai-context

        # Tag: CI
        cat, tags = classify_file_v2(Path(".github/workflows/test.yml"), ".yml")
        self.assertEqual(cat, "config")
        self.assertIn("ci", tags)

        # Tag: Script
        cat, tags = classify_file_v2(Path("scripts/deploy.sh"), ".sh")
        self.assertEqual(cat, "source")
        self.assertIn("script", tags)

    def test_generate_run_id(self):
        # Basic determinism
        rid1 = _generate_run_id(["repo1"], "dev", None, None, timestamp="250101-1200")
        rid2 = _generate_run_id(["repo1"], "dev", None, None, timestamp="250101-1200")
        self.assertEqual(rid1, rid2)
        self.assertIn("repo1", rid1)
        self.assertIn("dev", rid1)
        self.assertIn("250101-1200", rid1)

        # Multi-repo
        rid_multi = _generate_run_id(["repo1", "repo2"], "max", None, None, timestamp="250101-1200")
        self.assertIn("multi-", rid_multi)
        self.assertIn("max", rid_multi)

    def test_determine_inclusion_status(self):
        # Mock FileInfo
        fi = FileInfo(
            root_label="root",
            abs_path=Path("fake"),
            rel_path=Path("fake"),
            size=100,
            is_text=True,
            md5="abc",
            category="source",
            tags=[],
            ext=".py"
        )

        # Max profile -> full
        self.assertEqual(determine_inclusion_status(fi, "max", 0), "full")

        # Dev profile, source file -> full
        self.assertEqual(determine_inclusion_status(fi, "dev", 0), "full")

        # Dev profile, other file -> meta-only
        fi.category = "other"
        self.assertEqual(determine_inclusion_status(fi, "dev", 0), "meta-only")

        # Size limit (0 means unlimited)
        fi.size = 20000000
        self.assertEqual(determine_inclusion_status(fi, "max", 0), "full")

        # Binary file
        fi.is_text = False
        self.assertEqual(determine_inclusion_status(fi, "max", 0), "omitted")

    def test_unbound_local_error_regression(self):
        """
        Regression test for UnboundLocalError when text_files_count > 0.
        Ensures content_present/manifest_present/structure_present are always defined.
        """
        fi = FileInfo(
            root_label="test_repo",
            abs_path=Path("/tmp/test.txt"),
            rel_path=Path("test.txt"),
            size=100,
            is_text=True,
            md5="abc",
            category="source",
            tags=[],
            ext=".txt",
            content="hello",
            inclusion_reason="normal"
        )

        # We need at least one text file to trigger the else-branch avoidance in legacy code
        files = [fi]
        # sources expects List[Path] according to signature
        sources = [Path("/tmp/test_repo")]

        # Should not raise UnboundLocalError
        # Consume iterator to verify no crash
        # We catch UnboundLocalError specifically to fail with clarity,
        # but unittest will catch it anyway.
        iterator = iter_report_blocks(
            files=files,
            level="dev",
            max_file_bytes=1000,
            sources=sources,
            plan_only=False,
            debug=False
        )
        try:
            # Consume only until @meta:end to avoid FS access (or full iteration)
            for block in iterator:
                if "@meta:end" in block:
                    break
        except UnboundLocalError:
            self.fail("iter_report_blocks raised UnboundLocalError! Fix is likely inactive or broken.")

if __name__ == '__main__':
    unittest.main()
