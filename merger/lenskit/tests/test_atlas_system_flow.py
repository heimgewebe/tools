import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from merger.lenskit.service.app import app, init_service, state

client = TestClient(app)

@pytest.fixture
def mock_state():
    # Setup mock state
    mock_hub = Path("/tmp/mock_hub")
    mock_hub.mkdir(parents=True, exist_ok=True)
    mock_merges = Path("/tmp/mock_merges")
    mock_merges.mkdir(parents=True, exist_ok=True)

    init_service(hub_path=mock_hub, merges_dir=mock_merges)

    # Mock Security Config
    with patch("merger.lenskit.service.app.get_security_config") as mock_get_sec:
        mock_sec_instance = MagicMock()
        mock_sec_instance.validate_path.side_effect = lambda p: p # Pass through
        mock_get_sec.return_value = mock_sec_instance

        yield state

    # Cleanup
    import shutil
    shutil.rmtree(mock_hub, ignore_errors=True)
    shutil.rmtree(mock_merges, ignore_errors=True)

def test_atlas_system_root_mapping(mock_state):
    """
    Verify that root_id="system" maps to Path.home() in the application logic.
    Note: This tests the mapping logic. The actual path security policy is mocked here
    to focus on the 'system' keyword handling.
    """
    # We need to bypass the actual AtlasScanner execution since it scans real files
    with patch("merger.lenskit.service.app.AtlasScanner") as MockScanner:
        with patch("merger.lenskit.service.app.render_atlas_md") as mock_render:
            mock_instance = MockScanner.return_value
            mock_instance.scan.return_value = {"root": str(Path.home()), "tree": {}}
            mock_render.return_value = "Mock MD"

            payload = {
                "root_id": "system",
                "max_depth": 1,
                "max_entries": 100
            }

            response = client.post("/api/atlas", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["id"].startswith("atlas-")

            # The API returns the RESOLVED path in root_scanned
            # We expect it to be user home
            expected_home = str(Path.home().resolve())
            assert data["root_scanned"] == expected_home

def test_atlas_missing_root_400(mock_state):
    """
    Verify that missing both root_id and root_token returns 400
    """
    payload = {
        "max_depth": 1
    }

    response = client.post("/api/atlas", json=payload)
    assert response.status_code == 400
    assert "Missing Atlas root" in response.json()["detail"]

def test_atlas_invalid_root_id(mock_state):
    """
    Verify that invalid root_id returns 400
    """
    payload = {
        "root_id": "invalid_root",
        "max_depth": 1
    }

    response = client.post("/api/atlas", json=payload)
    assert response.status_code == 400
    assert "Invalid Atlas root_id" in response.json()["detail"]
