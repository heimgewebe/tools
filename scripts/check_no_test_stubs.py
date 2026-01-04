#!/usr/bin/env python3
import sys
import importlib.util
from pathlib import Path

def check_no_test_stubs():
    """
    Guards against the re-introduction of 'tests/stubs' directory which
    caused shadowing of real packages (fastapi, pydantic, starlette).
    """
    repo_root = Path(__file__).parent.parent

    # Check specifically for tests/stubs
    stubs_dir = repo_root / "merger" / "lenskit" / "tests" / "stubs"
    if stubs_dir.exists():
        print(f"ERROR: Forbidden directory found: {stubs_dir}")
        print("FAIL: We have decided to abolish extensive stubs in favor of real dependencies.")
        print("Please remove this directory to prevent import shadowing.")
        sys.exit(1)

    print("OK: No forbidden 'tests/stubs' directory found.")
    sys.exit(0)

if __name__ == "__main__":
    check_no_test_stubs()
