#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc-merger – Working-Copy Merger.
Enhanced AI-optimized reports with strict Pflichtenheft structure.
"""

import sys
import os
import traceback
from pathlib import Path
from typing import List

# Try importing Pythonista modules
# In Shortcuts-App-Extension werfen diese Importe NotImplementedError.
# Deshalb JEGLICHEN Import-Fehler abfangen, nicht nur ImportError.
try:
    import ui        # type: ignore
except Exception:
    ui = None        # type: ignore

try:
    import console   # type: ignore
except Exception:
    console = None   # type: ignore

try:
    import editor    # type: ignore
except Exception:
    editor = None    # type: ignore

# Import core logic
try:
    from merge_core import (
        MERGES_DIR_NAME,
        DEFAULT_MAX_BYTES,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
    )
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from merge_core import (
        MERGES_DIR_NAME,
        DEFAULT_MAX_BYTES,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
    )


# --- Helper ---

def find_repos_in_hub(hub: Path) -> List[str]:
    repos: List[str] = []
    if not hub.exists():
        return []
    for child in sorted(hub.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name in SKIP_ROOTS:
            continue
        if child.name == MERGES_DIR_NAME:
            continue
        if child.name.startswith("."):
            continue
        repos.append(child.name)
    return repos

def parse_human_size(text: str) -> int:
    text = text.upper().strip()
    if not text: return 0
    if text.isdigit(): return int(text)

    units = {"K": 1024, "M": 1024**2, "G": 1024**3}
    for u, m in units.items():
        if text.endswith(u) or text.endswith(u+"B"):
            val = text.rstrip(u+"B").rstrip(u)
            try:
                return int(float(val) * m)
            except ValueError:
                return 0
    return 0


# --- UI Class (Pythonista) ---

class MergerUI(object):
    def __init__(self, hub: Path) -> None:
        self.hub = hub
        self.repos = find_repos_in_hub(hub)

        # Basic argv parsing for UI defaults
        # Expected format: wc-merger.py --level max --mode gesamt ...
        import argparse
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--level", default="dev")
        parser.add_argument("--mode", default="gesamt")
        parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
        parser.add_argument("--split-size", default="0")
        # Ignore unknown args
        args, _ = parser.parse_known_args()

        v = ui.View()
        v.name = "WC-Merger"
        # Dark background, accent color in classic iOS blue for good contrast
        v.background_color = "#111111"
        v.frame = (0, 0, 540, 660) # Increased height
        self.view = v

        # kleine Helper-Funktion für Dark-Theme-Textfelder
        def _style_textfield(tf: ui.TextField) -> None:
            tf.background_color = "#222222"
            tf.text_color = "white"
            tf.tint_color = "white"
            # Border bewusst einfach halten, damit iOS nicht wieder weiß hinterlegt
            tf.border_style = ui.TEXT_FIELD_BORDER_ROUNDED

        y = 10

        base_label = ui.Label()
        base_label.frame = (10, y, v.width - 20, 34)
        base_label.flex = "W"
        base_label.number_of_lines = 2
        base_label.text = f"Base-Dir: {hub}"
        base_label.text_color = "white"
        base_label.background_color = "#111111"
        base_label.font = ("<System>", 11)
        v.add_subview(base_label)
        self.base_label = base_label
        y += 40

        repo_label = ui.Label()
        repo_label.frame = (10, y, v.width - 20, 20)
        repo_label.flex = "W"
        repo_label.text = "Repos (Tap to select – None = All):"
        repo_label.text_color = "white"
        repo_label.background_color = "#111111"
        repo_label.font = ("<System>", 13)
        v.add_subview(repo_label)
        y += 22

        tv = ui.TableView()
        tv.frame = (10, y, v.width - 20, 160)
        tv.flex = "W"
        tv.background_color = "#111111"
        tv.separator_color = "#333333"
        tv.row_height = 32
        tv.allows_multiple_selection = True
        # Improve readability on dark background
        tv.tint_color = "#007aff"

        ds = ui.ListDataSource(self.repos)
        ds.text_color = "white"
        ds.highlight_color = "#333333"
        ds.tableview_cell_for_row = self._tableview_cell
        tv.data_source = ds
        tv.delegate = ds
        v.add_subview(tv)
        self.tv = tv
        self.ds = ds

        y += 170

        ext_field = ui.TextField()
        ext_field.frame = (10, y, v.width - 20, 28)
        ext_field.flex = "W"
        ext_field.placeholder = ".md,.yml,.rs (empty = all)"
        ext_field.text = ""
        _style_textfield(ext_field)
        v.add_subview(ext_field)
        self.ext_field = ext_field

        y += 34

        path_field = ui.TextField()
        path_field.frame = (10, y, v.width - 20, 28)
        path_field.flex = "W"
        path_field.placeholder = "Path contains (e.g. docs/ or .github/)"
        _style_textfield(path_field)
        path_field.autocorrection_type = False
        path_field.spellchecking_type = False
        v.add_subview(path_field)
        self.path_field = path_field

        y += 36

        detail_label = ui.Label()
        detail_label.text = "Detail:"
        detail_label.text_color = "white"
        detail_label.background_color = "#111111"
        detail_label.frame = (10, y, 60, 22)
        v.add_subview(detail_label)

        seg_detail = ui.SegmentedControl()
        seg_detail.segments = ["overview", "summary", "dev", "max"]
        try:
            seg_detail.selected_index = seg_detail.segments.index(args.level)
        except ValueError:
            seg_detail.selected_index = 2 # Default dev
        seg_detail.frame = (70, y - 2, 220, 28)
        seg_detail.flex = "W"
        # Use standard iOS blue instead of white for better contrast
        seg_detail.tint_color = "#007aff"
        seg_detail.background_color = "#111111"
        v.add_subview(seg_detail)
        self.seg_detail = seg_detail

        mode_label = ui.Label()
        mode_label.text = "Mode:"
        mode_label.text_color = "white"
        mode_label.background_color = "#111111"
        mode_label.frame = (300, y, 60, 22)
        v.add_subview(mode_label)

        seg_mode = ui.SegmentedControl()
        seg_mode.segments = ["combined", "per repo"]
        if args.mode == "pro-repo":
             seg_mode.selected_index = 1
        else:
             seg_mode.selected_index = 0
        seg_mode.frame = (360, y - 2, v.width - 370, 28)
        seg_mode.flex = "W"
        # Same accent color as detail segmented control
        seg_mode.tint_color = "#007aff"
        seg_mode.background_color = "#111111"
        v.add_subview(seg_mode)
        self.seg_mode = seg_mode

        y += 36

        max_label = ui.Label()
        max_label.text = "Max Bytes/File:"
        max_label.text_color = "white"
        max_label.background_color = "#111111"
        max_label.frame = (10, y, 120, 22)
        v.add_subview(max_label)

        max_field = ui.TextField()
        max_field.text = str(args.max_bytes)
        max_field.frame = (130, y - 2, 140, 28)
        max_field.flex = "W"
        _style_textfield(max_field)
        max_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        v.add_subview(max_field)
        self.max_field = max_field

        y += 36

        split_label = ui.Label()
        split_label.text = "Split Size (MB):"
        split_label.text_color = "white"
        split_label.background_color = "#111111"
        split_label.frame = (10, y, 120, 22)
        v.add_subview(split_label)

        split_field = ui.TextField()
        split_field.placeholder = "0 = No Split"
        split_field.text = args.split_size if args.split_size != "0" else ""
        split_field.frame = (130, y - 2, 140, 28)
        split_field.flex = "W"
        _style_textfield(split_field)
        split_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        v.add_subview(split_field)
        self.split_field = split_field

        y += 36

        info_label = ui.Label()
        info_label.text_color = "white"
        info_label.background_color = "#111111"
        info_label.font = ("<System>", 11)
        info_label.number_of_lines = 1
        info_label.frame = (10, y, v.width - 20, 18)
        info_label.flex = "W"
        v.add_subview(info_label)
        self.info_label = info_label
        self._update_repo_info()

        y += 26

        btn = ui.Button()
        btn.title = "Run Merge"
        btn.frame = (10, y, v.width - 20, 40)
        btn.flex = "W"
        btn.background_color = "#007aff"
        btn.tint_color = "white"
        btn.corner_radius = 6.0
        btn.action = self.run_merge
        v.add_subview(btn)
        self.run_button = btn

    def _update_repo_info(self) -> None:
        if not self.repos:
            self.info_label.text = "No repos found in Hub."
        else:
            self.info_label.text = f"{len(self.repos)} Repos found."

    def _tableview_cell(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.background_color = "#111111"
        if 0 <= row < len(self.repos):
            cell.text_label.text = self.repos[row]
        cell.text_label.text_color = "white"
        cell.text_label.background_color = "#111111"

        selected_bg = ui.View()
        selected_bg.background_color = "#333333"
        cell.selected_background_view = selected_bg
        return cell

    def _get_selected_repos(self) -> List[str]:
        tv = self.tv
        rows = tv.selected_rows or []
        if not rows:
            return list(self.repos)
        names: List[str] = []
        for section, row in rows:
            if 0 <= row < len(self.repos):
                names.append(self.repos[row])
        return names

    def _parse_max_bytes(self) -> int:
        txt = (self.max_field.text or "").strip()
        if not txt:
            return DEFAULT_MAX_BYTES
        try:
            val = int(txt)
            if val <= 0:
                raise ValueError()
            return val
        except Exception:
            return DEFAULT_MAX_BYTES

    def _parse_split_size(self) -> int:
        txt = (self.split_field.text or "").strip()
        if not txt:
            return 0
        try:
            # Assume MB if plain number in UI, or allow "1GB"
            if txt.isdigit():
                return int(txt) * 1024 * 1024
            return parse_human_size(txt)
        except Exception:
            return 0

    def run_merge(self, sender) -> None:
        try:
            self._run_merge_inner()
        except Exception as e:
            traceback.print_exc()
            msg = f"Error: {e}"
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(msg, file=sys.stderr)

    def _run_merge_inner(self) -> None:
        selected = self._get_selected_repos()
        if not selected:
            if console:
                console.alert("wc-merger", "No repos selected.", "OK", hide_cancel_button=True)
            return

        ext_text = (self.ext_field.text or "").strip()
        extensions = _normalize_ext_list(ext_text)

        path_contains = (self.path_field.text or "").strip() or None

        detail_idx = self.seg_detail.selected_index
        detail = ["overview", "summary", "dev", "max"][detail_idx]

        mode_idx = self.seg_mode.selected_index
        mode = ["gesamt", "pro-repo"][mode_idx]

        max_bytes = self._parse_max_bytes()
        split_size = self._parse_split_size()
        plan_only = False

        summaries = []
        for name in selected:
            root = self.hub / name
            if not root.is_dir():
                continue
            summary = scan_repo(root, extensions or None, path_contains, max_bytes)
            summaries.append(summary)

        if not summaries:
            if console:
                console.alert("wc-merger", "No valid repos found.", "OK", hide_cancel_button=True)
            return

        merges_dir = get_merges_dir(self.hub)
        out_paths = write_reports_v2(
            merges_dir,
            self.hub,
            summaries,
            detail,
            mode,
            max_bytes,
            plan_only,
            split_size,
            path_contains,
            extensions or None,
        )

        if not out_paths:
            if console:
                console.alert("wc-merger", "No report generated.", "OK", hide_cancel_button=True)
            else:
                print("No report generated.")
            return

        main_report = out_paths[0]
        if editor:
            try:
                editor.open_file(str(main_report))
            except Exception:
                pass

        msg = f"Generated {len(out_paths)} report(s)."
        if console:
            try:
                console.hud_alert(msg)
            except Exception:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
        else:
            print(f"wc-merger: OK ({msg})")
            for p in out_paths:
                print(f"  - {p.name}")


# --- CLI Mode ---

def _is_headless_requested() -> bool:
    # Headless wenn:
    # 1) --headless Flag, oder
    # 2) WC_HEADLESS=1 in der Umgebung, oder
    # 3) ui-Framework nicht verfügbar
    return ("--headless" in sys.argv) or (os.environ.get("WC_HEADLESS") == "1") or (ui is None)

def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="wc-merger CLI")
    parser.add_argument("paths", nargs="*", help="Repositories to merge")
    parser.add_argument("--hub", help="Base directory (wc-hub)")
    parser.add_argument("--level", choices=["overview", "summary", "dev", "max"], default="dev")
    parser.add_argument("--mode", choices=["gesamt", "pro-repo"], default="gesamt")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--split-size", help="Split output into chunks (e.g. 50MB, 1GB)")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--headless", action="store_true", help="Force headless (no Pythonista UI/editor)")

    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    hub = detect_hub_dir(script_path, args.hub)

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

    summaries = []
    for src in sources:
        print(f"Scanning {src.name}...")
        summary = scan_repo(src, None, None, args.max_bytes)
        summaries.append(summary)

    split_size = 0
    if args.split_size:
        split_size = parse_human_size(args.split_size)
        print(f"Splitting at {split_size} bytes")

    merges_dir = get_merges_dir(hub)
    out_paths = write_reports_v2(
        merges_dir,
        hub,
        summaries,
        args.level,
        args.mode,
        args.max_bytes,
        args.plan_only,
        split_size,
        debug=args.debug,
        path_filter=None,
        ext_filter=None,
    )

    print(f"Generated {len(out_paths)} report(s):")
    for p in out_paths:
        print(f"  - {p}")


def main():
    # Headless in Shortcuts-Extension erzwingen (kein ui/editor erlaubt).
    if not _is_headless_requested():
        script_path = Path(__file__).resolve()
        hub = detect_hub_dir(script_path)
        try:
            ui_obj = MergerUI(hub)
            ui_obj.view.present("sheet")
        except Exception as e:
            # Fallback auf CLI (headless), falls UI trotz ui-Import nicht verfügbar ist
            if console:
                console.alert("wc-merger", f"UI not available, falling back to CLI. ({e})", "OK", hide_cancel_button=True)
            main_cli()
    else:
        main_cli()

if __name__ == "__main__":
    main()
