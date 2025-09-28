#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ordnermerger_batch – Batch-here Merger für macOS/Windows/Linux.

Funktion:
- scannt einen Arbeitsordner (Default: CWD) nach Unterordnern (ohne merge/, .*, _*)
- erzeugt je Unterordner einen Markdown-Merge: merge/<name>_merge_yymmddhhmm.md
- löscht den Quellordner nach erfolgreichem Merge
- behält nur die letzten N Merges (Default 3)

Beispiele:
  python ordnermerger_batch.py --yes
  python ordnermerger_batch.py --pick --retain 5
  python ordnermerger_batch.py --include-dirs "proj*,notes-*" --dry-run
"""

from __future__ import annotations
import os, sys, argparse, shutil, hashlib
from pathlib import Path
from datetime import datetime, timezone

try:
    import tkinter as _tk   # nur für optionalen Picker
    from tkinter import filedialog as _fd
    _HAS_TK = True
except Exception:
    _HAS_TK = False

ENC = "utf-8"
DEFAULT_RETAIN = 3
DEFAULT_NAME_PATTERN = "{name}_merge_%y%m%d%H%M"
BINARY_EXTS = {
    ".png",".jpg",".jpeg",".gif",".webp",".avif",".bmp",".ico",
    ".pdf",".mp3",".wav",".flac",".ogg",".m4a",".aac",
    ".mp4",".mkv",".mov",".avi",
    ".zip",".gz",".bz2",".xz",".7z",".rar",".zst",
    ".ttf",".otf",".woff",".woff2",
    ".so",".dylib",".dll",".exe",
    ".db",".sqlite",".sqlite3",".realm",".mdb",".pack",".idx",
}
LANG_MAP = {
    'py':'python','js':'javascript','ts':'typescript','html':'html','css':'css','scss':'scss','sass':'sass',
    'json':'json','xml':'xml','yaml':'yaml','yml':'yaml','md':'markdown','sh':'bash','sql':'sql','php':'php',
    'cpp':'cpp','c':'c','java':'java','cs':'csharp','go':'go','rs':'rust','rb':'ruby','swift':'swift',
    'kt':'kotlin','svelte':'svelte','toml':'toml','ini':'ini','cfg':'ini','txt':''
}

def human(n:int)->str:
    u=["B","KB","MB","GB","TB"]; f=float(n); i=0
    while f>=1024 and i<len(u)-1: f/=1024; i+=1
    return f"{f:.1f} {u[i]}"

def is_text_file(p: Path) -> bool:
    if p.suffix.lower() in BINARY_EXTS: return False
    try:
        with p.open("rb") as fh: fh.read(4096).decode(ENC)
        return True
    except Exception:
        return False

def md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as fh:
        for ch in iter(lambda: fh.read(1<<16), b""): h.update(ch)
    return h.hexdigest()

def lang_for(p: Path)->str:
    return LANG_MAP.get(p.suffix.lstrip(".").lower(), "")

def write_tree(out, root: Path, max_depth=None):
    def rec(cur: Path, depth: int):
        if max_depth is not None and depth>max_depth: return
        try: entries=sorted(cur.iterdir(), key=lambda x:(not x.is_dir(), x.name.lower()))
        except Exception: return
        for e in entries:
            rel=e.relative_to(root)
            mark="📁" if e.is_dir() else "📄"
            out.write(f"{'  '*depth}- {mark} {rel}\n")
            if e.is_dir(): rec(e, depth+1)
    out.write("```tree\n"); out.write(f"{root}\n"); rec(root,0); out.write("```\n")

def out_path_for(src: Path, target_dir: Path, utc: bool, pattern: str) -> Path:
    now = datetime.now(timezone.utc if utc else None)
    stem = now.strftime(pattern.replace("{name}", src.name))
    return target_dir / f"{stem}.md"

def merge_one_folder(source: Path, out_file: Path, max_depth, max_bytes, dry_run: bool) -> bool:
    included=[]; skipped=[]; total=0
    for dirpath, _, files in os.walk(source):
        d = Path(dirpath)
        for fn in files:
            p=d/fn; rel=p.relative_to(source)
            if not is_text_file(p): skipped.append(f"{rel} (binär)"); continue
            try:
                sz=p.stat().st_size; digest=md5(p)
            except Exception as e:
                skipped.append(f"{rel} (err {e})"); continue
            included.append((p, rel, sz, digest)); total+=sz
    included.sort(key=lambda t: str(t[1]).lower())

    if dry_run:
        print(f"🧪 DRY: {source.name} -> {out_file} | Dateien: {len(included)} | Größe: {human(total)}")
        return True

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding=ENC) as out:
        out.write(f"# Ordner-Merge: {source.name}\n\n")
        out.write(f"**Zeitpunkt:** {datetime.now():%Y-%m-%d %H:%M}\n")
        out.write(f"**Quelle:** `{source.name}`\n")
        out.write(f"**Dateien:** {len(included)}\n")
        out.write(f"**Gesamtgröße:** {human(total)}\n\n")
        out.write("## 📁 Struktur\n\n"); write_tree(out, source, max_depth); out.write("\n")
        out.write("## 📦 Dateien\n\n")

        for p, rel, sz, digest in included:
            out.write(f"### 📄 {rel}\n\n**Größe:** {human(sz)} | **md5:** `{digest}`\n\n```{lang_for(p)}\n")
            try:
                if max_bytes and sz > max_bytes:
                    with p.open("rb") as fh: raw=fh.read(max_bytes)
                    txt=raw.decode(ENC, errors="replace")
                    out.write(txt)
                    if not txt.endswith("\n"): out.write("\n")
                    out.write("```\n\n> ⚠️ Datei gekürzt.\n\n")
                else:
                    txt=p.read_text(encoding=ENC, errors="replace")
                    out.write(txt)
                    if not txt.endswith("\n"): out.write("\n")
                    out.write("```\n\n")
            except Exception as e:
                out.write(f"<<Lesefehler: {e}>>\n```\n\n")

        if skipped:
            out.write("## ⏭️ Übersprungen\n\n")
            for s in skipped: out.write(f"- {s}\n")

    print(f"✅ Merge geschrieben: {out_file} ({human(out_file.stat().st_size)})")
    return True

def retention_clean(merge_dir: Path, keep: int, dry_run: bool):
    files = sorted(merge_dir.glob("*_merge_*.md"), key=lambda p: p.stat().st_mtime)
    if keep < 0: keep = 0
    to_delete = files[:-keep] if keep and len(files)>keep else (files if keep==0 else [])
    if not to_delete:
        print("ℹ️ Retention: nichts zu löschen."); return
    print(f"🧹 Retention: lösche {len(to_delete)} alte Merge(s), behalte {keep}.")
    for f in to_delete:
        if dry_run: print(f"  🧪 DRY: {f}")
        else:
            try: f.unlink(); print(f"  🗑️ {f.name}")
            except Exception as e: print(f"  ⚠️ {f}: {e}")

def pick_folder(start: Path) -> Path | None:
    if not _HAS_TK: return None
    try:
        root = _tk.Tk(); root.withdraw()
        p = _fd.askdirectory(title="Arbeitsordner wählen", initialdir=str(start))
        root.destroy()
        return Path(p) if p else None
    except Exception:
        return None

def parse_args(argv):
    ap = argparse.ArgumentParser(description="ordnermerger_batch – Batch-here Merger")
    ap.add_argument("--workdir", help="Arbeitsordner (Default: aktueller Ordner)")
    ap.add_argument("--pick", action="store_true", help="GUI-Picker für Arbeitsordner")
    ap.add_argument("--retain", type=int, default=DEFAULT_RETAIN, help="Wie viele Merges behalten (Default 3)")
    ap.add_argument("--max-depth", type=int, default=None, help="Baumdarstellung begrenzen (nur Anzeige)")
    ap.add_argument("--max-bytes", type=int, default=None, help="Maximale Bytes pro Datei (Inhalt kappen)")
    ap.add_argument("--utc", action="store_true", help="UTC statt lokale Zeit im Timestamp")
    ap.add_argument("--pattern", default=DEFAULT_NAME_PATTERN, help=f"Namensmuster (strftime) – Default: {DEFAULT_NAME_PATTERN}")
    ap.add_argument("--include-dirs", help="CSV-Globs der zu verarbeitenden Ordner (Whitelist)")
    ap.add_argument("--exclude-dirs", help="CSV-Globs für Ausschlüsse (Blacklist)")
    ap.add_argument("--yes","-y", action="store_true", help="Rückfrage überspringen")
    ap.add_argument("--dry-run","-n", action="store_true", help="Nur anzeigen – nichts schreiben/löschen")
    return ap.parse_args(argv)

def should_take(name: str, inc: list[str], exc: list[str]) -> bool:
    import fnmatch
    if inc and not any(fnmatch.fnmatch(name, p) for p in inc): return False
    if exc and any(fnmatch.fnmatch(name, p) for p in exc): return False
    return True

def main(argv) -> int:
    a = parse_args(argv)

    base = Path(a.workdir).expanduser() if a.workdir else Path.cwd()
    if a.pick:
        p = pick_folder(base)
        if p: base = p

    if not base.is_dir():
        print(f"❌ Kein Ordner: {base}"); return 2

    merge_dir = base / "merge"
    merge_dir.mkdir(parents=True, exist_ok=True)

    inc = [x.strip() for x in (a.include_dirs or "").split(",") if x.strip()]
    exc = [x.strip() for x in (a.exclude_dirs or "").split(",") if x.strip()]
    # Standard-Ausschlüsse
    exc = list(set(exc) | {"merge", ".*", "_*"})

    # Kandidaten sammeln
    candidates=[]
    for c in sorted(base.iterdir(), key=lambda p: p.name.lower()):
        if not c.is_dir(): continue
        if not should_take(c.name, inc, exc): continue
        candidates.append(c)

    if not candidates:
        print("ℹ️ Keine passenden Unterordner gefunden."); return 0

    print("🧺 Batch-here")
    print(f"  Arbeitsordner: {base}")
    print(f"  Ziel:          {merge_dir}")
    print(f"  Ordner:        {', '.join(p.name for p in candidates)}")
    print(f"  Retain:        {a.retain}")
    if not a.yes:
        ok = input("Fortfahren? [Y/n] ").strip().lower()
        if ok in ("n","no"): print("Abgebrochen."); return 1

    successes=[]
    for src in candidates:
        out_file = out_path_for(src, merge_dir, a.utc, a.pattern)
        ok = merge_one_folder(src, out_file, a.max_depth, a.max_bytes, a.dry_run)
        if ok: successes.append((src, out_file))

    # Quelle löschen nur bei Erfolg
    for src, _ in successes:
        if a.dry_run:
            print(f"🧪 DRY: würde Quellordner löschen: {src}")
        else:
            try: shutil.rmtree(src); print(f"🗑️ Quelle gelöscht: {src.name}")
            except Exception as e: print(f"⚠️ Quelle nicht gelöscht ({src.name}): {e}")

    # Retention
    retention_clean(merge_dir, a.retain, a.dry_run)
    print("✅ Fertig.")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
