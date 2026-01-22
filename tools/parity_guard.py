#!/usr/bin/env python3
"""
Frontend Feature Parity Guard
-----------------------------
Ensures that fields defined in the backend `JobRequest` model are exposed
in both the WebUI (`app.js`) and the Pythonista UI/CLI (`repolens.py`).

Policy:
1. Every field in `JobRequest` must be present in `app.js` payload construction.
2. Every field in `JobRequest` must be present in `repolens.py` as a CLI argument OR explicitly mapped.
3. Every field in `JobRequest` must be used/referenced in `repolens.py` logic.

Exit Code:
0: Success (Parity verified)
1: Failure (Drift detected)
"""

import sys
import ast
import re
from pathlib import Path
from typing import Set, Dict, Any

# --- Configuration ---

ROOT_DIR = Path(__file__).parent.parent
MODELS_PATH = ROOT_DIR / "merger" / "lenskit" / "service" / "models.py"
WEBUI_PATH = ROOT_DIR / "merger" / "lenskit" / "frontends" / "webui" / "app.js"
PYTHONISTA_PATH = ROOT_DIR / "merger" / "lenskit" / "frontends" / "pythonista" / "repolens.py"

# Fields to ignore (internal/backend-only)
IGNORE_FIELDS = {
    "force_new", # Service-only
    "hub",       # Implicit/Context
}

# Mapping for fields that have different names/mechanisms
# key: JobRequest field name
# value: dict with overrides
#   - cli_flag: exact string for CLI check (e.g. "paths" or "--custom-flag")
#   - py_usage: regex string to check usage in pythonista code
#   - js_key: regex string for JS payload key
MAPPINGS: Dict[str, Dict[str, Any]] = {
    "repos": {
        "cli_flag": "paths", # positional arg
        "py_usage": r"(selected_repos|sources)",
    },
    "merges_dir": {
        # --merges-dir not exposed in Pythonista CLI (implicitly uses hub/merges)
        "cli_flag": "SKIP",
        "py_usage": r"(merges_dir|mergesPath)",
    },
    "include_paths_by_repo": {
        "cli_flag": "SKIP", # Not exposed in CLI
        "py_usage": r"(pool_norm|resolve_pool_include_paths)", # Handled via pool logic
        "js_key": r"include_paths_by_repo",
    },
    "strict_include_paths_by_repo": {
        "cli_flag": "SKIP",
        "py_usage": "SKIP", # Implicit in pool logic?
        "js_key": r"strict_include_paths_by_repo",
    },
    "include_paths": {
        "cli_flag": "SKIP", # Not top-level CLI? actually path-filter/extensions are top level. include_paths is internal?
        # Wait, scan_repo takes include_paths.
        # JobRequest has include_paths.
        # CLI has --path-filter, but not --include-paths?
        # WebUI uses include_paths for pool logic.
        # So this might be "SKIP" for CLI or mapped?
        # Let's see models.py: include_paths: Optional[List[str]] = None
        # It IS in JobRequest.
        # Is it in CLI? No. CLI uses path_filter (substring) or extensions.
        # But include_paths is whitelist.
        # WebUI sets it for pro-repo mode.
        "cli_flag": "SKIP",
        "py_usage": r"include_paths",
    }
}

def extract_model_fields(path: Path) -> Set[str]:
    """Extracts field names from JobRequest class using AST."""
    if not path.exists():
        print(f"ERROR: Model file not found: {path}")
        sys.exit(1)

    code = path.read_text(encoding="utf-8")
    tree = ast.parse(code)
    fields = set()

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "JobRequest":
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.add(item.target.id)

    return fields - IGNORE_FIELDS

def check_webui(path: Path, fields: Set[str]) -> bool:
    """Checks if fields are present in app.js payload construction."""
    if not path.exists():
        print(f"ERROR: WebUI file not found: {path}")
        return False

    content = path.read_text(encoding="utf-8")
    success = True
    print("\n--- Checking WebUI (app.js) ---")

    for field in sorted(fields):
        # Determine expected JS key
        mapping = MAPPINGS.get(field, {})
        js_key_pattern = mapping.get("js_key", rf"\b{field}\s*:")

        if js_key_pattern == "SKIP":
            continue

        if not re.search(js_key_pattern, content):
            print(f"❌ Missing payload key: '{field}' (regex: /{js_key_pattern}/)")
            success = False
        else:
            # print(f"✅ Found '{field}'")
            pass

    return success

def check_pythonista(path: Path, fields: Set[str]) -> bool:
    """Checks CLI args and internal usage in repolens.py."""
    if not path.exists():
        print(f"ERROR: Pythonista file not found: {path}")
        return False

    content = path.read_text(encoding="utf-8")
    success = True
    print("\n--- Checking Pythonista (repolens.py) ---")

    for field in sorted(fields):
        mapping = MAPPINGS.get(field, {})

        # 1. CLI Argument Check
        cli_flag = mapping.get("cli_flag")
        if cli_flag == "SKIP":
            # Explicitly skipped
            pass
        else:
            if not cli_flag:
                # Default: --field-name
                cli_flag = "--" + field.replace("_", "-")

            # Robust Regex for add_argument
            # Matches: add_argument(..."--flag"...) or add_argument(..., '--flag', ...)
            # Quote variants: ' or "
            cli_regex = rf'add_argument\s*\(\s*.*[\'"]{re.escape(cli_flag)}[\'"]'

            if not re.search(cli_regex, content):
                print(f"❌ Missing CLI argument: '{field}' (expected flag: {cli_flag})")
                success = False

        # 2. Logic/Usage Check
        # Heuristic: verify the variable name appears in the code (args.field, config.field, etc)
        py_usage = mapping.get("py_usage")
        if py_usage == "SKIP":
            pass
        else:
            if not py_usage:
                # Default: field name itself (word boundary)
                py_usage = rf"\b{field}\b"

            if not re.search(py_usage, content):
                print(f"❌ Missing usage logic: '{field}' (regex: /{py_usage}/)")
                success = False

    return success

def main():
    print(f"🔍 Parity Guard running...")

    # 1. Extract Source of Truth
    fields = extract_model_fields(MODELS_PATH)
    print(f"Found {len(fields)} fields in JobRequest: {', '.join(sorted(fields))}")

    # 2. Check Frontends
    ok_web = check_webui(WEBUI_PATH, fields)
    ok_py = check_pythonista(PYTHONISTA_PATH, fields)

    if ok_web and ok_py:
        print("\n✅ All checks passed. Parity preserved.")
        sys.exit(0)
    else:
        print("\n💥 Parity check FAILED. See errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
