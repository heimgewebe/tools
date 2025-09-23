#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ordnermerger – interaktiver Quell-/Zielauswahl, ohne Auto-Cleanup

Ergebnisdatei:
  [Quellordnername]_merge_yymmddhhmm.md
"""

from __future__ import annotations
import os, sys, argparse, hashlib
from pathlib import Path
from datetime import datetime

# ---------- Defaults ----------
DEFAULT_ENCODING = os.environ.get("REPOENC", "utf-8")

BINARY_EXTS = {".png",".jpg",".jpeg",".gif",".webp",".avif",".bmp",".ico",
    ".pdf",".mp3",".wav",".flac",".ogg",".m4a",".aac",
    ".mp4",".mkv",".mov",".avi",
    ".zip",".gz",".bz2",".xz",".7z",".rar",".zst",
    ".ttf",".otf",".woff",".woff2",
    ".so",".dylib",".dll",".exe",
    ".db",".sqlite",".sqlite3",".realm",".mdb",".pack",".idx"}

LANG_MAP = {
    'py':'python','js':'javascript','ts':'typescript','html':'html','css':'css',
    'json':'json','xml':'xml','yaml':'yaml','yml':'yaml','md':'markdown','sh':'bash',
    'sql':'sql','php':'php','cpp':'cpp','c':'c','java':'java','cs':'csharp','go':'go',
    'rs':'rust','rb':'ruby','swift':'swift','kt':'kotlin','svelte':'svelte'
}

# ---------- Utils ----------
def human(n: int) -> str:
    u=["B","KB","MB","GB","TB"]; f=float(n); i=0
    while f>=1024 and i<len(u)-1: f/=1024; i+=1
    return f"{f:.1f} {u[i]}"

def is_text_file(p: Path) -> bool:
    if p.suffix.lower() in BINARY_EXTS: return False
    try:
        with p.open("rb") as fh: fh.read(2048).decode(DEFAULT_ENCODING)
        return True
    except Exception: return False

def lang_for(p: Path) -> str:
    return LANG_MAP.get(p.suffix.lstrip(".").lower(), "")

def file_md5(p: Path) -> str:
    h=hashlib.md5()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1<<16), b""): h.update(chunk)
    return h.hexdigest()

def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True); return p

# ---------- Merge ----------
def do_merge(source: Path, out_file: Path, encoding=DEFAULT_ENCODING):
    included, skipped, total = [], [], 0
    for dirpath, _, files in os.walk(source):
        for fn in files:
            p = Path(dirpath)/fn
            rel = p.relative_to(source)
            if not is_text_file(p):
                skipped.append(f"{rel} (binär)"); continue
            try: sz = p.stat().st_size
            except Exception as e: skipped.append(f"{rel} (stat error: {e})"); continue
            included.append((p, rel, sz, file_md5(p)))
            total += sz

    included.sort(key=lambda t: str(t[1]).lower())
    ensure_dir(out_file.parent)

    with out_file.open("w", encoding=encoding) as out:
        out.write(f"# Ordner-Merge: {source.name}\n\n")
        out.write(f"**Zeitpunkt:** {datetime.now():%Y-%m-%d %H:%M}\n")
        out.write(f"**Quelle:** `{source}`\n")
        out.write(f"**Dateien (inkludiert):** {len(included)}\n")
        out.write(f"**Gesamtgröße:** {human(total)}\n\n")

        for p, rel, sz, h in included:
            out.write(f"## 📄 {rel}\n\n**Größe:** {human(sz)} | **md5:** `{h}`\n\n```{lang_for(p)}\n")
            try: txt = p.read_text(encoding=encoding, errors="replace")
            except Exception as e: txt = f"<<Lesefehler: {e}>>"
            out.write(txt + ("\n" if not txt.endswith("\n") else ""))
            out.write("```\n\n")

        if skipped:
            out.write("## ⏭️ Übersprungen\n\n")
            for s in skipped: out.write(f"- {s}\n")

    print(f"✅ Merge geschrieben: {out_file} ({human(out_file.stat().st_size)})")

# ---------- CLI ----------
def parse_args(argv):
    ap = argparse.ArgumentParser(description="ordnermerger – Quelle/Ziel wählen, ohne Auto-Cleanup")
    ap.add_argument("--source","-s", help="Quellordner")
    ap.add_argument("--target","-t", help="Zielordner (Default: ./merge)")
    ap.add_argument("--encoding", default=DEFAULT_ENCODING, help="Datei-Encoding")
    return ap.parse_args(argv)

def ask_path(prompt: str, default: Path) -> Path:
    try: s = input(f"{prompt} [{default}]: ").strip()
    except EOFError: s=""
    return Path(s or default).expanduser()

def main(argv) -> int:
    a = parse_args(argv)
    src = Path(a.source).expanduser() if a.source else ask_path("Quellordner", Path.cwd())
    if not src.is_dir(): print(f"❌ Kein Ordner: {src}"); return 2

    tgt_dir = Path(a.target).expanduser() if a.target else (Path.cwd()/ "merge")
    ensure_dir(tgt_dir)
    ts = datetime.now().strftime("%y%m%d%H%M")
    out_path = tgt_dir / f"{src.name}_merge_{ts}.md"

    do_merge(src, out_path, encoding=a.encoding)
    return 0

if __name__=="__main__":
    sys.exit(main(sys.argv[1:]))