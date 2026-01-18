import pytest
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import app logic
from merger.lenskit.service.app import app, init_service, state, download_artifact
from merger.lenskit.service.models import JobRequest, Artifact
from merger.lenskit.adapters.security import get_security_config

client = TestClient(app)

@pytest.fixture
def secure_env(tmp_path):
    """
    Sets up a secure environment with:
    - hub_dir (allowed)
    - allowed_merges (allowed)
    - forbidden_dir (NOT allowed)
    """
    hub = tmp_path / "hub"
    hub.mkdir()

    allowed_merges = tmp_path / "allowed_merges"
    allowed_merges.mkdir()

    forbidden = tmp_path / "forbidden"
    forbidden.mkdir()
    (forbidden / "secret.md").write_text("SECRET DATA")

    # Initialize service, allowlisting ONLY hub and allowed_merges
    # forbidden is NOT included
    init_service(hub_path=hub, merges_dir=allowed_merges)

    # Return context
    return {
        "hub": hub,
        "allowed": allowed_merges,
        "forbidden": forbidden
    }

def test_download_custom_merges_dir_success(secure_env):
    """
    Test that downloading from an allowed custom merges_dir works.
    """
    # Create file in allowed dir
    target_file = secure_env["allowed"] / "report.md"
    target_file.write_text("Valid Content")

    # Mock Artifact with custom merges_dir
    req = JobRequest(repos=["r1"], merges_dir=str(secure_env["allowed"]))
    art = Artifact(
        id="art-ok",
        job_id="job-ok",
        hub=str(secure_env["hub"]),
        repos=["r1"],
        created_at="2023-01-01T00:00:00",
        paths={"md": target_file.name},
        params=req
    )
    state.job_store.add_artifact(art)

    # Act
    # We call the function directly to test logic, as TestClient might complicate FileResponse handling
    # (though TestClient handles it, direct call is more unit-test-like for this specific logic)
    response = download_artifact(id="art-ok")

    # Assert
    assert str(response.path) == str(target_file)

def test_download_custom_merges_dir_forbidden(secure_env):
    """
    Test that a custom merges_dir pointing to a forbidden directory raises 403.
    """
    # Mock Artifact with FORBIDDEN merges_dir
    # Note: The Artifact itself is just metadata. The attack is setting params.merges_dir to somewhere else.
    req = JobRequest(repos=["r1"], merges_dir=str(secure_env["forbidden"]))
    art = Artifact(
        id="art-bad",
        job_id="job-bad",
        hub=str(secure_env["hub"]),
        repos=["r1"],
        created_at="2023-01-01T00:00:00",
        paths={"md": "secret.md"},
        params=req
    )
    state.job_store.add_artifact(art)

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        download_artifact(id="art-bad")

    assert exc.value.status_code == 403
    assert "Access denied" in exc.value.detail

def test_download_symlink_bypass_blocked(secure_env):
    """
    Test that a symlink INSIDE an allowed directory pointing OUTSIDE is blocked (403).
    """
    # Create symlink: allowed/link.md -> forbidden/secret.md
    link_path = secure_env["allowed"] / "link.md"
    target_path = secure_env["forbidden"] / "secret.md"

    try:
        link_path.symlink_to(target_path)
    except OSError:
        pytest.skip("Symlinks not supported on this platform")

    # Mock Artifact: points to valid dir, but file is a symlink
    req = JobRequest(repos=["r1"], merges_dir=str(secure_env["allowed"]))
    art = Artifact(
        id="art-link",
        job_id="job-link",
        hub=str(secure_env["hub"]),
        repos=["r1"],
        created_at="2023-01-01T00:00:00",
        paths={"md": link_path.name},
        params=req
    )
    state.job_store.add_artifact(art)

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        download_artifact(id="art-link")

    # Should be 403 because validate_path resolves the symlink and sees it's in forbidden root
    assert exc.value.status_code == 403
    assert "Access denied" in exc.value.detail
