import unittest
import os
from pathlib import Path
import sys

sys.path.append(os.path.abspath("merger"))

from lenskit.adapters.security import resolve_secure_path, resolve_relative_path, resolve_any_path, get_security_config

class TestSecurityPaths(unittest.TestCase):
    def setUp(self):
        self.root = Path("/tmp/mock_root").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        # Reset config and configure security for absolute path testing
        config = get_security_config()
        config.allowlist_roots = [self.root]

    def test_resolve_secure_path(self):
        # Valid relative
        res = resolve_secure_path(self.root, "subdir/file.txt")
        self.assertEqual(res, self.root / "subdir/file.txt")

        # Invalid: Absolute
        with self.assertRaises(ValueError):
            resolve_secure_path(self.root, "/etc/passwd")

        # Invalid: Traversal
        with self.assertRaises(ValueError):
            resolve_secure_path(self.root, "../outside")

    def test_resolve_relative_path_strictness(self):
        from fastapi import HTTPException

        # Valid
        res = resolve_relative_path(self.root, "ok.txt")
        self.assertEqual(res, self.root / "ok.txt")

        # Invalid: Absolute should be forbidden in strictly relative context
        try:
            resolve_relative_path(self.root, str(self.root / "file.txt"))
            self.fail("Absolute path passed resolve_relative_path")
        except HTTPException as e:
            self.assertEqual(e.status_code, 403)
        except ValueError:
             # Should be caught inside
             self.fail("ValueError leaked")

    def test_resolve_any_path(self):
        # 1. Absolute allowed
        abs_p = self.root / "allowed.txt"
        res = resolve_any_path(self.root, str(abs_p))
        self.assertEqual(res, abs_p)

        # 2. Absolute denied (outside root)
        with self.assertRaises(Exception): # HTTPException 403 from validate_path
             resolve_any_path(self.root, "/etc/passwd")

        # 3. Relative allowed
        res = resolve_any_path(self.root, "rel.txt")
        self.assertEqual(res, self.root / "rel.txt")

if __name__ == '__main__':
    unittest.main()
