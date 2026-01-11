import unittest
from merger.lenskit.frontends.pythonista.repolens_helpers import resolve_pool_include_paths

class TestiPadPoolResilience(unittest.TestCase):

    def test_resolve_pool_include_paths_basic(self):
        pool = {
            "repo1": {"compressed": ["file1.txt"], "raw": ["file1.txt"]}
        }
        # Normal case
        self.assertEqual(resolve_pool_include_paths(pool, "repo1"), ["file1.txt"])

        # Missing repo
        self.assertIsNone(resolve_pool_include_paths(pool, "missing"))

        # ALL state (None)
        pool["repo_all"] = {"compressed": None, "raw": None}
        self.assertIsNone(resolve_pool_include_paths(pool, "repo_all"))

    def test_resolve_pool_include_paths_block_vs_fallback(self):
        # 1. Explicit Block (empty list, no flag)
        pool_block = {
            "repo_block": {
                "compressed": [],
                "raw": ["something"], # Raw might linger but no flag set
                "_sanitized_dropped": False
            }
        }
        # Should return empty list (Block)
        self.assertEqual(resolve_pool_include_paths(pool_block, "repo_block"), [])

        # 2. Corruption/Sanitization Fallback
        pool_fallback = {
            "repo_corrupt": {
                "compressed": [], # Empty due to drop?
                "raw": ["valid.txt", 123], # Contains valid and invalid
                "_sanitized_dropped": True # Flag set!
            }
        }
        # Should return filtered raw
        result = resolve_pool_include_paths(pool_fallback, "repo_corrupt")
        self.assertEqual(result, ["valid.txt"])

        # 3. Fallback but raw is empty too
        pool_empty_raw = {
            "repo_empty": {
                "compressed": [],
                "raw": [],
                "_sanitized_dropped": True
            }
        }
        # Should remain blocked
        self.assertEqual(resolve_pool_include_paths(pool_empty_raw, "repo_empty"), [])

    def test_resolve_pool_normalization(self):
        # normalize_repo_id doesn't handle -/_ swapping or complex normalization beyond basic path/case
        # It handles: strip, \, ./, trailing /, basename, lower

        # Case 1: Simple case drift
        pool = {
            "repo_norm": {"compressed": ["foo/"], "raw": ["foo/"]}
        }
        self.assertEqual(resolve_pool_include_paths(pool, "Repo_Norm"), ["foo/"])
        self.assertEqual(resolve_pool_include_paths(pool, "./repo_norm/"), ["foo/"])

if __name__ == '__main__':
    unittest.main()
