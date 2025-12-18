#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
repoLens – A structural lens for repositories.
Enhanced AI-optimized reports with strict Pflichtenheft structure.

Default-Config (Dec 2025)
------------------------
- level: max
- mode: gesamt (UI: combined)
- split: ON via split-size default (25MB)
- max-bytes: 0 (keine Kürzung einzelner Dateien)
- extras default ON:
  health, augment_sidecar, organism_index, fleet_panorama, json_sidecar, ai_heatmap

Rationale:
- max-bytes auf Dateiebene ist semantisch riskant (halbe Datei = halbe Wahrheit).
- Split ist logistisch: alles bleibt drin, nur auf mehrere Parts verteilt.
"""

import sys
import os
import json
import traceback
import time
from pathlib import Path
from typing import List, Any, Dict, Optional, Set


DEFAULT_LEVEL = "max"
DEFAULT_MODE = "gesamt"  # combined
DEFAULT_SPLIT_SIZE = "25MB"
DEFAULT_MAX_FILE_BYTES = 0
DEFAULT_EXTRAS = "health,augment_sidecar,organism_index,fleet_panorama,json_sidecar,heatmap"

try:
    import appex  # type: ignore
except Exception:
    appex = None  # type: ignore

# Try importing Pythonista modules
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
# This prevents stacking multiple fullscreen windows when the script is opened repeatedly.
_ACTIVE_MERGER_VIEW = None


def safe_script_path() -> Path:
    """
    Versucht, den Pfad dieses Skripts robust zu bestimmen.

    Reihenfolge:
    1. __file__ (Standard-Python)
    2. sys.argv[0] (z. B. in Shortcuts / eingebetteten Umgebungen)
    3. aktuelle Arbeitsdirectory (Last Resort)
    """
    try:
        return Path(__file__).resolve()
    except NameError:
        # Pythonista / Shortcuts oder exotischer Kontext
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

        # Fallback: aktuelle Arbeitsdirectory
        return Path.cwd().resolve()


# Cache script path at module level for consistent behavior
SCRIPT_PATH = safe_script_path()
SCRIPT_DIR = SCRIPT_PATH.parent


def force_close_files(paths: List[Path]) -> None:
    """
    Ensures generated files are not left open in the editor.
    """
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


# Merger-UI merkt sich die letzte Auswahl in dieser JSON-Datei im Hub:
LAST_STATE_FILENAME = ".repoLens-state.json"

# Import core logic
try:
    from merge_core import (
        MERGES_DIR_NAME,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        MergeArtifacts,
    parse_human_size,
    )
except ImportError:
    sys.path.append(str(SCRIPT_DIR))
    from merge_core import (
        MERGES_DIR_NAME,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
        MergeArtifacts,
        parse_human_size,
    )

PROFILE_DESCRIPTIONS = {
    # Kurzbeschreibung der Profile für den UI-Hint
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

# Voreinstellungen pro Profil:
# - Split-Größe (Part-Größe): standardmäßig 25 MB, d. h. große Merges
#   werden in mehrere Dateien aufgeteilt – es gibt aber kein Gesamtlimit.
# - Max Bytes/File: 0 = unbegrenzt (volle Dateien), Limit nur,
#   wenn explizit gesetzt.
PROFILE_PRESETS = {
    "overview": {
        # 0 → „kein per-File-Limit“
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


def _pick_primary_artifact(paths):
    # Prefer primary JSON for agent chains, else fallback to markdown.
    for p in paths:
        try:
            if str(p).lower().endswith(".json"):
                return p
        except Exception:
            pass
    for p in paths:
        try:
            if str(p).lower().endswith(".md"):
                return p
        except Exception:
            pass
    return paths[0] if paths else None


def _pick_human_md(paths) -> Optional[Path]:
    for p in paths:
        try:
            if str(p).lower().endswith(".md"):
                return p
        except Exception:
            pass
    return None


def _parse_extras_csv(extras_csv: str) -> List[str]:
    items = [x.strip().lower() for x in (extras_csv or "").split(",") if x.strip()]
    normalized = []
    for item in items:
        if item == "ai_heatmap":
            item = "heatmap"
        normalized.append(item)
    return normalized


def _load_repolens_extractor_module():
    """Dynamically load repolens-extractor.py from the same directory."""
    from importlib.machinery import SourceFileLoader
    import types

    extractor_path = SCRIPT_PATH.with_name("repolens-extractor.py")
    if not extractor_path.exists():
        return None
    try:
        loader = SourceFileLoader("repolens_extractor", str(extractor_path))
        mod = types.ModuleType(loader.name)
        loader.exec_module(mod)
        return mod
    except Exception as exc:
        print(f"[repoLens] could not load repolens-extractor: {exc}")
        return None


# --- UI Class (Pythonista) ---

def _run_extractor_on_start(hub: Path) -> None:
    """Run repolens-extractor automatically at app start (best-effort, quiet)."""
    try:
        extractor = _load_repolens_extractor_module()
        if extractor is None:
            return
        if hasattr(extractor, "run_extractor"):
            try:
                extractor.run_extractor(hub_override=hub, show_alert=False, incremental=True)
            except TypeError:
                extractor.run_extractor(hub)
            return
    except Exception as e:
        sys.stderr.write(f"[repoLens] Extractor auto-run warning: {e}\n")
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
    """Starte den Merger im Vollbild-UI-Modus ohne Pythonista-Titlebar."""
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

        # Ignore-Konfiguration für das Heimgewebe-Set
        self.ignore_mode = False
        self.ignored_repos = set()

        # Repo Sets (Benannte Gruppen)
        self.repo_sets: Dict[str, List[str]] = {}

        # Pfad zur State-Datei
        self._state_path = (self.hub / LAST_STATE_FILENAME).resolve()

        # Basis-Konfig laden (Ignore, Sets, Defaults)
        self._load_state_initial()

        # Auto-run / warm the extractor on startup (best-effort).
        try:
            mod = _load_repolens_extractor_module()
            try:
                mod.detect_hub(str(self.hub))
            except TypeError:
                mod.detect_hub()
        except Exception as e:
            print(f"[extractor] warmup skipped: {e}")

        # Basic argv parsing for UI defaults
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
                except Exception:
                    pass
            parent_view.add_subview(tf)

        def _style_textfield(tf: ui.TextField) -> None:
            tf.autocorrection_type = False
            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE

        margin = 10
        top_padding = 22
        y = 10 + top_padding

        # --- TOP HEADER ---
        btn_width = 76
        btn_height = 28
        btn_margin_right = 10
        btn_spacing = 6

        # Close
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

        # Smart All (formerly Set)
        select_all_btn = ui.Button()
        select_all_btn.title = "Smart All"
        select_all_btn.font = ("<System-Bold>", 13)
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

        # Sets Button (New)
        sets_btn = ui.Button()
        sets_btn.title = "Sets..."
        sets_btn.frame = (
            select_all_btn.frame[0] - btn_spacing - btn_width,
            close_btn.frame[1],
            btn_width,
            btn_height,
        )
        sets_btn.flex = "L"
        sets_btn.background_color = "#007aff"
        sets_btn.tint_color = "white"
        sets_btn.corner_radius = 4.0
        sets_btn.action = self.show_sets_sheet
        v.add_subview(sets_btn)
        self.sets_button = sets_btn

        # Ignore
        ignore_btn = ui.Button()
        ignore_btn.title = "Ignore…"
        ignore_btn.frame = (
            sets_btn.frame[0] - btn_spacing - btn_width,
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

        # Base-Dir-Label
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
        repo_label.frame = (10, y, v.width - 20, 20)
        repo_label.flex = "W"
        repo_label.text = "Repos (Tap = Auswahl, None = All, Smart All = Ignore-Filter):"
        repo_label.text_color = "white"
        repo_label.background_color = "#111111"
        repo_label.font = ("<System>", 13)
        v.add_subview(repo_label)

        y += 22
        top_header_height = y

        # --- BOTTOM SETTINGS & ACTIONS ---
        cy = 10
        cw = v.width

        bottom_container = ui.View()
        bottom_container.frame = (0, 0, cw, 100)
        bottom_container.background_color = "#111111"

        # Filters
        ext_label = ui.Label(frame=(10, cy, 130, 24), text="Filter: Extensions", text_color="white", font=("<System>", 12))
        bottom_container.add_subview(ext_label)
        self.ext_field = ui.TextField(frame=(140, cy, cw - 150, 28), placeholder=".py,.rs,.md (leer = alle)")
        _style_textfield(self.ext_field)
        _wrap_textfield_in_dark_bg(bottom_container, self.ext_field)
        cy += 30

        path_label = ui.Label(frame=(10, cy, 130, 24), text="Filter: Pfad", text_color="white", font=("<System>", 12))
        bottom_container.add_subview(path_label)
        self.path_field = ui.TextField(frame=(140, cy, cw - 150, 28), placeholder="z. B. merger/, src/, docs/")
        _style_textfield(self.path_field)
        self.path_field.autocorrection_type = False
        self.path_field.spellchecking_type = False
        _wrap_textfield_in_dark_bg(bottom_container, self.path_field)
        cy += 36

        # Detail
        detail_label = ui.Label(frame=(10, cy, 60, 22), text="Detail:", text_color="white", background_color="#111111")
        bottom_container.add_subview(detail_label)

        seg_detail = ui.SegmentedControl()
        seg_detail.segments = ["overview", "summary", "dev", "max"]
        try:
            seg_detail.selected_index = seg_detail.segments.index(args.level)
        except ValueError:
            seg_detail.selected_index = 3  # Default to 'max' (index 3)
        seg_detail.frame = (70, cy - 2, cw - 80, 28)
        seg_detail.flex = "W"
        seg_detail.tint_color = "#007aff"
        seg_detail.background_color = "#dddddd"
        seg_detail.action = self.on_profile_changed
        bottom_container.add_subview(seg_detail)
        self.seg_detail = seg_detail

        self.profile_hint = ui.Label(frame=(margin, cy + 28, cw - 2 * margin, 20), flex="W", text="", text_color="white", font=("<system>", 12))
        bottom_container.add_subview(self.profile_hint)
        cy += 24 + 36

        # Mode
        mode_label = ui.Label(frame=(10, cy, 60, 22), text="Mode:", text_color="white", background_color="#111111")
        bottom_container.add_subview(mode_label)
        seg_mode = ui.SegmentedControl(segments=["combined", "per repo"])
        seg_mode.selected_index = 1 if args.mode == "pro-repo" else 0
        seg_mode.frame = (70, cy - 2, cw - 80, 28)
        seg_mode.flex = "W"
        seg_mode.tint_color = "#007aff"
        seg_mode.background_color = "#dddddd"
        bottom_container.add_subview(seg_mode)
        self.seg_mode = seg_mode
        cy += 36

        # Limits
        max_label = ui.Label(frame=(10, cy, 120, 22), text="Max Bytes/File:", text_color="white", background_color="#111111")
        bottom_container.add_subview(max_label)
        max_field = ui.TextField(frame=(130, cy - 2, 140, 28), placeholder="0 / empty = unlimited")
        max_field.flex = "W"
        if args.max_bytes and args.max_bytes > 0: max_field.text = str(args.max_bytes)
        _style_textfield(max_field)
        max_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        _wrap_textfield_in_dark_bg(bottom_container, max_field)
        self.max_field = max_field
        cy += 36

        split_label = ui.Label(frame=(10, cy, 120, 22), text="Split Size (MB):", text_color="white", background_color="#111111")
        bottom_container.add_subview(split_label)
        split_field = ui.TextField(frame=(130, cy - 2, 140, 28), placeholder="leer/0 = kein Split")
        split_field.flex = "W"
        raw_split = (getattr(args, "split_size", "") or "").strip()
        if raw_split and raw_split != "0":
            if raw_split.isdigit():
                split_field.text = raw_split
            else:
                try:
                    mb = int(round(parse_human_size(raw_split) / (1024 * 1024)))
                    split_field.text = str(mb) if mb > 0 else ""
                except Exception:
                    split_field.text = raw_split
        _style_textfield(split_field)
        split_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        _wrap_textfield_in_dark_bg(bottom_container, split_field)
        self.split_field = split_field
        cy += 36

        # Plan Only / Code Only
        plan_label = ui.Label(frame=(10, cy, 120, 22), text="Plan only:", text_color="white", background_color="#111111")
        bottom_container.add_subview(plan_label)
        plan_switch = ui.Switch(frame=(130, cy - 2, 60, 32))
        plan_switch.flex = "W"
        plan_switch.value = False
        bottom_container.add_subview(plan_switch)
        self.plan_only_switch = plan_switch

        code_label = ui.Label(frame=(210, cy, 120, 22), text="Code only:", text_color="white", background_color="#111111")
        bottom_container.add_subview(code_label)
        code_switch = ui.Switch(frame=(330, cy - 2, 60, 32))
        code_switch.flex = "W"
        code_switch.value = False
        bottom_container.add_subview(code_switch)
        self.code_only_switch = code_switch
        cy += 36

        # Info Label
        info_label = ui.Label(frame=(10, cy, cw - 20, 18), text_color="white", background_color="#111111", font=("<System>", 11))
        info_label.flex = "W"
        bottom_container.add_subview(info_label)
        self.info_label = info_label
        self._update_repo_info()

        self.on_profile_changed(None)
        cy += 26 + 10

        # Actions
        small_btn_height = 32
        extras_btn = ui.Button(title="Extras...", font=("<System>", 14), frame=(10, cy, cw - 20, small_btn_height))
        extras_btn.flex = "W"
        extras_btn.background_color = "#333333"
        extras_btn.tint_color = "white"
        extras_btn.corner_radius = 6.0
        extras_btn.action = self.show_extras_sheet
        bottom_container.add_subview(extras_btn)
        cy += small_btn_height + 10

        load_btn = ui.Button(title="Reload Last Config", font=("<System>", 14), frame=(10, cy, cw - 20, small_btn_height))
        load_btn.flex = "W"
        load_btn.background_color = "#333333"
        load_btn.tint_color = "white"
        load_btn.corner_radius = 6.0
        load_btn.action = self.restore_last_state
        bottom_container.add_subview(load_btn)
        cy += small_btn_height + 10

        delta_btn = ui.Button(title="Delta from Last Import", font=("<System>", 14), frame=(10, cy, cw - 20, small_btn_height))
        delta_btn.flex = "W"
        delta_btn.background_color = "#444444"
        delta_btn.tint_color = "white"
        delta_btn.corner_radius = 6.0
        delta_btn.action = self.run_delta_from_last_import
        bottom_container.add_subview(delta_btn)
        self.delta_button = delta_btn
        cy += small_btn_height + 10

        run_height = 40
        btn = ui.Button(title="Run Merge", frame=(10, cy, cw - 20, run_height))
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

        # TableView - Increased row height for better touch
        tv = ui.TableView()
        list_height = v.height - top_header_height - container_height
        tv.frame = (10, top_header_height, v.width - 20, list_height)
        tv.flex = "WH"
        tv.background_color = "#111111"
        tv.separator_color = "#333333"
        tv.row_height = 44  # Increased for easier selection
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

        # Finally, auto-restore last config defaults (without modifying repo selection)
        self.restore_last_state(load_selection=False)

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
            # Disable other selection buttons in ignore mode
            self.select_all_button.enabled = False
            self.sets_button.enabled = False
        else:
            rows = self.tv.selected_rows or []
            newly_ignored: set[str] = set()
            for sec, idx in rows:
                if sec == 0 and 0 <= idx < len(self.repos):
                    newly_ignored.add(self.repos[idx])

            if newly_ignored:
                self.ignored_repos = newly_ignored
            self.ignore_button.title = "Ignore…"
            self.select_all_button.enabled = True
            self.sets_button.enabled = True

            self.save_last_state(ignore_only=True)
            self.tv.selected_rows = []

        self._update_repo_info()

    def select_all_repos(self, sender) -> None:
        if not self.repos:
            return
        excluded = self.ignored_repos
        rows: List[tuple[int, int]] = []
        for idx, name in enumerate(self.repos):
            if name in excluded:
                continue
            rows.append((0, idx))

        # If all valid repos are already selected, deselect all.
        current = self.tv.selected_rows or []
        if set(current) == set(rows) and rows:
            self.tv.selected_rows = []
        else:
            self.tv.selected_rows = rows
        self._update_repo_info()

    def show_sets_sheet(self, sender):
        """Shows the Sets management sheet."""
        s = ui.View()
        s.name = "Repo Sets"
        s.background_color = "#222222"
        s.frame = (0, 0, 400, 500)

        # List of sets
        set_names = sorted(self.repo_sets.keys())

        tbl = ui.TableView()
        tbl.frame = (0, 60, s.width, s.height - 120)
        tbl.flex = "WH"
        tbl.background_color = "#222222"
        tbl.text_color = "white"
        tbl.row_height = 44

        def load_set(sender):
            row = sender.selected_row
            if row >= 0 and row < len(set_names):
                name = set_names[row]
                repos = self.repo_sets.get(name, [])
                self._apply_selected_repo_names(repos)
                console.hud_alert(f"Set '{name}' loaded")
                s.close()

        class SetsDataSource(ui.ListDataSource):
            def tableview_delete(self, tv, section, row):
                name = self.items[row]
                del self.outer.repo_sets[name]
                self.items.remove(name)
                tv.delete_rows([row])
                self.outer.save_last_state(ignore_only=True) # Save sets immediately

        ds = SetsDataSource(set_names)
        ds.outer = self
        ds.text_color = "white"
        ds.highlight_color = "#0050ff"
        ds.delete_enabled = True
        ds.action = load_set

        tbl.data_source = ds
        tbl.delegate = ds
        s.add_subview(tbl)

        # Save current button
        def save_current(sender):
            current = self._collect_selected_repo_names()
            if not current:
                console.alert("No repos selected")
                return

            def on_name(text):
                name = (text or "").strip()
                if name:
                    self.repo_sets[name] = current
                    self.save_last_state(ignore_only=True)
                    ds.items = sorted(self.repo_sets.keys())
                    tbl.reload_data()

            # Input alert is blocking in standard pythonista, but callback handling depends on version.
            # Assuming standard blocking input_alert returning text or specific dialogs module.
            # Actually console.input_alert returns text or raises KeyboardInterrupt.
            try:
                name = console.input_alert("New Set", "Name for current selection:", "", "Save")
                on_name(name)
            except KeyboardInterrupt:
                pass

        btn_save = ui.Button(title="Save Current Selection as Set")
        btn_save.frame = (10, 10, s.width - 20, 40)
        btn_save.background_color = "#007aff"
        btn_save.tint_color = "white"
        btn_save.corner_radius = 6
        btn_save.action = save_current
        s.add_subview(btn_save)

        # Close button
        btn_close = ui.Button(title="Close")
        btn_close.frame = (10, s.height - 50, s.width - 20, 40)
        btn_close.flex = "T"
        btn_close.background_color = "#444444"
        btn_close.tint_color = "white"
        btn_close.corner_radius = 6
        def close_me(sender): s.close()
        btn_close.action = close_me
        s.add_subview(btn_close)

        s.present('sheet')

    def close_view(self, sender=None) -> None:
        global _ACTIVE_MERGER_VIEW
        try:
            _dismiss_view_best_effort(self.view)
        except Exception:
            pass
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
        dynamic_h = max(260, min(100 + len(items) * row_h, 540))
        s.frame = (0, 0, 420, dynamic_h)

        y = 20
        margin = 20
        w = s.width - 2 * margin

        lbl = ui.Label(frame=(margin, y, w, 40))
        lbl.text = "Optionale Zusatzanalysen"
        lbl.text_color = "white"
        lbl.alignment = ui.ALIGN_CENTER
        s.add_subview(lbl)
        y += 50

        def add_switch(key, title):
            nonlocal y
            sw = ui.Switch()
            sw.value = getattr(self.extras_config, key)
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
        def close_action(sender): s.close()
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
            self.max_field.text = str(int(max_bytes)) if max_bytes and max_bytes > 0 else ""
            split_mb = preset.get("split_mb")
            self.split_field.text = str(int(split_mb)) if split_mb and split_mb > 0 else ""

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
        if rows:
            self.tv.selected_rows = rows
            self._update_repo_info()

    def _load_state_initial(self) -> None:
        try:
            raw = self._state_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                self.ignored_repos = set(data.get("ignored_repos", []))
                self.repo_sets = data.get("repo_sets", {})
        except Exception:
            pass

    def save_last_state(self, ignore_only: bool = False) -> None:
        data: Dict[str, Any] = {}
        if self._state_path.exists():
            try:
                raw = self._state_path.read_text(encoding="utf-8")
                existing = json.loads(raw)
                if isinstance(existing, dict):
                    data.update(existing)
            except Exception:
                pass

        data["ignored_repos"] = sorted(self.ignored_repos)
        data["repo_sets"] = self.repo_sets

        if not ignore_only:
            profile = None
            try:
                segments = getattr(self.seg_detail, "segments", [])
                idx = getattr(self.seg_detail, "selected_index", 0)
                if 0 <= idx < len(segments):
                    profile = segments[idx]
            except Exception:
                profile = None
            if profile:
                data["detail_profile"] = profile

            data.update({
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
            })

        try:
            self._state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[repoLens] could not persist state: {exc}")

    def restore_last_state(self, sender=None, load_selection=True) -> None:
        try:
            raw = self._state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            if sender and console:
                console.alert("repoLens", "No saved state found.", "OK", hide_cancel_button=True)
            return
        except Exception:
            return

        try:
            data = json.loads(raw)
        except Exception:
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

        # Ignore/Sets already loaded in _load_state_initial but harmless to reload
        self.ignored_repos = set(data.get("ignored_repos", []))
        self.repo_sets = data.get("repo_sets", {})

        extras_data = data.get("extras", {})
        if extras_data:
            for k, v in extras_data.items():
                if hasattr(self.extras_config, k):
                    setattr(self.extras_config, k, v)

        self.on_profile_changed(None)

        if load_selection:
            selected = data.get("selected_repos") or []
            if selected:
                self._apply_selected_repo_names(selected)

        if sender and console:
            try:
                console.hud_alert("Config loaded")
            except Exception:
                pass

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
        return val if val > 0 else 0

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
        merges_dir = get_merges_dir(self.hub)
        try:
            candidates = list(merges_dir.glob("*-import-diff-*.md"))
        except Exception:
            candidates = []

        if not candidates:
            if console: console.alert("repoLens", "No import diff found.", "OK", hide_cancel_button=True)
            return

        try:
            diff_path = max(candidates, key=lambda p: p.stat().st_mtime)
        except Exception:
            return

        name = diff_path.name
        prefix = "-import-diff-"
        repo_name = name.split(prefix, 1)[0] if prefix in name else name
        repo_root = self.hub / repo_name
        if not repo_root.exists():
            if console: console.alert("repoLens", f"Repo root not found for {diff_path.name}", "OK")
            return

        mod = _load_repolens_extractor_module()
        if mod is None:
            if console: console.alert("repoLens", "Delta helper (repolens-extractor) not available.", "OK")
            return

        try:
            delta_meta = None
            diff_mtime = diff_path.stat().st_mtime
            if hasattr(mod, "extract_delta_meta_from_diff_file"):
                delta_meta = mod.extract_delta_meta_from_diff_file(diff_path)

            if not delta_meta:
                 if console: console.alert("repoLens", "Could not extract delta metadata from diff.", "OK")
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

            allowed_paths = set()
            if "files_added" in delta_meta and isinstance(delta_meta["files_added"], list):
                allowed_paths.update(delta_meta["files_added"])
            if "files_changed" in delta_meta and isinstance(delta_meta["files_changed"], list):
                for item in delta_meta["files_changed"]:
                    if isinstance(item, dict):
                        p = item.get("path")
                        if p: allowed_paths.add(p)
                    elif isinstance(item, str):
                        allowed_paths.add(item)

            if allowed_paths:
                filtered_files = [f for f in summary["files"] if f.rel_path.as_posix() in allowed_paths]
                summary["files"] = filtered_files
                summary["total_files"] = len(filtered_files)
                summary["total_bytes"] = sum(f.size for f in filtered_files)

            artifacts = write_reports_v2(
                merges_dir,
                self.hub,
                [summary],
                "max",
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
            msg = f"Delta report generated: {primary_path.name}" if primary_path else "Delta report generated"
            if console: console.hud_alert(msg)

        except Exception as exc:
            if console: console.alert("repoLens", f"Delta merge failed: {exc}", "OK")

    def run_merge(self, sender) -> None:
        try:
            import ui as _ui
            in_bg = getattr(_ui, "in_background", None)
        except Exception:
            in_bg = None

        if in_bg:
            in_bg(self._run_merge_safe)()
        else:
            self._run_merge_safe()

    def _run_merge_safe(self) -> None:
        try:
            self.save_last_state()
            self._run_merge_inner()
        except Exception as e:
            traceback.print_exc()
            msg = f"Error: {e}"
            if console:
                console.alert("repoLens", msg, "OK", hide_cancel_button=True)
            else:
                print(msg, file=sys.stderr)

    def _run_merge_inner(self) -> None:
        selected = self._get_selected_repos()
        if not selected:
            if console: console.alert("repoLens", "No repos selected.", "OK", hide_cancel_button=True)
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
        plan_only = bool(self.plan_only_switch.value)
        code_only = bool(getattr(self, "code_only_switch", None) and self.code_only_switch.value)
        if plan_only and code_only: code_only = False

        summaries = []
        total = len(selected)
        for i, name in enumerate(selected, start=1):
            root = self.hub / name
            if not root.is_dir(): continue
            if console:
                try: console.hud_alert(f"Scanning {i}/{total}: {name}", duration=0.6)
                except Exception: pass
            try:
                import ui as _ui
                _ui.delay(lambda: None, 0.0)
            except Exception: pass
            summary = scan_repo(root, extensions or None, path_contains, max_bytes)
            summaries.append(summary)

        if not summaries:
            if console: console.alert("repoLens", "No valid repos found.", "OK", hide_cancel_button=True)
            return

        merges_dir = get_merges_dir(self.hub)
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
        )

        out_paths = artifacts.get_all_paths()
        if not out_paths:
            if console: console.alert("repoLens", "No report generated.", "OK", hide_cancel_button=True)
            return

        force_close_files(out_paths)
        primary = _pick_primary_artifact(out_paths)
        msg = f"Merge generated: {primary.name}" if primary else "Merge generated"
        if console: console.hud_alert(msg, "success", 1.2)
        else: print(f"repoLens: {msg}")


# --- CLI Mode ---

def _is_headless_requested() -> bool:
    return ("--headless" in sys.argv) or (os.environ.get("REPOLENS_HEADLESS") == "1") or (ui is None)

def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="repoLens CLI")
    parser.add_argument("paths", nargs="*", help="Repositories to merge")
    parser.add_argument("--hub", help="Base directory (repolens-hub)")
    parser.add_argument("--level", choices=["overview", "summary", "dev", "max"], default=DEFAULT_LEVEL)
    parser.add_argument("--mode", choices=["gesamt", "pro-repo"], default=DEFAULT_MODE)
    parser.add_argument("--max-bytes", type=str, default=str(DEFAULT_MAX_FILE_BYTES), help="Max bytes per file")
    parser.add_argument("--split-size", help="Split output into chunks", default=DEFAULT_SPLIT_SIZE)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--code-only", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--extras", help="Comma-separated extras", default=DEFAULT_EXTRAS)
    parser.add_argument("--extensions", help="Comma-separated extensions", default=None)
    parser.add_argument("--path-filter", help="Path substring to include", default=None)
    parser.add_argument("--json-sidecar", action="store_true", help="Generate JSON sidecar")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--token", help="Security token")

    args = parser.parse_args()
    hub = detect_hub_dir(SCRIPT_PATH, args.hub)

    if args.serve:
        try:
            sys.path.append(str(SCRIPT_DIR))
            from repolens_service import run_server
            run_server(hub, args.host, args.port, args.open, args.token)
            return
        except ImportError as e:
            print(f"Service error: {e}")
            sys.exit(1)

    sources = []
    if args.paths:
        for p in args.paths:
            path = Path(p)
            if not path.exists(): path = hub / p
            if path.exists() and path.is_dir(): sources.append(path)
    else:
        for r in find_repos_in_hub(hub): sources.append(hub / r)

    if not sources: sources.append(Path.cwd())

    print(f"Hub: {hub}")
    print(f"Sources: {[s.name for s in sources]}")

    max_bytes = parse_human_size(str(args.max_bytes))
    if max_bytes < 0: max_bytes = 0
    ext_list = _normalize_ext_list(args.extensions) if args.extensions else None

    summaries = []
    for src in sources:
        print(f"Scanning {src.name}...")
        summaries.append(scan_repo(src, ext_list, args.path_filter, max_bytes))

    split_size = parse_human_size(args.split_size) if args.split_size else 0
    extras_config = ExtrasConfig()
    if args.extras and args.extras.lower() != "none":
        for part in _parse_extras_csv(args.extras):
            if hasattr(extras_config, part): setattr(extras_config, part, True)
    if args.json_sidecar: extras_config.json_sidecar = True

    merges_dir = get_merges_dir(hub)
    delta_meta = None
    # Only try to extract delta if explicitly enabled and single repo
    if extras_config.delta_reports and len(summaries) == 1:
        try:
            mod = _load_repolens_extractor_module()
            if mod:
                 diff_path = mod.find_latest_diff_for_repo(merges_dir, summaries[0]["name"])
                 if diff_path: delta_meta = mod.extract_delta_meta_from_diff_file(diff_path)
        except Exception: pass

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
        path_filter=args.path_filter,
        ext_filter=ext_list,
        extras=extras_config,
        delta_meta=delta_meta,
    )

    for p in artifacts.get_all_paths():
        print(f"  - {p}")


def main():
    use_ui = (ui is not None and not _is_headless_requested() and (appex is None or not appex.is_running_extension()))
    if use_ui:
        try:
            hub = detect_hub_dir(SCRIPT_PATH)
            return run_ui(hub)
        except Exception as e:
            if console: console.alert("repoLens", f"UI fallback: {e}", "OK", hide_cancel_button=True)
            main_cli()
    else:
        main_cli()

if __name__ == "__main__":
    main()
