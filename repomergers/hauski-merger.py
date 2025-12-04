#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
hauski-merger – Shortcuts-freundlich, Dotfiles inklusive, Basename/Env/Config-Fallbacks, keep last N merges

Nutzung auf iOS (Shortcuts → "Run Pythonista Script" → Arguments):
    – GIB GENAU EINE DER VARIANTEN, KEINE UMBRÜCHE:
      1) --source-dir "/private/var/.../hauski"
      2) "/private/var/.../hauski"
      3) file:///private/var/.../hauski"
      4) hauski   (nur Basename; Fallback-Suche aktiv)
    – Alternativ Env: HAUSKI_SOURCE="/private/var/.../hauski"

Ausgabe:
    ./merge/hauski_DDMM.md
    (bei Mehrfach-Merges am selben Tag: hauski_DDMM_2.md, hauski_DDMM_3.md, ...)
    – Standard: nur die letzten 2 Merges bleiben (per Config / CLI änderbar)

Konfig (optional):
    ~/.config/hauski-merger/config.ini

    [general]
    keep = 2
    merge_dirname = merge
    merge_prefix  = hauski
    max_search_depth = 4
    encoding = utf-8

    [aliases]
    hauski = /private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/hauski
"""

import sys
import os
import argparse
import hashlib
import urllib.parse
import configparser
from pathlib import Path
from datetime import datetime

# ===== Defaults =====
DEF_KEEP          = 2
DEF_MERGE_DIRNAME = "merge"
# Basisname im Dateinamen, z. B. "hauski" -> hauski_DDMM.md
DEF_MERGE_PREFIX  = "hauski"
DEF_ENCODING      = "utf-8"
DEF_SRCH_DEPTH    = 4

# nur wirklich binäre Endungen (Dotfiles & .svg bleiben erhalten)
BINARY_EXT = {
    ".png",".jpg",".jpeg",".gif",".bmp",".ico",".webp",".heic",".heif",".psd",".ai",
    ".mp3",".wav",".flac",".ogg",".m4a",".aac",".mp4",".mkv",".mov",".avi",".wmv",".flv",".webm",
    ".zip",".rar",".7z",".tar",".gz",".bz2",".xz",".tgz",
    ".ttf",".otf",".woff",".woff2",
    ".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".pages",".numbers",".key",
    ".exe",".dll",".so",".dylib",".bin",".class",".o",".a",
    ".db",".sqlite",".sqlite3",".realm",".mdb",".pack",".idx",
}

LANG_MAP = {
    "py": "python","js": "javascript","ts": "typescript","html": "html","css": "css",
    "scss": "scss","sass": "sass","json": "json","xml": "xml","yaml": "yaml","yml": "yaml",
    "md": "markdown","sh": "bash","bat": "batch","sql": "sql","php": "php","cpp": "cpp",
    "c": "c","java": "java","cs": "csharp","go": "go","rs": "rust","rb": "ruby",
    "swift": "swift","kt": "kotlin","svelte": "svelte",
}

COMMON_BASES = [
    Path("/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents"),
    Path.home() / "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents",
    Path.home() / "Documents",
]

# --- Klassifikations-Hilfen --------------------------------------------------

DOC_EXTENSIONS = {".md", ".rst", ".txt"}

SOURCE_EXTENSIONS = {
    ".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".svelte",
    ".c", ".cpp", ".h", ".hpp", ".go", ".java", ".cs",
}

CONFIG_FILENAMES = {
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "Cargo.toml",
    "Cargo.lock",
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Justfile",
    "Makefile",
    "toolchain.versions.yml",
    ".editorconfig",
    ".markdownlint.jsonc",
    ".markdownlint.yaml",
    ".yamllint",
    ".yamllint.yml",
    ".lychee.toml",
    ".vale.ini",
}

# ===== Utilities ============================================================

def human(n: int) -> str:
    u = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(u) - 1:
        f /= 1024
        i += 1
    return f"{f:.2f} {u[i]}"


def is_text_file(p: Path, sniff: int = 4096) -> bool:
    # harte Binär-Endungen
    if p.suffix.lower() in BINARY_EXT:
        return False
    # .env / .env.* aus Sicherheitsgründen ignorieren, außer Vorlagen
    name = p.name
    if name.startswith(".env") and name not in (".env.example", ".env.template", ".env.sample"):
        return False
    try:
        with p.open("rb") as f:
            chunk = f.read(sniff)
        if not chunk:
            return True
        if b"\x00" in chunk:
            return False
        try:
            chunk.decode("utf-8")
            return True
        except UnicodeDecodeError:
            chunk.decode("latin-1", errors="ignore")
            return True
    except Exception:
        return False


def lang_for(p: Path) -> str:
    return LANG_MAP.get(p.suffix.lower().lstrip("."), "")


def file_md5(p: Path, block: int = 65536) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_is_dir(p: Path) -> bool:
    try:
        return p.is_dir()
    except Exception:
        return False


def _deurl(s: str) -> str:
    if s and s.lower().startswith("file://"):
        return urllib.parse.unquote(s[7:])
    return s or ""


def load_config() -> tuple[configparser.ConfigParser, Path]:
    cfg = configparser.ConfigParser()
    cfg_path = Path.home() / ".config" / "hauski-merger" / "config.ini"
    try:
        if cfg_path.exists():
            cfg.read(cfg_path, encoding="utf-8")
    except Exception as e:
        print(f"Warning: Failed to read config from {cfg_path}: {e}", file=sys.stderr)
    return cfg, cfg_path


def cfg_get_int(cfg, section, key, default):
    try:
        return cfg.getint(section, key, fallback=default)
    except Exception:
        return default


def cfg_get_str(cfg, section, key, default):
    try:
        return cfg.get(section, key, fallback=default)
    except Exception:
        return default

# ===== Klassifikation & Statistik ===========================================

def classify_category(rel: Path, ext: str) -> str:
    """Grobe Heuristik: doc / config / source / other."""
    name = rel.name
    if name in CONFIG_FILENAMES:
        return "config"
    if ext in DOC_EXTENSIONS:
        return "doc"
    if ext in SOURCE_EXTENSIONS:
        return "source"
    parts = [p.lower() for p in rel.parts]
    if any(p in ("config", "configs", "settings", "etc", ".github") for p in parts):
        return "config"
    if "docs" in parts or "doc" in parts:
        return "doc"
    return "other"


def summarize_ext(manifest_rows):
    """
    manifest_rows: Liste von (rel:Path, size:int, md5:str, cat:str, ext:str)
    -> (ext_counts, ext_sizes)
    """
    counts: dict[str, int] = {}
    sizes: dict[str, int] = {}
    for rel, sz, md5, cat, ext in manifest_rows:
        key = ext or "<none>"
        counts[key] = counts.get(key, 0) + 1
        sizes[key] = sizes.get(key, 0) + sz
    return counts, sizes


def summarize_cat(manifest_rows):
    """
    Kleine Übersicht nach Kategorien.
    -> dict cat -> (count, size)
    """
    result: dict[str, list[int]] = {}
    for rel, sz, md5, cat, ext in manifest_rows:
        if cat not in result:
            result[cat] = [0, 0]
        result[cat][0] += 1
        result[cat][1] += sz
    return result

# ===== Basename-Fallback ====================================================

def find_dir_by_basename(basename: str, aliases: dict[str, str], search_depth: int = DEF_SRCH_DEPTH) -> tuple[Path | None, list[Path]]:
    # 0) Aliases
    if basename in aliases:
        p = Path(_deurl(aliases[basename]).strip('"'))
        if safe_is_dir(p):
            return p, []

    candidates: list[Path] = []
    for base in COMMON_BASES:
        if not base.exists():
            continue

        # schnelle Treffer
        pref = [
            base / basename,
            base / "ordnermerger" / basename,
            base / "Obsidian" / basename,
        ]
        for c in pref:
            if safe_is_dir(c):
                candidates.append(c)

        # vorsichtige Suche
        try:
            max_depth_abs = len(str(base).split(os.sep)) + max(1, int(search_depth))
            for p in base.rglob(basename):
                if p.is_dir() and p.name == basename and len(str(p).split(os.sep)) <= max_depth_abs:
                    candidates.append(p)
        except OSError:
            pass  # Permission denied etc.
        except Exception as e:
            print(f"Warning: Error searching in {base}: {e}", file=sys.stderr)

    uniq: list[Path] = []
    seen: set[str] = set()
    for c in candidates:
        s = str(c)
        if s not in seen:
            uniq.append(c)
            seen.add(s)

    if not uniq:
        return None, []
    best = sorted(uniq, key=lambda p: (len(str(p)), str(p)))[0]
    others = [p for p in uniq if p != best]
    return best, others

# ===== Dateinamen-Logik =====================================================

def make_output_filename(merge_dir: Path, base_name: str) -> Path:
    """
    Erzeugt einen Dateinamen nach Schema:
        <base_name>_DDMM.md
    und hängt bei Kollisionen _2, _3, ... an.
    """
    now = datetime.now()
    ddmm = now.strftime("%d%m")
    base = f"{base_name}_{ddmm}"
    candidate = merge_dir / f"{base}.md"
    idx = 2
    while candidate.exists():
        candidate = merge_dir / f"{base}_{idx}.md"
        idx += 1
    return candidate

# ===== Manifest/Diff/Tree ===================================================

def write_tree(out, root: Path, max_depth: int | None = None):
    def lines(d: Path, lvl: int = 0):
        if max_depth is not None and lvl >= max_depth:
            return []
        res: list[str] = []
        try:
            items = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            dirs = [i for i in items if i.is_dir()]
            files = [i for i in items if i.is_file()]
            for i, sub in enumerate(dirs):
                pref = "└── " if (i == len(dirs) - 1 and not files) else "├── "
                res.append("    " * lvl + f"{pref}📁 {sub.name}/")
                res += lines(sub, lvl + 1)
            for i, f in enumerate(files):
                pref = "└── " if i == len(files) - 1 else "├── "
                try:
                    icon = "📄" if is_text_file(f) else "🔒"
                    res.append("    " * lvl + f"{pref}{icon} {f.name} ({human(f.stat().st_size)})")
                except Exception:
                    res.append("    " * lvl + f"{pref}📄 {f.name}")
        except PermissionError:
            res.append("    " * lvl + "❌ Zugriff verweigert")
        return res

    out.write("```\n")
    out.write(f"📁 {root.name}/\n")
    for ln in lines(root):
        out.write(ln + "\n")
    out.write("```\n\n")


def parse_manifest(md: Path) -> dict[str, tuple[str, int]]:
    m: dict[str, tuple[str, int]] = {}
    if not md or not md.exists():
        return m
    try:
        inside = False
        with md.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if s.startswith("## 🧾 Manifest"):
                    inside = True
                    continue
                if inside:
                    if not s.startswith("- "):
                        if s.startswith("## "):
                            break
                        continue
                    row = s[2:]
                    parts = [p.strip() for p in row.split("|")]
                    rel = parts[0] if parts else ""
                    md5 = ""
                    size = 0
                    for p in parts[1:]:
                        if p.startswith("md5="):
                            md5 = p[4:].strip()
                        elif p.startswith("size="):
                            try:
                                size = int(p[5:].strip())
                            except Exception:
                                size = 0
                    if rel:
                        m[rel] = (md5, size)
    except Exception as e:
        print(f"Warning: Failed to parse manifest {md}: {e}", file=sys.stderr)
    return m


def build_diff(current: list[tuple[Path, Path, int, str]], merge_dir: Path, merge_prefix: str):
    # merge_prefix als Basisname: <prefix>_DDMM*.md
    merges = sorted(merge_dir.glob(f"{merge_prefix}_*.md"))
    if not merges:
        return [], 0, 0, 0
    last = merges[-1]
    old = parse_manifest(last)

    cur_paths = {str(rel) for _, rel, _, _ in current}
    old_paths = set(old.keys())

    added = sorted(cur_paths - old_paths)
    removed = sorted(old_paths - cur_paths)
    changed: list[str] = []
    for _, rel, _, h in current:
        r = str(rel)
        old_h = old.get(r, ("", 0))[0]
        if r in old_paths and old_h and h and old_h != h:
            changed.append(r)
    changed.sort()
    diffs = [("+", p) for p in added] + [("-", p) for p in removed] + [("~", p) for p in changed]
    return diffs, len(added), len(removed), len(changed)


def keep_last_n(merge_dir: Path, keep: int, keep_new: Path | None = None, merge_prefix: str = DEF_MERGE_PREFIX):
    merges = sorted(merge_dir.glob(f"{merge_prefix}_*.md"))
    if keep_new and keep_new not in merges:
        merges.append(keep_new)
        merges.sort()
    if keep <= 0 or len(merges) <= keep:
        return
    for old in merges[:-keep]:
        try:
            old.unlink()
        except Exception as e:
            print(f"Warning: Failed to delete old merge {old}: {e}", file=sys.stderr)

# ===== Merge ================================================================

def do_merge(
    source: Path,
    out_file: Path,
    *,
    encoding: str,
    keep: int,
    merge_dir: Path,
    merge_prefix: str,
    max_tree_depth: int | None,
    search_info: str | None,
):
    included: list[tuple[Path, Path, int, str]] = []
    manifest_rows: list[tuple[Path, int, str, str, str]] = []
    skipped: list[str] = []
    total = 0

    for dirpath, _, files in os.walk(source):
        d = Path(dirpath)
        for fn in files:
            p = d / fn
            rel = p.relative_to(source)

            if not is_text_file(p):
                skipped.append(f"{rel} (binär/ignoriert)")
                continue

            try:
                sz = p.stat().st_size
            except Exception as e:
                skipped.append(f"{rel} (stat error: {e})")
                continue
            try:
                h = file_md5(p)
            except Exception:
                h = ""

            total += sz
            included.append((p, rel, sz, h))

            ext = p.suffix.lower()
            cat = classify_category(rel, ext)
            manifest_rows.append((rel, sz, h, cat, ext))

    included.sort(key=lambda t: str(t[1]).lower())
    manifest_rows.sort(key=lambda t: str(t[0]).lower())

    out_file.parent.mkdir(parents=True, exist_ok=True)

    base_prefix = merge_prefix.rstrip("_")

    diffs, add_c, del_c, chg_c = build_diff(included, out_file.parent, base_prefix)
    ext_counts, ext_sizes = summarize_ext(manifest_rows)
    cat_stats = summarize_cat(manifest_rows)

    with out_file.open("w", encoding=encoding) as out:
        out.write("# HausKI-Merge\n\n")
        out.write(f"**Zeitpunkt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"**Quelle:** `{source}`\n")
        if search_info:
            out.write(f"**Quelle ermittelt:** {search_info}\n")
        out.write(f"**Dateien (inkludiert):** {len(included)}\n")
        out.write(f"**Gesamtgröße:** {human(total)}\n")
        if diffs:
            out.write(f"**Änderungen seit letztem Merge:** +{add_c} / -{del_c} / ~{chg_c}\n")
        out.write("\n")

        # KI-Hinweisblock
        out.write("> Hinweis für KIs:\n")
        out.write("> - Dies ist ein Schnappschuss des Dateisystems, keine vollständige Git-Historie.\n")
        out.write("> - Die Baumstruktur findest du unter `## 📁 Struktur`.\n")
        out.write("> - Alle aufgenommenen Dateien stehen im `## 🧾 Manifest`.\n")
        out.write("> - Dateiinhalte stehen unter `## 📄 Dateiinhalte`.\n")
        out.write("> - `.env` und ähnliche Dateien können bewusst fehlen (Sicherheitsfilter).\n\n")

        # Plan / Übersicht
        out.write("## 🧮 Plan\n\n")
        out.write(f"- Textdateien im Merge: **{len(included)}**\n")
        out.write(f"- Gesamtgröße der Quellen: **{human(total)}**\n")

        if cat_stats:
            out.write("\n**Dateien nach Kategorien:**\n\n")
            out.write("| Kategorie | Dateien | Gesamtgröße |\n")
            out.write("| --- | ---: | ---: |\n")
            for cat in sorted(cat_stats.keys()):
                cnt, sz = cat_stats[cat]
                out.write(f"| `{cat}` | {cnt} | {human(sz)} |\n")
            out.write("\n")

        if ext_counts:
            out.write("**Statistik nach Dateiendungen:**\n\n")
            out.write("| Ext | Dateien | Gesamtgröße |\n")
            out.write("| --- | ---: | ---: |\n")
            for ext in sorted(ext_counts.keys()):
                out.write(f"| `{ext}` | {ext_counts[ext]} | {human(ext_sizes[ext])} |\n")
            out.write("\n")

        out.write("Hinweis: Obwohl `.env`-ähnliche Dateien gefiltert werden, können sensible Daten ")
        out.write("in anderen Dateien (z. B. JSON/YAML) vorkommen. Nutze den Merge nicht als public Dump.\n\n")

        out.write("## 📁 Struktur\n\n")
        write_tree(out, source, max_tree_depth)

        if diffs:
            out.write("## 📊 Änderungen seit letztem Merge\n\n")
            for sym, pth in diffs:
                out.write(f"{sym} {pth}\n")
            out.write("\n")

        if skipped:
            out.write("## ⏭️ Übersprungen\n\n")
            for s in skipped:
                out.write(f"- {s}\n")
            out.write("\n")

        out.write("## 🧾 Manifest\n\n")
        for rel, sz, h, cat, ext in manifest_rows:
            out.write(f"- {rel} | md5={h} | size={sz} | cat={cat}\n")
        out.write("\n")

        out.write("## 📄 Dateiinhalte\n\n")
        for p, rel, sz, h in included:
            out.write(f"### 📄 {rel}\n\n**Größe:** {human(sz)}\n\n```{lang_for(p)}\n")
            try:
                txt = p.read_text(encoding=encoding, errors="replace")
            except Exception as e:
                txt = f"<<Lesefehler: {e}>>"
            out.write(txt)
            if not txt.endswith("\n"):
                out.write("\n")
            out.write("```\n\n")

    keep_last_n(out_file.parent, keep=keep, keep_new=out_file, merge_prefix=base_prefix)
    print(f"✅ Merge geschrieben: {out_file} ({human(out_file.stat().st_size)})")

# ===== CLI ==================================================================

def build_parser():
    p = argparse.ArgumentParser(description="hauski-merger – genau ein Quellordner", add_help=False)
    p.add_argument("--source-dir", dest="src_flag")
    p.add_argument("--keep", type=int, dest="keep")
    p.add_argument("--encoding", dest="encoding")
    p.add_argument("--max-depth", type=int, dest="max_tree_depth")
    p.add_argument("--search-depth", type=int, dest="search_depth")
    p.add_argument("--merge-dirname", dest="merge_dirname")
    p.add_argument("--merge-prefix", dest="merge_prefix")  # Basisname für Dateinamen (Default: hauski)
    p.add_argument("-h", "--help", action="store_true", dest="help")
    p.add_argument("rest", nargs="*")
    return p


def print_help():
    print(__doc__.strip())


def extract_source_path(argv: list[str], *, aliases: dict[str, str], search_depth: int) -> tuple[Path | None, str | None]:
    """
    Akzeptiert:
      - --source-dir <PATH|BASENAME|file://>
      - <PATH|BASENAME|file://>
      - Datei → Elternordner
      - Env: HAUSKI_SOURCE
      - Fallback: Nur-Basename unter COMMON_BASES
    Rückgabe: (Pfad, InfoStringFürReport)
    """
    # Env
    env_src = os.environ.get("HAUSKI_SOURCE", "").strip()
    if env_src:
        p = Path(_deurl(env_src).strip('"'))
        if not safe_is_dir(p) and p.exists():
            p = p.parent
        if safe_is_dir(p):
            return p, "HAUSKI_SOURCE (ENV)"

    # Tokens
    tokens: list[str] = []
    if "--source-dir" in argv:
        idx = argv.index("--source-dir")
        if idx + 1 < len(argv):
            tokens.append(argv[idx + 1])
    tokens += [t for t in argv if t != "--source-dir"]

    # Direktpfad
    for tok in tokens:
        cand = _deurl((tok or "").strip('"'))
        if not cand:
            continue
        if os.sep not in cand and not cand.lower().startswith("file://"):
            continue
        p = Path(cand)
        if p.exists():
            if p.is_file():
                p = p.parent
            if safe_is_dir(p):
                return p, "direktes Argument"

    # Basename/Alias
    for tok in tokens:
        cand = _deurl((tok or "").strip('"'))
        if not cand:
            continue
        if os.sep in cand or cand.lower().startswith("file://"):
            continue
        base = cand
        hit, others = find_dir_by_basename(base, aliases, search_depth=search_depth)
        if hit:
            info = f"Basename-Fallback ('{base}')"
            if others:
                others_s = " | ".join(str(p) for p in others[:5])
                print(f"__HAUSKI_MERGER_INFO__: Mehrere Kandidaten gefunden, nehme kürzesten: {hit} | weitere: {others_s}")
            return hit, info
    return None, None


def _running_in_shortcuts() -> bool:
    return os.environ.get("HAUSKI_SHORTCUTS", "1") == "1"


def main(argv: list[str]) -> int:
    cfg, cfg_path = load_config()
    args = build_parser().parse_args(argv)
    if args.help:
        print_help()
        return 0

    keep = args.keep if args.keep is not None else cfg_get_int(cfg, "general", "keep", DEF_KEEP)
    merge_dirname = args.merge_dirname or cfg_get_str(cfg, "general", "merge_dirname", DEF_MERGE_DIRNAME)
    merge_prefix = args.merge_prefix or cfg_get_str(cfg, "general", "merge_prefix", DEF_MERGE_PREFIX)
    encoding = args.encoding or cfg_get_str(cfg, "general", "encoding", DEF_ENCODING)
    search_depth = args.search_depth if args.search_depth is not None else cfg_get_int(cfg, "general", "max_search_depth", DEF_SRCH_DEPTH)
    max_tree_depth = args.max_tree_depth if args.max_tree_depth is not None else None

    aliases: dict[str, str] = {}
    if cfg.has_section("aliases"):
        for k, v in cfg.items("aliases"):
            aliases[k] = v

    src, src_info = extract_source_path(
        [args.src_flag] + args.rest if args.src_flag else args.rest,
        aliases=aliases,
        search_depth=search_depth,
    )
    if not src:
        print("❌ Quelle fehlt/unerkannt. Übergib Pfad/URL/Basename oder setze HAUSKI_SOURCE. (-h für Hilfe)")
        return 2
    if not safe_is_dir(src):
        print(f"❌ Quelle nicht gefunden oder kein Ordner: {src}")
        return 1

    script_root = Path(__file__).resolve().parent
    merge_dir = ensure_dir(script_root / merge_dirname)

    # Dateiname: <merge_prefix>_DDMM(.md) + Kollision-Handling
    base_name = merge_prefix.rstrip("_")
    out_file = make_output_filename(merge_dir, base_name=base_name)

    do_merge(
        src,
        out_file,
        encoding=encoding,
        keep=keep,
        merge_dir=merge_dir,
        merge_prefix=merge_prefix,
        max_tree_depth=max_tree_depth,
        search_info=src_info,
    )
    return 0


def _safe_main():
    try:
        rc = main(sys.argv[1:])
    except SystemExit as e:
        rc = int(getattr(e, "code", 1) or 0)
    except Exception as e:
        print(f"__HAUSKI_MERGER_ERR__: {e}")
        rc = 1
    if _running_in_shortcuts():
        if rc != 0:
            print(f"__HAUSKI_MERGER_WARN__: Exit {rc}")
        print("__HAUSKI_MERGER_OK__")
    else:
        sys.exit(rc)


if __name__ == "__main__":
    _safe_main()
