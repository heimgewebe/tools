#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ordnermerger — Ordner zu Markdown zusammenführen (non-destructive by default)

MODI:
--selected <PATH>: (Standard) Verarbeitet den/die angegebenen Ordner. Mehrfach nutzbar.
--here:            Verarbeitet den aktuellen Ordner (PWD).
--batch:           Verarbeitet alle Unterordner im Arbeitsverzeichnis (--workdir, default PWD).

OPTIONEN:
--delete:          Löscht Quellordner nach erfolgreichem Merge (destruktiv!).
--retain <N>:      Behält nur die N neuesten Merges im Zielordner.
--yes, -y:         Überspringt die Sicherheitsabfrage bei --delete.
--utc:             Verwendet UTC im Zeitstempel des Dateinamens.
--pattern <P>:     Format für den Dateinamen (default: "{name}_merge_%y%m%d%H%M").

ZIELORDNER:
Der Zielordner "merges" wird standardmäßig neben der Skriptdatei angelegt.
Dies kann via Environment-Variable ORDNERMERGER_HOME angepasst werden.
"""

from __future__ import annotations
import os, sys, shutil
from pathlib import Path
from datetime import datetime, timezone
from merger_lib import human, is_text, md5, lang

ENC = "utf-8"
DEFAULT_NAME_PATTERN = "{name}_merge_%y%m%d%H%M"
FORBIDDEN_DIR_NAMES = {"merges", ".git", ".cache", ".venv", "__pycache__"}

def _script_home() -> Path:
    h = os.environ.get("ORDNERMERGER_HOME")
    if h: return Path(h).expanduser().resolve()
    return Path(__file__).resolve().parent

def _should_skip_dir(entry: Path, merge_dir: Path | None) -> bool:
    name = entry.name
    if name in FORBIDDEN_DIR_NAMES or name.startswith(".") or name.startswith("_"):
        return True
    if merge_dir is not None:
        try:
            if entry.resolve() == merge_dir.resolve():
                return True
        except Exception:
            return False
    return False

def _tree(out, root: Path, merge_dir: Path | None):
    def rec(cur: Path, depth:int):
        try: entries=sorted(cur.iterdir(), key=lambda x:(not x.is_dir(), x.name.lower()))
        except Exception: return
        for e in entries:
            if e.is_dir() and _should_skip_dir(e, merge_dir):
                continue
            rel=e.relative_to(root); mark="📁" if e.is_dir() else "📄"
            out.write(f"{'  '*depth}- {mark} {rel}\n")
            if e.is_dir(): rec(e, depth+1)
    out.write("```tree\n"); out.write(f"{root}\n"); rec(root,0); out.write("```\n")

def _out_path(src: Path, merge_dir: Path, utc: bool, pattern: str) -> Path:
    now = datetime.now(timezone.utc if utc else None)
    stem = now.strftime(pattern.replace("{name}", src.name))
    return merge_dir / f"{stem}.md"

def merge_folder(src: Path, out_file: Path):
    included=[]; skipped=[]; total=0
    merge_dir = out_file.parent.resolve()
    for dirpath, dirnames, files in os.walk(src):
        if dirnames:
            cur = Path(dirpath)
            dirnames[:] = [d for d in dirnames if not _should_skip_dir(cur / d, merge_dir)]
        for fn in files:
            p = Path(dirpath)/fn; rel=p.relative_to(src)
            if not is_text(p): skipped.append(f"{rel} (binär)"); continue
            try: sz=p.stat().st_size; dig=md5(p)
            except Exception as e: skipped.append(f"{rel} (err {e})"); continue
            included.append((p, rel, sz, dig)); total += sz
    included.sort(key=lambda t: str(t[1]).lower())

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding=ENC) as out:
        out.write(f"# Ordner-Merge: {src.name}\n\n")
        out.write(f"**Zeitpunkt:** {datetime.now():%Y-%m-%d %H:%M}\n")
        out.write(f"**Quelle:** `{src}`\n")
        out.write(f"**Dateien:** {len(included)}\n")
        out.write(f"**Gesamtgröße:** {human(total)}\n\n")
        out.write("## 📁 Struktur\n\n"); _tree(out, src, merge_dir); out.write("\n")
        out.write("## 📦 Dateien\n\n")
        for p, rel, sz, dig in included:
            out.write(f"### 📄 {rel}\n\n**Größe:** {human(sz)} | **md5:** `{dig}`\n\n```{lang(p)}\n")
            try: txt=p.read_text(encoding=ENC, errors="replace")
            except Exception as e: txt=f"<<Lesefehler: {e}>>"
            out.write(txt + ("\n" if not txt.endswith("\n") else ""))
            out.write("```\n\n")
        if skipped:
            out.write("## ⏭️ Übersprungen\n\n")
            for s in skipped: out.write(f"- {s}\n")

def retention_clean(merge_dir: Path, keep: int):
    """Behält nur die 'keep' neuesten Merges im Zielordner."""
    if keep < 0: keep = 0
    try:
        files = sorted(merge_dir.glob("*_merge_*.md"), key=lambda p: p.stat().st_mtime)
    except Exception as e:
        print(f"⚠️ Fehler beim Lesen des Merge-Verzeichnisses: {e}")
        return

    to_delete = files[:-keep] if keep > 0 and len(files) > keep else (files if keep == 0 else [])
    if not to_delete:
        print("ℹ️ Retention: Nichts zu löschen.")
        return

    print(f"🧹 Retention: Lösche {len(to_delete)} alte(n) Merge(s), behalte die neuesten {keep}.")
    for f in to_delete:
        try:
            f.unlink()
            print(f"  🗑️ Gelöscht: {f.name}")
        except Exception as e:
            print(f"  ⚠️ Fehler beim Löschen von {f.name}: {e}")

def parse_args(argv):
    import argparse
    ap = argparse.ArgumentParser(description="ordnermerger — Ordner zu Markdown zusammenführen")
    ap.add_argument("--selected", action="append", help="Einzelner Ordnerpfad; Option mehrfach nutzbar")
    ap.add_argument("--here", action="store_true", help="Aktuellen Ordner (PWD) als Quelle nehmen")
    ap.add_argument("--batch", action="store_true", help="Alle Unterordner im Arbeitsverzeichnis verarbeiten")
    ap.add_argument("--workdir", help="Arbeitsverzeichnis für --batch (Default: PWD)")
    ap.add_argument("--delete", action="store_true", help="Quellordner nach erfolgreichem Merge löschen")
    ap.add_argument("--retain", type=int, help="Nur die N neuesten Merges behalten, ältere löschen")
    ap.add_argument("-y", "--yes", action="store_true", help="Rückfragen überspringen (z.B. bei --delete)")
    ap.add_argument("--utc", action="store_true", help="UTC statt lokale Zeit im Dateinamen verwenden")
    ap.add_argument("--pattern", default=DEFAULT_NAME_PATTERN, help=f"Namensmuster für Zieldatei (Default: {DEFAULT_NAME_PATTERN})")
    return ap.parse_args(argv)

def main(argv:list[str])->int:
    args = parse_args(argv)

    home = _script_home()
    merge_dir = home / "merges"
    merge_dir.mkdir(parents=True, exist_ok=True)

    sources: list[Path] = []
    if args.batch:
        workdir = Path(args.workdir).expanduser() if args.workdir else Path.cwd()
        print(f"BATCH-Modus im Verzeichnis: {workdir}")
        for c in sorted(workdir.iterdir()):
            if not c.is_dir(): continue
            if _should_skip_dir(c, merge_dir): continue
            sources.append(c)
    elif args.selected:
        sources = [Path(s).expanduser() for s in args.selected]
    else: # Default is --here
        sources = [Path.cwd()]

    if not sources:
        print("ℹ️ Keine passenden Quellordner gefunden.")
        return 0

    if args.delete and not args.yes:
        print("\nWARNUNG: Die Option --delete löscht die Quellordner nach dem Merge.")
        print(f"Betroffene Ordner: {', '.join(p.name for p in sources)}")
        ok = input("Möchten Sie fortfahren? [y/N] ").strip().lower()
        if ok not in ("y", "yes"):
            print("Abgebrochen.")
            return 1

    successful_merges: list[Path] = []
    for src in sources:
        src_res = src.resolve()
        if not src_res.is_dir():
            print(f"⚠️ Überspringe (kein Ordner): {src}")
            continue
        if src_res == home or src_res == merge_dir:
            print(f"⛔ Überspringe geschützte Quelle: {src} (App-Home oder Merge-Ziel)")
            continue

        try:
            out = _out_path(src, merge_dir, args.utc, args.pattern)
            merge_folder(src, out)
            print(f"✅ {src.name} → {out}")
            successful_merges.append(src)
        except Exception as e:
            print(f"❌ Fehler beim Mergen von {src.name}: {e}")

    if args.delete:
        for src in successful_merges:
            try:
                shutil.rmtree(src)
                print(f"🗑️ Quelle gelöscht: {src.name}")
            except Exception as e:
                print(f"⚠️ Quelle konnte nicht gelöscht werden ({src.name}): {e}")

    if args.retain is not None:
        retention_clean(merge_dir, args.retain)

    print(f"📂 Ziel: {merge_dir}")
    return 0 if successful_merges else 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
