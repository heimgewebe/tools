# -*- coding: utf-8 -*-
import sys
import os
import argparse
from pathlib import Path
from typing import List, Optional

try:
    from core import (
        DEFAULT_LEVEL,
        DEFAULT_MODE,
        DEFAULT_MAX_FILE_BYTES,
        DEFAULT_SPLIT_SIZE,
        DEFAULT_EXTRAS,
        detect_hub_dir,
        find_repos_in_hub,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        _parse_extras_csv,
        parse_human_size,
        get_merges_dir,
        _load_wc_extractor_module,
    )
except ImportError:
    from .core import (
        DEFAULT_LEVEL,
        DEFAULT_MODE,
        DEFAULT_MAX_FILE_BYTES,
        DEFAULT_SPLIT_SIZE,
        DEFAULT_EXTRAS,
        detect_hub_dir,
        find_repos_in_hub,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        _parse_extras_csv,
        parse_human_size,
        get_merges_dir,
        _load_wc_extractor_module,
    )

def safe_script_path() -> Path:
    """
    Versucht, den Pfad dieses Skripts robust zu bestimmen.
    Copied from wc-merger.py for standalone usage if needed.
    """
    try:
        return Path(__file__).resolve()
    except NameError:
        argv0 = None
        try:
            if getattr(sys, "argv", None):
                argv0 = sys.argv[0] or None
        except Exception:
            argv0 = None

        if argv0:
            try:
                return Path(argv0).resolve()
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to resolve argv0 path: {e}\n")

        return Path.cwd().resolve()

SCRIPT_PATH = safe_script_path()

def _is_headless_requested() -> bool:
    # Headless wenn:
    # 1) --headless Flag, oder
    # 2) WC_HEADLESS=1 in der Umgebung, oder
    # 3) ui-Framework nicht verfügbar (checked elsewhere usually)
    return ("--headless" in sys.argv) or (os.environ.get("WC_HEADLESS") == "1")

def main_cli():
    parser = argparse.ArgumentParser(description="wc-merger CLI")
    parser.add_argument("paths", nargs="*", help="Repositories to merge")
    parser.add_argument("--hub", help="Base directory (wc-hub)")
    parser.add_argument("--level", choices=["overview", "summary", "dev", "max"], default=DEFAULT_LEVEL)
    parser.add_argument("--mode", choices=["gesamt", "pro-repo"], default=DEFAULT_MODE)
    # 0 = unbegrenzt pro Datei
    parser.add_argument(
        "--max-bytes",
        type=str,
        default=str(DEFAULT_MAX_FILE_BYTES),
        help="Max bytes per file (e.g. 5MB, 500K, or 0 for unlimited)",
    )
    # Default: ab 25 MB wird gesplittet, aber kein Gesamtlimit – es werden
    # beliebig viele Parts erzeugt.
    parser.add_argument("--split-size", help="Split output into chunks (e.g. 50MB, 1GB)", default=DEFAULT_SPLIT_SIZE)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--code-only", action="store_true", help="Include only code/test/config/contract categories")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--headless", action="store_true", help="Force headless (no Pythonista UI/editor)")
    parser.add_argument(
        "--extras",
        help="Comma-separated list of extras (health,organism_index,fleet_panorama,delta_reports,augment_sidecar,json_sidecar,heatmap; alias: ai_heatmap) or 'none'",
        default=DEFAULT_EXTRAS,
    )
    parser.add_argument("--extensions", help="Comma-separated list of extensions (e.g. .md,.py) to include", default=None)
    parser.add_argument("--path-filter", help="Path substring to include (e.g. docs/)", default=None)
    parser.add_argument("--json-sidecar", action="store_true", help="Generate JSON sidecar file alongside markdown report")

    args = parser.parse_args()

    hub = detect_hub_dir(SCRIPT_PATH, args.hub)

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

    # Default: ab 25 MB wird gesplittet, aber kein Gesamtlimit – es werden
    # beliebig viele Parts erzeugt.
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

    # Handle --json-sidecar flag
    if args.json_sidecar:
        extras_config.json_sidecar = True

    merges_dir = get_merges_dir(hub)

    # Try to extract delta_meta if delta_reports is enabled
    delta_meta = None
    if extras_config.delta_reports and summaries and len(summaries) == 1:
        # Only try to find delta for single-repo merges
        repo_name = summaries[0]["name"]
        try:
            mod = _load_wc_extractor_module(SCRIPT_PATH)
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
