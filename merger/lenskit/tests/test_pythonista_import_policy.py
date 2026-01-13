import pytest
from pathlib import Path
import re
import os

# Define the target directory relative to this test file
# Location: merger/lenskit/tests/test_pythonista_import_policy.py
# Target:   merger/lenskit/frontends/pythonista/
PYTHONISTA_DIR = Path(__file__).resolve().parents[2] / "lenskit" / "frontends" / "pythonista"

# Regex to find "from ." or "from .xyz"
# We strictly forbid relative imports to ensure Pythonista compatibility
RELATIVE_IMPORT_PATTERN = re.compile(r"^\s*from\s+\.", re.MULTILINE)

def test_pythonista_has_no_relative_imports():
    """
    Enforces the 'Option 1' Architecture Policy:
    Files in 'frontends/pythonista' must use absolute imports (flat layout),
    relying on sys.path manipulation in the entry point rather than relative package imports.
    """
    if not PYTHONISTA_DIR.exists():
        pytest.skip(f"Pythonista directory not found at {PYTHONISTA_DIR}")

    offenders = []

    # Scan all .py files in the directory
    for p in PYTHONISTA_DIR.glob("*.py"):
        # Skip __init__.py as it might legitimately use relative imports in a package context,
        # though in this specific 'flat script' architecture, even that is discouraged.
        # For now, we enforce it on everything to be strict.

        try:
            content = p.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not read {p}: {e}")
            continue

        if RELATIVE_IMPORT_PATTERN.search(content):
            offenders.append(p.name)

    assert not offenders, (
        f"Relative imports found in Pythonista frontend files: {offenders}. "
        "Policy: Use absolute imports (e.g. 'from repolens_utils import ...') and "
        "ensure sys.path is set correctly in entry points."
    )
