import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

# Add the service directory to sys.path
sys.path.append(os.path.abspath("merger/repoLens"))

from service.app import api_sync_metarepo
from service.app import state

# Mock state
state.hub = Path("mock_hub")

# Mock sync_from_metarepo to return error
with patch("service.app.sync_from_metarepo") as mock_sync:
    mock_sync.return_value = {"status": "error", "message": "Manifest invalid"}

    print("Testing error case...")
    try:
        api_sync_metarepo({"mode": "dry_run"})
        print("FAIL: Should have raised HTTPException")
    except HTTPException as e:
        if e.status_code == 500 and "Manifest invalid" in e.detail:
            print("PASS: Caught expected 500 error")
        else:
            print(f"FAIL: Unexpected error code or detail: {e.status_code} {e.detail}")

# Mock sync_from_metarepo to return ok
with patch("service.app.sync_from_metarepo") as mock_sync:
    mock_sync.return_value = {"status": "ok", "summary": {}}

    print("Testing success case...")
    try:
        resp = api_sync_metarepo({"mode": "dry_run"})
        if resp["status"] == "ok":
            print("PASS: Success response received")
        else:
            print("FAIL: Status not ok")
    except Exception as e:
        print(f"FAIL: Raised exception on success: {e}")
