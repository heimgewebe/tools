#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc-merger – Working-Copy-orientierter Gewebe-Merger für Pythonista.

Ziele
- Direkt auf den Repos im wc-hub arbeiten (Working-Copy-Exporte).
- Interaktive Auswahl von Repos, optional Filter auf Dateiendungen / Pfade.
- Ausgabe eines oder mehrerer Markdown-Berichte (overview / summary / max).

Besonderheiten
- Read-only: wc-merger löscht niemals Quellen.
- Detailstufe-Default: "max".
- Max. Dateigröße-Default: 10 MB.
- Zwei Merge-Modi:
  - "gesamt"   => kombinierter Bericht über alle gewählten Repos
  - "pro-repo" => je Repo ein eigener Bericht

Erwartetes Layout (im „Pythonista 3“-Ordner in Dateien):

  Pythonista3/Documents/
    wc-hub/
      <deine Repos>/
      merges/          <- Ausgabeverzeichnis
"""

import sys
import traceback
from pathlib import Path
from typing import List

try:
    import ui        # type: ignore
    import console   # type: ignore
    import editor    # type: ignore
except ImportError:
    ui = None        # type: ignore
    console = None   # type: ignore
    editor = None    # type: ignore

from merge_core import (  # merge_core benutzt den hart kodierten Hub-Pfad
    MERGES_DIR_NAME,
    DEFAULT_MAX_BYTES,
    detect_hub_dir,
    get_merges_dir,
    scan_repo,
    write_reports,
    _normalize_ext_list,
)


# ---------------------------------------------------------------------------
# Repo-Liste im Hub
# ---------------------------------------------------------------------------

def find_repos_in_hub(hub: Path) -> List[str]:
    """
    Sucht nach Repos im Hub:
    - direkte Unterordner
    - ignoriert "merges" und versteckte Ordner.
    """
    repos: List[str] = []
    for child in sorted(hub.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name == MERGES_DIR_NAME:
            continue
        if child.name.startswith("."):
            continue
        repos.append(child.name)
    return repos


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

class MergerUI(object):
    def __init__(self, hub: Path) -> None:
        self.hub = hub
        self.repos = find_repos_in_hub(hub)

        # Root-View: fester Rahmen wie in der alten Version
        v = ui.View()
        v.name = "WC-Merger"
        v.background_color = "#111111"
        v.frame = (0, 0, 540, 620)
        self.view = v

        y = 10

        # Base-Dir Label (oben, schwarze Leiste)
        base_label = ui.Label()
        base_label.frame = (10, y, v.width - 20, 34)
        base_label.flex = "W"
        base_label.number_of_lines = 2
        base_label.text = f"Base-Dir: {hub}"
        base_label.text_color = "white"
        base_label.background_color = "#000000"
        base_label.font = ("<System>", 11)
        v.add_subview(base_label)
        self.base_label = base_label
        y += 40

        # Überschrift für Repo-Liste
        repo_label = ui.Label()
        repo_label.frame = (10, y, v.width - 20, 20)
        repo_label.flex = "W"
        repo_label.text = "Repos (Tippen zum Auswählen – nix = alle):"
        repo_label.text_color = "white"
        repo_label.background_color = "#111111"
        repo_label.font = ("<System>", 13)
        v.add_subview(repo_label)
        y += 22

        # Repos Table (wie alte Version, aber dark)
        tv = ui.TableView()
        tv.frame = (10, y, v.width - 20, 160)
        tv.flex = "W"
        tv.background_color = "#111111"
        tv.row_height = 32
        tv.allows_multiple_selection = True

        ds = ui.ListDataSource(self.repos)
        tv.data_source = ds
        tv.delegate = ds
        v.add_subview(tv)
        self.tv = tv
        self.ds = ds

        y += 170

        # Extensions TextField
        ext_field = ui.TextField()
        ext_field.frame = (10, y, v.width - 20, 28)
        ext_field.flex = "W"
        ext_field.placeholder = ".md,.yml (leer = Auto-Ermittlung/Alles)"
        ext_field.text = ""
        ext_field.background_color = "#222222"
        ext_field.text_color = "white"
        ext_field.tint_color = "white"
        ext_field.autocorrection_type = False
        ext_field.spellchecking_type = False
        v.add_subview(ext_field)
        self.ext_field = ext_field

        y += 34

        # Pfad enthält
        path_field = ui.TextField()
        path_field.frame = (10, y, v.width - 20, 28)
        path_field.flex = "W"
        path_field.placeholder = "Pfad enthält (z.B. docs/ oder .github/)"
        path_field.background_color = "#222222"
        path_field.text_color = "white"
        path_field.tint_color = "white"
        path_field.autocorrection_type = False
        path_field.spellchecking_type = False
        v.add_subview(path_field)
        self.path_field = path_field

        y += 36

        # Detail SegmentedControl
        detail_label = ui.Label()
        detail_label.text = "Detail:"
        detail_label.text_color = "white"
        detail_label.background_color = "#111111"
        detail_label.frame = (10, y, 60, 22)
        v.add_subview(detail_label)

        seg_detail = ui.SegmentedControl()
        seg_detail.segments = ["overview", "summary", "max"]
        seg_detail.selected_index = 2  # max
        seg_detail.frame = (70, y - 2, 220, 28)
        seg_detail.flex = "W"
        seg_detail.tint_color = "#ffffff"
        v.add_subview(seg_detail)
        self.seg_detail = seg_detail

        # Modus SegmentedControl
        mode_label = ui.Label()
        mode_label.text = "Modus:"
        mode_label.text_color = "white"
        mode_label.background_color = "#111111"
        mode_label.frame = (300, y, 60, 22)
        v.add_subview(mode_label)

        seg_mode = ui.SegmentedControl()
        seg_mode.segments = ["gesamt", "pro Repo"]
        seg_mode.selected_index = 0
        seg_mode.frame = (360, y - 2, v.width - 370, 28)
        seg_mode.flex = "W"
        seg_mode.tint_color = "#ffffff"
        v.add_subview(seg_mode)
        self.seg_mode = seg_mode

        y += 36

        # Max Bytes
        max_label = ui.Label()
        max_label.text = "Max Bytes/File:"
        max_label.text_color = "white"
        max_label.background_color = "#111111"
        max_label.frame = (10, y, 120, 22)
        v.add_subview(max_label)

        max_field = ui.TextField()
        max_field.text = str(DEFAULT_MAX_BYTES)
        max_field.frame = (130, y - 2, 140, 28)
        max_field.flex = "W"
        max_field.background_color = "#222222"
        max_field.text_color = "white"
        max_field.tint_color = "white"
        max_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        v.add_subview(max_field)
        self.max_field = max_field

        # Plan only Switch
        plan_switch = ui.Switch()
        plan_switch.value = False
        plan_switch.frame = (10, y + 32, 0, 0)
        v.add_subview(plan_switch)
        self.plan_switch = plan_switch

        plan_label = ui.Label()
        plan_label.text = "Plan only (kein Inhalt im Bericht)"
        plan_label.text_color = "white"
        plan_label.background_color = "#111111"
        plan_label.frame = (60, y + 32, v.width - 70, 22)
        plan_label.flex = "W"
        v.add_subview(plan_label)

        y += 64

        # Info Label für Repo-Anzahl
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

        # Merge Button
        btn = ui.Button()
        btn.title = "Merge ausführen"
        btn.frame = (10, y, v.width - 20, 40)
        btn.flex = "W"
        btn.background_color = "#007aff"
        btn.tint_color = "white"
        btn.corner_radius = 6.0
        btn.action = self.run_merge
        v.add_subview(btn)
        self.run_button = btn

    # ----------------------------

    def _update_repo_info(self) -> None:
        if not self.repos:
            self.info_label.text = "Keine Repos im Hub gefunden."
        else:
            self.info_label.text = f"{len(self.repos)} Repos im Hub gefunden."

    def _get_selected_repos(self) -> List[str]:
        tv = self.tv
        rows = tv.selected_rows or []
        if not rows:
            # Nichts ausgewählt => alle
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

    def run_merge(self, sender) -> None:
        try:
            self._run_merge_inner()
        except Exception as e:
            traceback.print_exc()
            msg = f"Fehler: {e}"
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(msg, file=sys.stderr)

    def _run_merge_inner(self) -> None:
        selected = self._get_selected_repos()
        if not selected:
            if console:
                console.alert(
                    "wc-merger",
                    "Keine Repos ausgewählt und auch keine im Hub gefunden.",
                    "OK",
                    hide_cancel_button=True,
                )
            return

        ext_text = (self.ext_field.text or "").strip()
        extensions = _normalize_ext_list(ext_text)

        path_contains = (self.path_field.text or "").strip()
        if not path_contains:
            path_contains = None

        detail_idx = self.seg_detail.selected_index
        detail = ["overview", "summary", "max"][detail_idx]

        mode_idx = self.seg_mode.selected_index
        mode = ["gesamt", "pro-repo"][mode_idx]

        max_bytes = self._parse_max_bytes()
        plan_only = bool(self.plan_switch.value)

        summaries = []
        for name in selected:
            root = self.hub / name
            if not root.is_dir():
                continue
            summary = scan_repo(root, extensions or None, path_contains, max_bytes)
            summary["name"] = name
            summaries.append(summary)

        if not summaries:
            if console:
                console.alert(
                    "wc-merger",
                    "Keine gültigen Repos gefunden.",
                    "OK",
                    hide_cancel_button=True,
                )
            return

        merges_dir = get_merges_dir(self.hub)  # -> <wc-hub>/merges
        out_paths = write_reports(
            merges_dir,
            self.hub,
            summaries,
            detail,
            mode,
            max_bytes,
            plan_only,
        )

        if not out_paths:
            if console:
                console.alert("wc-merger", "Kein Bericht erzeugt.", "OK", hide_cancel_button=True)
            else:
                print("Kein Bericht erzeugt.")
            return

        main_report = out_paths[0]

        # Bericht direkt im Pythonista-Editor öffnen
        if editor is not None:
            try:
                editor.open_file(str(main_report))
            except Exception:
                print("Bericht:", main_report)
        else:
            print("Bericht:", main_report)

        # dezentes Feedback
        if console is not None:
            try:
                console.hud_alert("wc-merger: OK")
            except Exception:
                console.alert("wc-merger", str(main_report), "OK", hide_cancel_button=True)
        else:
            print("wc-merger: OK")


# ---------------------------------------------------------------------------
# Einstieg
# ---------------------------------------------------------------------------

def main_ui() -> None:
    script_path = Path(__file__).resolve()
    hub = detect_hub_dir(script_path)
    ui_obj = MergerUI(hub)
    # wie alte Version: Sheet, nicht Fullscreen
    ui_obj.view.present("sheet")


if __name__ == "__main__":
    if ui is None:
        print("Pythonista ui-Modul nicht verfügbar – UI-Modus benötigt Pythonista.")
        sys.exit(1)
    main_ui()
