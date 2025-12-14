# -*- coding: utf-8 -*-

"""
cli – CLI logic for wc-merger.
Separated from core and UI.
"""

import sys
import os
import argparse
from pathlib import Path

# Import core logic
# Use relative import if running as package, else fallback to sys.path
try:
    from .core import (
        detect_hub_dir,
        find_repos_in_hub,
        scan_repo,
        write_reports_v2,
        get_merges_dir,
        _normalize_ext_list,
        parse_human_size,
        _parse_extras_csv,
        ExtrasConfig,
        DEFAULT_MAX_BYTES,
    )
except ImportError:
    # Fallback
    try:
        from core import (
            detect_hub_dir,
            find_repos_in_hub,
            scan_repo,
            write_reports_v2,
            get_merges_dir,
            _normalize_ext_list,
            parse_human_size,
            _parse_extras_csv,
            ExtrasConfig,
            DEFAULT_MAX_BYTES,
        )
    except ImportError:
        # If running from different CWD
        sys.path.append(str(Path(__file__).resolve().parent))
        from core import (
            detect_hub_dir,
            find_repos_in_hub,
            scan_repo,
            write_reports_v2,
            get_merges_dir,
            _normalize_ext_list,
            parse_human_size,
            _parse_extras_csv,
            ExtrasConfig,
            DEFAULT_MAX_BYTES,
        )

DEFAULT_LEVEL = "dev"
DEFAULT_MODE = "gesamt"
DEFAULT_SPLIT_SIZE = "25MB"
DEFAULT_MAX_FILE_BYTES = 0
DEFAULT_EXTRAS = "health,augment_sidecar,organism_index,fleet_panorama,json_sidecar,ai_heatmap"

def _load_wc_extractor_module():
    """Helper to load wc-extractor for delta logic."""
    from importlib.machinery import SourceFileLoader
    import types
    # Assume wc-extractor.py is in the same directory as this script
    script_dir = Path(__file__).resolve().parent
    extractor_path = script_dir / "wc-extractor.py"

    if not extractor_path.exists():
        return None
    try:
        loader = SourceFileLoader("wc_extractor", str(extractor_path))
        mod = types.ModuleType(loader.name)
        loader.exec_module(mod)
        return mod
    except Exception as exc:
        print(f"[cli] could not load wc-extractor: {exc}")
        return None

def main_cli():
    parser = argparse.ArgumentParser(description="wc-merger CLI")
    parser.add_argument("paths", nargs="*", help="Repositories to merge")
    parser.add_argument("--hub", help="Base directory (wc-hub)")
    parser.add_argument("--level", choices=["overview", "summary", "dev", "max"], default=DEFAULT_LEVEL)
    parser.add_argument("--mode", choices=["gesamt", "pro-repo"], default=DEFAULT_MODE)
    parser.add_argument(
        "--max-bytes",
        type=str,
        default=str(DEFAULT_MAX_FILE_BYTES),
        help="Max bytes per file (e.g. 5MB, 500K, or 0 for unlimited)",
    )
    parser.add_argument("--split-size", help="Split output into chunks (e.g. 50MB, 1GB)", default=DEFAULT_SPLIT_SIZE)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--code-only", action="store_true", help="Include only code/test/config/contract categories")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--headless", action="store_true", help="Force headless (no Pythonista UI/editor)")
    parser.add_argument(
        "--extras",
        help="Comma-separated list of extras or 'none'",
        default=DEFAULT_EXTRAS,
    )
    parser.add_argument("--extensions", help="Comma-separated list of extensions (e.g. .md,.py) to include", default=None)
    parser.add_argument("--path-filter", help="Path substring to include (e.g. docs/)", default=None)
    parser.add_argument("--json-sidecar", action="store_true", help="Generate JSON sidecar file alongside markdown report")

    args = parser.parse_args()

    hub = detect_hub_dir(Path(__file__).resolve(), args.hub)

    sources = []
    if args.paths:
        for p in args.paths:
            path = Path(p)
            if not path.exists():
                path = hub / p
            if path.exists() and path.is_dir():
                sources.append(path)
            else:
                print(f"Warning: {path} not found.")
    else:
        repos = find_repos_in_hub(hub)
        for r in repos:
            sources.append(hub / r)

    if not sources:
        cwd = Path.cwd()
        print(f"No sources in hub ({hub}). Scanning current directory: {cwd}")
        sources.append(cwd)

    print(f"Hub: {hub}")
    print(f"Sources: {[s.name for s in sources]}")

    max_bytes = parse_human_size(str(args.max_bytes))
    if max_bytes < 0:
        max_bytes = 0

    ext_list = _normalize_ext_list(args.extensions) if args.extensions else None
    path_filter = args.path_filter

    summaries = []
    for src in sources:
        print(f"Scanning {src.name}...")
        summary = scan_repo(src, ext_list, path_filter, max_bytes)
        summaries.append(summary)

    split_size = 0
    if args.split_size:
        split_size = parse_human_size(args.split_size)
        print(f"Splitting at {split_size} bytes")

    extras_config = ExtrasConfig()
    if args.extras and args.extras.lower() != "none":
        for part in _parse_extras_csv(args.extras):
            if hasattr(extras_config, part):
                setattr(extras_config, part, True)
            else:
                print(f"Warning: Unknown extra '{part}' ignored.")

    if args.json_sidecar:
        extras_config.json_sidecar = True

    merges_dir = get_merges_dir(hub)

    delta_meta = None
    if extras_config.delta_reports and summaries and len(summaries) == 1:
        repo_name = summaries[0]["name"]
        try:
            mod = _load_wc_extractor_module()
            if mod and hasattr(mod, "find_latest_diff_for_repo") and hasattr(mod, "extract_delta_meta_from_diff_file"):
                diff_path = mod.find_latest_diff_for_repo(merges_dir, repo_name)
                if diff_path:
                    delta_meta = mod.extract_delta_meta_from_diff_file(diff_path)
                    if delta_meta and args.debug:
                        print(f"Delta metadata extracted from {diff_path.name}")
        except Exception as e:
            if args.debug:
                print(f"Warning: Could not extract delta metadata: {e}")

    artifacts = write_reports_v2(
        merges_dir,
        hub,
        summaries,
        args.level,
        args.mode,
        max_bytes,
        args.plan_only,
        args.code_only,
        split_size,
        debug=args.debug,
        path_filter=path_filter,
        ext_filter=ext_list,
        extras=extras_config,
        delta_meta=delta_meta,
    )

    out_paths = artifacts.get_all_paths()
    print(f"Generated {len(out_paths)} report(s):")
    for p in out_paths:
        print(f"  - {p}")

if __name__ == "__main__":
    main_cli()
