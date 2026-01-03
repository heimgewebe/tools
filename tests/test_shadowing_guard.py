import os
import subprocess
import sys
from pathlib import Path


def test_no_shadowing_script_passes():
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "check_no_shadowing.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_no_shadowing_script_fails_on_forbidden(tmp_path):
    forbidden = tmp_path / "fastapi"
    forbidden.mkdir()

    script = Path(__file__).resolve().parents[1] / "scripts" / "check_no_shadowing.py"
    env = {**os.environ, "RLENS_ROOT": str(tmp_path)}
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, env=env)

    assert result.returncode == 1
    assert "fastapi" in (result.stderr or "")
