#!/usr/bin/env python3
"""
Parity Guard
------------
Ensures feature parity between the Backend Model (JobRequest),
Pythonista UI (repoLens), and Web UI (rLens).

Checks:
1. JobRequest model fields (Source of Truth).
2. repolens.py (CLI args, usage, and UI logic).
3. Web UI (index.html inputs and app.js payload construction).
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
        "html_id": "profile",
        "js_key": "level",
        "repolens_usage": "args.level"
    },
    "mode": {
        "cli_arg": "--mode",
        "html_id": "mode",
        "js_key": "mode",
        "repolens_usage": "args.mode"
    },
    "max_bytes": {
        "cli_arg": "--max-bytes",
        "html_id": "maxBytes",
        "js_key": "max_bytes",
        "repolens_usage": "args.max_bytes" # ArgumentParser automatically converts - to _
    },
    "split_size": {
        "cli_arg": "--split-size",
        "html_id": "splitSize",
        "js_key": "split_size",
        "repolens_usage": "args.split_size"
    },
    "plan_only": {
        "cli_arg": "--plan-only",
        "html_id": "planOnly",
        "js_key": "plan_only",
        "repolens_usage": "args.plan_only"
    },
    "code_only": {
        "cli_arg": "--code-only",
        "html_id": "codeOnly",
        "js_key": "code_only",
        "repolens_usage": "args.code_only"
    },
    "meta_density": {
        "cli_arg": "--meta-density",
        "html_id": "metaDensity",
        "js_key": "meta_density",
        "repolens_usage": "args.meta_density"
    },
    "json_sidecar": {
        "cli_arg": "--json-sidecar",
        # Explicit decision: Treat as a payload key in JS (even if logic is derived).
        # In JobRequest it is a field.
        "js_key": "json_sidecar",
        "repolens_usage": "args.json_sidecar"
    },
    # Filters
    "extensions": {
        "cli_arg": "--extensions",
        "html_id": "extFilter",
        "js_key": "extensions",
        "repolens_usage": "args.extensions"
    },
    "path_filter": {
        "cli_arg": "--path-filter",
        "html_id": "pathFilter",
        "js_key": "path_filter",
        "repolens_usage": "args.path_filter"
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
            # 1. CLI Arg Check (Robust Regex)
            cli_arg = config.get("cli_arg")
            if cli_arg:
                # Matches: add_argument(..., "--flag", ...) or add_argument("--flag", ...)
                # Allows single/double quotes, whitespace, and newlines.
                # Pattern: add_argument \s* \( ... (quote)cli_arg(quote)
                # We simply check if the string appears inside an add_argument call.

                # Simplified robust check: Look for the argument string quoted, near add_argument
                # A full parser is overkill, but a targeted regex works.
                # Regex: add_argument \s* \( .*? ['"]--flag['"]
                # Note: dotall is needed for multiline.

                regex = r"add_argument\s*\(\s*(?:['\"]-[a-zA-Z]['\"]\s*,\s*)?['\"]" + re.escape(cli_arg) + r"['\"]"
                if re.search(regex, content, re.MULTILINE | re.DOTALL):
                    self.log_pass(f"repoLens CLI: {cli_arg} definition found.")
                else:
                    self.log_error(f"repoLens CLI: Definition for {cli_arg} missing (feature: {feature}).")

            # 2. Usage Check
            # Verify that the parsed argument is actually accessed/used.
            usage_key = config.get("repolens_usage")
            if usage_key:
                if usage_key in content:
                    self.log_pass(f"repoLens Usage: {usage_key} accessed.")
                else:
                    # Fallback check: sometimes passed as **vars(args) or dict?
                    # But repolens.py usually does explicit args.field access.
                    self.log_error(f"repoLens Usage: {usage_key} not accessed in script.")

    def check_webui_html(self):
        """Check index.html for IDs."""
        print(f"Checking WebUI HTML in {WEBUI_HTML_PATH}...")
        content = WEBUI_HTML_PATH.read_text("utf-8")

        for feature, config in FEATURES.items():
            html_id = config.get("html_id")
            if html_id:
                # Regex for id="value" or id='value'
                if re.search(f'id=["\']{html_id}["\']', content):
                    self.log_pass(f"WebUI HTML: Element #{html_id} found for '{feature}'.")
                else:
                    self.log_error(f"WebUI HTML: Element #{html_id} missing for feature '{feature}'.")

    def _strip_js_comments(self, js_content):
        """Remove single line // and multi-line /* */ comments."""
        # Multi-line
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        # Single line
        js_content = re.sub(r'//.*', '', js_content)
        return js_content

    def check_webui_js(self):
        """Check app.js for payload construction."""
        print(f"Checking WebUI JS in {WEBUI_JS_PATH}...")
        content = WEBUI_JS_PATH.read_text("utf-8")
        clean_content = self._strip_js_comments(content)

        for feature, config in FEATURES.items():
            js_key = config.get("js_key")

            if js_key:
                # Look for payload key assignment: "key:"
                # Strict check: key followed by optional whitespace and a colon.
                if re.search(rf'\b{js_key}\s*:', clean_content):
                    self.log_pass(f"WebUI JS: Payload key '{js_key}' found.")
                else:
                    self.log_error(f"WebUI JS: Payload key '{js_key}' missing for feature '{feature}'.")

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
