#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc-merger CLI tool.
Generates structured merge reports from local repositories.
"""

import argparse
import sys
import os
from pathlib import Path
from merge_core import scan_repo, generate_report

def main():
    parser = argparse.ArgumentParser(description="wc-merger: Generate structured merge reports for AI context.")
    parser.add_argument("paths", nargs="*", help="Paths to repositories or directories to merge.")
    parser.add_argument("--level", choices=["plan", "compact", "max"], default="compact", help="Detail level (default: compact).")
    parser.add_argument("--max-bytes", type=int, default=500_000, help="Max bytes per file content (default: 500KB).")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout).")
    parser.add_argument("--hub", help="Base path for 'wc-hub' if paths are relative names.")

    args = parser.parse_args()

    sources = []

    # Resolve sources
    if not args.paths:
        # Default to current directory if no paths provided
        sources.append(Path.cwd())
    else:
        for p in args.paths:
            path = Path(p)
            if not path.exists() and args.hub:
                hub_path = Path(args.hub) / p
                if hub_path.exists():
                    path = hub_path

            if path.exists() and path.is_dir():
                sources.append(path.resolve())
            else:
                print(f"Warning: Path '{p}' not found or is not a directory.", file=sys.stderr)

    if not sources:
        print("Error: No valid sources found.", file=sys.stderr)
        sys.exit(1)

    all_files = []
    for src in sources:
        print(f"Scanning {src}...", file=sys.stderr)
        root_label = src.name
        files = scan_repo(src, root_label, args.max_bytes)
        all_files.extend(files)

    print(f"Generating report (Level: {args.level})...", file=sys.stderr)
    report = generate_report(
        sources=[str(s) for s in sources],
        file_infos=all_files,
        level=args.level,
        max_file_bytes=args.max_bytes
    )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Report written to {out_path}", file=sys.stderr)
    else:
        print(report)

if __name__ == "__main__":
    main()
