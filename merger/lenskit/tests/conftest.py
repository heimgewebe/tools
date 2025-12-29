
import pytest
import shutil
import tempfile
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

# Adjust imports based on your project structure
try:
    from merger.lenskit.service.app import app, init_service, state
    from merger.lenskit.service.models import JobRequest
except ImportError:
    # Fallback if running from a different root
    from lenskit.service.app import app, init_service, state
    from lenskit.service.models import JobRequest

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
    init_service(hub_path, token=token, merges_dir=merges_dir)

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
