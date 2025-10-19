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
