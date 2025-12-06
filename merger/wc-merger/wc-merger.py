#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc-merger – Working-Copy Merger.
Enhanced AI-optimized reports with strict Pflichtenheft structure.
"""

import sys
import os
import json
import traceback
from pathlib import Path
from typing import List

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
            except Exception:
                pass


# Merger-UI merkt sich die letzte Auswahl in dieser JSON-Datei im Hub:
LAST_STATE_FILENAME = ".wc-merger-state.json"

PROFILE_DESCRIPTIONS = {
    "overview": "Docs + CI, kompakt, kombiniert",
    "summary": "Docs + zentrale Config + Kern-Code",
    "dev": "Code + Config pro Repo, für PR-Reviews",
    "max": "Alles, maximal detailreich (Vorsicht, groß)",
}

# Voreinstellungen pro Profil:
# Ziel:
# - overview  → sehr knapp, kleine Dateien
# - summary   → mittlere Tiefe
# - dev       → tief, aber nicht grenzenlos
# - max       → nutzt das globale DEFAULT_MAX_BYTES (Textfeld leer lassen)
PROFILE_PRESETS = {
    "overview": {
        "max_bytes": 150_000,   # ~150 KB
        "split_mb": 5,
    },
    "summary": {
        "max_bytes": 250_000,   # ~250 KB
        "split_mb": 15,
    },
    "dev": {
        "max_bytes": 600_000,   # ~600 KB
        "split_mb": 25,
    },
    "max": {
        "max_bytes": None,      # leer = DEFAULT_MAX_BYTES
        "split_mb": 50,
    },
}


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

def run_ui(hub: Path) -> int:
    """Starte den Merger im Vollbild-UI-Modus ohne Pythonista-Titlebar."""
    ui_obj = MergerUI(hub)
    v = ui_obj.view
    # Volle Fläche, eigene „Titlebar“ im View, keine weiße System-Leiste
    v.present('fullscreen', hide_title_bar=True)
    return 0

class MergerUI(object):
    def __init__(self, hub: Path) -> None:
        self.hub = hub
        self.repos = find_repos_in_hub(hub)

        # Pfad zur State-Datei
        self._state_path = (self.hub / LAST_STATE_FILENAME).resolve()

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
                except Exception:
                    pass

            # Kein extra Hintergrund-View mehr – direkt hinzufügen
            parent_view.add_subview(tf)

        # kleine Helper-Funktion für Dark-Theme-Textfelder
        def _style_textfield(tf: ui.TextField) -> None:
            """Basis-Styling, Wrapper übernimmt das Dunkel-Thema."""
            tf.autocorrection_type = False
            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE

        margin = 10
        y = 10

        base_label = ui.Label()
        # etwas Platz rechts für den Close-Button lassen
        base_label.frame = (10, y, v.width - 80, 34)
        base_label.flex = "W"
        base_label.number_of_lines = 2
        base_label.text = f"Base-Dir: {hub}"
        base_label.text_color = "white"
        base_label.background_color = "#111111"
        base_label.font = ("<System>", 11)
        v.add_subview(base_label)
        self.base_label = base_label

        # Close-Button rechts oben – leicht nach innen versetzt,
        # damit er nicht mit iOS-Ecken kollidiert.
        close_btn = ui.Button()
        close_btn.title = "Close"
        # etwas mehr Rand nach rechts: ca. 20pt Abstand
        close_btn.frame = (v.width - 80, y + 3, 60, 28)
        close_btn.flex = "WL"
        close_btn.background_color = "#333333"
        close_btn.tint_color = "white"
        close_btn.corner_radius = 4.0
        close_btn.action = self.close_view
        v.add_subview(close_btn)
        self.close_button = close_btn

        y += 40

        repo_label = ui.Label()
        # Platz lassen für „Alle auswählen“-Button rechts
        repo_label.frame = (10, y, v.width - 110, 20)
        repo_label.flex = "W"
        repo_label.text = "Repos (Tap to select – None = All):"
        repo_label.text_color = "white"
        repo_label.background_color = "#111111"
        repo_label.font = ("<System>", 13)
        v.add_subview(repo_label)

        select_all_btn = ui.Button()
        select_all_btn.title = "All"
        select_all_btn.frame = (v.width - 90, y - 2, 80, 24)
        select_all_btn.flex = "WL"
        select_all_btn.background_color = "#333333"
        select_all_btn.tint_color = "white"
        select_all_btn.corner_radius = 4.0
        select_all_btn.action = self.select_all_repos
        v.add_subview(select_all_btn)
        self.select_all_button = select_all_btn
        # interner Toggle-Status für den All-Button
        self._all_toggle_selected = False

        y += 22

        tv = ui.TableView()
        # Höhe dynamisch: mind. 160, sonst ca. 45% des Screens
        list_height = max(160, v.height * 0.40)
        tv.frame = (10, y, v.width - 20, list_height)
        tv.flex = "WH"
        tv.background_color = "#111111"
        tv.separator_color = "#333333"
        tv.row_height = 32
        tv.allows_multiple_selection = True
        # Improve readability on dark background
        tv.tint_color = "#007aff"

        ds = ui.ListDataSource(self.repos)
        ds.text_color = "white"
        # deutliche Selektion: kräftiges Blau statt „grau auf schwarz“
        ds.highlight_color = "#0050ff"
        ds.tableview_cell_for_row = self._tableview_cell
        tv.data_source = ds
        tv.delegate = ds
        v.add_subview(tv)
        self.tv = tv
        self.ds = ds

        # Alle folgenden Elemente direkt UNTER die Liste setzen
        y = tv.frame.y + tv.frame.height + 10

        ext_field = ui.TextField()
        ext_field.frame = (10, y, v.width - 20, 28)
        ext_field.flex = "W"
        ext_field.placeholder = ".md,.yml,.rs (empty = all)"
        ext_field.text = ""
        _style_textfield(ext_field)
        _wrap_textfield_in_dark_bg(v, ext_field)
        self.ext_field = ext_field

        y += 34

        path_field = ui.TextField()
        path_field.frame = (10, y, v.width - 20, 28)
        path_field.flex = "W"
        path_field.placeholder = "Path contains (e.g. docs/ or .github/)"
        _style_textfield(path_field)
        path_field.autocorrection_type = False
        path_field.spellchecking_type = False
        _wrap_textfield_in_dark_bg(v, path_field)
        self.path_field = path_field

        y += 36

        # --- Detail: eigene Zeile ---
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
            seg_detail.selected_index = 2  # Default dev
        seg_detail.frame = (70, y - 2, v.width - 80, 28)
        seg_detail.flex = "W"
        # Use standard iOS blue instead of white for better contrast
        seg_detail.tint_color = "#007aff"
        seg_detail.background_color = "#dddddd"
        seg_detail.action = self.on_profile_changed
        v.add_subview(seg_detail)
        self.seg_detail = seg_detail

        # Kurzer Text unterhalb der Detail-Presets
        self.profile_hint = ui.Label(
            frame=(margin, y + 28, v.width - 2 * margin, 20),
            flex="W",
            text="",
            text_color="white",
            font=("<system>", 12),
        )
        # Direkt unter dem SegmentControl anzeigen, bevor Mode kommt
        # Wir müssen "y" etwas anpassen, damit Mode weiter runter rutscht
        v.add_subview(self.profile_hint)
        y += 24 # Platz für Hint

        y += 36  # neue Zeile für Mode

        # --- Mode: darunter, eigene Zeile ---
        mode_label = ui.Label()
        mode_label.text = "Mode:"
        mode_label.text_color = "white"
        mode_label.background_color = "#111111"
        mode_label.frame = (10, y, 60, 22)
        v.add_subview(mode_label)

        seg_mode = ui.SegmentedControl()
        seg_mode.segments = ["combined", "per repo"]
        if args.mode == "pro-repo":
            seg_mode.selected_index = 1
        else:
            seg_mode.selected_index = 0
        seg_mode.frame = (70, y - 2, v.width - 80, 28)
        seg_mode.flex = "W"
        # Same accent color as detail segmented control
        seg_mode.tint_color = "#007aff"
        seg_mode.background_color = "#dddddd"
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
        _wrap_textfield_in_dark_bg(v, max_field)
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
        _wrap_textfield_in_dark_bg(v, split_field)
        self.split_field = split_field

        y += 36

        # --- Plan Only Switch ---
        plan_label = ui.Label()
        plan_label.text = "Plan only:"
        plan_label.text_color = "white"
        plan_label.background_color = "#111111"
        plan_label.frame = (10, y, 120, 22)
        v.add_subview(plan_label)

        plan_switch = ui.Switch()
        plan_switch.frame = (130, y - 2, 60, 32)
        plan_switch.flex = "W"
        plan_switch.value = False
        v.add_subview(plan_switch)
        self.plan_only_switch = plan_switch

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

        # Initiale Anzeige des Hints
        self.on_profile_changed(None)

        y += 26

        # --- Load State Button ---
        # Vor dem Run-Button, damit man alte Configs laden kann
        load_btn = ui.Button()
        load_btn.title = "Load Last Config"
        load_btn.font = ("<System>", 14)
        # Position: gleiche Breite wie Felder, etwas niedriger als Standard-Button
        load_btn.frame = (10, y, v.width - 20, 32)
        load_btn.flex = "W"
        load_btn.background_color = "#333333"
        load_btn.tint_color = "white"
        load_btn.corner_radius = 6.0
        load_btn.action = self.restore_last_state
        v.add_subview(load_btn)

        y += 42

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
            # None = All – das explizit kenntlich machen
            self.info_label.text = f"{total} Repos found (none selected = all)."
        else:
            self.info_label.text = f"{total} Repos found ({len(rows)} selected)."

    def select_all_repos(self, sender) -> None:
        """
        Toggle: nichts → alle ausgewählt, alles ausgewählt → Auswahl löschen.
        Semantik bleibt: „keine Auswahl = alle Repos“, nur die Optik ändert sich.
        """
        if not self.repos:
            return

        tv = self.tv
        rows = tv.selected_rows or []

        if rows and len(rows) == len(self.repos):
            # alles war ausgewählt → Auswahl löschen (zurück zu „none = all“)
            tv.selected_rows = []
        else:
            # explizit alle Zeilen selektieren
            tv.selected_rows = [(0, i) for i in range(len(self.repos))]

        # Info-Zeile aktualisieren
        self._update_repo_info()

    def close_view(self, sender=None) -> None:
        """Schließt den Merger-Screen in Pythonista."""
        try:
            self.view.close()
        except Exception:
            # im Zweifel lieber still scheitern, statt iOS-Alert zu nerven
            pass

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
            max_bytes = preset.get("max_bytes")
            if max_bytes is None:
                # Leer = DEFAULT_MAX_BYTES (wird in _parse_max_bytes aufgelöst)
                self.max_field.text = ""
            else:
                self.max_field.text = str(int(max_bytes))

            split_mb = preset.get("split_mb")
            if split_mb is not None:
                # UI-Textfeld erwartet MB als Zahl
                self.split_field.text = str(int(split_mb))

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
                if any(r == idx for sec, r in rows):
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
            except Exception:
                pass

    def save_last_state(self) -> None:
        """
        Persistiert den aktuellen UI-Zustand in einer JSON-Datei.

        Speichert die ausgewählten Repositories, Filtereinstellungen, das gewählte Profil,
        sowie weitere relevante UI-Parameter in einer Datei unter `self._state_path`.
        Dies ermöglicht das Wiederherstellen des letzten Zustands beim nächsten Start.
        """
        if not self.repos:
            return

        detail_idx = self.seg_detail.selected_index
        if 0 <= detail_idx < len(self.seg_detail.segments):
            detail = self.seg_detail.segments[detail_idx]
        elif self.seg_detail.segments:
            detail = self.seg_detail.segments[0]
        else:
            detail = ""

        data = {
            "selected_repos": self._collect_selected_repo_names(),
            "ext_filter": self.ext_field.text or "",
            "path_filter": self.path_field.text or "",
            "detail_profile": detail,
            "max_bytes": self.max_field.text or "",
            "split_mb": self.split_field.text or "",
            "plan_only": bool(self.plan_only_switch.value),
        }
        try:
            self._state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[wc-merger] could not persist state: {exc}")

    def restore_last_state(self, sender=None) -> None:
        try:
            raw = self._state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            if sender: # Nur bei Klick Feedback geben
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

        # Felder setzen
        profile = data.get("detail_profile")
        if profile and profile in self.seg_detail.segments:
            try:
                self.seg_detail.selected_index = self.seg_detail.segments.index(profile)
            except ValueError:
                # If the profile is not found in segments, just skip setting selected_index.
                pass

        self.ext_field.text = data.get("ext_filter", "")
        self.path_field.text = data.get("path_filter", "")
        self.max_field.text = data.get("max_bytes", "")
        self.split_field.text = data.get("split_mb", "")
        self.plan_only_switch.value = bool(data.get("plan_only", False))

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
            except Exception:
                pass

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
            # Aktuellen Zustand merken
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

        # Plan-only wird aus dem Switch gelesen; falls Switch nicht existiert,
        # bleibt der Modus aus.
        plan_switch = getattr(self, "plan_only_switch", None)
        plan_only = bool(plan_switch and plan_switch.value)

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
            debug=False,
            path_filter=path_contains,
            ext_filter=extensions or None,
        )

        if not out_paths:
            if console:
                console.alert("wc-merger", "No report generated.", "OK", hide_cancel_button=True)
            else:
                print("No report generated.")
            return

        # Force close any tabs that might have opened
        force_close_files(out_paths)

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
    # UI nur verwenden, wenn wir NICHT als App-Extension laufen und NICHT headless requested ist
    use_ui = (
        ui is not None
        and not _is_headless_requested()
        and (appex is None or not appex.is_running_extension())
    )

    if use_ui:
        try:
            script_path = Path(__file__).resolve()
            hub = detect_hub_dir(script_path)
            return run_ui(hub)
        except Exception as e:
            # Fallback auf CLI (headless), falls UI trotz ui-Import nicht verfügbar ist
            if console:
                try:
                    console.alert(
                        "wc-merger",
                        f"UI not available, falling back to CLI. ({e})",
                        "OK",
                        hide_cancel_button=True,
                    )
                except Exception:
                    pass
            else:
                print(
                    f"wc-merger: UI not available, falling back to CLI. ({e})",
                    file=sys.stderr,
                )
            main_cli()
    else:
        main_cli()

if __name__ == "__main__":
    main()
