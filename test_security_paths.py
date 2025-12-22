import unittest
import os
from pathlib import Path
import sys

# Adjust path to root so we can import 'merger' package
sys.path.append(os.path.abspath("."))

from merger.lenskit.core.path_security import resolve_secure_path
from merger.lenskit.adapters.security import resolve_any_path, get_security_config
from fastapi import HTTPException

class TestSecurityPaths(unittest.TestCase):
    def setUp(self):
        self.root = Path("/tmp/mock_root").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        # Reset config and configure security for absolute path testing
        config = get_security_config()
        config.allowlist_roots = [self.root]

    def test_resolve_secure_path(self):
        # Valid relative
        # Note: resolve_secure_path resolves the path.
        res = resolve_secure_path(self.root, "subdir/file.txt")
        self.assertEqual(res, self.root / "subdir/file.txt")

        # Invalid: Absolute
        with self.assertRaises(ValueError):
            resolve_secure_path(self.root, "/etc/passwd")

        # Invalid: Traversal
        with self.assertRaises(ValueError):
            resolve_secure_path(self.root, "../outside")

    def test_resolve_any_path(self):
        # 1. Absolute allowed
        abs_p = self.root / "allowed.txt"

        res = resolve_any_path(self.root, str(abs_p))
        self.assertEqual(res, abs_p)

        # 2. Absolute denied (outside root)
        with self.assertRaises(HTTPException) as cm:
             resolve_any_path(self.root, "/etc/passwd")
        self.assertEqual(cm.exception.status_code, 403)

        # 3. Relative allowed
        res = resolve_any_path(self.root, "rel.txt")
        self.assertEqual(res, self.root / "rel.txt")

if __name__ == '__main__':
    unittest.main()
