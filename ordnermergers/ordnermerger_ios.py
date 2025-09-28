# -*- coding: utf-8 -*-
# ordnermerger_batch_ios.py — iOS/Pythonista: Batch-here mit auto-delete & retention

import os, sys, shutil, hashlib, datetime, re
from pathlib import Path

# ==== Einstellungen ====
ENC = "utf-8"
RETAIN = 3                 # wie viele Merges in ./merge behalten
MAX_BYTES = None           # z.B. 200_000 um große Dateien zu kappen
MAX_DEPTH = None           # Baumtiefe nur für Anzeige (None = unlimitiert)

# Binär-Endungen (Heuristik)
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

# ==== Helpers ====
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

def build_out_name(src_folder: Path)->str:
    ts = datetime.datetime.now().strftime("%y%m%d%H%M")  # yymmddhhmm
    return f"{src_folder.name}_merge_{ts}.md"

# ==== Merge einer Quelle ====
def merge_one_folder(source: Path, merge_dir: Path) -> Path:
    out_file = merge_dir / build_out_name(source)
    included=[]; skipped=[]; total=0

    for dirpath, _, files in os.walk(source):
        d = Path(dirpath)
        for fn in files:
            p = d / fn
            rel = p.relative_to(source)
            if not is_text_file(p):
                skipped.append(f"{rel} (binär)"); continue
            try:
                sz=p.stat().st_size; digest=md5(p)
            except Exception as e:
                skipped.append(f"{rel} (err {e})"); continue
            included.append((p, rel, sz, digest)); total += sz

    included.sort(key=lambda t: str(t[1]).lower())
    with out_file.open("w", encoding=ENC) as out:
        out.write(f"# Ordner-Merge: {source.name}\n\n")
        out.write(f"**Zeitpunkt:** {datetime.datetime.now():%Y-%m-%d %H:%M}\n")
        out.write(f"**Quelle:** `{source.name}`\n")
        out.write(f"**Dateien:** {len(included)}\n")
        out.write(f"**Gesamtgröße:** {human(total)}\n\n")

        out.write("## 📁 Struktur\n\n"); write_tree(out, source, MAX_DEPTH); out.write("\n")
        out.write("## 📦 Dateien\n\n")
        for p, rel, sz, digest in included:
            out.write(f"### 📄 {rel}\n\n**Größe:** {human(sz)} | **md5:** `{digest}`\n\n```{lang_for(p)}\n")
            try:
                if MAX_BYTES and sz > MAX_BYTES:
                    with p.open("rb") as fh: raw=fh.read(MAX_BYTES)
                    txt=raw.decode(ENC, errors="replace")
                    out.write(txt); 
                    if not txt.endswith("\n"): out.write("\n")
                    out.write("```\n\n> ⚠️ Datei gekürzt.\n\n")
                else:
                    txt=p.read_text(encoding=ENC, errors="replace")
                    out.write(txt); 
                    if not txt.endswith("\n"): out.write("\n")
                    out.write("```\n\n")
            except Exception as e:
                out.write(f"<<Lesefehler: {e}>>\n```\n\n")

        if skipped:
            out.write("## ⏭️ Übersprungen\n\n")
            for s in skipped: out.write(f"- {s}\n")

    print(f"✅ Merge: {out_file} ({human(out_file.stat().st_size)})")
    return out_file

# ==== Retention (nur letzte N behalten) ====
def retention_clean(merge_dir: Path, keep: int):
    files = sorted(merge_dir.glob("*_merge_*.md"), key=lambda p: p.stat().st_mtime)
    if keep < 0: keep = 0
    to_delete = files[:-keep] if keep and len(files)>keep else (files if keep==0 else [])
    for f in to_delete:
        try:
            f.unlink()
            print(f"🗑️ alt entfernt: {f.name}")
        except Exception as e:
            print(f"⚠️ konnte {f} nicht löschen: {e}")

# ==== Main ====
def main():
    base = Path(__file__).resolve().parent
    merge_dir = base / "merge"
    merge_dir.mkdir(parents=True, exist_ok=True)

    # Kandidaten: alle Unterordner, außer merge/, .* , _*
    candidates=[]
    for c in sorted(base.iterdir(), key=lambda p: p.name.lower()):
        if not c.is_dir(): continue
        if c.name == "merge": continue
        if c.name.startswith(".") or c.name.startswith("_"): continue
        candidates.append(c)

    if not candidates:
        print("ℹ️ Keine zu mergen Ordner neben dem Skript gefunden.")
        return 0

    # Mergen & danach Quelle löschen
    for src in candidates:
        try:
            out_file = merge_one_folder(src, merge_dir)
            # Quelle löschen (nur wenn Merge erfolgreich geschrieben)
            try:
                shutil.rmtree(src)
                print(f"🗑️ Quelle gelöscht: {src.name}")
            except Exception as e:
                print(f"⚠️ Quelle nicht gelöscht ({src.name}): {e}")
        except Exception as e:
            print(f"❌ Fehler bei {src.name}: {e}")

    # Retention
    retention_clean(merge_dir, RETAIN)
    print("✅ Fertig.")

    # Ausgabe an Shortcuts zurückgeben (optional)
    try:
        import appex
        if appex.is_running_extension():
            # gib den jüngsten Merge zurück
            latest = max(merge_dir.glob("*_merge_*.md"), key=lambda p: p.stat().st_mtime, default=None)
            if latest:
                appex.set_output_file(str(latest))
    except Exception:
        pass

if __name__ == "__main__":
    sys.exit(main())