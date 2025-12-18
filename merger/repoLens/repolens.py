#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
repoLens – A structural lens for repositories.
Enhanced AI-optimized reports with strict Pflichtenheft structure.

Default-Config (Dec 2025)
------------------------
- level: dev
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
from typing import List, Any, Dict, Optional


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
# In Shortcuts-App-Extension werfen diese Importe NotImplementedError.
# Deshalb JEGLICHEN Import-Fehler abfangen, nicht nur ImportError.
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
    """Dynamically load repolens-extractor.py from the same directory.

    In Pythonista ist ``__file__`` nicht immer gesetzt (z. B. bei Ausführung
    aus bestimmten UI-/Shortcut-Kontexten). In dem Fall fallen wir auf
    ``sys.argv[0]`` bzw. das aktuelle Arbeitsverzeichnis zurück, statt mit
    einem ``NameError`` abzustürzen.
    """
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
        # Preferred API (added for startup auto-run)
        if hasattr(extractor, "run_extractor"):
            try:
                # Use incremental=True to avoid unnecessary work
                extractor.run_extractor(hub_override=hub, show_alert=False, incremental=True)
            except TypeError:
                # Fallback if incremental arg is not yet available in loaded module (race condition or old version)
                extractor.run_extractor(hub)
            return
        # Fallback: do nothing rather than popping alerts or blocking startup.
    except Exception as e:
        sys.stderr.write(f"[repoLens] Extractor auto-run warning: {e}\n")
        return


def _dismiss_view_best_effort(v) -> None:
    """
    Pythonista-UI: möglichst robust schließen, unabhängig davon,
    ob der View via present()/sheet()/fullscreen oder als Subview hängt.
    Reihenfolge ist Absicht: dismiss() ist bei präsentierten Views am wirksamsten.
    """
    if v is None:
        return
    # 1) dismiss (für present('fullscreen'/'sheet'/etc.))
    try:
        v.dismiss()
    except Exception:
        pass
    # 2) close (für manche Kontexte / Fallback)
    try:
        v.close()
    except Exception:
        pass
    # 3) remove_from_superview (falls der View irgendwo eingebettet ist)
    try:
        if getattr(v, "superview", None) is not None:
            v.remove_from_superview()
    except Exception:
        pass


def run_ui(hub: Path) -> int:
    """Starte den Merger im Vollbild-UI-Modus ohne Pythonista-Titlebar."""
    global _ACTIVE_MERGER_VIEW
    # If there is already a Merger view on screen, close it before presenting a new one.
    try:
        if _ACTIVE_MERGER_VIEW is not None:
            _dismiss_view_best_effort(_ACTIVE_MERGER_VIEW)
            _ACTIVE_MERGER_VIEW = None
    except Exception:
        # Never block opening a new UI because cleanup failed.
        pass

    _run_extractor_on_start(hub)

    ui_obj = MergerUI(hub)
    v = ui_obj.view
    _ACTIVE_MERGER_VIEW = v
    # Volle Fläche, eigene „Titlebar“ im View, keine weiße System-Leiste
    v.present('fullscreen', hide_title_bar=True)
    return 0

class MergerUI(object):
    def __init__(self, hub: Path) -> None:
        self.hub = hub
        self.repos = find_repos_in_hub(hub)

        # Ignore-Konfiguration für das Heimgewebe-Set
        self.ignore_mode = False
        self.ignored_repos = set()

        # Pfad zur State-Datei
        self._state_path = (self.hub / LAST_STATE_FILENAME).resolve()
        # Beim Start nur die persistierte Ignore-Liste laden – nicht die gesamte UI-Config
        self._load_ignored_repos_from_state()

        # Auto-run / warm the extractor on startup (best-effort).
        # This makes delta/inspection features immediately usable and surfaces hub issues early,
        # without breaking the main UI if anything is missing.
        try:
            mod = _load_repolens_extractor_module()
            # Prefer passing the detected hub explicitly so extractor and UI agree.
            try:
                mod.detect_hub(str(self.hub))
            except TypeError:
                # older extractor signature: detect_hub() with no args
                mod.detect_hub()
        except Exception as e:
            # Keep UI functional; extractor is an enhancement, not a hard dependency.
            print(f"[extractor] warmup skipped: {e}")

        # Basic argv parsing for UI defaults
        # Expected format: repolens.py --level max --mode gesamt ...
        import argparse
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--level", default=DEFAULT_LEVEL)
        parser.add_argument("--mode", default=DEFAULT_MODE)
        # 0 = unbegrenzt
        parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
        # Default: ab 25 MB wird gesplittet
        parser.add_argument("--split-size", default=DEFAULT_SPLIT_SIZE)
        parser.add_argument("--extras", default=DEFAULT_EXTRAS)
        # Ignore unknown args
        args, _ = parser.parse_known_args()

        # Initiale Extras aus CLI args
        self.extras_config = ExtrasConfig()
        if args.extras and args.extras.lower() != "none":
            for part in _parse_extras_csv(args.extras):
                if hasattr(self.extras_config, part):
                    setattr(self.extras_config, part, True)

        v = ui.View()
        v.name = "WC-Merger"
        v.background_color = "#111111"

        # Vollbild nutzen – die Größe übernimmt dann das fullscreen-Present.
        try:
            screen_w, screen_h = ui.get_screen_size()
            v.frame = (0, 0, screen_w, screen_h)
        except Exception:
            # Fallback, falls get_screen_size nicht verfügbar ist
            v.frame = (0, 0, 1024, 768)
        v.flex = "WH"

        self.view = v

        def _wrap_textfield_in_dark_bg(parent_view, tf):
            """
            Wrapper für Eingabefelder.

            Wichtiger als „perfekt dunkel“ ist hier:
            - Text immer gut lesbar
            - keine weiße Schrift auf weißem Feld

            Darum nutzen wir den systemhellen TextField-Hintergrund
            und erzwingen nur gut sichtbare Schrift / Cursor.
            """

            # System-Hintergrund (hell) beibehalten
            tf.background_color = None
            tf.text_color = "black"        # gut lesbar auf hell
            tf.tint_color = "#007aff"      # Standard-iOS-Blau für Cursor/Markierung

            if hasattr(tf, "border_style"):
                try:
                    tf.border_style = TF_BORDER_NONE
                except Exception as e:
                    sys.stderr.write(f"Warning: Failed to set text field border style: {e}\n")

            # Kein extra Hintergrund-View mehr – direkt hinzufügen
            parent_view.add_subview(tf)

        # kleine Helper-Funktion für Dark-Theme-Textfelder
        def _style_textfield(tf: ui.TextField) -> None:
            """Basis-Styling, Wrapper übernimmt das Dunkel-Thema."""
            tf.autocorrection_type = False
            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE

        margin = 10
        top_padding = 22  # etwas mehr Abstand zur iOS-Statusleiste
        y = 10 + top_padding

        # --- TOP HEADER ---
        # Gemeinsame Button-Leiste rechts oben: [Ignore] [Set] [Close]
        btn_width = 76
        btn_height = 28
        btn_margin_right = 10
        btn_spacing = 6

        # Close ganz rechts
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

        # Set links neben Close
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

        # Ignore links von Set
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

        # Base-Dir-Label bekommt rechts ausreichend Platz vor der Button-Leiste
        base_label = ui.Label()
        max_label_width = ignore_btn.frame[0] - 10 - 4  # kleiner Sicherheitsabstand
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
        # Platz lassen für „Alle auswählen“-Button rechts
        repo_label.frame = (10, y, v.width - 110, 20)
        repo_label.flex = "W"
        repo_label.text = "Repos (Tap = Auswahl, None = All, SET = Heimgewebe):"
        repo_label.text_color = "white"
        repo_label.background_color = "#111111"
        repo_label.font = ("<System>", 13)
        v.add_subview(repo_label)
        # interner Toggle-Status für den All-Button
        self._all_toggle_selected = False

        y += 22
        top_header_height = y

        # --- BOTTOM SETTINGS & ACTIONS ---
        # Container view for all controls that should stick to the bottom
        # Layout calculation inside the container (starts at y=0)
        cy = 10
        cw = v.width
        # We'll set the container height at the end

        # We need a temporary container to add subviews to, but we'll attach it to v later
        bottom_container = ui.View()
        # Set initial width so subview flex calculations (right margin) work correctly
        bottom_container.frame = (0, 0, cw, 100)
        bottom_container.background_color = "#111111" # Same as v

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

        # --- Detail: eigene Zeile ---
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
            seg_detail.selected_index = 2  # Default dev für arbeitsfähiges Profil
        seg_detail.frame = (70, cy - 2, cw - 80, 28)
        seg_detail.flex = "W"
        # Use standard iOS blue instead of white for better contrast
        seg_detail.tint_color = "#007aff"
        seg_detail.background_color = "#dddddd"
        seg_detail.action = self.on_profile_changed
        bottom_container.add_subview(seg_detail)
        self.seg_detail = seg_detail

        # Kurzer Text unterhalb der Detail-Presets
        self.profile_hint = ui.Label(
            frame=(margin, cy + 28, cw - 2 * margin, 20),
            flex="W",
            text="",
            text_color="white",
            font=("<system>", 12),
        )
        bottom_container.add_subview(self.profile_hint)
        cy += 24 # Platz für Hint

        cy += 36  # neue Zeile für Mode

        # --- Mode: darunter, eigene Zeile ---
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
        # Same accent color as detail segmented control
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
        # 0 oder kleiner = „unbegrenzt“ → Feld leer lassen
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
        # Globale Split-Größe:
        # steuert optional, ob der Merge in mehrere Dateien aufgeteilt wird,
        # ist aber **kein** harter Global-Limit-Cut.
        split_label.text = "Split Size (MB):"
        split_label.text_color = "white"
        split_label.background_color = "#111111"
        split_label.frame = (10, cy, 120, 22)
        bottom_container.add_subview(split_label)

        split_field = ui.TextField()
        # Leer oder 0 = kein Split → ein Merge ohne globales Größenlimit.
        split_field.placeholder = "leer/0 = kein Split"
        # UI erwartet MB als Zahl; CLI/Config dürfen aber auch "25MB" o.ä. liefern.
        split_text = ""
        raw_split = (getattr(args, "split_size", "") or "").strip()
        if raw_split and raw_split != "0":
            if raw_split.isdigit():
                split_text = raw_split
            else:
                try:
                    mb = int(round(parse_human_size(raw_split) / (1024 * 1024)))
                    split_text = str(mb) if mb > 0 else ""
                except Exception:
                    # Fallback: lieber sichtbar machen als stillschweigend löschen
                    split_text = raw_split
        split_field.text = split_text
        split_field.frame = (130, cy - 2, 140, 28)
        split_field.flex = "W"
        _style_textfield(split_field)
        split_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        _wrap_textfield_in_dark_bg(bottom_container, split_field)
        self.split_field = split_field

        cy += 36

        # --- Plan Only Switch ---
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

        # --- Code Only Switch (direkt neben Plan Only) ---
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

        # Initiale Anzeige des Hints
        self.on_profile_changed(None)

        cy += 26

        # --- Buttons am unteren Rand (innerhalb des Containers) ---

        cy += 10 # Gap

        small_btn_height = 32

        # --- Extras Button ---
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

        cy += small_btn_height + 10 # Gap

        # --- Load State Button ---
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

        cy += small_btn_height + 10 # Gap

        # --- Delta Button ---
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

        cy += small_btn_height + 10 # Gap

        # --- Run Button ---
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

        cy += run_height + 24 # Bottom margin inside container

        container_height = cy

        # Now place the container at the bottom of the main view
        bottom_container.frame = (0, v.height - container_height, v.width, container_height)
        bottom_container.flex = "WT" # Width flex, Top margin flex (stays at bottom)
        v.add_subview(bottom_container)

        # --- REPO LIST ---
        # The list fills the space between header and bottom container
        tv = ui.TableView()

        # Calculate height: available space between top header and bottom container
        list_height = v.height - top_header_height - container_height

        tv.frame = (10, top_header_height, v.width - 20, list_height)
        tv.flex = "WH" # Width flex, Height flex (fills space)
        tv.background_color = "#111111"
        tv.separator_color = "#333333"
        tv.row_height = 32
        tv.allows_multiple_selection = True
        # Improve readability on dark background
        tv.tint_color = "#007aff"

        ds = ui.ListDataSource(self.repos)
        ds.text_color = "white"
        # Bei Auswahl/Deselektion die Statuszeile aktualisieren
        ds.action = self._on_repo_selection_changed
        ds.tableview_did_select = self._tableview_did_select
        ds.tableview_did_deselect = self._tableview_did_deselect
        # deutliche Selektion: kräftiges Blau statt „grau auf schwarz“
        ds.highlight_color = "#0050ff"
        ds.tableview_cell_for_row = self._tableview_cell
        tv.data_source = ds
        tv.delegate = ds
        v.add_subview(tv)
        self.tv = tv
        self.ds = ds

        # Beim Start: Defaults verwenden, nur Ignore-Liste wurde bereits geladen.
        # Info-Zeile initial aktualisieren.
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
        """Callback des ListDataSource – hält die Info-Zeile in Sync."""
        self._update_repo_info()

    def _update_repo_info(self) -> None:
        """Zeigt unten an, wie viele Repos es gibt und wie viele ausgewählt sind."""
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
            # Semantik „none = all“ steht bereits in der Überschrift über der Liste.
            self.info_label.text = f"{total} Repos found."
        else:
            self.info_label.text = f"{total} Repos found ({len(rows)} selected)."

    def toggle_ignore_mode(self, sender) -> None:
        """Umschalten zwischen Normalmodus und Ignore-Auswahlmodus."""
        self.ignore_mode = not self.ignore_mode

        if self.ignore_mode:
            # Bisher ignorierte Repos markieren
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

            # Wenn aus irgendeinem Grund keine Zeilen selektiert sind,
            # lassen wir eine bereits existierende Ignore-Liste intakt,
            # statt sie stillschweigend zu leeren.
            if newly_ignored:
                self.ignored_repos = newly_ignored
            self.ignore_button.title = "Ignore…"
            # Nur die Ignore-Liste persistent machen, nicht die gesamte Merge-Config
            self.save_last_state(ignore_only=True)

            # Zurück in den Merge-Modus ohne Vorauswahl
            self.tv.selected_rows = []

        self._update_repo_info()

    def select_all_repos(self, sender) -> None:
        """
        SET: Wählt das Heimgewebe-Set an Repositories aus.

        Semantik:
        - Wenn die Ignore-Liste leer ist:
          → Alle Repos selektieren (wie früher „All“).
        - Wenn die Ignore-Liste gefüllt ist:
          → Alle Repos selektieren, deren Name NICHT in der Ignore-Liste steht.

        „None = All“-Semantik bleibt außerhalb von SET bestehen:
        - Keine Selektion = alle Repos mergen.
        """
        if not self.repos:
            return

        excluded = self.ignored_repos
        tv = self.tv

        rows: List[tuple[int, int]] = []
        for idx, name in enumerate(self.repos):
            if name in excluded:
                continue
            rows.append((0, idx))

        # Wenn nichts übrig bleibt → lieber keine Selektion setzen,
        # damit das Verhalten klar sichtbar bleibt.
        if not rows:
            tv.selected_rows = []
        else:
            tv.selected_rows = rows

        self._update_repo_info()

    def close_view(self, sender=None) -> None:
        """Schließt den Merger-Screen in Pythonista."""
        global _ACTIVE_MERGER_VIEW
        try:
            # dismiss() ist bei präsentierten Views zuverlässiger als close()
            _dismiss_view_best_effort(self.view)
        except Exception as e:
            # im Zweifel lieber still scheitern, statt iOS-Alert zu nerven, aber loggen
            sys.stderr.write(f"Warning: Failed to close view: {e}\n")
        finally:
            # If this instance is the active one, clear the pointer.
            try:
                if _ACTIVE_MERGER_VIEW is self.view:
                    _ACTIVE_MERGER_VIEW = None
            except Exception:
                pass

    def show_extras_sheet(self, sender):
        """Zeigt ein Sheet zur Konfiguration der Extras."""
        s = ui.View()
        s.name = "Extras"
        s.background_color = "#222222"

        # Items definieren, um Höhe zu berechnen
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
        title_height = 50 # War 40 + gap, wir nehmen etwas mehr für 2 Zeilen

        dynamic_h = padding_top + title_height + len(items) * row_h + padding_bottom + 60 # +60 für Done-Button + Gap

        # Mindest- und Maximalhöhe setzen (Pythonista Sheet Constraints)
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

        # Helper for switches
        def add_switch(key, title):
            nonlocal y
            sw = ui.Switch()
            sw.value = getattr(self.extras_config, key)
            sw.name = key
            # Action: direkt in self.extras_config schreiben
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

        # Close button
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
        """
        Aktualisiert den Hint-Text und setzt sinnvolle Defaults
        für max_bytes / split_size basierend auf dem gewählten Profil.

        Wichtig: Pfad- und Extension-Filter bleiben unverändert, damit
        man sie frei kombinieren kann (Profil + eigener Filter).
        """
        idx = self.seg_detail.selected_index
        if not (0 <= idx < len(self.seg_detail.segments)):
            return

        seg_name = self.seg_detail.segments[idx]

        # Hint-Text aktualisieren
        desc = PROFILE_DESCRIPTIONS.get(seg_name, "")
        self.profile_hint.text = desc

        # Presets anwenden (nur max_bytes + split_mb)
        preset = PROFILE_PRESETS.get(seg_name)
        if preset:
            # Max Bytes/File:
            # 0 oder None = unbegrenzt → Feld leer lassen
            max_bytes = preset.get("max_bytes", 0)
            if max_bytes is None or max_bytes <= 0:
                self.max_field.text = ""
            else:
                try:
                    self.max_field.text = str(int(max_bytes))
                except Exception:
                    # Fallback: lieber „unlimited“ als ein falscher Wert
                    self.max_field.text = ""

            # Gesamtlimit (Total Limit / Split = Part-Größe):
            split_mb = preset.get("split_mb")
            # None oder <=0 = kein Split → Feld leer lassen
            if split_mb is None or (
                isinstance(split_mb, (int, float)) and split_mb <= 0
            ):
                self.split_field.text = ""
            else:
                try:
                    self.split_field.text = str(int(split_mb))
                except Exception:
                    self.split_field.text = ""

    # --- State-Persistenz -------------------------------------------------

    def _collect_selected_repo_names(self) -> List[str]:
        """Liest die aktuell in der Liste selektierten Repos aus."""
        # abhängig davon, wie deine TableView/DataSource arbeitet:
        ds = self.ds
        selected: List[str] = []
        if hasattr(ds, "items"):
            # Standard ui.ListDataSource
            rows = getattr(self.tv, "selected_rows", None) or []
            for idx, name in enumerate(ds.items):
                # selected_rows ist eine Liste von Tupeln (section, row)
                if any(sec == 0 and r == idx for sec, r in rows):
                    selected.append(name)
        return selected

    def _apply_selected_repo_names(self, names: List[str]) -> None:
        """Setzt die Repo-Auswahl anhand gespeicherter Namen."""
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
            # Fallback: nur die erste gefundene Zeile selektieren
            try:
                tv.selected_row = rows[0]
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to select row in fallback: {e}\n")

    def _load_ignored_repos_from_state(self) -> None:
        """Lädt beim Start nur die persistierte Ignore-Liste."""
        # _state_path wird im __init__ gesetzt
        try:
            raw = self._state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return
        except Exception as exc:
            print(f"[repoLens] could not read ignore state: {exc!r}")
            return

        try:
            data = json.loads(raw)
        except Exception as exc:
            print(f"[repoLens] invalid ignore state JSON: {exc!r}")
            return

        if isinstance(data, dict):
            self.ignored_repos = set(data.get("ignored_repos", []))

    def save_last_state(self, ignore_only: bool = False) -> None:
        """
        Speichert den UI-Zustand in einer JSON-Datei.

        ignore_only = True:
            Nur die Ignore-Liste aktualisieren, sonstige Felder unangetastet lassen.
        ignore_only = False:
            Vollständige Config (Filter, Profile, Auswahl, Extras) + Ignore-Liste speichern.
        """
        data: Dict[str, Any] = {}

        # Bestehenden Zustand laden, damit wir bei ignore_only nicht alles überschreiben
        if self._state_path.exists():
            try:
                raw = self._state_path.read_text(encoding="utf-8")
                existing = json.loads(raw)
                if isinstance(existing, dict):
                    data.update(existing)
            except Exception as exc:
                print(f"[repoLens] could not read existing state: {exc!r}")

        # Ignore-Liste wird *immer* aktualisiert
        data["ignored_repos"] = sorted(self.ignored_repos)

        # Nur wenn wir *nicht* im ignore_only-Modus sind, die restliche Config überschreiben
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
            print(f"[repoLens] could not persist state: {exc}")

    def restore_last_state(self, sender=None) -> None:
        try:
            raw = self._state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            if sender: # Nur bei Klick Feedback geben
                if console:
                    console.alert("repoLens", "No saved state found.", "OK", hide_cancel_button=True)
            return
        except Exception as exc:
            print(f"[repoLens] could not read state: {exc!r}", file=sys.stderr)
            return

        try:
            data = json.loads(raw)
        except Exception as exc:
            print(f"[repoLens] invalid state JSON: {exc!r}", file=sys.stderr)
            return

        # Felder setzen
        profile = data.get("detail_profile")
        if profile and profile in self.seg_detail.segments:
            try:
                self.seg_detail.selected_index = self.seg_detail.segments.index(profile)
            except ValueError as e:
                # If the profile is not found in segments, just skip setting selected_index.
                print(f"[repoLens] Profile '{profile}' not found in segments: {e}", file=sys.stderr)

        self.ext_field.text = data.get("ext_filter", "")
        self.path_field.text = data.get("path_filter", "")
        self.max_field.text = data.get("max_bytes", "")
        self.split_field.text = data.get("split_mb", "")
        self.plan_only_switch.value = bool(data.get("plan_only", False))
        if getattr(self, "code_only_switch", None) is not None:
            self.code_only_switch.value = bool(data.get("code_only", False))

        self.ignored_repos = set(data.get("ignored_repos", []))

        # Restore Extras
        # Important: only overwrite if key exists, otherwise keep default (which might be True for new features)
        extras_data = data.get("extras", {})
        if extras_data:
            if "health" in extras_data:
                self.extras_config.health = extras_data["health"]
            if "organism_index" in extras_data:
                self.extras_config.organism_index = extras_data["organism_index"]
            if "fleet_panorama" in extras_data:
                self.extras_config.fleet_panorama = extras_data["fleet_panorama"]
            if "delta_reports" in extras_data:
                self.extras_config.delta_reports = extras_data["delta_reports"]
            if "augment_sidecar" in extras_data:
                self.extras_config.augment_sidecar = extras_data["augment_sidecar"]
            if "heatmap" in extras_data:
                self.extras_config.heatmap = extras_data["heatmap"]
            if "json_sidecar" in extras_data:
                self.extras_config.json_sidecar = extras_data["json_sidecar"]

        # Update hint text to match restored profile
        self.on_profile_changed(None)

        selected = data.get("selected_repos") or []
        if selected:
            # Direkt anwenden – ohne ui.delay, das auf manchen Wegen nicht verfügbar ist
            self._apply_selected_repo_names(selected)

        if sender and console:
            # Kurzes Feedback, aber niemals hart failen
            try:
                console.hud_alert("Config loaded")
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to show HUD alert: {e}\n")

        # Info-Zeile nach dem Wiederherstellen aktualisieren
        self._update_repo_info()


    def _tableview_cell(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.background_color = "#111111"
        if 0 <= row < len(self.repos):
            cell.text_label.text = self.repos[row]
        cell.text_label.text_color = "white"
        cell.text_label.background_color = "#111111"

        selected_bg = ui.View()
        # gut sichtbarer Selected-Hintergrund
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
        # Leeres Feld → Standard: unbegrenzt (0 = „no limit“)
        if not txt:
            return 0

        # Optional: Eingaben wie "10M", "512K", "1G" akzeptieren
        try:
            val = parse_human_size(txt)
        except Exception:
            val = 0

        # <=0 interpretieren wir bewusst als „kein Limit“
        if val <= 0:
            return 0
        return val

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

    def run_delta_from_last_import(self, sender) -> None:
        """
        Erzeugt einen Delta-Merge aus dem neuesten Import-Diff im merges-Ordner.
        Nutzt die Delta-Helfer aus repolens-extractor.py (falls verfügbar).
        """
        merges_dir = get_merges_dir(self.hub)
        try:
            candidates = list(merges_dir.glob("*-import-diff-*.md"))
        except Exception as exc:
            print(f"[repoLens] could not scan merges dir: {exc}")
            candidates = []

        if not candidates:
            if console:
                console.alert(
                    "repoLens",
                    "No import diff found.",
                    "OK",
                    hide_cancel_button=True,
                )
            else:
                print("[repoLens] No import diff found.")
            return

        # jüngstes Diff wählen
        try:
            diff_path = max(candidates, key=lambda p: p.stat().st_mtime)
        except Exception as exc:
            if console:
                console.alert(
                    "repoLens",
                    f"Failed to select latest diff: {exc}",
                    "OK",
                    hide_cancel_button=True,
                )
            else:
                print(f"[repoLens] Failed to select latest diff: {exc}")
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
                console.alert("repoLens", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[repoLens] {msg}")
            return

        mod = _load_repolens_extractor_module()
        if mod is None or not hasattr(mod, "create_delta_merge_from_diff"):
            msg = "Delta helper (repolens-extractor) not available."
            if console:
                console.alert("repoLens", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[repoLens] {msg}")
            return

        # Execute delta extraction (without generating a legacy report)
        try:
            # We bypass create_delta_merge_from_diff to avoid double-writing.
            # Instead we extract metadata directly from the diff file.
            delta_meta = None
            extract_returned_none = False
            diff_mtime = None

            try:
                diff_mtime = diff_path.stat().st_mtime
            except Exception:
                diff_mtime = None

            if hasattr(mod, "extract_delta_meta_from_diff_file"):
                try:
                    delta_meta = mod.extract_delta_meta_from_diff_file(diff_path)
                    if delta_meta is None:
                        extract_returned_none = True
                except Exception as e:
                    sys.stderr.write(f"[ERROR] Delta extraction failed: {e}\n")

            # Wenn der Extraktor erfolgreich lief, aber kein Delta liefert, kein Fallback zulassen
            if extract_returned_none:
                msg = "Diff enthält keine Delta-Zeilen (keine Änderungen?) – breche ohne Fallback ab."
                if console:
                    console.alert("repoLens", msg, "OK", hide_cancel_button=True)
                else:
                    print(f"[repoLens] {msg}")
                return

            # Fallback nur, wenn der Extraktor nicht verfügbar war oder fehlgeschlagen ist
            if delta_meta is None:
                try:
                    candidate_paths = []
                    delta_from_diff = diff_path.with_suffix(".delta.json")
                    candidate_paths.append(delta_from_diff)
                    try:
                        repo_specific = sorted(
                            merges_dir.glob(f"{repo_name}-import-diff-*.delta.json"),
                            key=lambda p: p.stat().st_mtime,
                            reverse=True,
                        )
                        candidate_paths.extend(repo_specific)
                    except Exception:
                        pass
                    legacy_delta = merges_dir / "delta.json"
                    candidate_paths.append(legacy_delta)

                    for candidate in candidate_paths:
                        if not candidate.exists():
                            continue
                        # Verhindere veraltete Artefakte: nur Dateien akzeptieren, die zeitlich zum Diff passen
                        try:
                            cand_mtime = candidate.stat().st_mtime
                            if diff_mtime is not None and cand_mtime + 1 < diff_mtime:
                                continue
                        except Exception:
                            pass
                        raw = json.loads(candidate.read_text(encoding="utf-8"))
                        if (
                            isinstance(raw, dict)
                            and raw.get("type") == "repolens-delta"
                            and "summary" in raw
                        ):
                            delta_meta = raw
                            break
                except Exception as e:
                    print(f"[repoLens] Failed to read delta metadata: {e}", file=sys.stderr)

            if not delta_meta:
                msg = "Could not extract delta metadata from diff."
                if console:
                    console.alert("repoLens", msg, "OK", hide_cancel_button=True)
                else:
                    print(f"[repoLens] {msg}")
                return

            # Determine extras config consistent with UI
            # We use self.extras_config but enable delta_reports
            extras = ExtrasConfig(
                health=self.extras_config.health,
                organism_index=self.extras_config.organism_index,
                fleet_panorama=self.extras_config.fleet_panorama,
                augment_sidecar=self.extras_config.augment_sidecar,
                heatmap=self.extras_config.heatmap,
                delta_reports=True # Force enable
            )

            # Need to scan repo for write_reports_v2
            # Delta Report Strategy:
            # 1. Scan repo fully (max_bytes=0 => unlimited)
            # 2. Filter file list based on delta_meta (changed + added)
            # 3. Use profile 'max' to ensure full content is included for these files

            summary = scan_repo(repo_root, extensions=None, path_contains=None, max_bytes=0)

            # Filter files to include only changed/added
            # Helper to collect paths from delta_meta
            allowed_paths = set()

            # Check for legacy arrays
            if "files_added" in delta_meta and isinstance(delta_meta["files_added"], list):
                allowed_paths.update(delta_meta["files_added"])

            if "files_changed" in delta_meta and isinstance(delta_meta["files_changed"], list):
                for item in delta_meta["files_changed"]:
                    if isinstance(item, dict):
                        path = item.get("path")
                        if path: allowed_paths.add(path)
                    elif isinstance(item, str):
                        allowed_paths.add(item)

            # Check for summary object (repolens-delta schema) if arrays are missing/empty
            # Note: The schema stores lists in top-level usually. If they are missing, we can't filter.
            # If allowed_paths is empty but summary says there are changes, we might have a problem.
            # But assume delta_meta is well-formed from extractor.

            if allowed_paths:
                # Filter the file list in summary
                # Use normalized posix string for comparison
                filtered_files = []
                for f in summary["files"]:
                    if f.rel_path.as_posix() in allowed_paths:
                        filtered_files.append(f)

                summary["files"] = filtered_files
                # Update stats
                summary["total_files"] = len(filtered_files)
                summary["total_bytes"] = sum(f.size for f in filtered_files)

            # Generate merge reports
            # Use 'max' profile to ensure full content for the changed/added files
            # (dev/doc logic might otherwise hide content for doc changes)
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
                delta_meta=delta_meta,    # << NEW: real delta injected
            )

            # Close files
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
                    console.alert("repoLens", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[repoLens] {msg}")

        except Exception as exc:
            msg = f"Delta merge failed: {exc}"
            if console:
                console.alert("repoLens", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[repoLens] {msg}")
            return

    def run_merge(self, sender) -> None:
        """
        UI-Handler: niemals schwere Arbeit im Main-Thread ausführen,
        sonst wirkt Pythonista "eingefroren" – besonders bei Multi-Repo.
        """
        try:
            import ui as _ui
            in_bg = getattr(_ui, "in_background", None)
        except Exception:
            in_bg = None

        if in_bg:
            in_bg(self._run_merge_safe)()
        else:
            # Fallback: wenigstens nicht crashen – aber UI kann dann weiterhin blocken.
            self._run_merge_safe()

    def _run_merge_safe(self) -> None:
        try:
            # Aktuellen Zustand merken
            self.save_last_state()
            self._run_merge_inner()
        except Exception as e:
            traceback.print_exc()

            # Use specific messaging for validation errors if possible
            if "ValidationException" in type(e).__name__ or "Structure Violation" in str(e):
                msg = f"Validation Error: {e}"
            else:
                msg = f"Error: {e}"

            if console:
                console.alert("repoLens", msg, "OK", hide_cancel_button=True)
            else:
                print(msg, file=sys.stderr)

    def _run_merge_inner(self) -> None:
        selected = self._get_selected_repos()
        if not selected:
            if console:
                console.alert("repoLens", "No repos selected.", "OK", hide_cancel_button=True)
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

        # Plan-only wird aus dem Switch gelesen; falls Switch nicht existiert,
        # bleibt der Modus aus.
        plan_switch = getattr(self, "plan_only_switch", None)
        plan_only = bool(plan_switch and plan_switch.value)
        code_switch = getattr(self, "code_only_switch", None)
        code_only = bool(code_switch and code_switch.value)

        # Mutual exclusion: plan_only wins to avoid ambiguous semantics.
        if plan_only and code_only:
            code_only = False

        summaries = []
        total = len(selected)
        for i, name in enumerate(selected, start=1):
            root = self.hub / name
            if not root.is_dir():
                continue
            # Mini-Progress + UI-Yield (hilft spürbar bei Pythonista)
            if console:
                try:
                    console.hud_alert(f"Scanning {i}/{total}: {name}", duration=0.6)
                except Exception:
                    pass
            try:
                import ui as _ui
                # yield to main loop without slowing down much
                _ui.delay(lambda: None, 0.0)
            except Exception:
                pass
            summary = scan_repo(root, extensions or None, path_contains, max_bytes)
            summaries.append(summary)

        if not summaries:
            if console:
                console.alert("repoLens", "No valid repos found.", "OK", hide_cancel_button=True)
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
            if console:
                console.alert("repoLens", "No report generated.", "OK", hide_cancel_button=True)
            else:
                print("No report generated.")
            return

        # Force close any tabs that might have opened
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
                console.alert("repoLens", msg, "OK", hide_cancel_button=True)
        else:
            print(f"repoLens: {msg}")
            for p in out_paths:
                print(f"  - {p.name}")


# --- CLI Mode ---

def _is_headless_requested() -> bool:
    # Headless wenn:
    # 1) --headless Flag, oder
    # 2) REPOLENS_HEADLESS=1 in der Umgebung, oder
    # 3) ui-Framework nicht verfügbar
    return ("--headless" in sys.argv) or (os.environ.get("REPOLENS_HEADLESS") == "1") or (ui is None)

def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="repoLens CLI")
    parser.add_argument("paths", nargs="*", help="Repositories to merge")
    parser.add_argument("--hub", help="Base directory (repolens-hub)")
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
            mod = _load_repolens_extractor_module()
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


def main():
    # UI nur verwenden, wenn wir NICHT als App-Extension laufen und NICHT headless requested ist
    use_ui = (
        ui is not None
        and not _is_headless_requested()
        and (appex is None or not appex.is_running_extension())
    )

    if use_ui:
        try:
            hub = detect_hub_dir(SCRIPT_PATH)
            return run_ui(hub)
        except Exception as e:
            # Fallback auf CLI (headless), falls UI trotz ui-Import nicht verfügbar ist
            if console:
                try:
                    console.alert(
                        "repoLens",
                        f"UI not available, falling back to CLI. ({e})",
                        "OK",
                        hide_cancel_button=True,
                    )
                except Exception:
                    pass
            else:
                print(
                    f"repoLens: UI not available, falling back to CLI. ({e})",
                    file=sys.stderr,
                )
            main_cli()
    else:
        main_cli()

if __name__ == "__main__":
    main()
