# -*- coding: utf-8 -*-
"""
merger_lib — Gemeinsame Hilfsfunktionen für ordnermerger Skripte.
"""

from __future__ import annotations
import hashlib
from pathlib import Path

ENC = "utf-8"

BINARY_EXTS = {".png",".jpg",".jpeg",".gif",".webp",".avif",".bmp",".ico",
    ".pdf",".mp3",".wav",".flac",".ogg",".m4a",".aac",
    ".mp4",".mkv",".mov",".avi",
    ".zip",".gz",".bz2",".xz",".7z",".rar",".zst",
    ".ttf",".otf",".woff",".woff2",
    ".so",".dylib",".dll",".exe",
    ".db",".sqlite",".sqlite3",".realm",".mdb",".pack",".idx"}

LANG_MAP = {"py":"python","js":"javascript","ts":"typescript","html":"html","css":"css",
            "md":"markdown","json":"json","xml":"xml","yaml":"yaml","yml":"yaml",
            "sh":"bash","sql":"sql","txt":""}

def human(n:int)->str:
    u=["B","KB","MB","GB","TB"]; f=float(n); i=0
    while f>=1024 and i<len(u)-1: f/=1024; i+=1
    return f"{f:.1f} {u[i]}"

def is_text(p: Path)->bool:
    if p.suffix.lower() in BINARY_EXTS: return False
    try:
        with p.open("rb") as fh: fh.read(2048).decode(ENC)
        return True
    except Exception: return False

def md5(p: Path)->str:
    h=hashlib.md5()
    with p.open("rb") as fh:
        for ch in iter(lambda: fh.read(1<<16), b""): h.update(ch)
    return h.hexdigest()

def lang(p: Path)->str:
    return LANG_MAP.get(p.suffix.lstrip(".").lower(), "")
