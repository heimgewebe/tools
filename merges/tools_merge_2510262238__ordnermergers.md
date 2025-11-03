### 📄 ordnermergers/merger_lib.py

**Größe:** 6 KB | **md5:** `226cd71e9058783905e7c9f327e07c2a`

```python
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
                    parts = [p.strip() for p in row.split("|")]
                    rel = parts[0] if parts else ""
                    md5_val, size_val = "", 0
                    for p in parts[1:]:
                        if p.startswith("md5="): md5_val = p[4:].strip()
                        elif p.startswith("size="):
                            try: size_val = int(p[5:].strip())
                            except ValueError: size_val = 0
                    if rel: m[rel] = (md5_val, size_val)
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
```

### 📄 ordnermergers/ordnermerger.py

**Größe:** 8 KB | **md5:** `7c7f113184c030bd929ec2413b4c7772`

```python
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
```

### 📄 ordnermergers/repomerger_lib.py

**Größe:** 11 KB | **md5:** `2710ba68732292186876d185c827fe8a`

```python
# -*- coding: utf-8 -*-
"""
repomerger_lib — Hauptlogik für die repo-spezifischen Merger-Skripte.
"""

from __future__ import annotations
import os, sys, argparse, configparser, urllib.parse
from pathlib import Path
from datetime import datetime
from . import merger_lib as ml

# Gemeinsame Basispfade für die Suche
COMMON_BASES = [
    Path("/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents"),
    Path.home() / "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents",
    Path.home() / "Documents",
]

class RepoMerger:
    """
    Diese Klasse kapselt die Logik zum Mergen eines bestimmten Repo-Ordners.
    Sie wird von den Wrapper-Skripten (hauski-merger.py, etc.) instanziiert und ausgeführt.
    """
    def __init__(self, *, config_name:str, title:str, env_var:str, merge_prefix:str, def_basename:str):
        self.config_name = config_name
        self.title = title
        self.env_var = env_var
        self.merge_prefix = merge_prefix
        self.def_basename = def_basename
        self.DEF_KEEP = 2
        self.DEF_MERGE_DIRNAME = "merge"
        self.DEF_ENCODING = "utf-8"
        self.DEF_SRCH_DEPTH = 4

    def _deurl(self, s: str) -> str:
        if s and s.lower().startswith("file://"):
            return urllib.parse.unquote(s[7:])
        return s or ""

    def _safe_is_dir(self, p: Path) -> bool:
        try: return p.is_dir()
        except Exception: return False

    def _load_config(self) -> tuple[configparser.ConfigParser, Path]:
        cfg = configparser.ConfigParser()
        cfg_path = Path.home() / ".config" / self.config_name / "config.ini"
        try:
            if cfg_path.exists(): cfg.read(cfg_path, encoding="utf-8")
        except Exception: pass
        return cfg, cfg_path

    def _cfg_get_int(self, cfg, section, key, default):
        try: return cfg.getint(section, key, fallback=default)
        except Exception: return default

    def _cfg_get_str(self, cfg, section, key, default):
        try: return cfg.get(section, key, fallback=default)
        except Exception: return default

    def _find_dir_by_basename(self, basename:str, aliases:dict[str,str], search_depth:int) -> tuple[Path|None, list[Path]]:
        if basename in aliases:
            p = Path(self._deurl(aliases[basename]).strip('"'))
            if self._safe_is_dir(p): return p, []

        candidates=[]
        for base in COMMON_BASES:
            if not base.exists(): continue
            pref = [base / basename, base / "ordnermerger" / basename, base / "Obsidian" / basename]
            for c in pref:
                if self._safe_is_dir(c): candidates.append(c)
            try:
                max_depth_abs = len(str(base).split(os.sep)) + max(1, int(search_depth))
                for p in base.rglob(basename):
                    if p.is_dir() and p.name == basename and len(str(p).split(os.sep)) <= max_depth_abs:
                        candidates.append(p)
            except Exception: pass

        uniq = sorted(list(set(candidates)), key=lambda p: (len(str(p)), str(p)))
        if not uniq: return None, []

        best = uniq[0]
        others = uniq[1:]
        return best, others

    def _extract_source_path(self, argv: list[str], *, aliases:dict[str,str], search_depth:int) -> tuple[Path|None,str|None]:
        env_src = os.environ.get(self.env_var, "").strip()
        if env_src:
            p = Path(self._deurl(env_src).strip('"'))
            if not self._safe_is_dir(p) and p.exists(): p = p.parent
            if self._safe_is_dir(p): return p, f"{self.env_var} (ENV)"

        tokens = [t for t in argv if t and t != "--source-dir"]
        if "--source-dir" in argv:
            try:
                idx = argv.index("--source-dir")
                if idx + 1 < len(argv): tokens.insert(0, argv[idx+1])
            except ValueError: pass

        for tok in tokens:
            cand = self._deurl((tok or "").strip('"'))
            if not cand: continue
            if os.sep in cand or cand.lower().startswith("file://"):
                p = Path(cand)
                if p.exists():
                    if p.is_file(): p = p.parent
                    if self._safe_is_dir(p): return p, "direktes Argument"

        for tok in tokens:
            cand = self._deurl((tok or "").strip('"'))
            if not cand or os.sep in cand or cand.lower().startswith("file://"): continue

            hit, others = self._find_dir_by_basename(cand, aliases, search_depth=search_depth)
            if hit:
                info = f"Basename-Fallback ('{cand}')"
                if others:
                    others_s = " | ".join(str(p) for p in others[:3])
                    print(f"__{self.config_name.upper()}_INFO__: Mehrere Kandidaten, nehme kürzesten: {hit} | weitere: {others_s}")
                return hit, info

        return None, None

    def _keep_last_n(self, merge_dir: Path, keep: int, keep_new: Path|None=None, *, merge_prefix: str | None = None):
        prefix = merge_prefix or self.merge_prefix
        merges = sorted(merge_dir.glob(f"{prefix}*.md"))
        if keep_new and keep_new not in merges:
            merges.append(keep_new)
            merges.sort(key=lambda p: p.stat().st_mtime)

        if keep > 0 and len(merges) > keep:
            for old in merges[:-keep]:
                try: old.unlink()
                except Exception: pass

    def _do_merge(
        self,
        source: Path,
        out_file: Path,
        *,
        encoding:str,
        keep:int,
        merge_dir:Path,
        max_tree_depth:int|None,
        search_info:str|None,
        merge_prefix:str,
    ):
        included, skipped, total = [], [], 0
        for dirpath, _, files in os.walk(source):
            d = Path(dirpath)
            for fn in files:
                p = d / fn
                rel = p.relative_to(source)
                if not ml.is_text(p):
                    skipped.append(f"{rel} (binär)"); continue
                try:
                    sz = p.stat().st_size
                    h = ml.md5(p)
                    included.append((p, rel, sz, h)); total += sz
                except Exception as e:
                    skipped.append(f"{rel} (Fehler: {e})")

        included.sort(key=lambda t: str(t[1]).lower())
        out_file.parent.mkdir(parents=True, exist_ok=True)

        diffs, add_c, del_c, chg_c = ml.build_diff(included, merge_dir, merge_prefix)

        with out_file.open("w", encoding=encoding) as out:
            out.write(f"# {self.title}\n\n")
            out.write(f"**Zeitpunkt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            out.write(f"**Quelle:** `{source}`\n")
            if search_info: out.write(f"**Quelle ermittelt:** {search_info}\n")
            out.write(f"**Dateien (inkludiert):** {len(included)}\n")
            out.write(f"**Gesamtgröße:** {ml.human(total)}\n")
            if diffs: out.write(f"**Änderungen:** +{add_c} / -{del_c} / ~{chg_c}\n")
            out.write("\n## 📁 Struktur\n\n"); ml.write_tree(out, source, max_tree_depth)
            if diffs:
                out.write("## 📊 Änderungen\n\n")
                for sym, pth in diffs: out.write(f"{sym} {pth}\n")
                out.write("\n")
            if skipped:
                out.write("## ⏭️ Übersprungen\n\n")
                for s in skipped: out.write(f"- {s}\n")
                out.write("\n")
            out.write("## 🧾 Manifest\n\n")
            for _, rel, sz, h in included: out.write(f"- {rel} | md5={h} | size={sz}\n")
            out.write("\n## 📄 Dateiinhalte\n\n")
            for p, rel, sz, _ in included:
                out.write(f"### 📄 {rel}\n\n**Größe:** {ml.human(sz)}\n\n```{ml.lang(p)}\n")
                try:
                    txt = p.read_text(encoding=encoding, errors="replace")
                    out.write(txt + ("" if txt.endswith("\n") else "\n"))
                except Exception as e:
                    out.write(f"<<Lesefehler: {e}>>\n")
                out.write("```\n\n")

        self._keep_last_n(merge_dir, keep, out_file, merge_prefix=merge_prefix)
        print(f"✅ Merge geschrieben: {out_file} ({ml.human(out_file.stat().st_size)})")

    def run(self, argv: list[str]):
        parser = argparse.ArgumentParser(description=self.title, add_help=False)
        parser.add_argument("--source-dir", dest="src_flag")
        parser.add_argument("--keep", type=int)
        parser.add_argument("--encoding")
        parser.add_argument("--max-depth", type=int, dest="max_tree_depth")
        parser.add_argument("--search-depth", type=int, dest="search_depth")
        parser.add_argument("--merge-dirname")
        parser.add_argument("--merge-prefix")
        parser.add_argument("-h", "--help", action="store_true")
        parser.add_argument("rest", nargs="*")

        args = parser.parse_args(argv)

        if args.help:
            print(f"Hilfe für {self.config_name}: Startskript zeigt Details.")
            return 0

        cfg, _ = self._load_config()

        keep = args.keep if args.keep is not None else self._cfg_get_int(cfg, "general", "keep", self.DEF_KEEP)
        merge_dirname = args.merge_dirname or self._cfg_get_str(cfg, "general", "merge_dirname", self.DEF_MERGE_DIRNAME)
        merge_prefix_final = args.merge_prefix or self._cfg_get_str(cfg, "general", "merge_prefix", self.merge_prefix)
        encoding = args.encoding or self._cfg_get_str(cfg, "general", "encoding", self.DEF_ENCODING)
        search_depth = args.search_depth if args.search_depth is not None else self._cfg_get_int(cfg, "general", "max_search_depth", self.DEF_SRCH_DEPTH)

        aliases = {k: v for k, v in cfg.items("aliases")} if cfg.has_section("aliases") else {}

        src_argv = ([args.src_flag] + args.rest) if args.src_flag else args.rest
        src, src_info = self._extract_source_path(src_argv, aliases=aliases, search_depth=search_depth)

        if not src:
            print(f"❌ Quelle nicht gefunden. Setze {self.env_var} oder gib einen Pfad an.")
            return 2
        if not self._safe_is_dir(src):
            print(f"❌ Quelle ist kein Ordner: {src}")
            return 1

        script_root = Path(sys.argv[0]).resolve().parent
        merge_dir = script_root / merge_dirname
        merge_dir.mkdir(parents=True, exist_ok=True)

        out_file = merge_dir / f"{merge_prefix_final}{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        self._do_merge(
            src,
            out_file,
            encoding=encoding,
            keep=keep,
            merge_dir=merge_dir,
            max_tree_depth=args.max_tree_depth,
            search_info=src_info,
            merge_prefix=merge_prefix_final,
        )
        return 0
```

