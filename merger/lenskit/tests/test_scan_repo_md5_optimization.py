import pytest
from unittest.mock import patch
from pathlib import Path
from merger.lenskit.core.merge import scan_repo

def test_scan_repo_skips_threadpool_when_calculate_md5_false(tmp_path):
    """
    Regression Test:
    Ensures that when calculate_md5=False, the expensive ThreadPoolExecutor
    is not even initialized, proving the optimization is active.
    """
    # Setup: Create a dummy file so scan_repo has something to do
    (tmp_path / "file.txt").write_text("content")

    # Patch ThreadPoolExecutor where scan_repo uses it
    # scan_repo imports concurrent.futures directly
    with patch("merger.lenskit.core.merge.concurrent.futures.ThreadPoolExecutor") as mock_executor:
        scan_repo(tmp_path, calculate_md5=False)

        # Assertion: Executor should NOT be initialized
        mock_executor.assert_not_called()

def test_scan_repo_uses_threadpool_when_calculate_md5_true(tmp_path):
    """
    Control Test:
    Ensures that when calculate_md5=True (default), the ThreadPoolExecutor
    is initialized and used for hashing.
    """
    # Setup: Create a dummy file so scan_repo has something to do
    (tmp_path / "file.txt").write_text("content")

    # Patch ThreadPoolExecutor
    with patch("merger.lenskit.core.merge.concurrent.futures.ThreadPoolExecutor") as mock_executor:
        # We need the context manager to return a mock that has a map method
        mock_instance = mock_executor.return_value
        mock_instance.__enter__.return_value = mock_instance

        # Mock map to return iterator of results (md5 strings).
        # Note: map is called with paths and limits. The number of files is 1.
        mock_instance.map.return_value = ["dummy_md5"]

        result = scan_repo(tmp_path, calculate_md5=True)

        # Assertion: Executor SHOULD be initialized
        mock_executor.assert_called()

        # Also verify MD5 was set (indirectly proving usage and correct mapping)
        assert len(result["files"]) == 1
        assert result["files"][0].md5 == "dummy_md5"
