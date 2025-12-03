#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc-extractor.py
Extracts ZIP archives into a target directory (wc-hub) and generates a diff report.
"""

import argparse
import sys
import os
import shutil
import zipfile
import filecmp
from pathlib import Path

def compare_dirs(old_dir, new_dir):
    """
    Compares two directories recursively and returns a list of changes.
    """
    changes = []

    old_files = set()
    new_files = set()

    for dirpath, _, filenames in os.walk(old_dir):
        rel_dir = os.path.relpath(dirpath, old_dir)
        if rel_dir == ".": rel_dir = ""
        for fn in filenames:
            old_files.add(os.path.join(rel_dir, fn))

    for dirpath, _, filenames in os.walk(new_dir):
        rel_dir = os.path.relpath(dirpath, new_dir)
        if rel_dir == ".": rel_dir = ""
        for fn in filenames:
            new_files.add(os.path.join(rel_dir, fn))

    all_files = old_files.union(new_files)

    for f in sorted(all_files):
        in_old = f in old_files
        in_new = f in new_files

        if in_old and not in_new:
            changes.append(f"❌ REMOVED: {f}")
        elif not in_old and in_new:
            changes.append(f"✨ ADDED:   {f}")
        else:
            # In both, check content
            old_p = os.path.join(old_dir, f)
            new_p = os.path.join(new_dir, f)
            if not filecmp.cmp(old_p, new_p, shallow=False):
                 changes.append(f"📝 MODIFIED: {f}")

    return changes

def main():
    parser = argparse.ArgumentParser(description="Extract ZIP to wc-hub with diff report.")
    parser.add_argument("zipfile", help="Path to the source ZIP file.")
    parser.add_argument("destination", help="Target directory (wc-hub repo path).")
    parser.add_argument("--force", action="store_true", help="Overwrite without confirmation.")

    args = parser.parse_args()

    zip_path = Path(args.zipfile).resolve()
    dest_path = Path(args.destination).resolve()

    if not zip_path.exists():
        print(f"Error: ZIP file not found: {zip_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Preparing to extract {zip_path.name} to {dest_path}...", file=sys.stderr)

    # Create temp dir for extraction
    temp_dir = dest_path.parent / (dest_path.name + "_temp_extract")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # If destination exists, compare
        if dest_path.exists():
            print("Destination exists. Comparing...", file=sys.stderr)
            changes = compare_dirs(str(dest_path), str(temp_dir))

            if not changes:
                print("No changes detected.", file=sys.stderr)
            else:
                print("\n--- DIFF REPORT ---")
                for c in changes:
                    print(c)
                print("-------------------\n")

            if not args.force:
                print("Dry run completed. Use --force to apply changes.", file=sys.stderr)
                shutil.rmtree(temp_dir)
                return

            # Apply changes: Remove old, move new
            # Better: rsync-like sync? For now, replace logic as requested implies extraction.
            # "Extracts into target... comparing... before replacement"

            print("Replacing content...", file=sys.stderr)
            shutil.rmtree(dest_path)
            shutil.move(str(temp_dir), str(dest_path))
            print("Done.", file=sys.stderr)

        else:
            print("Destination does not exist. Creating...", file=sys.stderr)
            shutil.move(str(temp_dir), str(dest_path))
            print("Done.", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        sys.exit(1)

if __name__ == "__main__":
    main()
