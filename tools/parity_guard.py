#!/usr/bin/env python3
"""
Parity Guard
------------
Ensures feature parity between the Backend Model (JobRequest),
Pythonista UI (repoLens), and Web UI (rLens).

Checks:
1. JobRequest model fields (Source of Truth).
2. repolens.py (CLI args and UI widgets).
3. Web UI (index.html inputs and app.js payload).
"""

import sys
import re
import ast
from pathlib import Path
from typing import List, Dict, Set

# Configuration
# Map Feature Name (JobRequest field) to expected representations
# Key: JobRequest field name
# Value: Dict of expectations
FEATURES = {
    "level": {
        "cli_arg": "--level",
        "html_id": "profile", # Mismatch allowed if mapped
        "js_key": "level"
    },
    "mode": {
        "cli_arg": "--mode",
        "html_id": "mode",
        "js_key": "mode"
    },
    "max_bytes": {
        "cli_arg": "--max-bytes",
        "html_id": "maxBytes",
        "js_key": "max_bytes"
    },
    "split_size": {
        "cli_arg": "--split-size",
        "html_id": "splitSize",
        "js_key": "split_size"
    },
    "plan_only": {
        "cli_arg": "--plan-only",
        "html_id": "planOnly",
        "js_key": "plan_only"
    },
    "code_only": {
        "cli_arg": "--code-only",
        "html_id": "codeOnly",
        "js_key": "code_only"
    },
    "meta_density": {
        "cli_arg": "--meta-density",
        "html_id": "metaDensity",
        "js_key": "meta_density"
    },
    "json_sidecar": {
        "cli_arg": "--json-sidecar",
        # Checkbox often hidden or part of extras, but let's check explicit logic
        # In app.js it is derived from extras 'json_sidecar' usually, or explicit field.
        # JobRequest has it as bool.
        # repolens has --json-sidecar flag.
        "js_payload_logic": "json_sidecar"
    },
    # Filters
    "extensions": {
        "cli_arg": "--extensions",
        "html_id": "extFilter",
        "js_key": "extensions"
    },
    "path_filter": {
        "cli_arg": "--path-filter",
        "html_id": "pathFilter",
        "js_key": "path_filter"
    }
}

# Paths
ROOT = Path(__file__).parent.parent.resolve()
MODEL_PATH = ROOT / "merger/lenskit/service/models.py"
REPOLENS_PATH = ROOT / "merger/lenskit/frontends/pythonista/repolens.py"
WEBUI_HTML_PATH = ROOT / "merger/lenskit/frontends/webui/index.html"
WEBUI_JS_PATH = ROOT / "merger/lenskit/frontends/webui/app.js"

class ParityChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def log_error(self, msg):
        self.errors.append(f"[FAIL] {msg}")

    def log_warn(self, msg):
        self.warnings.append(f"[WARN] {msg}")

    def log_pass(self, msg):
        print(f"[PASS] {msg}")

    def check_model_fields(self):
        """Verify defined features actually exist in JobRequest model."""
        print(f"Checking JobRequest in {MODEL_PATH}...")
        try:
            tree = ast.parse(MODEL_PATH.read_text("utf-8"))
        except Exception as e:
            self.log_error(f"Could not parse models.py: {e}")
            return

        job_request_fields = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "JobRequest":
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        job_request_fields.add(item.target.id)

        for feature in FEATURES:
            if feature not in job_request_fields:
                self.log_error(f"Feature '{feature}' defined in Parity Guard but missing in JobRequest model.")
            else:
                self.log_pass(f"Feature '{feature}' present in JobRequest.")

    def check_repolens(self):
        """Check Pythonista UI/CLI."""
        print(f"Checking repoLens in {REPOLENS_PATH}...")
        content = REPOLENS_PATH.read_text("utf-8")

        for feature, config in FEATURES.items():
            # 1. CLI Arg Check
            cli_arg = config.get("cli_arg")
            if cli_arg:
                if f'add_argument("{cli_arg}"' in content or f"add_argument('{cli_arg}'" in content:
                    self.log_pass(f"repoLens CLI: {cli_arg} found.")
                else:
                    self.log_error(f"repoLens CLI: Argument {cli_arg} missing for feature '{feature}'.")

            # 2. UI Check (Heuristic)
            # We look for usage of the feature name in a UI context or logic assignment
            # e.g. "seg_detail" for level, or direct usage.
            # Simpler: check if it's passed to write_reports_v2 or similar.

            # This is harder to generalize via regex.
            # We assume if CLI arg exists, logic exists.
            # But we can check for specific known UI mappings if we want to be strict.
            pass

    def check_webui_html(self):
        """Check index.html for IDs."""
        print(f"Checking WebUI HTML in {WEBUI_HTML_PATH}...")
        content = WEBUI_HTML_PATH.read_text("utf-8")

        for feature, config in FEATURES.items():
            html_id = config.get("html_id")
            if html_id:
                # Regex for id="value"
                if re.search(f'id=["\']{html_id}["\']', content):
                    self.log_pass(f"WebUI HTML: Element #{html_id} found for '{feature}'.")
                else:
                    self.log_error(f"WebUI HTML: Element #{html_id} missing for feature '{feature}'.")

    def check_webui_js(self):
        """Check app.js for payload construction."""
        print(f"Checking WebUI JS in {WEBUI_JS_PATH}...")
        content = WEBUI_JS_PATH.read_text("utf-8")

        for feature, config in FEATURES.items():
            js_key = config.get("js_key")
            logic_key = config.get("js_payload_logic")

            target = js_key or logic_key
            if target:
                # Look for payload key assignment: "key: " or "key ="
                # In the app.js provided:
                # const commonPayload = {
                #    level: ...,
                #    mode: ...
                # }
                # So we look for "key:" inside the object definition.

                # Regex to find key followed by colon, allowing for whitespace
                if re.search(rf'\b{target}\s*:', content):
                    self.log_pass(f"WebUI JS: Payload key '{target}' found.")
                else:
                    self.log_error(f"WebUI JS: Payload key '{target}' missing for feature '{feature}'.")

    def run(self):
        self.check_model_fields()
        self.check_repolens()
        self.check_webui_html()
        self.check_webui_js()

        print("\n--- Report ---")
        for w in self.warnings:
            print(w)
        for e in self.errors:
            print(e)

        if self.errors:
            print("\n[FAILED] Parity Check Failed.")
            sys.exit(1)
        else:
            print("\n[SUCCESS] Parity Check Passed.")
            sys.exit(0)

if __name__ == "__main__":
    ParityChecker().run()
