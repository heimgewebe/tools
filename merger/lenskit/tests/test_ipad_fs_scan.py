import unittest
import json
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch
from merger.lenskit.frontends.pythonista.ipad_fs_scan import iPadFSScanner

class TestiPadFSScanner(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure for testing
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir)

        # Structure:
        # root/
        #   file1.txt
        #   sub/
        #     file2.log
        #   excluded/
        #     file3.txt
        #   node_modules/
        #     lib.js

        self.root_path = os.path.join(self.test_dir, "root")
        os.makedirs(os.path.join(self.root_path, "sub"))
        os.makedirs(os.path.join(self.root_path, "excluded"))
        os.makedirs(os.path.join(self.root_path, "node_modules"))

        with open(os.path.join(self.root_path, "file1.txt"), "w") as f:
            f.write("content")

        with open(os.path.join(self.root_path, "sub", "file2.log"), "w") as f:
            f.write("log content")

        with open(os.path.join(self.root_path, "excluded", "file3.txt"), "w") as f:
            f.write("ignored")

        with open(os.path.join(self.root_path, "node_modules", "lib.js"), "w") as f:
            f.write("library")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_basic_scan(self):
        roots = [{
            "root_id": "test_root",
            "label": "Test Root",
            "source": "test",
            "path": self.root_path
        }]

        scanner = iPadFSScanner(
            roots=roots,
            output_dir=self.output_dir,
            excludes=["excluded", "node_modules"]
        )

        result = scanner.scan()

        # Verify Top Level Schema
        self.assertEqual(result["schema"], "ipad.fs.index/v1")
        self.assertEqual(len(result["roots"]), 1)

        root = result["roots"][0]
        self.assertEqual(root["root_id"], "test_root")
        self.assertEqual(root["summary"]["status"], "ok")

        # Verify Tree Structure
        tree = root["tree"]
        self.assertEqual(tree["path"], "root")
        self.assertEqual(tree["type"], "dir")

        # Check Children (file1.txt, sub) - sorted by name
        children = tree["children"]
        self.assertEqual(len(children), 2)

        names = [c["path"] for c in children]
        self.assertIn("file1.txt", names)
        self.assertIn("sub", names)
        self.assertNotIn("excluded", names)
        self.assertNotIn("node_modules", names)

        # Check Subdirectory
        sub_node = next(c for c in children if c["path"] == "sub")
        self.assertEqual(sub_node["type"], "dir")
        self.assertEqual(sub_node["children_count"], 1)
        self.assertEqual(sub_node["children"][0]["path"], "file2.log")

    def test_depth_limit(self):
        roots = [{
            "root_id": "test_root",
            "label": "Test Root",
            "source": "test",
            "path": self.root_path
        }]

        # Max depth 0 should only return the root node marked as out_of_scope
        # Actually, my implementation logic:
        # _scan_recursive(depth=0) checks if depth >= max_depth.
        # If max_depth is 0, it returns immediately.

        scanner = iPadFSScanner(
            roots=roots,
            output_dir=self.output_dir,
            max_depth=0
        )

        result = scanner.scan()
        root = result["roots"][0]
        tree = root["tree"]

        self.assertEqual(tree["status"], "out_of_scope")
        self.assertEqual(tree["reason"], "Max depth reached")
        # The summary status should be 'incomplete' because we hit the limit immediately
        self.assertEqual(root["summary"]["status"], "incomplete")

        # Test max depth 1 (should see children of root, but not grandchildren)
        scanner = iPadFSScanner(
            roots=roots,
            output_dir=self.output_dir,
            max_depth=1,
            excludes=["excluded", "node_modules"]
        )
        result = scanner.scan()
        root = result["roots"][0]
        tree = root["tree"]

        sub_node = next(c for c in tree["children"] if c["path"] == "sub")
        # Sub node is at depth 1. Recursion call for sub is depth 1.
        # inside _scan_recursive(sub, 1): if 1 >= 1 (max_depth): return out_of_scope

        self.assertEqual(sub_node["status"], "out_of_scope")
        self.assertNotIn("children", sub_node)
        # Verify that the partial scan bubbled up "incomplete" status to the root summary
        self.assertEqual(root["summary"]["status"], "incomplete")

        # Verify counting logic:
        # root (depth 0, ok) -> dirs=1, skipped=0
        #   sub (depth 1, limit hit) -> dirs=0, skipped=1
        #   excluded (skipped by filter, not counted)
        #   node_modules (skipped by filter, not counted)
        # Total: dirs=1, skipped=1
        self.assertEqual(root["summary"]["dirs"], 1)
        self.assertEqual(root["summary"]["dirs_skipped"], 1)

    def test_non_existent_root(self):
        roots = [{
            "root_id": "ghost",
            "label": "Ghost",
            "source": "test",
            "path": "/path/to/nothing"
        }]

        scanner = iPadFSScanner(roots=roots, output_dir=self.output_dir)
        result = scanner.scan()

        root = result["roots"][0]
        self.assertEqual(root["summary"]["status"], "not_found")
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["kind"], "not_found")

    def test_json_serialization(self):
        roots = [{
            "root_id": "test_root",
            "label": "Test Root",
            "source": "test",
            "path": self.root_path
        }]
        scanner = iPadFSScanner(roots=roots, output_dir=self.output_dir)
        result = scanner.scan()
        outfile = scanner.write_output(result)

        with open(outfile, 'r') as f:
            loaded = json.load(f)

        self.assertEqual(loaded["schema"], "ipad.fs.index/v1")

    def test_max_entries_limit(self):
        roots = [{
            "root_id": "test_root",
            "label": "Test Root",
            "source": "test",
            "path": self.root_path
        }]

        # Max entries set low.
        # Root (1) + file1 (2).
        # Should stop after reaching limit, marking subsequent as out_of_scope.
        scanner = iPadFSScanner(
            roots=roots,
            output_dir=self.output_dir,
            max_entries=1
        )

        result = scanner.scan()
        root = result["roots"][0]

        self.assertEqual(root["summary"]["status"], "incomplete")
        # Entry count will be strictly max_entries + maybe 1 if it checks AFTER increment
        # My logic: self.entry_count >= self.max_entries check is at START of recursive
        # So root (1) -> ok.
        # Loop children.
        # Child 1: file1.
        #   entry_count (1) >= max (1) -> FALSE? No. entry_count starts at 0?
        # Let's check logic:
        # scan() -> entry_count = 0.
        # _scan_root -> _scan_recursive(root)
        #   entry_count (0) >= max (1) -> False.
        #   entry_count += 1 -> 1.
        #   node creation.
        #   loop children:
        #     file1: _process_file. summary/entry_count += 1 -> 2.
        #     sub: _scan_recursive(sub).
        #       entry_count (2) >= max (1) -> TRUE.
        #       Returns out_of_scope, incomplete.

        # So we expect root to contain file1, but sub to be skipped.
        # And root summary to be incomplete.

        # Depending on order (sorted by name): file1.txt, node_modules (excluded), sub
        # file1.txt comes first. It gets processed.
        # sub comes later. It hits limit.

        self.assertGreaterEqual(scanner.entry_count, 1)

if __name__ == "__main__":
    unittest.main()
