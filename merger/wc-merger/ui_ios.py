# -*- coding: utf-8 -*-
import sys
import os
import json
import traceback
from pathlib import Path
from typing import List, Any, Dict, Optional

try:
    from core import (
        DEFAULT_LEVEL,
        DEFAULT_MODE,
        DEFAULT_MAX_FILE_BYTES,
        DEFAULT_SPLIT_SIZE,
        DEFAULT_EXTRAS,
        MERGES_DIR_NAME,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        MergeArtifacts,
        find_repos_in_hub,
        _pick_primary_artifact,
        _pick_human_md,
        parse_human_size,
        _parse_extras_csv,
        _load_wc_extractor_module,
    )
except ImportError:
    from .core import (
        DEFAULT_LEVEL,
        DEFAULT_MODE,
        DEFAULT_MAX_FILE_BYTES,
        DEFAULT_SPLIT_SIZE,
        DEFAULT_EXTRAS,
        MERGES_DIR_NAME,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        MergeArtifacts,
        find_repos_in_hub,
        _pick_primary_artifact,
        _pick_human_md,
        parse_human_size,
        _parse_extras_csv,
        _load_wc_extractor_module,
    )

try:
    import appex  # type: ignore
except Exception:
    appex = None  # type: ignore

try:
    import ui        # type: ignore
except Exception:
    ui = None        # type: ignore

try:
    TF_BORDER_NONE = ui.TEXT_FIELD_BORDER_NONE  # neuere Pythonista-Versionen
except Exception:
    TF_BORDER_NONE = 0  # Fallback: Standardwert, entspricht "kein Rahmen"

try:
    import console   # type: ignore
except Exception:
    console = None   # type: ignore

try:
    import editor    # type: ignore
except Exception:
    editor = None    # type: ignore

# Keep track of the currently presented Merger UI view (Pythonista).
_ACTIVE_MERGER_VIEW = None

# Copied from wc-merger.py for standalone usage if needed.
def safe_script_path() -> Path:
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
SCRIPT_DIR = SCRIPT_PATH.parent

LAST_STATE_FILENAME = ".wc-merger-state.json"

PROFILE_DESCRIPTIONS = {
    "overview": (
        "Index-Profil: Struktur + Manifest. "
        "Nur README / Runbooks / ai-context mit Inhalt."
    ),
    "summary": (
        "Doku-/Kontext-Profil: Docs, zentrale Config, CI, Contracts voll. "
        "Code größtenteils nur im Manifest."
    ),
    "dev": (
        "Arbeits-Profil: Code, Tests, Config, CI voll. "
        "Doku nur für README/Runbooks/ai-context voll."
    ),
    "machine-lean": (
        "Schlankes Maschinen-Profil: Manifest + Index + Content ohne Baum-Dekoration."
    ),
    "max": (
        "Vollsnapshot: alle Textdateien mit Inhalt (bis zum Max-Bytes-Limit pro Datei)."
    ),
}

PROFILE_PRESETS = {
    "overview": {
        "max_bytes": 0,
        "split_mb": 25,
    },
    "summary": {
        "max_bytes": 0,
        "split_mb": 25,
    },
    "dev": {
        "max_bytes": 0,
        "split_mb": 25,
    },
    "machine-lean": {
        "max_bytes": 0,
        "split_mb": 25,
    },
    "max": {
        "max_bytes": 0,
        "split_mb": 25,
    },
}

def force_close_files(paths: List[Path]) -> None:
    if editor is None:
        return

    try:
        open_files = editor.get_open_files()
    except Exception:
        return

    target_names = {p.name for p in paths}

    for fpath in open_files:
        if os.path.basename(fpath) in target_names:
            try:
                editor.close_file(fpath)
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to close {fpath}: {e}\n")

def _run_extractor_on_start(hub: Path) -> None:
    """Run wc-extractor automatically at app start (best-effort, quiet)."""
    try:
        extractor = _load_wc_extractor_module(SCRIPT_PATH)
        if extractor is None:
            return
        if hasattr(extractor, "run_extractor"):
            try:
                extractor.run_extractor(hub_override=hub, show_alert=False, incremental=True)
            except TypeError:
                extractor.run_extractor(hub)
            return
    except Exception:
        return

def _dismiss_view_best_effort(v) -> None:
    if v is None:
        return
    try:
        v.dismiss()
    except Exception:
        pass
    try:
        v.close()
    except Exception:
        pass
    try:
        if getattr(v, "superview", None) is not None:
            v.remove_from_superview()
    except Exception:
        pass

def run_ui(hub: Path) -> int:
    global _ACTIVE_MERGER_VIEW
    try:
        if _ACTIVE_MERGER_VIEW is not None:
            _dismiss_view_best_effort(_ACTIVE_MERGER_VIEW)
            _ACTIVE_MERGER_VIEW = None
    except Exception:
        pass

    _run_extractor_on_start(hub)

    ui_obj = MergerUI(hub)
    v = ui_obj.view
    _ACTIVE_MERGER_VIEW = v
    v.present('fullscreen', hide_title_bar=True)
    return 0

class MergerUI(object):
    def __init__(self, hub: Path) -> None:
        self.hub = hub
        self.repos = find_repos_in_hub(hub)

        self.ignore_mode = False
        self.ignored_repos = set()

        self._state_path = (self.hub / LAST_STATE_FILENAME).resolve()
        self._load_ignored_repos_from_state()

        try:
            mod = _load_wc_extractor_module(SCRIPT_PATH)
            try:
                mod.detect_hub(str(self.hub))
            except TypeError:
                mod.detect_hub(str(self.hub))
        except Exception as e:
            print(f"[extractor] warmup skipped: {e}")

        import argparse
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--level", default=DEFAULT_LEVEL)
        parser.add_argument("--mode", default=DEFAULT_MODE)
        parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
        parser.add_argument("--split-size", default=DEFAULT_SPLIT_SIZE)
        parser.add_argument("--extras", default=DEFAULT_EXTRAS)
        args, _ = parser.parse_known_args()

        self.extras_config = ExtrasConfig()
        if args.extras and args.extras.lower() != "none":
            for part in _parse_extras_csv(args.extras):
                if hasattr(self.extras_config, part):
                    setattr(self.extras_config, part, True)

        v = ui.View()
        v.name = "WC-Merger"
        v.background_color = "#111111"

        try:
            screen_w, screen_h = ui.get_screen_size()
            v.frame = (0, 0, screen_w, screen_h)
        except Exception:
            v.frame = (0, 0, 1024, 768)
        v.flex = "WH"

        self.view = v

        def _wrap_textfield_in_dark_bg(parent_view, tf):
            tf.background_color = None
            tf.text_color = "black"
            tf.tint_color = "#007aff"

            if hasattr(tf, "border_style"):
                try:
                    tf.border_style = TF_BORDER_NONE
                except Exception as e:
                    sys.stderr.write(f"Warning: Failed to set text field border style: {e}\n")

            parent_view.add_subview(tf)

        def _style_textfield(tf: ui.TextField) -> None:
            tf.autocorrection_type = False
            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE

        margin = 10
        top_padding = 22
        y = 10 + top_padding

        btn_width = 76
        btn_height = 28
        btn_margin_right = 10
        btn_spacing = 6

        close_btn = ui.Button()
        close_btn.title = "Close"
        close_btn.frame = (
            v.width - btn_margin_right - btn_width,
            y,
            btn_width,
            btn_height,
        )
        close_btn.flex = "L"
        close_btn.background_color = "#333333"
        close_btn.tint_color = "white"
        close_btn.corner_radius = 4.0
        close_btn.action = self.close_view
        v.add_subview(close_btn)
        self.close_button = close_btn

        select_all_btn = ui.Button()
        select_all_btn.title = "Set"
        select_all_btn.frame = (
            close_btn.frame[0] - btn_spacing - btn_width,
            close_btn.frame[1],
            btn_width,
            btn_height,
        )
        select_all_btn.flex = "L"
        select_all_btn.background_color = "#333333"
        select_all_btn.tint_color = "white"
        select_all_btn.corner_radius = 4.0
        select_all_btn.action = self.select_all_repos
        v.add_subview(select_all_btn)
        self.select_all_button = select_all_btn

        ignore_btn = ui.Button()
        ignore_btn.title = "Ignore…"
        ignore_btn.frame = (
            select_all_btn.frame[0] - btn_spacing - btn_width,
            close_btn.frame[1],
            btn_width,
            btn_height,
        )
        ignore_btn.flex = "L"
        ignore_btn.background_color = "#444444"
        ignore_btn.tint_color = "white"
        ignore_btn.corner_radius = 4.0
        ignore_btn.action = self.toggle_ignore_mode
        v.add_subview(ignore_btn)
        self.ignore_button = ignore_btn

        base_label = ui.Label()
        max_label_width = ignore_btn.frame[0] - 10 - 4
        base_label.frame = (10, y, max_label_width, 34)
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
        repo_label.frame = (10, y, v.width - 110, 20)
        repo_label.flex = "W"
        repo_label.text = "Repos (Tap = Auswahl, None = All, SET = Heimgewebe):"
        repo_label.text_color = "white"
        repo_label.background_color = "#111111"
        repo_label.font = ("<System>", 13)
        v.add_subview(repo_label)
        self._all_toggle_selected = False

        y += 22
        top_header_height = y

        cy = 10
        cw = v.width

        bottom_container = ui.View()
        bottom_container.frame = (0, 0, cw, 100)
        bottom_container.background_color = "#111111"

        ext_label = ui.Label(
            frame=(10, cy, 130, 24),
            text="Filter: Extensions",
            text_color="white",
            font=("<System>", 12),
        )
        bottom_container.add_subview(ext_label)

        self.ext_field = ui.TextField(
            frame=(140, cy, cw - 150, 28),
            placeholder=".py,.rs,.md (leer = alle)",
        )
        _style_textfield(self.ext_field)
        _wrap_textfield_in_dark_bg(bottom_container, self.ext_field)
        cy += 30

        path_label = ui.Label(
            frame=(10, cy, 130, 24),
            text="Filter: Pfad",
            text_color="white",
            font=("<System>", 12),
        )
        bottom_container.add_subview(path_label)

        self.path_field = ui.TextField(
            frame=(140, cy, cw - 150, 28),
            placeholder="z. B. merger/, src/, docs/",
        )
        _style_textfield(self.path_field)
        self.path_field.autocorrection_type = False
        self.path_field.spellchecking_type = False
        _wrap_textfield_in_dark_bg(bottom_container, self.path_field)
        cy += 36

        detail_label = ui.Label()
        detail_label.text = "Detail:"
        detail_label.text_color = "white"
        detail_label.background_color = "#111111"
        detail_label.frame = (10, cy, 60, 22)
        bottom_container.add_subview(detail_label)

        seg_detail = ui.SegmentedControl()
        seg_detail.segments = ["overview", "summary", "dev", "max"]
        try:
            seg_detail.selected_index = seg_detail.segments.index(args.level)
        except ValueError:
            seg_detail.selected_index = 2
        seg_detail.frame = (70, cy - 2, cw - 80, 28)
        seg_detail.flex = "W"
        seg_detail.tint_color = "#007aff"
        seg_detail.background_color = "#dddddd"
        seg_detail.action = self.on_profile_changed
        bottom_container.add_subview(seg_detail)
        self.seg_detail = seg_detail

        self.profile_hint = ui.Label(
            frame=(margin, cy + 28, cw - 2 * margin, 20),
            flex="W",
            text="",
            text_color="white",
            font=("<system>", 12),
        )
        bottom_container.add_subview(self.profile_hint)
        cy += 24 + 36

        mode_label = ui.Label()
        mode_label.text = "Mode:"
        mode_label.text_color = "white"
        mode_label.background_color = "#111111"
        mode_label.frame = (10, cy, 60, 22)
        bottom_container.add_subview(mode_label)

        seg_mode = ui.SegmentedControl()
        seg_mode.segments = ["combined", "per repo"]
        if args.mode == "pro-repo":
            seg_mode.selected_index = 1
        else:
            seg_mode.selected_index = 0
        seg_mode.frame = (70, cy - 2, cw - 80, 28)
        seg_mode.flex = "W"
        seg_mode.tint_color = "#007aff"
        seg_mode.background_color = "#dddddd"
        bottom_container.add_subview(seg_mode)
        self.seg_mode = seg_mode

        cy += 36

        max_label = ui.Label()
        max_label.text = "Max Bytes/File:"
        max_label.text_color = "white"
        max_label.background_color = "#111111"
        max_label.frame = (10, cy, 120, 22)
        bottom_container.add_subview(max_label)

        max_field = ui.TextField()
        if args.max_bytes and args.max_bytes > 0:
            max_field.text = str(args.max_bytes)
        else:
            max_field.text = ""
        max_field.frame = (130, cy - 2, 140, 28)
        max_field.flex = "W"
        max_field.placeholder = "0 / empty = unlimited"
        _style_textfield(max_field)
        max_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        _wrap_textfield_in_dark_bg(bottom_container, max_field)
        self.max_field = max_field

        cy += 36

        split_label = ui.Label()
        split_label.text = "Split Size (MB):"
        split_label.text_color = "white"
        split_label.background_color = "#111111"
        split_label.frame = (10, cy, 120, 22)
        bottom_container.add_subview(split_label)

        split_field = ui.TextField()
        split_field.placeholder = "leer/0 = kein Split"
        split_field.text = args.split_size if args.split_size != "0" else ""
        split_field.frame = (130, cy - 2, 140, 28)
        split_field.flex = "W"
        _style_textfield(split_field)
        split_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        _wrap_textfield_in_dark_bg(bottom_container, split_field)
        self.split_field = split_field

        cy += 36

        plan_label = ui.Label()
        plan_label.text = "Plan only:"
        plan_label.text_color = "white"
        plan_label.background_color = "#111111"
        plan_label.frame = (10, cy, 120, 22)
        bottom_container.add_subview(plan_label)

        plan_switch = ui.Switch()
        plan_switch.frame = (130, cy - 2, 60, 32)
        plan_switch.flex = "W"
        plan_switch.value = False
        bottom_container.add_subview(plan_switch)
        self.plan_only_switch = plan_switch

        code_label = ui.Label()
        code_label.text = "Code only:"
        code_label.text_color = "white"
        code_label.background_color = "#111111"
        code_label.frame = (210, cy, 120, 22)
        bottom_container.add_subview(code_label)

        code_switch = ui.Switch()
        code_switch.frame = (330, cy - 2, 60, 32)
        code_switch.flex = "W"
        code_switch.value = False
        bottom_container.add_subview(code_switch)
        self.code_only_switch = code_switch

        cy += 36

        info_label = ui.Label()
        info_label.text_color = "white"
        info_label.background_color = "#111111"
        info_label.font = ("<System>", 11)
        info_label.number_of_lines = 1
        info_label.frame = (10, cy, cw - 20, 18)
        info_label.flex = "W"
        bottom_container.add_subview(info_label)
        self.info_label = info_label
        self._update_repo_info()

        self.on_profile_changed(None)

        cy += 26 + 10

        small_btn_height = 32

        extras_btn = ui.Button()
        extras_btn.title = "Extras..."
        extras_btn.font = ("<System>", 14)
        extras_btn.frame = (10, cy, cw - 20, small_btn_height)
        extras_btn.flex = "W"
        extras_btn.background_color = "#333333"
        extras_btn.tint_color = "white"
        extras_btn.corner_radius = 6.0
        extras_btn.action = self.show_extras_sheet
        bottom_container.add_subview(extras_btn)

        cy += small_btn_height + 10

        load_btn = ui.Button()
        load_btn.title = "Load Last Config"
        load_btn.font = ("<System>", 14)
        load_btn.frame = (10, cy, cw - 20, small_btn_height)
        load_btn.flex = "W"
        load_btn.background_color = "#333333"
        load_btn.tint_color = "white"
        load_btn.corner_radius = 6.0
        load_btn.action = self.restore_last_state
        bottom_container.add_subview(load_btn)

        cy += small_btn_height + 10

        delta_btn = ui.Button()
        delta_btn.title = "Delta from Last Import"
        delta_btn.font = ("<System>", 14)
        delta_btn.frame = (10, cy, cw - 20, small_btn_height)
        delta_btn.flex = "W"
        delta_btn.background_color = "#444444"
        delta_btn.tint_color = "white"
        delta_btn.corner_radius = 6.0
        delta_btn.action = self.run_delta_from_last_import
        bottom_container.add_subview(delta_btn)
        self.delta_button = delta_btn

        cy += small_btn_height + 10

        run_height = 40
        btn = ui.Button()
        btn.title = "Run Merge"
        btn.frame = (10, cy, cw - 20, run_height)
        btn.flex = "W"
        btn.background_color = "#007aff"
        btn.tint_color = "white"
        btn.corner_radius = 6.0
        btn.action = self.run_merge
        bottom_container.add_subview(btn)
        self.run_button = btn

        cy += run_height + 24

        container_height = cy

        bottom_container.frame = (0, v.height - container_height, v.width, container_height)
        bottom_container.flex = "WT"
        v.add_subview(bottom_container)

        list_height = v.height - top_header_height - container_height

        tv = ui.TableView()
        tv.frame = (10, top_header_height, v.width - 20, list_height)
        tv.flex = "WH"
        tv.background_color = "#111111"
        tv.separator_color = "#333333"
        tv.row_height = 32
        tv.allows_multiple_selection = True
        tv.tint_color = "#007aff"

        ds = ui.ListDataSource(self.repos)
        ds.text_color = "white"
        ds.action = self._on_repo_selection_changed
        ds.tableview_did_select = self._tableview_did_select
        ds.tableview_did_deselect = self._tableview_did_deselect
        ds.highlight_color = "#0050ff"
        ds.tableview_cell_for_row = self._tableview_cell
        tv.data_source = ds
        tv.delegate = ds
        v.add_subview(tv)
        self.tv = tv
        self.ds = ds

        self._update_repo_info()

    def _tableview_did_select(self, tableview, section, row):
        if self.ignore_mode:
            self._update_repo_info()
            return
        self._on_repo_selection_changed(tableview)

    def _tableview_did_deselect(self, tableview, section, row):
        if self.ignore_mode:
            self._update_repo_info()
            return
        self._on_repo_selection_changed(tableview)

    def _on_repo_selection_changed(self, sender) -> None:
        self._update_repo_info()

    def _update_repo_info(self) -> None:
        if not self.repos:
            self.info_label.text = "No repos found in Hub."
            return

        total = len(self.repos)
        tv = getattr(self, "tv", None)
        if tv is None:
            self.info_label.text = f"{total} Repos found."
            return

        rows = tv.selected_rows or []
        if not rows:
            self.info_label.text = f"{total} Repos found."
        else:
            self.info_label.text = f"{total} Repos found ({len(rows)} selected)."

    def toggle_ignore_mode(self, sender) -> None:
        self.ignore_mode = not self.ignore_mode

        if self.ignore_mode:
            self.tv.selected_rows = [
                (0, idx) for idx, name in enumerate(self.repos)
                if name in self.ignored_repos
            ]
            self.ignore_button.title = "Save"
        else:
            rows = self.tv.selected_rows or []
            newly_ignored: set[str] = set()

            for sec, idx in rows:
                if sec == 0 and 0 <= idx < len(self.repos):
                    newly_ignored.add(self.repos[idx])

            if newly_ignored:
                self.ignored_repos = newly_ignored
            self.ignore_button.title = "Ignore…"
            self.save_last_state(ignore_only=True)

            self.tv.selected_rows = []

        self._update_repo_info()

    def select_all_repos(self, sender) -> None:
        if not self.repos:
            return

        excluded = self.ignored_repos
        tv = self.tv

        rows: List[tuple[int, int]] = []
        for idx, name in enumerate(self.repos):
            if name in excluded:
                continue
            rows.append((0, idx))

        if not rows:
            tv.selected_rows = []
        else:
            tv.selected_rows = rows

        self._update_repo_info()

    def close_view(self, sender=None) -> None:
        global _ACTIVE_MERGER_VIEW
        try:
            _dismiss_view_best_effort(self.view)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to close view: {e}\n")
        finally:
            try:
                if _ACTIVE_MERGER_VIEW is self.view:
                    _ACTIVE_MERGER_VIEW = None
            except Exception:
                pass

    def show_extras_sheet(self, sender):
        s = ui.View()
        s.name = "Extras"
        s.background_color = "#222222"

        items = [
            ("Repo Health Checks", "health"),
            ("Organism Index", "organism_index"),
            ("Fleet Panorama", "fleet_panorama"),
            ("Delta Reports", "delta_reports"),
            ("Augment Sidecar", "augment_sidecar"),
            ("AI Heatmap", "heatmap"),
            ("JSON Sidecar", "json_sidecar")
        ]

        row_h = 44
        padding_top = 20
        padding_bottom = 20
        title_height = 50

        dynamic_h = padding_top + title_height + len(items) * row_h + padding_bottom + 60
        dynamic_h = max(260, min(dynamic_h, 540))

        s.frame = (0, 0, 420, dynamic_h)

        y = 20
        margin = 20
        w = s.width - 2 * margin

        lbl = ui.Label(frame=(margin, y, w, 40))
        lbl.text = "Optionale Zusatzanalysen\n(Health, Organism, etc.)"
        lbl.number_of_lines = 2
        lbl.text_color = "white"
        lbl.alignment = ui.ALIGN_CENTER
        s.add_subview(lbl)
        y += 50

        def add_switch(key, title):
            nonlocal y
            sw = ui.Switch()
            sw.value = getattr(self.extras_config, key)
            sw.name = key
            def action(sender):
                setattr(self.extras_config, key, sender.value)
            sw.action = action
            sw.frame = (w - 60, y, 60, 32)

            l = ui.Label(frame=(margin, y, w - 70, 32))
            l.text = title
            l.text_color = "white"

            s.add_subview(l)
            s.add_subview(sw)
            y += row_h

        for title, key in items:
            add_switch(key, title)

        y += 10
        btn = ui.Button(frame=(margin, y, w, 40))
        btn.title = "Done"
        btn.background_color = "#007aff"
        btn.tint_color = "white"
        btn.corner_radius = 6
        def close_action(sender):
            s.close()
        btn.action = close_action
        s.add_subview(btn)

        s.present("sheet")

    def on_profile_changed(self, sender):
        idx = self.seg_detail.selected_index
        if not (0 <= idx < len(self.seg_detail.segments)):
            return

        seg_name = self.seg_detail.segments[idx]

        desc = PROFILE_DESCRIPTIONS.get(seg_name, "")
        self.profile_hint.text = desc

        preset = PROFILE_PRESETS.get(seg_name)
        if preset:
            max_bytes = preset.get("max_bytes", 0)
            if max_bytes is None or max_bytes <= 0:
                self.max_field.text = ""
            else:
                try:
                    self.max_field.text = str(int(max_bytes))
                except Exception:
                    self.max_field.text = ""

            split_mb = preset.get("split_mb")
            if split_mb is None or (
                isinstance(split_mb, (int, float)) and split_mb <= 0
            ):
                self.split_field.text = ""
            else:
                try:
                    self.split_field.text = str(int(split_mb))
                except Exception:
                    self.split_field.text = ""

    def _collect_selected_repo_names(self) -> List[str]:
        ds = self.ds
        selected: List[str] = []
        if hasattr(ds, "items"):
            rows = getattr(self.tv, "selected_rows", None) or []
            for idx, name in enumerate(ds.items):
                if any(sec == 0 and r == idx for sec, r in rows):
                    selected.append(name)
        return selected

    def _apply_selected_repo_names(self, names: List[str]) -> None:
        ds = self.ds
        if not hasattr(ds, "items"):
            return

        name_to_index = {name: i for i, name in enumerate(ds.items)}

        rows = []
        for name in names:
            idx = name_to_index.get(name)
            if idx is not None:
                rows.append((0, idx))

        if not rows:
            return

        tv = self.tv
        try:
            tv.selected_rows = rows
        except Exception:
            try:
                tv.selected_row = rows[0]
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to select row in fallback: {e}\n")

    def _load_ignored_repos_from_state(self) -> None:
        try:
            raw = self._state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return
        except Exception as exc:
            print(f"[wc-merger] could not read ignore state: {exc!r}")
            return

        try:
            data = json.loads(raw)
        except Exception as exc:
            print(f"[wc-merger] invalid ignore state JSON: {exc!r}")
            return

        if isinstance(data, dict):
            self.ignored_repos = set(data.get("ignored_repos", []))

    def save_last_state(self, ignore_only: bool = False) -> None:
        data: Dict[str, Any] = {}

        if self._state_path.exists():
            try:
                raw = self._state_path.read_text(encoding="utf-8")
                existing = json.loads(raw)
                if isinstance(existing, dict):
                    data.update(existing)
            except Exception as exc:
                print(f"[wc-merger] could not read existing state: {exc!r}")

        data["ignored_repos"] = sorted(self.ignored_repos)

        if not ignore_only:
            profile = None
            try:
                segments = getattr(self.seg_detail, "segments", [])
                idx = getattr(self.seg_detail, "selected_index", 0)
                if 0 <= idx < len(segments):
                    profile = segments[idx]
            except Exception:
                profile = None

            if profile is not None:
                data["detail_profile"] = profile

            data.update(
                {
                    "ext_filter": self.ext_field.text or "",
                    "path_filter": self.path_field.text or "",
                    "max_bytes": self.max_field.text or "",
                    "split_mb": self.split_field.text or "",
                    "plan_only": bool(self.plan_only_switch.value),
                    "code_only": bool(getattr(self, "code_only_switch", False) and self.code_only_switch.value),
                    "selected_repos": self._get_selected_repos(),
                    "extras": {
                        "health": self.extras_config.health,
                        "organism_index": self.extras_config.organism_index,
                        "fleet_panorama": self.extras_config.fleet_panorama,
                        "delta_reports": self.extras_config.delta_reports,
                        "augment_sidecar": self.extras_config.augment_sidecar,
                        "heatmap": self.extras_config.heatmap,
                        "json_sidecar": self.extras_config.json_sidecar,
                    },
                }
            )

        try:
            self._state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[wc-merger] could not persist state: {exc}")

    def restore_last_state(self, sender=None) -> None:
        try:
            raw = self._state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            if sender:
                if console:
                    console.alert("wc-merger", "No saved state found.", "OK", hide_cancel_button=True)
            return
        except Exception as exc:
            print(f"[wc-merger] could not read state: {exc!r}")
            return

        try:
            data = json.loads(raw)
        except Exception as exc:
            print(f"[wc-merger] invalid state JSON: {exc!r}")
            return

        profile = data.get("detail_profile")
        if profile and profile in self.seg_detail.segments:
            try:
                self.seg_detail.selected_index = self.seg_detail.segments.index(profile)
            except ValueError:
                pass

        self.ext_field.text = data.get("ext_filter", "")
        self.path_field.text = data.get("path_filter", "")
        self.max_field.text = data.get("max_bytes", "")
        self.split_field.text = data.get("split_mb", "")
        self.plan_only_switch.value = bool(data.get("plan_only", False))
        if getattr(self, "code_only_switch", None) is not None:
            self.code_only_switch.value = bool(data.get("code_only", False))

        self.ignored_repos = set(data.get("ignored_repos", []))

        extras_data = data.get("extras", {})
        if extras_data:
            self.extras_config.health = extras_data.get("health", False)
            self.extras_config.organism_index = extras_data.get("organism_index", False)
            self.extras_config.fleet_panorama = extras_data.get("fleet_panorama", False)
            self.extras_config.delta_reports = extras_data.get("delta_reports", False)
            self.extras_config.augment_sidecar = extras_data.get("augment_sidecar", False)
            self.extras_config.heatmap = extras_data.get("heatmap", False)
            self.extras_config.json_sidecar = extras_data.get("json_sidecar", False)

        self.on_profile_changed(None)

        selected = data.get("selected_repos") or []
        if selected:
            self._apply_selected_repo_names(selected)

        if sender and console:
            try:
                console.hud_alert("Config loaded")
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to show HUD alert: {e}\n")

        self._update_repo_info()


    def _tableview_cell(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.background_color = "#111111"
        if 0 <= row < len(self.repos):
            cell.text_label.text = self.repos[row]
        cell.text_label.text_color = "white"
        cell.text_label.background_color = "#111111"

        selected_bg = ui.View()
        selected_bg.background_color = "#0050ff"
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
            return 0

        try:
            val = parse_human_size(txt)
        except Exception:
            val = 0

        if val <= 0:
            return 0
        return val

    def _parse_split_size(self) -> int:
        txt = (self.split_field.text or "").strip()
        if not txt:
            return 0
        try:
            if txt.isdigit():
                return int(txt) * 1024 * 1024
            return parse_human_size(txt)
        except Exception:
            return 0

    def run_delta_from_last_import(self, sender) -> None:
        """
        Erzeugt einen Delta-Merge aus dem neuesten Import-Diff im merges-Ordner.
        """
        merges_dir = get_merges_dir(self.hub)
        try:
            candidates = list(merges_dir.glob("*-import-diff-*.md"))
        except Exception as exc:
            print(f"[wc-merger] could not scan merges dir: {exc}")
            candidates = []

        if not candidates:
            if console:
                console.alert(
                    "wc-merger",
                    "No import diff found.",
                    "OK",
                    hide_cancel_button=True,
                )
            else:
                print("[wc-merger] No import diff found.")
            return

        try:
            diff_path = max(candidates, key=lambda p: p.stat().st_mtime)
        except Exception as exc:
            if console:
                console.alert(
                    "wc-merger",
                    f"Failed to select latest diff: {exc}",
                    "OK",
                    hide_cancel_button=True,
                )
            else:
                print(f"[wc-merger] Failed to select latest diff: {exc}")
            return

        name = diff_path.name
        prefix = "-import-diff-"
        if prefix in name:
            repo_name = name.split(prefix, 1)[0]
        else:
            repo_name = name

        repo_root = self.hub / repo_name
        if not repo_root.exists():
            msg = f"Repo root not found for diff {diff_path.name}"
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[wc-merger] {msg}")
            return

        mod = _load_wc_extractor_module(SCRIPT_PATH)
        if mod is None:
            msg = "Delta helper (wc-extractor) not available."
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[wc-merger] {msg}")
            return

        try:
            # FIX: Do NOT call create_delta_merge_from_diff.
            # Use extract_delta_meta_from_diff_file to get data,
            # then let write_reports_v2 generate the report.
            delta_meta = None
            if hasattr(mod, "extract_delta_meta_from_diff_file"):
                delta_meta = mod.extract_delta_meta_from_diff_file(diff_path)

            if not delta_meta:
                msg = "Could not extract delta metadata from diff file."
                if console:
                    console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
                else:
                    print(f"[wc-merger] {msg}")
                return

            extras = ExtrasConfig(
                health=self.extras_config.health,
                organism_index=self.extras_config.organism_index,
                fleet_panorama=self.extras_config.fleet_panorama,
                augment_sidecar=self.extras_config.augment_sidecar,
                heatmap=self.extras_config.heatmap,
                delta_reports=True
            )

            summary = scan_repo(repo_root, extensions=None, path_contains=None, max_bytes=0)

            artifacts = write_reports_v2(
                merges_dir,
                self.hub,
                [summary],
                "dev",
                "repo",
                0,
                plan_only=False,
                code_only=False,
                debug=False,
                path_filter=None,
                ext_filter=None,
                extras=extras,
                delta_meta=delta_meta,
            )

            out_paths = artifacts.get_all_paths()
            force_close_files(out_paths)

            primary_path = artifacts.get_primary_path()
            msg = (
                f"Delta report generated: {primary_path.name}"
                if primary_path is not None
                else "Delta report generated"
            )
            if console:
                try:
                    console.hud_alert(msg)
                except Exception:
                    console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[wc-merger] {msg}")

        except Exception as exc:
            msg = f"Delta merge failed: {exc}"
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[wc-merger] {msg}")
            return

    def run_merge(self, sender) -> None:
        try:
            self.save_last_state()
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

        plan_switch = getattr(self, "plan_only_switch", None)
        plan_only = bool(plan_switch and plan_switch.value)
        code_switch = getattr(self, "code_only_switch", None)
        code_only = bool(code_switch and code_switch.value)

        if plan_only and code_only:
            code_only = False

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

        # Try to extract delta_meta if delta_reports is enabled (similar to CLI)
        delta_meta = None
        if self.extras_config.delta_reports and summaries and len(summaries) == 1:
            repo_name = summaries[0]["name"]
            try:
                mod = _load_wc_extractor_module(SCRIPT_PATH)
                if mod and hasattr(mod, "find_latest_diff_for_repo") and hasattr(mod, "extract_delta_meta_from_diff_file"):
                    diff_path = mod.find_latest_diff_for_repo(merges_dir, repo_name)
                    if diff_path:
                        delta_meta = mod.extract_delta_meta_from_diff_file(diff_path)
            except Exception as e:
                print(f"Warning: Could not extract delta metadata: {e}")

        artifacts = write_reports_v2(
            merges_dir,
            self.hub,
            summaries,
            detail,
            mode,
            max_bytes,
            plan_only,
            code_only,
            split_size,
            debug=False,
            path_filter=path_contains,
            ext_filter=extensions or None,
            extras=self.extras_config,
            delta_meta=delta_meta,
        )

        out_paths = artifacts.get_all_paths()
        if not out_paths:
            if console:
                console.alert("wc-merger", "No report generated.", "OK", hide_cancel_button=True)
            else:
                print("No report generated.")
            return

        force_close_files(out_paths)

        primary = _pick_primary_artifact(out_paths)
        human_md = _pick_human_md(out_paths)
        if primary and human_md and primary != human_md:
            msg = f"Merge generated: {primary.name} (human: {human_md.name})"
            status = "success"
        elif primary:
            msg = f"Merge generated: {primary.name}"
            status = "success"
        else:
            msg = "Merge failed: no artifacts returned"
            status = "error"

        if console:
            try:
                console.hud_alert(msg, status, 1.2 if status == "success" else 1.5)
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to show HUD alert (falling back to alert): {e}\n")
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
        else:
            print(f"wc-merger: {msg}")
            for p in out_paths:
                print(f"  - {p.name}")
