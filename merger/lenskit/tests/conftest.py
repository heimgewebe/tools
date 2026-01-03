
import os
import sys
from pathlib import Path

STUBS_PATH = Path(__file__).parent / "stubs"
# Allow opting out of stubs when real dependencies are installed
def _running_under_pytest() -> bool:
    if os.getenv("PYTEST_CURRENT_TEST") is not None:
        return True

    if "pytest" in sys.modules:
        return True

    if any("pytest" in Path(arg).stem for arg in sys.argv):
        return True

    try:
        import pytest  # type: ignore  # local import to avoid hard dependency
    except ImportError:
        return False

    # Final defensive check: pytest imported successfully, so assume test context
    return True


if os.getenv("RLENS_TEST_STUBS", "1") == "1" and _running_under_pytest():
    # Ensure test stubs shadow external deps only for pytest runs
    sys.path.insert(0, str(STUBS_PATH))

import pytest
import shutil
import tempfile
from fastapi.testclient import TestClient

# Canonical imports only - strict environment check
from merger.lenskit.service.app import app, init_service, state, SnapshotLogStreamProvider

@pytest.fixture
def service_client():
    # Setup
    temp_dir = tempfile.mkdtemp()
    hub_path = Path(temp_dir) / "hub"
    hub_path.mkdir()
    merges_dir = hub_path / "merges"
    merges_dir.mkdir()

    # Create a dummy repo for scanning
    (hub_path / "repo-test").mkdir()
    (hub_path / "repo-test" / "README.md").write_text("Test Content")

    token = "test-token-123"

    # Initialize service with explicit token and merges_dir
    init_service(hub_path, token=token, merges_dir=merges_dir, log_stream_provider=SnapshotLogStreamProvider())

    client = TestClient(app)
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Expose useful objects
    class Context:
        def __init__(self):
            self.client = client
            self.headers = auth_headers
            self.store = state.job_store
            self.hub_path = hub_path
            self.merges_dir = merges_dir
            self.runner = state.runner

    ctx = Context()

    yield ctx

    # Teardown
    shutil.rmtree(temp_dir, ignore_errors=True)
