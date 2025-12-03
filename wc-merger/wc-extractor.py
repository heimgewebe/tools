#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc_extractor – ZIPs im wc-hub entpacken und Repos aktualisieren.

Funktion:
- Suche alle *.zip im Hub (wc-hub).
- Für jede ZIP:
  - Entpacke in temporären Ordner.
  - Wenn es bereits einen Zielordner mit gleichem Namen gibt:
    - Erzeuge einfachen Diff-Bericht (Markdown) alt vs. neu.
    - Lösche den alten Ordner.
  - Benenne Temp-Ordner in Zielordner um.
  - Lösche die ZIP-Datei.

Diff-Berichte:
- Liegen direkt im merges-Verzeichnis des Hubs (wie die Merge-Berichte).
- Dateiname z.B.: <repo>-import-diff-YYMMDD-HHMMSS.md
"""

import sys
import shutil
import zipfile
import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional, List

try:
    import console  # type: ignore
except ImportError:
    console = None  # type: ignore

# Import from core
try:
    from merge_core import (
        detect_hub_dir,
        get_merges_dir,
        get_repo_snapshot,
    )
except ImportError:
    # Fallback if running from root
    sys.path.append(str(Path(__file__).parent))
    from merge_core import (
        detect_hub_dir,
        get_merges_dir,
        get_repo_snapshot,
    )


def detect_hub() -> Path:
    script_path = Path(__file__).resolve()
    return detect_hub_dir(script_path)


def diff_trees(
    old: Path,
    new: Path,
    repo_name: str,
    merges_dir: Path,
) -> Path:
    """
    Vergleicht zwei Repo-Verzeichnisse und schreibt einen Markdown-Diff-Bericht.
    Rückgabe: Pfad zur Diff-Datei.
    """
    # Use scan_repo / get_repo_snapshot via merge_core to respect ignores
    old_map = get_repo_snapshot(old)
    new_map = get_repo_snapshot(new)

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    only_old = sorted(old_keys - new_keys)
    only_new = sorted(new_keys - old_keys)
    common = sorted(old_keys & new_keys)

    changed = []
    for rel in common:
        size_old, md5_old = old_map[rel]
        size_new, md5_new = new_map[rel]
        if size_old != size_new or md5_old != md5_new:
            changed.append((rel, size_old, size_new))

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    fname = "{}-import-diff-{}.md".format(repo_name, ts)
    out_path = merges_dir / fname

    lines = []
    lines.append("# Import-Diff `{}`".format(repo_name))
    lines.append("")
    lines.append("- Zeitpunkt: `{}`".format(now))
    lines.append("- Alter Pfad: `{}`".format(old))
    lines.append("- Neuer Pfad (Temp): `{}`".format(new))
    lines.append("")
    lines.append("- Dateien nur im alten Repo: **{}**".format(len(only_old)))
    lines.append("- Dateien nur im neuen Repo: **{}**".format(len(only_new)))
    lines.append("- Dateien mit geändertem Inhalt: **{}**".format(len(changed)))
    lines.append("")

    if only_old:
        lines.append("## Nur im alten Repo")
        lines.append("")
        for rel in only_old:
            lines.append("- `{}`".format(rel))
        lines.append("")

    if only_new:
        lines.append("## Nur im neuen Repo")
        lines.append("")
        for rel in only_new:
            lines.append("- `{}`".format(rel))
        lines.append("")

    if changed:
        lines.append("## Geänderte Dateien")
        lines.append("")
        lines.append("| Pfad | Größe alt | Größe neu |")
        lines.append("| --- | ---: | ---: |")
        for rel, s_old, s_new in changed:
            lines.append(
                "| `{}` | {} | {} |".format(rel, s_old, s_new)
            )
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def import_zip(zip_path: Path, hub: Path, merges_dir: Path) -> Optional[Path]:
    """
    Entpackt eine einzelne ZIP-Datei in den Hub, behandelt Konflikte,
    schreibt ggf. Diff und ersetzt das alte Repo.

    Rückgabe:
      Pfad zum Diff-Bericht oder None.
    """
    repo_name = zip_path.stem
    target_dir = hub / repo_name
    tmp_dir = hub / ("__extract_tmp_" + repo_name)

    print("Verarbeite ZIP:", zip_path.name, "-> Repo", repo_name)

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    tmp_dir.mkdir(parents=True, exist_ok=True)

    # ZIP entpacken
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp_dir)

    diff_path = None  # type: Optional[Path]

    # Wenn es schon ein Repo mit diesem Namen gibt → Diff + löschen
    if target_dir.exists():
        print("  Zielordner existiert bereits:", target_dir)
        try:
            diff_path = diff_trees(target_dir, tmp_dir, repo_name, merges_dir)
            print("  Diff-Bericht:", diff_path)
        except Exception as e:
            print(f"  Warnung: Fehler beim Diff-Erstellen ({e}). Fahre fort.")

        shutil.rmtree(target_dir)
        print("  Alter Ordner gelöscht:", target_dir)
    else:
        print("  Kein vorhandenes Repo – frischer Import.")

    # Temp-Ordner ins Ziel verschieben
    tmp_dir.rename(target_dir)
    print("  Neuer Repo-Ordner:", target_dir)

    # ZIP nach erfolgreichem Import löschen
    try:
        zip_path.unlink()
        print("  ZIP gelöscht:", zip_path.name)
    except OSError as e:
        print(f"  Warnung: Konnte ZIP nicht löschen ({e})")
    print("")

    return diff_path


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="wc-extractor: Import ZIPs to hub.")
    parser.add_argument("--hub", help="Hub directory override.")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    hub = detect_hub_dir(script_path, args.hub)

    if not hub.exists():
         print(f"Hub directory not found: {hub}")
         return 1

    merges_dir = get_merges_dir(hub)

    print("wc_extractor – Hub:", hub)
    zips = sorted(hub.glob("*.zip"))

    if not zips:
        msg = "Keine ZIP-Dateien im Hub gefunden."
        print(msg)
        if console:
            console.alert("wc_extractor", msg, "OK", hide_cancel_button=True)
        return 0

    diff_paths = []

    for zp in zips:
        try:
            diff = import_zip(zp, hub, merges_dir)
            if diff is not None:
                diff_paths.append(diff)
        except Exception as e:
            print("Fehler bei {}: {}".format(zp, e), file=sys.stderr)

    summary_lines = []
    summary_lines.append("Import fertig.")
    summary_lines.append("Hub: {}".format(hub))
    if diff_paths:
        summary_lines.append(
            "Diff-Berichte ({}):".format(len(diff_paths))
        )
        for p in diff_paths:
            summary_lines.append("  - {}".format(p))
    else:
        summary_lines.append("Keine Diff-Berichte erzeugt.")

    summary = "\n".join(summary_lines)
    print(summary)

    if console:
        console.alert("wc_extractor", summary, "OK", hide_cancel_button=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
