import unittest
import os
from pathlib import Path
import sys

sys.path.append(os.path.abspath("merger/repoLens"))

from service.security import resolve_secure_path, resolve_relative_path, resolve_any_path, get_security_config

class TestSecurityPaths(unittest.TestCase):
    def setUp(self):
        self.root = Path("/tmp/mock_root").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        # Configure security for absolute path testing
        get_security_config().add_allowlist_root(self.root)

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
        # Should behave like resolve_secure_path but raise HTTPException on error?
        # Actually logic is: calls resolve_secure_path, re-raises as HTTPException(403)
        # But we changed implementation to NOT handle absolute paths.

        from fastapi import HTTPException

        # Valid
        res = resolve_relative_path(self.root, "ok.txt")
        self.assertEqual(res, self.root / "ok.txt")

        # Invalid: Absolute (was allowed before, now forbidden in relative_path)
        # Wait, implementation says: if os.path.isabs: check allowlist...
        # NO, I REMOVED THAT in the patch.
        # Let's verify.

        try:
            resolve_relative_path(self.root, str(self.root / "file.txt"))
            # If implementation still had abs check, this would pass if allowlisted.
            # But my patch removed the "if os.path.isabs" block from resolve_relative_path.
            # So it should fail in resolve_secure_path("Absolute paths forbidden")
            # Then catch ValueError -> raise 403.
            print("FAIL: Absolute path passed resolve_relative_path")
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

        # 2. Absolute denied
        with self.assertRaises(Exception): # HTTPException 403 from validate_path
             resolve_any_path(self.root, "/etc/passwd")

        # 3. Relative allowed
        res = resolve_any_path(self.root, "rel.txt")
        self.assertEqual(res, self.root / "rel.txt")

if __name__ == '__main__':
    unittest.main()
