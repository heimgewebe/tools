# -*- coding: utf-8 -*-
"""
merger_lib — Gemeinsame Hilfsfunktionen für ordnermerger Skripte.
"""

from __future__ import annotations
import hashlib
from pathlib import Path
from typing import TextIO

ENC = "utf-8"

# Robuster Satz von binären Erweiterungen
BINARY_EXTS = {
    # Bilder
    ".png",".jpg",".jpeg",".gif",".bmp",".ico",".webp",".heic",".heif",".psd",".ai",
    # Audio & Video
    ".mp3",".wav",".flac",".ogg",".m4a",".aac",".mp4",".mkv",".mov",".avi",".wmv",".flv",".webm",
    # Archive
    ".zip",".rar",".7z",".tar",".gz",".bz2",".xz",".tgz",
    # Schriften
    ".ttf",".otf",".woff",".woff2",
    # Dokumente
    ".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".pages",".numbers",".key",
    # Kompilierte/Binärdateien
    ".exe",".dll",".so",".dylib",".bin",".class",".o",".a",
    # Datenbanken
    ".db",".sqlite",".sqlite3",".realm",".mdb",".pack",".idx",
}

# Umfangreiche Sprachzuordnung
LANG_MAP = {
    'py':'python','js':'javascript','ts':'typescript','html':'html','css':'css','scss':'scss','sass':'sass',
    'json':'json','xml':'xml','yaml':'yaml','yml':'yaml','md':'markdown','sh':'bash','bat':'batch',
    'sql':'sql','php':'php','cpp':'cpp','c':'c','java':'java','cs':'csharp','go':'go','rs':'rust',
    'rb':'ruby','swift':'swift','kt':'kotlin','svelte':'svelte','txt':''
}

def human(n:int)->str:
    """Konvertiert Bytes in ein menschenlesbares Format (KB, MB, ...)."""
    u=["B","KB","MB","GB","TB"]; f=float(n); i=0
    while f>=1024 and i<len(u)-1: f/=1024; i+=1
    return f"{f:.2f} {u[i]}"

def is_text(p: Path, sniff_bytes=4096)->bool:
    """
    Prüft, ob eine Datei wahrscheinlich Text ist.
    Kombiniert eine Prüfung der Dateiendung mit einer Inhaltsanalyse (Sniffing).
    """
    if p.suffix.lower() in BINARY_EXTS: return False
    try:
        with p.open("rb") as f:
            chunk = f.read(sniff_bytes)
            if not chunk: return True  # Leere Datei ist Text
            if b"\x00" in chunk: return False # Null-Bytes sind ein starkes Indiz für Binärdaten
            # Versuche, als UTF-8 zu dekodieren, wenn das fehlschlägt, ist es wahrscheinlich kein Text.
            chunk.decode("utf-8")
            return True
    except UnicodeDecodeError:
        return False # Konnte nicht als UTF-8 dekodiert werden
    except Exception:
        return False # Andere Fehler (z.B. Lesefehler)

def md5(p: Path, block_size=65536)->str:
    """Berechnet den MD5-Hash einer Datei."""
    h=hashlib.md5()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()

def lang(p: Path)->str:
    """Gibt die Markdown-Sprachkennung für eine Datei zurück."""
    return LANG_MAP.get(p.suffix.lstrip(".").lower(), "")

def write_tree(out: TextIO, root: Path, max_depth: int|None = None):
    """Schreibt eine Baumdarstellung des Ordners `root` in den Stream `out`."""
    def lines(d: Path, lvl=0):
        if max_depth is not None and lvl >= max_depth: return []
        res=[]
        try:
            items = sorted(d.iterdir(), key=lambda x:(not x.is_dir(), x.name.lower()))
            dirs  = [i for i in items if i.is_dir()]
            files = [i for i in items if i.is_file()]
            for i, sub in enumerate(dirs):
                pref = "└── " if (i==len(dirs)-1 and not files) else "├── "
                res.append("    "*lvl + f"{pref}📁 {sub.name}/")
                res += lines(sub, lvl+1)
            for i, f in enumerate(files):
                pref = "└── " if i==len(files)-1 else "├── "
                try:
                    icon = "📄" if is_text(f) else "🔒"
                    res.append("    "*lvl + f"{pref}{icon} {f.name} ({human(f.stat().st_size)})")
                except Exception:
                    res.append("    "*lvl + f"{pref}📄 {f.name}")
        except PermissionError:
            res.append("    "*lvl + "❌ Zugriff verweigert")
        return res

    out.write("```\n"); out.write(f"📁 {root.name}/\n")
    for ln in lines(root): out.write(ln+"\n")
    out.write("```\n\n")

def parse_manifest(md: Path)->dict[str, tuple[str,int]]:
    """Liest ein Manifest aus einer früheren Merge-Datei."""
    m: dict[str, tuple[str,int]] = {}
    if not md or not md.exists(): return m
    try:
        inside = False
        with md.open("r", encoding=ENC, errors="ignore") as f:
            for line in f:
                s = line.strip()
                if s.startswith("## 🧾 Manifest"):
                    inside = True; continue
                if inside:
                    if not s.startswith("- "):
                        if s.startswith("## "): break
                        continue
                    row = s[2:]
                    parts = row.split("|")
                    rel, md5_val, size_val = "", "", 0

                    if len(parts) >= 3:
                        # Parse from right to left to be robust against '|' in filename
                        size_part = parts[-1].strip()
                        md5_part = parts[-2].strip()

                        has_size = size_part.startswith("size=")
                        has_md5 = md5_part.startswith("md5=")

                        if has_size:
                            try:
                                size_val = int(size_part[5:].strip())
                            except ValueError:
                                size_val = 0

                        if has_md5:
                            md5_val = md5_part[4:].strip()

                        if has_size or has_md5:
                            rel = "|".join(parts[:-2]).strip()
                    elif len(parts) == 2:
                        # Handle case where only one of md5 or size is present
                        p1 = parts[0].strip()
                        p2 = parts[1].strip()
                        if p2.startswith("md5="):
                            md5_val = p2[4:].strip()
                            rel = p1
                        elif p2.startswith("size="):
                            try:
                                size_val = int(p2[5:].strip())
                            except ValueError:
                                size_val = 0
                            rel = p1

                    elif len(parts) == 1:
                        rel = parts[0].strip()

                    if rel:
                        m[rel] = (md5_val, size_val)
    except Exception:
        pass
    return m

def build_diff(current: list[tuple[Path,Path,int,str]], merge_dir: Path, merge_prefix:str)->tuple[list[tuple[str,str]], int, int, int]:
    """Vergleicht den aktuellen Zustand mit dem letzten Merge und erstellt einen Diff."""
    try:
        merges = sorted(merge_dir.glob(f"{merge_prefix}*.md"))
        if not merges: return [], 0, 0, 0
    except Exception:
        return [], 0, 0, 0

    last = merges[-1]
    old = parse_manifest(last)

    cur_paths = {str(rel) for _, rel, _, _ in current}
    old_paths = set(old.keys())

    added   = sorted(cur_paths - old_paths)
    removed = sorted(old_paths - cur_paths)
    changed = []
    for _, rel, _, h in current:
        r = str(rel)
        old_h, _ = old.get(r, ("", 0))
        if r in old_paths and old_h and h and old_h != h:
            changed.append(r)
    changed.sort()
    diffs = [("+", p) for p in added] + [("-", p) for p in removed] + [("~", p) for p in changed]
    return diffs, len(added), len(removed), len(changed)
