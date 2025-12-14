# -*- coding: utf-8 -*-

"""
ui_ios – Pythonista UI implementation for wc-merger.
Separated from core logic for portability.
"""

import sys
import json
import traceback
from pathlib import Path
from typing import List, Any, Dict, Optional

# Try importing Pythonista modules
try:
    import ui        # type: ignore
except Exception:
    ui = None        # type: ignore

try:
    TF_BORDER_NONE = ui.TEXT_FIELD_BORDER_NONE  # type: ignore
except Exception:
    TF_BORDER_NONE = 0

try:
    import console   # type: ignore
except Exception:
    console = None   # type: ignore

try:
    import editor    # type: ignore
except Exception:
    editor = None    # type: ignore

# Import core logic
# Use relative import if running as package, else fallback to sys.path
try:
    from .core import (
        MERGES_DIR_NAME,
        SKIP_ROOTS,
        detect_hub_dir,
        find_repos_in_hub,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        parse_human_size,
        _parse_extras_csv,
        ExtrasConfig,
        MergeArtifacts,
        DEFAULT_MAX_BYTES,
    )
except ImportError:
    # Fallback if running as script from same dir
    from core import (
        MERGES_DIR_NAME,
        SKIP_ROOTS,
        detect_hub_dir,
        find_repos_in_hub,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        parse_human_size,
        _parse_extras_csv,
        ExtrasConfig,
        MergeArtifacts,
        DEFAULT_MAX_BYTES,
    )

# Defaults reused from original script
DEFAULT_LEVEL = "dev"
DEFAULT_MODE = "gesamt"
DEFAULT_SPLIT_SIZE = "25MB"
DEFAULT_MAX_FILE_BYTES = 0
DEFAULT_EXTRAS = "health,augment_sidecar,organism_index,fleet_panorama,json_sidecar,ai_heatmap"
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
    "overview": {"max_bytes": 0, "split_mb": 25},
    "summary": {"max_bytes": 0, "split_mb": 25},
    "dev": {"max_bytes": 0, "split_mb": 25},
    "machine-lean": {"max_bytes": 0, "split_mb": 25},
    "max": {"max_bytes": 0, "split_mb": 25},
}

_ACTIVE_MERGER_VIEW = None

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
            except Exception:
                pass
        return Path.cwd().resolve()

SCRIPT_PATH = safe_script_path()
SCRIPT_DIR = SCRIPT_PATH.parent

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
            except Exception:
                pass


def _load_wc_extractor_module():
    from importlib.machinery import SourceFileLoader
    import types
    extractor_path = SCRIPT_DIR / "wc-extractor.py"
    if not extractor_path.exists():
        return None
    try:
        loader = SourceFileLoader("wc_extractor", str(extractor_path))
        mod = types.ModuleType(loader.name)
        loader.exec_module(mod)
        return mod
    except Exception as exc:
        print(f"[ui_ios] could not load wc-extractor: {exc}")
        return None

def _run_extractor_on_start(hub: Path) -> None:
    try:
        extractor = _load_wc_extractor_module()
        if extractor is None:
            return
        if hasattr(extractor, "run_extractor"):
            try:
                extractor.run_extractor(hub_override=hub, show_alert=False, incremental=True)
            except TypeError:
                extractor.run_extractor(hub)
    except Exception:
        pass

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
            mod = _load_wc_extractor_module()
            try:
                mod.detect_hub(str(self.hub))
            except TypeError:
                mod.detect_hub(str(self.hub))
        except Exception as e:
            print(f"[extractor] warmup skipped: {e}")

        # Basic defaults
        self.extras_config = ExtrasConfig()
        if DEFAULT_EXTRAS and DEFAULT_EXTRAS.lower() != "none":
            for part in _parse_extras_csv(DEFAULT_EXTRAS):
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

        btn_width = 76
        btn_height = 28
        btn_margin_right = 10
        btn_spacing = 6

        close_btn = ui.Button()
        close_btn.title = "Close"
        close_btn.frame = (v.width - btn_margin_right - btn_width, y, btn_width, btn_height)
        close_btn.flex = "L"
        close_btn.background_color = "#333333"
        close_btn.tint_color = "white"
        close_btn.corner_radius = 4.0
        close_btn.action = self.close_view
        v.add_subview(close_btn)
        self.close_button = close_btn

        select_all_btn = ui.Button()
        select_all_btn.title = "Set"
        select_all_btn.frame = (close_btn.frame[0] - btn_spacing - btn_width, close_btn.frame[1], btn_width, btn_height)
        select_all_btn.flex = "L"
        select_all_btn.background_color = "#333333"
        select_all_btn.tint_color = "white"
        select_all_btn.corner_radius = 4.0
        select_all_btn.action = self.select_all_repos
        v.add_subview(select_all_btn)
        self.select_all_button = select_all_btn

        ignore_btn = ui.Button()
        ignore_btn.title = "Ignore…"
        ignore_btn.frame = (select_all_btn.frame[0] - btn_spacing - btn_width, close_btn.frame[1], btn_width, btn_height)
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

        detail_label = ui.Label(text="Detail:", text_color="white", background_color="#111111", frame=(10, cy, 60, 22))
        bottom_container.add_subview(detail_label)
        seg_detail = ui.SegmentedControl()
        seg_detail.segments = ["overview", "summary", "dev", "max"]
        try:
            seg_detail.selected_index = seg_detail.segments.index(DEFAULT_LEVEL)
        except ValueError:
            seg_detail.selected_index = 2
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

        mode_label = ui.Label(text="Mode:", text_color="white", background_color="#111111", frame=(10, cy, 60, 22))
        bottom_container.add_subview(mode_label)
        seg_mode = ui.SegmentedControl()
        seg_mode.segments = ["combined", "per repo"]
        seg_mode.selected_index = 0
        seg_mode.frame = (70, cy - 2, cw - 80, 28)
        seg_mode.flex = "W"
        seg_mode.tint_color = "#007aff"
        seg_mode.background_color = "#dddddd"
        bottom_container.add_subview(seg_mode)
        self.seg_mode = seg_mode
        cy += 36

        max_label = ui.Label(text="Max Bytes/File:", text_color="white", background_color="#111111", frame=(10, cy, 120, 22))
        bottom_container.add_subview(max_label)
        max_field = ui.TextField()
        max_field.text = str(DEFAULT_MAX_FILE_BYTES) if DEFAULT_MAX_FILE_BYTES > 0 else ""
        max_field.frame = (130, cy - 2, 140, 28)
        max_field.flex = "W"
        max_field.placeholder = "0 / empty = unlimited"
        _style_textfield(max_field)
        max_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        _wrap_textfield_in_dark_bg(bottom_container, max_field)
        self.max_field = max_field
        cy += 36

        split_label = ui.Label(text="Split Size (MB):", text_color="white", background_color="#111111", frame=(10, cy, 120, 22))
        bottom_container.add_subview(split_label)
        split_field = ui.TextField()
        split_field.placeholder = "leer/0 = kein Split"
        split_field.text = DEFAULT_SPLIT_SIZE if DEFAULT_SPLIT_SIZE != "0" else ""
        split_field.frame = (130, cy - 2, 140, 28)
        split_field.flex = "W"
        _style_textfield(split_field)
        split_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        _wrap_textfield_in_dark_bg(bottom_container, split_field)
        self.split_field = split_field
        cy += 36

        plan_label = ui.Label(text="Plan only:", text_color="white", background_color="#111111", frame=(10, cy, 120, 22))
        bottom_container.add_subview(plan_label)
        plan_switch = ui.Switch()
        plan_switch.frame = (130, cy - 2, 60, 32)
        plan_switch.flex = "W"
        plan_switch.value = False
        bottom_container.add_subview(plan_switch)
        self.plan_only_switch = plan_switch

        code_label = ui.Label(text="Code only:", text_color="white", background_color="#111111", frame=(210, cy, 120, 22))
        bottom_container.add_subview(code_label)
        code_switch = ui.Switch()
        code_switch.frame = (330, cy - 2, 60, 32)
        code_switch.flex = "W"
        code_switch.value = False
        bottom_container.add_subview(code_switch)
        self.code_only_switch = code_switch
        cy += 36

        info_label = ui.Label(text_color="white", background_color="#111111", font=("<System>", 11), number_of_lines=1, frame=(10, cy, cw - 20, 18), flex="W")
        bottom_container.add_subview(info_label)
        self.info_label = info_label
        self._update_repo_info()
        self.on_profile_changed(None)
        cy += 26 + 10

        small_btn_height = 32
        extras_btn = ui.Button(title="Extras...", font=("<System>", 14), frame=(10, cy, cw - 20, small_btn_height), flex="W", background_color="#333333", tint_color="white", corner_radius=6.0, action=self.show_extras_sheet)
        bottom_container.add_subview(extras_btn)
        cy += small_btn_height + 10

        load_btn = ui.Button(title="Load Last Config", font=("<System>", 14), frame=(10, cy, cw - 20, small_btn_height), flex="W", background_color="#333333", tint_color="white", corner_radius=6.0, action=self.restore_last_state)
        bottom_container.add_subview(load_btn)
        cy += small_btn_height + 10

        delta_btn = ui.Button(title="Delta from Last Import", font=("<System>", 14), frame=(10, cy, cw - 20, small_btn_height), flex="W", background_color="#444444", tint_color="white", corner_radius=6.0, action=self.run_delta_from_last_import)
        bottom_container.add_subview(delta_btn)
        self.delta_button = delta_btn
        cy += small_btn_height + 10

        run_height = 40
        btn = ui.Button(title="Run Merge", frame=(10, cy, cw - 20, run_height), flex="W", background_color="#007aff", tint_color="white", corner_radius=6.0, action=self.run_merge)
        bottom_container.add_subview(btn)
        self.run_button = btn
        cy += run_height + 24

        container_height = cy
        bottom_container.frame = (0, v.height - container_height, v.width, container_height)
        bottom_container.flex = "WT"
        v.add_subview(bottom_container)

        list_height = v.height - top_header_height - container_height
        tv = ui.TableView(frame=(10, top_header_height, v.width - 20, list_height), flex="WH", background_color="#111111", separator_color="#333333", row_height=32, allows_multiple_selection=True, tint_color="#007aff")
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
            self.tv.selected_rows = [(0, idx) for idx, name in enumerate(self.repos) if name in self.ignored_repos]
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
        if not self.repos: return
        excluded = self.ignored_repos
        rows: List[tuple[int, int]] = []
        for idx, name in enumerate(self.repos):
            if name in excluded: continue
            rows.append((0, idx))
        self.tv.selected_rows = rows if rows else []
        self._update_repo_info()

    def close_view(self, sender=None) -> None:
        global _ACTIVE_MERGER_VIEW
        try:
            _dismiss_view_best_effort(self.view)
        finally:
            if _ACTIVE_MERGER_VIEW is self.view:
                _ACTIVE_MERGER_VIEW = None

    def show_extras_sheet(self, sender):
        s = ui.View(name="Extras", background_color="#222222")
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
        dynamic_h = max(260, min(20 + 50 + len(items) * row_h + 20 + 60, 540))
        s.frame = (0, 0, 420, dynamic_h)
        y = 20
        margin = 20
        w = s.width - 2 * margin
        lbl = ui.Label(frame=(margin, y, w, 40), text="Optionale Zusatzanalysen\n(Health, Organism, etc.)", number_of_lines=2, text_color="white", alignment=ui.ALIGN_CENTER)
        s.add_subview(lbl)
        y += 50
        def add_switch(key, title):
            nonlocal y
            sw = ui.Switch(value=getattr(self.extras_config, key), name=key)
            sw.action = lambda sender: setattr(self.extras_config, key, sender.value)
            sw.frame = (w - 60, y, 60, 32)
            l = ui.Label(frame=(margin, y, w - 70, 32), text=title, text_color="white")
            s.add_subview(l)
            s.add_subview(sw)
            y += row_h
        for title, key in items:
            add_switch(key, title)
        y += 10
        btn = ui.Button(frame=(margin, y, w, 40), title="Done", background_color="#007aff", tint_color="white", corner_radius=6, action=lambda sender: s.close())
        s.add_subview(btn)
        s.present("sheet")

    def on_profile_changed(self, sender):
        idx = self.seg_detail.selected_index
        if not (0 <= idx < len(self.seg_detail.segments)): return
        seg_name = self.seg_detail.segments[idx]
        self.profile_hint.text = PROFILE_DESCRIPTIONS.get(seg_name, "")
        preset = PROFILE_PRESETS.get(seg_name)
        if preset:
            max_bytes = preset.get("max_bytes", 0)
            self.max_field.text = str(int(max_bytes)) if max_bytes and max_bytes > 0 else ""
            split_mb = preset.get("split_mb")
            self.split_field.text = str(int(split_mb)) if split_mb and split_mb > 0 else ""

    def _get_selected_repos(self) -> List[str]:
        rows = self.tv.selected_rows or []
        if not rows: return list(self.repos)
        return [self.repos[row] for section, row in rows if 0 <= row < len(self.repos)]

    def _apply_selected_repo_names(self, names: List[str]) -> None:
        name_to_index = {name: i for i, name in enumerate(self.repos)}
        rows = []
        for name in names:
            if name in name_to_index:
                rows.append((0, name_to_index[name]))
        if rows:
            self.tv.selected_rows = rows

    def _load_ignored_repos_from_state(self) -> None:
        try:
            raw = self._state_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                self.ignored_repos = set(data.get("ignored_repos", []))
        except Exception:
            pass

    def save_last_state(self, ignore_only: bool = False) -> None:
        data: Dict[str, Any] = {}
        if self._state_path.exists():
            try:
                data.update(json.loads(self._state_path.read_text(encoding="utf-8")))
            except Exception:
                pass
        data["ignored_repos"] = sorted(self.ignored_repos)
        if not ignore_only:
            try:
                profile = self.seg_detail.segments[self.seg_detail.selected_index]
                data["detail_profile"] = profile
            except Exception:
                pass
            data.update({
                "ext_filter": self.ext_field.text or "",
                "path_filter": self.path_field.text or "",
                "max_bytes": self.max_field.text or "",
                "split_mb": self.split_field.text or "",
                "plan_only": bool(self.plan_only_switch.value),
                "code_only": bool(self.code_only_switch.value),
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
            print(f"[wc-merger] could not persist state: {exc}")

    def restore_last_state(self, sender=None) -> None:
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
        except Exception:
            if sender and console: console.alert("wc-merger", "No saved state found.", "OK", hide_cancel_button=True)
            return

        profile = data.get("detail_profile")
        if profile and profile in self.seg_detail.segments:
            self.seg_detail.selected_index = self.seg_detail.segments.index(profile)

        self.ext_field.text = data.get("ext_filter", "")
        self.path_field.text = data.get("path_filter", "")
        self.max_field.text = data.get("max_bytes", "")
        self.split_field.text = data.get("split_mb", "")
        self.plan_only_switch.value = bool(data.get("plan_only", False))
        self.code_only_switch.value = bool(data.get("code_only", False))
        self.ignored_repos = set(data.get("ignored_repos", []))

        extras_data = data.get("extras", {})
        if extras_data:
            for k, v in extras_data.items():
                if hasattr(self.extras_config, k):
                    setattr(self.extras_config, k, v)

        self.on_profile_changed(None)
        selected = data.get("selected_repos") or []
        if selected: self._apply_selected_repo_names(selected)
        if sender and console:
            try: console.hud_alert("Config loaded")
            except Exception: pass
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

    def _parse_max_bytes(self) -> int:
        txt = (self.max_field.text or "").strip()
        if not txt: return 0
        try:
            val = parse_human_size(txt)
        except Exception:
            val = 0
        return val if val > 0 else 0

    def _parse_split_size(self) -> int:
        txt = (self.split_field.text or "").strip()
        if not txt: return 0
        try:
            if txt.isdigit(): return int(txt) * 1024 * 1024
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
            if console: console.alert("wc-merger", "No import diff found.", "OK", hide_cancel_button=True)
            return
        diff_path = max(candidates, key=lambda p: p.stat().st_mtime)
        name = diff_path.name
        repo_name = name.split("-import-diff-")[0] if "-import-diff-" in name else name
        repo_root = self.hub / repo_name

        mod = _load_wc_extractor_module()
        if mod is None or not hasattr(mod, "create_delta_merge_from_diff"):
            if console: console.alert("wc-merger", "Delta helper not available.", "OK", hide_cancel_button=True)
            return

        try:
            _ = mod.create_delta_merge_from_diff(diff_path, repo_root, merges_dir, profile="delta-full")
            delta_meta = None
            try:
                if hasattr(mod, "extract_delta_meta_from_diff_file"):
                    delta_meta = mod.extract_delta_meta_from_diff_file(diff_path)
            except Exception:
                pass

            extras = ExtrasConfig(
                health=self.extras_config.health,
                organism_index=self.extras_config.organism_index,
                fleet_panorama=self.extras_config.fleet_panorama,
                augment_sidecar=self.extras_config.augment_sidecar,
                heatmap=self.extras_config.heatmap,
                delta_reports=True
            )
            summary = scan_repo(repo_root, max_bytes=0)
            artifacts = write_reports_v2(
                merges_dir, self.hub, [summary], "dev", "repo", 0,
                plan_only=False, code_only=False, debug=False,
                extras=extras, delta_meta=delta_meta
            )
            out_paths = artifacts.get_all_paths()
            force_close_files(out_paths)
            if console: console.hud_alert("Delta generated")
        except Exception as e:
            if console: console.alert("wc-merger", f"Delta merge failed: {e}", "OK", hide_cancel_button=True)

    def run_merge(self, sender) -> None:
        try:
            self.save_last_state()
            selected = self._get_selected_repos()
            if not selected:
                if console: console.alert("wc-merger", "No repos selected.", "OK", hide_cancel_button=True)
                return

            ext_text = (self.ext_field.text or "").strip()
            extensions = _normalize_ext_list(ext_text)
            path_contains = (self.path_field.text or "").strip() or None

            detail = self.seg_detail.segments[self.seg_detail.selected_index]
            mode = self.seg_mode.segments[self.seg_mode.selected_index]
            if mode == "combined": mode = "gesamt"
            elif mode == "per repo": mode = "pro-repo"

            max_bytes = self._parse_max_bytes()
            split_size = self._parse_split_size()
            plan_only = self.plan_only_switch.value
            code_only = self.code_only_switch.value
            if plan_only and code_only: code_only = False

            summaries = []
            for name in selected:
                root = self.hub / name
                if root.is_dir():
                    summaries.append(scan_repo(root, extensions or None, path_contains, max_bytes))

            if not summaries:
                if console: console.alert("wc-merger", "No valid repos found.", "OK", hide_cancel_button=True)
                return

            merges_dir = get_merges_dir(self.hub)
            artifacts = write_reports_v2(
                merges_dir, self.hub, summaries, detail, mode, max_bytes,
                plan_only, code_only, split_size,
                path_filter=path_contains, ext_filter=extensions or None,
                extras=self.extras_config
            )

            out_paths = artifacts.get_all_paths()
            if not out_paths:
                if console: console.alert("wc-merger", "No report generated.", "OK", hide_cancel_button=True)
                return

            force_close_files(out_paths)
            if console: console.hud_alert(f"Generated {len(out_paths)} reports", "success", 1.2)
            else: print(f"Generated {len(out_paths)} reports")

        except Exception as e:
            traceback.print_exc()
            if console: console.alert("wc-merger", f"Error: {e}", "OK", hide_cancel_button=True)
