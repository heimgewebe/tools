#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc_extractor – ZIPs im wc-hub entpacken und Repos aktualisieren.
Verwendet merge_core.

Funktion:
- Suche alle *.zip im Hub (wc-hub).
- Für jede ZIP:
  - Entpacke in temporären Ordner.
  - Wenn es bereits einen Zielordner mit gleichem Namen gibt:
    - Erzeuge einfachen Diff-Bericht (Markdown) alt vs. neu.
    - Lösche den alten Ordner.
  - Benenne Temp-Ordner in Zielordner um.
  - Lösche die ZIP-Datei.

Diff-Berichte:
- Liegen direkt im merges-Verzeichnis des Hubs.
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

    Neu: „Manifest-Anklang“
      - kleine Tabelle mit Pfad, Status, Kategorie, Größen und MD5-Änderung
      - Kategorien stammen aus merge_core.classify_file_v2 via get_repo_snapshot

    Rückgabe:
      Pfad zur Diff-Datei.
    """
    # Snapshot-Maps:
    #   rel_path -> (size, md5, category)
    old_map = get_repo_snapshot(old)
    new_map = get_repo_snapshot(new)

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    only_old = sorted(old_keys - new_keys)
    only_new = sorted(new_keys - old_keys)
    common = sorted(old_keys & new_keys)

    # Für gemeinsame Dateien merken wir uns auch MD5 und Kategorien
    changed = []
    for rel in common:
        size_old, md5_old, cat_old = old_map[rel]
        size_new, md5_new, cat_new = new_map[rel]
        if size_old != size_new or md5_old != md5_new:
            changed.append((rel, size_old, size_new, md5_old, md5_new, cat_old, cat_new))

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    fname = "{}-import-diff-{}.md".format(repo_name, ts)
    out_path = merges_dir / fname

    lines: List[str] = []
    lines.append("# Import-Diff `{}`".format(repo_name))
    lines.append("")
    lines.append("- Zeitpunkt: `{}`".format(now))
    lines.append("- Alter Pfad: `{}`".format(old))
    lines.append("- Neuer Pfad (Temp): `{}`".format(new))
    lines.append("")
    lines.append("- Dateien nur im alten Repo: **{}**".format(len(only_old)))
    lines.append("- Dateien nur im neuen Repo: **{}**".format(len(only_new)))
    lines.append("- Dateien mit geändertem Inhalt: **{}**".format(len(changed)))
    lines.append("")

    # Manifest-artige Tabelle: ein Eintrag pro betroffener Datei
    any_rows = bool(only_old or only_new or changed)
    if any_rows:
        lines.append("## Dateiliste (Manifest-Stil)")
        lines.append("")
        lines.append(
            "| Pfad | Status | Kategorie | Größe alt | Größe neu | Δ Größe | MD5 geändert |"
        )
        lines.append("| --- | --- | --- | ---: | ---: | ---: | --- |")

        # Entfernte Dateien
        for rel in only_old:
            size_old, md5_old, cat_old = old_map[rel]
            lines.append(
                "| `{path}` | removed | `{cat}` | {s_old} | - | -{delta} | n/a |".format(
                    path=rel,
                    cat=cat_old,
                    s_old=size_old,
                    delta=size_old,
                )
            )

        # Neue Dateien
        for rel in only_new:
            size_new, md5_new, cat_new = new_map[rel]
            lines.append(
                "| `{path}` | added | `{cat}` | - | {s_new} | +{delta} | n/a |".format(
                    path=rel,
                    cat=cat_new,
                    s_new=size_new,
                    delta=size_new,
                )
            )

        # Geänderte Dateien
        for (
            rel,
            s_old,
            s_new,
            md5_old,
            md5_new,
            cat_old,
            cat_new,
        ) in changed:
            delta = s_new - s_old
            md5_changed = "ja" if md5_old != md5_new else "nein"
            # Falls sich die Kategorie ändert (selten), neue Kategorie anzeigen
            cat_display = cat_new or cat_old
            lines.append(
                "| `{path}` | changed | `{cat}` | {s_old} | {s_new} | {delta:+d} | {md5_flag} |".format(
                    path=rel,
                    cat=cat_display,
                    s_old=s_old,
                    s_new=s_new,
                    delta=delta,
                    md5_flag=md5_changed,
                )
            )

        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def import_zip(zip_path: Path, hub: Path, merges_dir: Path) -> Optional[Path]:
    """
    Entpackt eine einzelne ZIP-Datei in den Hub, behandelt Konflikte,
    schreibt ggf. Diff und ersetzt das alte Repo.

    Rückgabe:
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

    # Wenn es schon ein Repo mit diesem Namen gibt -> Diff + löschen
    if target_dir.exists():
        print("  Zielordner existiert bereits:", target_dir)
        try:
            diff_path = diff_trees(target_dir, tmp_dir, repo_name, merges_dir)
            print("  Diff-Bericht:", diff_path)
        except Exception as e:
            print(f"  Warnung: Fehler beim Diff-Erstellen ({e}). Fahre fort.")

        shutil.rmtree(target_dir)
        print("  Alter Ordner gelöscht:", target_dir)
    else:
        print("  Kein vorhandenes Repo – frischer Import.")

    # Temp-Ordner ins Ziel verschieben
    tmp_dir.rename(target_dir)
    print("  Neuer Repo-Ordner:", target_dir)

    # ZIP nach erfolgreichem Import löschen
    try:
        zip_path.unlink()
        print("  ZIP gelöscht:", zip_path.name)
    except OSError as e:
        print(f"  Warnung: Konnte ZIP nicht löschen ({e})")
    print("")

    return diff_path


def import_zip_wrapper(zip_path: Path, hub: Path, merges_dir: Path) -> Optional[Path]:
    """Wraps import_zip with finally cleanup."""
    try:
        return import_zip(zip_path, hub, merges_dir)
    except Exception:
        raise
    finally:
        if zip_path.exists():
            try:
                zip_path.unlink()
                print(f"  Cleanup: ZIP gelöscht ({zip_path.name})")
            except OSError:
                pass


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="wc-extractor-v2: Import ZIPs to hub.")
    parser.add_argument("--hub", help="Hub directory override.")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    hub = detect_hub_dir(script_path, args.hub)

    if not hub.exists():
         print(f"Hub directory not found: {hub}")
         return 1

    merges_dir = get_merges_dir(hub)

    print("wc_extractor-v2 – Hub:", hub)
    zips = sorted(hub.glob("*.zip"))

    if not zips:
        msg = "Keine ZIP-Dateien im Hub gefunden."
        print(msg)
        if console:
            console.alert("wc_extractor-v2", msg, "OK", hide_cancel_button=True)
        return 0

    diff_paths = []

    for zp in zips:
        try:
            diff = import_zip_wrapper(zp, hub, merges_dir)
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
        console.alert("wc_extractor-v2", summary, "OK", hide_cancel_button=True)

    return 0



# ---------------------------------------------------------------------------
# Diff-Parser (Prototyp)
# ---------------------------------------------------------------------------

def parse_import_diff_table(text):
    """
    Parst die „Dateiliste (Manifest-Stil)“-Tabelle aus einem Import-Diff.

    Rückgabe:
      Liste von Dicts mit Schlüsseln:
        - path: str
        - status: "added" | "removed" | "changed"
        - category: str
        - size_old: Optional[int]
        - size_new: Optional[int]
        - delta: Optional[int]
        - md5_changed: Optional[bool]  # True/False/nicht verfügbar

    Wenn die Tabelle nicht gefunden wird, wird eine leere Liste zurückgegeben.
    """
    lines = text.splitlines()

    # Header-Zeile der Tabelle finden
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| Pfad | Status | Kategorie |"):
            header_idx = i
            break

    if header_idx is None or header_idx + 2 >= len(lines):
        return []

    # Nach der Headerzeile kommt die Separatorzeile, danach die Datenzeilen
    rows = []
    i = header_idx + 2
    while i < len(lines):
        line = lines[i]
        if not line.strip().startswith("|"):
            break
        # Spalten extrahieren: | col1 | col2 | ... |
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 7:
            i += 1
            continue

        path_raw, status, category_raw, s_old_raw, s_new_raw, delta_raw, md5_flag_raw = parts[:7]

        def _strip_ticks(s):
            s = s.strip()
            if s.startswith("`") and s.endswith("`") and len(s) >= 2:
                return s[1:-1]
            return s

        path = _strip_ticks(path_raw)
        category = _strip_ticks(category_raw)

        def _parse_int_or_none(s):
            s = s.strip()
            if s == "-" or not s:
                return None
            try:
                return int(s.replace("+", ""))
            except ValueError:
                return None

        size_old = _parse_int_or_none(s_old_raw)
        size_new = _parse_int_or_none(s_new_raw)
        delta = _parse_int_or_none(delta_raw)

        md5_flag = md5_flag_raw.strip().lower()
        if md5_flag in ("ja", "yes", "true"):
            md5_changed = True
        elif md5_flag in ("nein", "no", "false"):
            md5_changed = False
        else:
            md5_changed = None

        rows.append(
            {
                "path": path,
                "status": status.strip(),
                "category": category,
                "size_old": size_old,
                "size_new": size_new,
                "delta": delta,
                "md5_changed": md5_changed,
            }
        )
        i += 1

    return rows


# ---------------------------------------------------------------------------
# Delta-Merge auf Basis des Import-Diffs
# ---------------------------------------------------------------------------

def build_delta_merge_report(
    repo_root: Path,
    repo_name: str,
    diff_rows,
    merges_dir: Path,
    profile: str = "delta-full",
) -> Path:
    """
    Erzeugt einen WC-Merger-kompatiblen Delta-Report auf Basis eines
    Import-Diffs (parse_import_diff_table).

    Standardverhalten:
      - Status "changed" und "added" → mit Inhalt
      - Status "removed"             → nur im Manifest / Summary
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    ts = now.strftime("%y%m%d-%H%M")
    fname = f"{repo_name}_{profile}_delta_{ts}_merge.md"
    out_path = merges_dir / fname

    rows = list(diff_rows or [])
    changed = [r for r in rows if r.get("status") == "changed"]
    added = [r for r in rows if r.get("status") == "added"]
    removed = [r for r in rows if r.get("status") == "removed"]

    lines = []
    lines.append("# WC-Merger Delta Report (v2.x)")
    lines.append("")
    lines.append("## Source & Profile")
    lines.append(f"- **Source:** {repo_name}")
    lines.append(f"- **Profile:** `{profile}`")
    lines.append(f"- **Generated At:** {now.isoformat()} (UTC)")
    lines.append("- **Spec-Version:** 2.3")
    lines.append(
        f"- **Declared Purpose:** Delta-Merge – changed+added files for `{repo_name}`"
    )
    lines.append(f"- **Scope:** single repo `{repo_name}`")
    lines.append("")

    lines.append("## Change Summary")
    lines.append("")
    lines.append(f"- Changed files: **{len(changed)}**")
    lines.append(f"- Added files: **{len(added)}**")
    lines.append(f"- Removed files: **{len(removed)}**")
    lines.append("")

    if rows:
        lines.append("## File Manifest (Delta)")
        lines.append("")
        lines.append(
            "| Pfad | Status | Kategorie | Größe alt | Größe neu | Δ Größe | MD5 geändert |"
        )
        lines.append("| --- | --- | --- | ---: | ---: | ---: | --- |")

        def _fmt_int(v):
            if v is None:
                return "-"
            return str(v)

        for row in rows:
            path = row.get("path", "")
            status = row.get("status", "")
            category = row.get("category") or "-"
            size_old = row.get("size_old")
            size_new = row.get("size_new")
            delta = row.get("delta")
            md5_flag = row.get("md5_changed")
            if md5_flag is True:
                md5_text = "ja"
            elif md5_flag is False:
                md5_text = "nein"
            else:
                md5_text = "n/a"

            lines.append(
                f"| `{path}` | {status} | `{category}` | "
                f"{_fmt_int(size_old)} | {_fmt_int(size_new)} | {_fmt_int(delta)} | {md5_text} |"
            )

        lines.append("")

    def _anchor_for(rel_path: str) -> str:
        return "delta-" + rel_path.replace("/", "-").replace(".", "-")

    lines.append("## Content – changed & added")
    lines.append("")

    if not (changed or added):
        lines.append("_Keine geänderten oder neuen Dateien im Snapshot._")
    else:
        interesting = sorted(changed + added, key=lambda r: r.get("path", ""))
        for row in interesting:
            rel = row.get("path", "")
            status = row.get("status", "")
            category = row.get("category") or "-"
            size_old = row.get("size_old")
            size_new = row.get("size_new")
            delta = row.get("delta")
            md5_flag = row.get("md5_changed")
            if md5_flag is True:
                md5_text = "ja"
            elif md5_flag is False:
                md5_text = "nein"
            else:
                md5_text = "n/a"

            lines.append(f"<a id=\"file-{_anchor_for(rel)}\"></a>")
            lines.append(f"### `{rel}`")
            lines.append(f"- Status: `{status}`")
            lines.append(f"- Kategorie: `{category}`")
            if size_old is not None:
                lines.append(f"- Größe alt: {size_old}")
            if size_new is not None:
                lines.append(f"- Größe neu: {size_new}")
            if delta is not None:
                try:
                    lines.append(f"- Δ Größe: {int(delta):+d}")
                except Exception:
                    lines.append(f"- Δ Größe: {delta}")
            lines.append(f"- MD5 geändert: {md5_text}")
            lines.append("")

            target = (repo_root / rel)
            if status in ("changed", "added") and target.is_file():
                ext = target.suffix.lower()
                lang_map = {
                    ".py": "python",
                    ".rs": "rust",
                    ".ts": "ts",
                    ".tsx": "tsx",
                    ".js": "js",
                    ".json": "json",
                    ".toml": "toml",
                    ".yml": "yaml",
                    ".yaml": "yaml",
                }
                lang = lang_map.get(ext, "")
                fence = f"```{lang}".rstrip()
                lines.append(fence)
                try:
                    content = target.read_text(encoding="utf-8")
                except Exception:
                    try:
                        content = target.read_text(errors="replace")
                    except Exception:
                        content = "[Fehler beim Lesen der Datei]"
                lines.append(content)
                lines.append("```")
            else:
                lines.append("_Inhalt nicht verfügbar (Datei fehlt im Repo)._")

            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def create_delta_merge_from_diff(
    diff_path: Path,
    repo_root: Path,
    merges_dir: Path,
    profile: str = "delta-full",
) -> Path:
    """
    Komfort-Helfer:
      - liest einen vorhandenen Import-Diff
      - parst die Manifest-Tabelle
      - erzeugt einen Delta-Merge-Report

    Rückgabe:
      Pfad zur erzeugten Delta-Merge-Datei.
    """
    text = diff_path.read_text(encoding="utf-8")
    rows = parse_import_diff_table(text)
    return build_delta_merge_report(repo_root, repo_root.name, rows, merges_dir, profile=profile)


if __name__ == "__main__":
    sys.exit(main())
