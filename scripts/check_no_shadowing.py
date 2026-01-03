#!/usr/bin/env python3
import sys
import importlib.util
from pathlib import Path

def check_no_shadowing():
    # Modules that must NOT be shadowed by local files
    FORBIDDEN = ["fastapi", "pydantic", "starlette", "yaml", "httpx"]

    repo_root = Path(__file__).parent.parent

    # Check specifically for tests/stubs
    stubs_dir = repo_root / "merger" / "lenskit" / "tests" / "stubs"
    if stubs_dir.exists():
        print(f"ERROR: Shadowing directory found: {stubs_dir}")
        print("We have decided to abolish extensive stubs. Please delete this directory.")
        sys.exit(1)

    print("OK: No known shadowing stubs found.")
    sys.exit(0)

if __name__ == "__main__":
    check_no_shadowing()
