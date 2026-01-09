import unittest
import json
import os
import shutil
import tempfile
import unicodedata
from unittest.mock import patch, MagicMock
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
        #   ._test.txt  (AppleDouble noise)

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

        # Create AppleDouble noise file
        with open(os.path.join(self.root_path, "._test.txt"), "w") as f:
            f.write("resource fork")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_basic_scan(self):
        roots = [{
            "root_id": "test_root",
            "label": "Test Root",
            "source": "test",
            "path": self.root_path
        }]

        # Uses default excludes which should now include ._*
        scanner = iPadFSScanner(
            roots=roots,
            output_dir=self.output_dir,
            excludes=["excluded", "node_modules", "._*"]
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

        # Verify Root Relpath Determinism
        self.assertEqual(tree.get("relpath"), "")
        self.assertEqual(tree.get("segments"), [])

        # Check Children (file1.txt, sub) - sorted by name
        children = tree["children"]
        # Expected: file1.txt, sub.
        # Excluded: excluded, node_modules, ._test.txt
        names = [c["path"] for c in children]
        self.assertIn("file1.txt", names)
        self.assertIn("sub", names)
        self.assertNotIn("excluded", names)
        self.assertNotIn("node_modules", names)
        self.assertNotIn("._test.txt", names)

        # Check that os_name is preserved
        file1_node = next(c for c in children if c["path"] == "file1.txt")
        self.assertEqual(file1_node["os_name"], "file1.txt")

        # Check Subdirectory
        sub_node = next(c for c in children if c["path"] == "sub")
        self.assertEqual(sub_node["type"], "dir")
        self.assertEqual(sub_node["relpath"], "sub")
        self.assertEqual(sub_node["segments"], ["sub"])

        self.assertEqual(sub_node["children_count"], 1)
        file2_node = sub_node["children"][0]
        self.assertEqual(file2_node["path"], "file2.log")
        self.assertEqual(file2_node["relpath"], "sub/file2.log")
        self.assertEqual(file2_node["segments"], ["sub", "file2.log"])

    def test_depth_limit(self):
        roots = [{
            "root_id": "test_root",
            "label": "Test Root",
            "source": "test",
            "path": self.root_path
        }]

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
        self.assertEqual(root["summary"]["status"], "incomplete")

        # Test max depth 1
        scanner = iPadFSScanner(
            roots=roots,
            output_dir=self.output_dir,
            max_depth=1,
            excludes=["excluded", "node_modules", "._*"]
        )
        result = scanner.scan()
        root = result["roots"][0]
        tree = root["tree"]

        sub_node = next(c for c in tree["children"] if c["path"] == "sub")
        self.assertEqual(sub_node["status"], "out_of_scope")
        self.assertNotIn("children", sub_node)
        self.assertEqual(root["summary"]["status"], "incomplete")

        self.assertEqual(root["summary"]["dirs"], 1)
        self.assertEqual(root["summary"]["dirs_skipped"], 1)

    def test_unicode_normalization(self):
        # Create a file with NFD name
        nfd_name = unicodedata.normalize("NFD", "u\u0308ber.txt") # ü broken down
        nfc_name = unicodedata.normalize("NFC", "u\u0308ber.txt") # ü combined

        file_path = os.path.join(self.root_path, nfd_name)
        with open(file_path, "w") as f:
            f.write("unicode test")

        roots = [{
            "root_id": "test_root",
            "label": "Test Root",
            "source": "test",
            "path": self.root_path
        }]

        scanner = iPadFSScanner(
            roots=roots,
            output_dir=self.output_dir,
            excludes=["excluded", "node_modules", "._*"]
        )

        result = scanner.scan()
        tree = result["roots"][0]["tree"]

        # Find the unicode file
        # The scanner normalizes to NFC, so we should find NFC name
        children_paths = [c["path"] for c in tree["children"]]

        if nfd_name != nfc_name:
            # If the FS supports distinct NFD/NFC, or if we can write NFD,
            # we expect the output to be NFC.
            self.assertIn(nfc_name, children_paths)

            # Check segments
            file_node = next(c for c in tree["children"] if c["path"] == nfc_name)
            self.assertEqual(file_node["path"], nfc_name)
            self.assertEqual(file_node["segments"], [nfc_name])

            # relpath check
            self.assertEqual(file_node["relpath"], nfc_name)
        else:
            # If system auto-normalizes on creation (like some macOS/iOS versions),
            # then just verify we see the file.
            self.assertIn(nfc_name, children_paths)

    def test_collision_handling(self):
        """
        Simulate a directory containing two files that normalize to the same NFC string.
        """
        roots = [{
            "root_id": "test_root",
            "label": "Test Root",
            "source": "test",
            "path": self.root_path
        }]

        scanner = iPadFSScanner(
            roots=roots,
            output_dir=self.output_dir
        )

        # We need two strings that normalize to the same NFC but are different.
        # Example: 'Å' (U+00C5) and 'A' + combining ring (U+0041 U+030A)
        name1 = "\u00C5"       # NFC form
        name2 = "A\u030A"      # NFD form

        # Mocking os.scandir to return entries for these two names
        # We don't need real files on disk because we mock scandir.

        # Create mock entries
        mock_entry1 = MagicMock()
        mock_entry1.name = name1
        mock_entry1.is_file.return_value = True
        mock_entry1.is_dir.return_value = False
        mock_entry1.stat.return_value.st_size = 100
        mock_entry1.stat.return_value.st_mtime = 1234567890

        mock_entry2 = MagicMock()
        mock_entry2.name = name2
        mock_entry2.is_file.return_value = True
        mock_entry2.is_dir.return_value = False
        mock_entry2.stat.return_value.st_size = 200
        mock_entry2.stat.return_value.st_mtime = 1234567890

        # We need to mock os.scandir only for the specific path, but it's recursive.
        # Easier to mock it globally for this test block.

        # The recursion calls _scan_recursive(root_path).
        # We want the root to contain these two files.

        with patch('os.scandir') as mock_scandir:
            # os.scandir returns an iterator
            mock_scandir.return_value.__enter__.return_value = iter([mock_entry1, mock_entry2])

            # Since we mock scandir for root, we don't need real files.
            # But the scanner checks root existence first in _scan_root.
            # Real root exists (setUp), so that passes.

            result = scanner.scan()

            tree = result["roots"][0]["tree"]
            children = tree["children"]

            # Expect 2 children
            self.assertEqual(len(children), 2)

            # Both should have normalized path "Å" (\u00C5)
            normalized_target = unicodedata.normalize("NFC", name1)

            node1 = children[0]
            node2 = children[1]

            self.assertEqual(node1["path"], normalized_target)
            self.assertEqual(node2["path"], normalized_target)

            # One should be name1, one name2 (sorting order might vary depending on impl)
            # The scanner sorts by normalized name. They are equal. So original sort order or stable sort applies.
            # Let's check that both OS names are present.
            os_names = [c["os_name"] for c in children]
            self.assertIn(name1, os_names)
            self.assertIn(name2, os_names)

            # Check collision markers
            self.assertTrue(node1.get("collision"))
            self.assertTrue(node2.get("collision"))
            self.assertEqual(node1["collision_key"], normalized_target)

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

        scanner = iPadFSScanner(
            roots=roots,
            output_dir=self.output_dir,
            max_entries=1
        )

        result = scanner.scan()
        root = result["roots"][0]

        self.assertEqual(root["summary"]["status"], "incomplete")
        self.assertGreaterEqual(scanner.entry_count, 1)

if __name__ == "__main__":
    unittest.main()
