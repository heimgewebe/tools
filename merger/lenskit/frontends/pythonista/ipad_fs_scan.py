#!/usr/bin/env python3
"""
iPad FS Scanner (Jules Implementation)

A machine-readable filesystem scanner for iPadOS (Pythonista).
Generates a canonical 'ipad.fs.index.json' that explicitly maps the
folder structure, including visibility limits and permissions.

Goal: Provide AI systems with a reliable map of the iPad's accessible file system.
"""

import os
import sys
import json
import time
import datetime
import fnmatch
import platform
import pathlib
import logging

# Set up logging to stderr (machine-readable tools should not pollute stdout)
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("ipad_fs_scan")

# Try importing Pythonista-specific modules
try:
    import dialogs
    import ui
    import console
    HAS_UI = True
except ImportError:
    HAS_UI = False

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------

SCHEMA_VERSION = "ipad.fs.index/v1"
DEFAULT_MAX_DEPTH = 8
DEFAULT_MAX_ENTRIES = 200000
DEFAULT_EXCLUDES = [
    "__pycache__", ".git", ".idea", ".vscode", "node_modules",
    ".DS_Store", "venv", ".venv"
]
DEFAULT_OUTPUT_DIR = "fs-exports"

# -----------------------------------------------------------------------------
# Core Logic: iPadFSScanner
# -----------------------------------------------------------------------------

class iPadFSScanner:
    """
    Core scanner logic. Independent of UI components to allow for testing.
    """
    def __init__(self, roots, output_dir, max_depth=DEFAULT_MAX_DEPTH,
                 max_entries=DEFAULT_MAX_ENTRIES, excludes=None, follow_symlinks=False):
        """
        Initialize the scanner.

        Args:
            roots (list): List of dicts with keys 'path', 'label', 'root_id', 'source'.
            output_dir (str): Directory to save output files.
            max_depth (int): Maximum recursion depth.
            max_entries (int): Maximum total files/dirs to scan before aborting (safety).
            excludes (list): List of glob patterns to exclude.
            follow_symlinks (bool): Whether to follow symlinks (default False).
        """
        self.roots = roots
        self.output_dir = output_dir
        self.max_depth = max_depth
        self.max_entries = max_entries
        self.excludes = excludes or DEFAULT_EXCLUDES
        self.follow_symlinks = follow_symlinks

        self.entry_count = 0
        self.errors = []
        self.scan_start_time = None

    def scan(self):
        """
        Performs the scan and returns the complete JSON structure.
        """
        self.scan_start_time = datetime.datetime.now(datetime.timezone.utc)
        self.entry_count = 0
        self.errors = []

        processed_roots = []

        for root_def in self.roots:
            processed_roots.append(self._scan_root(root_def))

        result = {
            "schema": SCHEMA_VERSION,
            "generated_at": self.scan_start_time.isoformat(),
            "device": {
                "platform": platform.system(),
                "runtime": "Pythonista3" if HAS_UI else "Python",
                "note": "Scan scope depends on iOS file access permissions and provider visibility."
            },
            "scan_config": {
                "max_depth": self.max_depth,
                "max_entries": self.max_entries,
                "follow_symlinks": self.follow_symlinks,
                "excludes": self.excludes
            },
            "roots": processed_roots,
            "errors": self.errors
        }

        return result

    def _scan_root(self, root_def):
        """
        Scans a single root entry.
        """
        path_str = root_def.get('path')
        root_path = pathlib.Path(path_str) if path_str else None

        root_result = {
            "root_id": root_def.get('root_id', 'unknown'),
            "label": root_def.get('label', 'Unknown Root'),
            "source": root_def.get('source', 'manual'),
            "path": path_str,
            "summary": {
                "dirs": 0,
                "files": 0,
                "bytes": 0,
                "status": "pending"
            },
            "tree": None
        }

        if not path_str:
            root_result['summary']['status'] = "error"
            self.errors.append({
                "path": "ROOT",
                "kind": "config_error",
                "message": f"Root '{root_def.get('label')}' has no path defined."
            })
            return root_result

        if not root_path.exists():
            root_result['summary']['status'] = "not_found"
            self.errors.append({
                "path": path_str,
                "kind": "not_found",
                "message": "Root path does not exist."
            })
            return root_result

        if not root_path.is_dir():
            root_result['summary']['status'] = "error"
            self.errors.append({
                "path": path_str,
                "kind": "not_a_directory",
                "message": "Root path is not a directory."
            })
            return root_result

        # Start recursion
        try:
            tree, summary = self._scan_recursive(root_path, depth=0)
            root_result['tree'] = tree
            root_result['summary'] = summary
        except Exception as e:
            root_result['summary']['status'] = "error"
            self.errors.append({
                "path": path_str,
                "kind": "scan_exception",
                "message": str(e)
            })
            logger.exception(f"Error scanning root {path_str}")

        return root_result

    def _scan_recursive(self, current_path, depth):
        """
        Recursive scanner. Returns (node_dict, summary_dict).
        """
        # Global limit check
        if self.entry_count >= self.max_entries:
            return {
                "path": current_path.name,
                "type": "dir",
                "status": "out_of_scope",
                "reason": "Global entry limit reached"
            }, {"dirs": 0, "files": 0, "bytes": 0, "status": "incomplete"}

        self.entry_count += 1

        # Base node structure
        node = {
            "path": current_path.name,
            "type": "dir",
            "status": "ok",
            "mtime": self._safe_mtime(current_path)
        }

        summary = {"dirs": 1, "files": 0, "bytes": 0, "status": "ok"}

        # Depth limit check
        if depth >= self.max_depth:
            node["status"] = "out_of_scope"
            node["reason"] = "Max depth reached"
            return node, summary

        children_nodes = []

        try:
            # We use os.scandir for better performance
            with os.scandir(current_path) as it:
                entries = sorted(list(it), key=lambda e: e.name.lower())

                for entry in entries:
                    if self._is_excluded(entry.name):
                        continue

                    # Process File
                    if entry.is_file(follow_symlinks=self.follow_symlinks):
                        file_node = self._process_file(entry)
                        children_nodes.append(file_node)
                        summary["files"] += 1
                        summary["bytes"] += file_node.get("size", 0)
                        self.entry_count += 1

                    # Process Directory
                    elif entry.is_dir(follow_symlinks=self.follow_symlinks):
                        dir_node, dir_summary = self._scan_recursive(pathlib.Path(entry.path), depth + 1)
                        children_nodes.append(dir_node)
                        summary["dirs"] += dir_summary["dirs"]
                        summary["files"] += dir_summary["files"]
                        summary["bytes"] += dir_summary["bytes"]

                        if dir_summary["status"] != "ok":
                             summary["status"] = "has_warnings" # Propagate warning status

        except PermissionError:
            node["status"] = "permission_denied"
            self.errors.append({
                "path": str(current_path),
                "kind": "permission_denied",
                "message": "Access denied by OS"
            })
            summary["status"] = "error"

        except OSError as e:
            node["status"] = "error"
            node["reason"] = str(e)
            self.errors.append({
                "path": str(current_path),
                "kind": "os_error",
                "message": str(e)
            })
            summary["status"] = "error"

        # Finalize Directory Node
        node["children"] = children_nodes
        node["children_count"] = len(children_nodes)
        node["file_count"] = summary["files"]
        node["bytes"] = summary["bytes"]

        return node, summary

    def _process_file(self, entry):
        """
        Create a node for a file entry.
        """
        try:
            stat = entry.stat()
            size = stat.st_size
            mtime = self._fmt_time(stat.st_mtime)
        except OSError:
            size = 0
            mtime = None

        return {
            "path": entry.name,
            "type": "file",
            "status": "ok",
            "size": size,
            "mtime": mtime,
            "extension": pathlib.Path(entry.name).suffix.lower()
        }

    def _is_excluded(self, name):
        """
        Check if a name matches exclusion patterns.
        """
        for pattern in self.excludes:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def _safe_mtime(self, path_obj):
        try:
            return self._fmt_time(path_obj.stat().st_mtime)
        except OSError:
            return None

    def _fmt_time(self, timestamp):
        if timestamp is None:
            return None
        dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        return dt.isoformat()

    def write_output(self, scan_result):
        """
        Writes the JSON result to the output directory.
        """
        out_path = pathlib.Path(self.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        json_file = out_path / "ipad.fs.index.json"

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(scan_result, f, indent=2, ensure_ascii=False)

        logger.info(f"Scan complete. Output written to: {json_file}")
        return json_file

# -----------------------------------------------------------------------------
# UI Logic (Pythonista Only)
# -----------------------------------------------------------------------------

def run_ui():
    if not HAS_UI:
        print("This UI requires Pythonista (iOS).")
        return

    # Define Defaults
    default_roots = [
        "/private/var/mobile/Containers/Shared/AppGroup/605C3346-6819-4F54-8B7C-A5A43D2101F4/Pythonista3/Documents"
    ]
    # Try to detect if we are running in Pythonista and get the documents dir cleaner
    try:
        # Standard Pythonista documents path
        doc_path = os.path.expanduser("~/Documents")
        if os.path.exists(doc_path):
            default_roots = [doc_path]
    except Exception:
        pass

    roots_str = "\n".join(default_roots)
    excludes_str = ", ".join(DEFAULT_EXCLUDES)

    # Form Dialog
    fields = [
        {'type': 'text', 'title': 'Output Directory', 'key': 'output_dir', 'value': DEFAULT_OUTPUT_DIR},
        {'type': 'number', 'title': 'Max Depth', 'key': 'max_depth', 'value': str(DEFAULT_MAX_DEPTH)},
        {'type': 'number', 'title': 'Max Entries', 'key': 'max_entries', 'value': str(DEFAULT_MAX_ENTRIES)},
        {'type': 'text', 'title': 'Excludes (CSV)', 'key': 'excludes', 'value': excludes_str},
        {'type': 'text', 'title': 'Roots (One per line)', 'key': 'roots', 'value': roots_str, 'height': 100},
    ]

    result = dialogs.form_dialog(title='iPad FS Scanner', fields=fields)

    if not result:
        print("Cancelled.")
        return

    # Parse inputs
    try:
        output_dir = result['output_dir'].strip()
        max_depth = int(result['max_depth'])
        max_entries = int(result['max_entries'])

        excludes_raw = result['excludes'].split(',')
        excludes = [e.strip() for e in excludes_raw if e.strip()]

        roots_raw = result['roots'].strip().split('\n')
        roots = []
        for r in roots_raw:
            r = r.strip()
            if r:
                roots.append({
                    "root_id": os.path.basename(r) or "root",
                    "label": os.path.basename(r) or r,
                    "source": "manual_ui",
                    "path": r
                })

    except ValueError as e:
        console.alert("Input Error", f"Invalid number format: {e}", "OK", hide_cancel_button=True)
        return

    # Run Scan
    console.clear()
    print("Initializing Scan...")

    scanner = iPadFSScanner(
        roots=roots,
        output_dir=output_dir,
        max_depth=max_depth,
        max_entries=max_entries,
        excludes=excludes
    )

    print(f"Scanning {len(roots)} roots...")
    scan_result = scanner.scan()

    print("Writing Output...")
    json_path = scanner.write_output(scan_result)

    console.hud_alert(f"Saved: {os.path.basename(json_path)}", "success", 2.0)
    print(f"\nDone. \nLocation: {json_path}")
    print(f"Stats: {len(scan_result.get('errors', []))} errors recorded.")


if __name__ == "__main__":
    if HAS_UI:
        run_ui()
    else:
        # CLI fallback for testing or manual execution on standard python
        print("Running in CLI mode (No UI)")

        # Simple CLI argument parsing could go here, but for now we default to CWD
        current_dir = os.getcwd()
        print(f"Scanning current directory: {current_dir}")

        roots = [{
            "root_id": "cwd",
            "label": "Current Directory",
            "source": "cli_cwd",
            "path": current_dir
        }]

        scanner = iPadFSScanner(roots=roots, output_dir="fs-exports-cli")
        res = scanner.scan()
        scanner.write_output(res)
