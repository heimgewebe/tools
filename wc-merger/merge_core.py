#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merge_core – repomerger-inspirierter Kern für wc-merger / wc-extractor auf Pythonista.

Setup bei dir:

- Die Scripts (wc-merger.py, wc-extractor.py, merge_core.py) liegen im
  Pythonista-App-Speicher (Script-Library).
- Der Hub mit den Repos liegt NICHT dort, sondern in der Dateien-App unter:

    Auf meinem iPad / Pythonista 3 / wc-hub

  Interner Pfad (von show_path.py ermittelt):

    /private/var/mobile/Containers/Data/Application/
      B60D0157-973D-489A-AA59-464C3BF6D240/Documents/wc-hub

Daher wird der Hub hier über einen hart kodierten Pfad angesprochen.

Funktional:

- scan_repo(..) nutzt repomerger-Heuristiken:
  - SKIP_DIRS / SKIP_FILES / .env-Filter
  - Text-Erkennung
  - Kategorien (config / doc / source / other)
  - MD5-Hashes
- write_reports(..) erzeugt Berichte mit:
  - Plan-Abschnitt (Statistiken, Kategorien, Extensions)
  - Baumstruktur
  - Manifest (Root, Pfad, Kategorie, Text, Größe, MD5)
  - optional Dateiinhalte je nach Detailstufe
"""

import os
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# KONFIG: HIER IST DEIN HUB-PFAD HART KODIERT
# ---------------------------------------------------------------------------

HARDCODED_HUB_PATH = (
    "/private/var/mobile/Containers/Data/Application/"
    "B60D0157-973D-489A-AA59-464C3BF6D240/Documents/wc-hub"
)

MERGES_DIR_NAME = "merges"
DEFAULT_MAX_BYTES = 10_000_000  # 10 MB


# ---------------------------------------------------------------------------
# Heuristiken aus repomerger
# ---------------------------------------------------------------------------

# Verzeichnisse, die rekursiv ignoriert werden
SKIP_DIRS = {
    ".git",
    ".idea",
    "node_modules",
    ".svelte-kit",
    ".next",
    "dist",
    "build",
    "target",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}

# Einzelne Dateien, die ignoriert werden
SKIP_FILES = {
    ".DS_Store",
}

# Endungen, die sehr wahrscheinlich Text sind
TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".rs",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".jsonl",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".dockerfile",
    "dockerfile",
    ".svelte",
    ".css",
    ".scss",
    ".html",
    ".htm",
    ".xml",
    ".csv",
    ".log",
    ".lock",  # z.B. Cargo.lock, pnpm-lock.yaml
}

# Dateien, die typischerweise Konfiguration sind
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

DOC_EXTENSIONS = {".md", ".rst", ".txt"}

SOURCE_EXTENSIONS = {
    ".py",
    ".rs",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".svelte",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".go",
    ".java",
    ".cs",
}

LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "html": "html", "css": "css",
    "scss": "scss", "sass": "sass", "json": "json", "xml": "xml", "yaml": "yaml", "yml": "yaml",
    "md": "markdown", "sh": "bash", "bat": "batch", "sql": "sql", "php": "php", "cpp": "cpp",
    "c": "c", "java": "java", "cs": "csharp", "go": "go", "rs": "rust", "rb": "ruby",
    "swift": "swift", "kt": "kotlin", "svelte": "svelte",
}

class FileInfo(object):
    """
    Metadaten zu einer Datei innerhalb eines Repos.

    Inhalte werden NICHT hier gespeichert, sondern erst in write_reports()
    bei Bedarf aus dem Dateisystem gelesen.
    """

    def __init__(
        self,
        rel_path: str,
        size: int,
        is_text: bool,
        category: str,
        ext: str,
        md5: str,
    ) -> None:
        self.rel_path = rel_path      # Pfad relativ zum Repo-Root (as_posix)
        self.size = size
        self.is_text = is_text
        self.category = category      # config / doc / source / other
        self.ext = ext                # Dateiendung ('.md', '.rs', ...) oder ''
        self.md5 = md5                # MD5 (ggf. eingeschränkt)
        # werden in write_reports per Attribute ergänzt:
        #   .root_label (Repo-Name)
        #   .root_path  (Repo-Root Path)


# ---------------------------------------------------------------------------
# Hub-Erkennung (Hardcode + optionale Overrides)
# ---------------------------------------------------------------------------

def detect_hub_dir(script_path: Path, arg_base_dir: Optional[str] = None) -> Path:
    """
    Liefert das Basisverzeichnis (Hub) für die Repos.

    Priorität:
    1. Umgebungsvariable WC_MERGER_BASEDIR (falls gesetzt & gültig)
    2. HARDCODED_HUB_PATH (dein Pythonista-3-/wc-hub-Ordner in Dateien)
    3. CLI-Argument arg_base_dir (falls gesetzt & gültig)
    4. Fallback: Script-Ordner
    """

    # 1) ENV override (praktisch für Experimente)
    env_base = os.environ.get("WC_MERGER_BASEDIR")
    if env_base:
        p = Path(env_base).expanduser()
        try:
            p = p.resolve()
        except Exception:
            pass
        if p.is_dir():
            return p

    # 2) Hart kodierter Hub-Pfad
    p = Path(HARDCODED_HUB_PATH)
    try:
        p = p.expanduser().resolve()
    except Exception:
        pass
    if p.is_dir():
        return p

    # 3) explizites CLI-Argument
    if arg_base_dir:
        p = Path(arg_base_dir).expanduser()
        try:
            p = p.resolve()
        except Exception:
            pass
        if p.is_dir():
            return p

    # 4) brutaler Fallback: Script-Ordner
    return script_path.parent


def get_merges_dir(hub: Path) -> Path:
    """
    Liefert das 'merges'-Verzeichnis innerhalb des Hubs:

      wc-hub/
        merges/
          ...

    So landen alle Reports direkt im Dateien-Ordner neben deinen Repos.
    """
    merges = hub / MERGES_DIR_NAME
    merges.mkdir(parents=True, exist_ok=True)
    return merges


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def human_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    for u in units:
        if f < 1024.0 or u == units[-1]:
            return f"{f:.1f} {u}"
        f /= 1024.0
    return f"{n} B"


def compute_md5(path: Path, limit_bytes: Optional[int] = None) -> str:
    """
    MD5-Hash über die Datei. limit_bytes=None => komplette Datei.
    """
    h = hashlib.md5()
    read_bytes = 0
    chunk_size = 64 * 1024
    try:
        with path.open("rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                read_bytes += len(chunk)
                if limit_bytes is not None and read_bytes > limit_bytes:
                    chunk = chunk[: max(0, limit_bytes - (read_bytes - len(chunk)))]
                if not chunk:
                    break
                h.update(chunk)
                if limit_bytes is not None and read_bytes >= limit_bytes:
                    break
    except OSError:
        return "ERROR"
    return h.hexdigest()


def _normalize_ext_list(ext_text: str) -> List[str]:
    """
    '.md,.yml , rs' -> ['.md', '.yml', '.rs']
    Leerer String => leere Liste (kein Filter).
    """
    if not ext_text:
        return []
    parts = [p.strip() for p in ext_text.split(",")]
    cleaned: List[str] = []
    for p in parts:
        if not p:
            continue
        if not p.startswith("."):
            p = "." + p
        cleaned.append(p.lower())
    return cleaned


def is_probably_text(path: Path, size: int) -> bool:
    """
    Heuristik: Ist dies eher eine Textdatei?

    - bekannte Text-Endungen -> True
    - große unbekannte Dateien -> eher False
    - ansonsten: 4 KiB lesen, auf NUL-Bytes prüfen.
    """
    name = path.name.lower()
    base, ext = os.path.splitext(name)
    if ext in TEXT_EXTENSIONS or name in TEXT_EXTENSIONS:
        return True

    # sehr große unbekannte Dateien eher als binär behandeln
    if size > 20 * 1024 * 1024:  # 20 MiB
        return False

    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
    except OSError:
        return False

    if not chunk:
        return True
    if b"\x00" in chunk:
        return False

    return True


def classify_category(rel_path: Path, ext: str) -> str:
    """
    Grobe Einteilung in doc / config / source / other.
    """
    name = rel_path.name
    if name in CONFIG_FILENAMES:
        return "config"
    if ext in DOC_EXTENSIONS:
        return "doc"
    if ext in SOURCE_EXTENSIONS:
        return "source"

    parts = [p.lower() for p in rel_path.parts]
    for p in parts:
        if p in ("config", "configs", "settings", "etc", ".github"):
            return "config"
    if "docs" in parts or "doc" in parts:
        return "doc"
    return "other"


def summarize_extensions(file_infos: List[FileInfo]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Anzahl und Gesamtgröße pro Dateiendung.
    """
    counts: Dict[str, int] = {}
    sizes: Dict[str, int] = {}
    for fi in file_infos:
        ext = fi.ext or "<none>"
        counts[ext] = counts.get(ext, 0) + 1
        sizes[ext] = sizes.get(ext, 0) + fi.size
    return counts, sizes


def summarize_categories(file_infos: List[FileInfo]) -> Dict[str, Tuple[int, int]]:
    """
    Anzahl und Gesamtgröße pro Kategorie.
    """
    stats: Dict[str, Tuple[int, int]] = {}
    for fi in file_infos:
        cat = fi.category or "other"
        cnt, sz = stats.get(cat, (0, 0))
        stats[cat] = (cnt + 1, sz + fi.size)
    return stats


def build_tree(file_infos: List[FileInfo]) -> str:
    """
    Erzeugt eine einfache Baumdarstellung pro Root.
    Erwartung: file_infos haben .root_label und .rel_path.
    """
    by_root: Dict[str, List[Path]] = {}
    for fi in file_infos:
        root = getattr(fi, "root_label", "?")
        rel = Path(fi.rel_path)
        by_root.setdefault(root, []).append(rel)

    lines: List[str] = ["```"]
    for root in sorted(by_root.keys()):
        rels = by_root[root]
        lines.append(f"📁 {root}/")

        tree: Dict[str, Dict] = {}
        for r in rels:
            parts = list(r.parts)
            node = tree
            for p in parts:
                if p not in node:
                    node[p] = {}
                node = node[p]

        def walk(node: Dict[str, Dict], indent: str) -> None:
            dirs = []
            files = []
            for k, v in node.items():
                if v:
                    dirs.append(k)
                else:
                    files.append(k)
            for d in sorted(dirs):
                lines.append(f"{indent}📁 {d}/")
                walk(node[d], indent + "    ")
            for f in sorted(files):
                lines.append(f"{indent}📄 {f}")

        walk(tree, "    ")

    lines.append("```")
    return "\n".join(lines)


def lang_for(ext: str) -> str:
    """Ermittelt die Sprache für Markdown-Blöcke anhand der Endung."""
    return LANG_MAP.get(ext.lower().lstrip("."), "")


# ---------------------------------------------------------------------------
# Repo-Scan
# ---------------------------------------------------------------------------

def scan_repo(
    repo_root: Path,
    extensions: Optional[List[str]],
    path_contains: Optional[str],
    max_bytes: int,
) -> Dict:
    """
    Scannt ein Repo und liefert:
    {
      "root": Path,
      "files": List[FileInfo],
      "total_files": int,
      "total_bytes": int,
      "ext_hist": Dict[str,int],
      "max_file": Optional[str],
      "max_file_size": int,
    }

    - extensions = []  => kein Extension-Filter, volle repomerger-Heuristik
    - extensions != [] => nur diese Endungen werden berücksichtigt
    - path_contains    => einfacher Substring-Filter auf dem relativen Pfad
    """
    repo_root = repo_root.resolve()

    if extensions:
        ext_filter = set(e.lower() for e in extensions)
    else:
        ext_filter = None

    if path_contains:
        path_filter = path_contains.strip()
    else:
        path_filter = None

    files: List[FileInfo] = []
    total_files = 0
    total_bytes = 0
    ext_hist: Dict[str, int] = {}
    max_file_size = 0
    max_file: Optional[str] = None

    for dirpath, dirnames, filenames in os.walk(str(repo_root)):
        # Verzeichnisse filtern
        keep_dirs = []
        for d in dirnames:
            if d in SKIP_DIRS:
                continue
            keep_dirs.append(d)
        dirnames[:] = keep_dirs

        for fn in filenames:
            if fn in SKIP_FILES:
                continue

            # .env und .env.* ignorieren, außer expliziten Vorlagen
            if fn.startswith(".env") and fn not in (".env.example", ".env.template", ".env.sample"):
                continue

            abs_path = Path(dirpath) / fn
            try:
                st = abs_path.stat()
            except OSError:
                continue

            size = st.st_size
            rel = abs_path.relative_to(repo_root)
            rel_str = rel.as_posix()

            # Pfadfilter
            if path_filter and path_filter not in rel_str:
                continue

            ext = abs_path.suffix.lower()

            # Extension-Filter (falls explizit gesetzt)
            if ext_filter is not None and ext not in ext_filter:
                continue

            total_files += 1
            total_bytes += size

            # Extension-Statistik
            ext_hist[ext] = ext_hist.get(ext, 0) + 1

            # größte Datei
            if size > max_file_size:
                max_file_size = size
                max_file = rel_str

            is_text = is_probably_text(abs_path, size)

            # Für Textdateien MD5 bis max_bytes, sonst leer
            if is_text or size <= max_bytes:
                md5 = compute_md5(abs_path, max_bytes)
            else:
                md5 = ""

            category = classify_category(rel, ext)
            fi = FileInfo(
                rel_path=rel_str,
                size=size,
                is_text=is_text,
                category=category,
                ext=ext,
                md5=md5,
            )
            files.append(fi)

    files.sort(key=lambda fi: fi.rel_path)

    return {
        "root": repo_root,
        "files": files,
        "total_files": total_files,
        "total_bytes": total_bytes,
        "ext_hist": ext_hist,
        "max_file": max_file,
        "max_file_size": max_file_size,
    }


def make_output_filename(
    merges_dir: Path,
    repo_names: List[str],
    mode: str,
    detail: str,
) -> Path:
    ts = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    if not repo_names:
        base = "no-repos"
    else:
        base = "+".join(repo_names)
        if len(base) > 40:
            base = base[:37] + "..."
    fname = "merge_{mode}_{base}_{detail}_{ts}.md".format(
        mode=mode, base=base, detail=detail, ts=ts
    )
    return merges_dir / fname


# ---------------------------------------------------------------------------
# Report-Erzeugung (repomerger-Style)
# ---------------------------------------------------------------------------

def _write_single_report(
    out_path: Path,
    hub: Path,
    files: List[FileInfo],
    repo_names: List[str],
    detail: str,
    max_bytes: int,
    plan_only: bool,
) -> None:
    """
    Erzeugt einen einzelnen Bericht (entweder für alle Repos oder für ein Repo).
    """
    if not files:
        return

    # detail -> Level-Logik wie im repomerger
    if detail == "overview":
        level = "overview"
    elif detail == "summary":
        level = "summary"
    else:
        level = "full"

    now = datetime.datetime.now()

    total_size = sum(fi.size for fi in files)
    text_files = [fi for fi in files if fi.is_text]
    binary_files = [fi for fi in files if not fi.is_text]

    if level == "overview":
        planned_with_content = 0
    elif level == "summary":
        planned_with_content = sum(
            1 for fi in text_files if fi.size <= max_bytes
        )
    else:  # full
        planned_with_content = len(text_files)

    ext_counts, ext_sizes = summarize_extensions(files)
    cat_stats = summarize_categories(files)

    lines: List[str] = []

    # Header & Hinweise
    if len(repo_names) == 1:
        lines.append(f"# WC-Merge-Bericht für `{repo_names[0]}`")
    else:
        lines.append("# WC-Merge-Bericht (kombiniert)")
    lines.append("")
    lines.append(f"- Zeitpunkt: `{now.strftime('%Y-%m-%d %H:%M:%S')}`")
    lines.append(f"- Hub: `{hub}`")
    lines.append(
        "- Repos: {}".format(
            ", ".join(f"`{n}`" for n in sorted(set(repo_names)))
        )
    )
    lines.append(f"- Detailstufe: `{detail}`")
    lines.append(f"- Plan only: `{'ja' if plan_only else 'nein'}`")
    lines.append(f"- Max Bytes/File: `{max_bytes}`")
    lines.append("")
    lines.append("> Hinweis für KIs:")
    lines.append("> - Dies ist ein Schnappschuss des Dateisystems, keine Git-Historie.")
    lines.append("> - Baumansicht: `## 📁 Struktur`.")
    lines.append("> - Manifest: `## 🧾 Manifest`.")
    if level == "overview":
        lines.append("> - In dieser Detailstufe werden keine Dateiinhalte eingebettet.")
    elif level == "summary":
        lines.append("> - Inhalte kleiner Textdateien werden eingebettet;")
        lines.append(">   größere erscheinen nur im Manifest.")
    else:
        lines.append("> - Inhalte aller Textdateien werden eingebettet;")
        lines.append(">   große Dateien werden nach einer Byte-Grenze gekürzt.")
    lines.append("> - `.env`-ähnliche Dateien werden gefiltert; sensible Daten können trotzdem")
    lines.append(">   in anderen Textdateien vorkommen. Merge nicht als öffentlichen Dump nutzen.")
    lines.append("")

    # Plan
    lines.append("## 🧮 Plan")
    lines.append("")
    lines.append(f"- Gefundene Dateien gesamt: **{len(files)}**")
    lines.append(f"- Davon Textdateien: **{len(text_files)}**")
    lines.append(f"- Davon Binärdateien: **{len(binary_files)}**")
    lines.append(f"- Geplante Dateien mit Inhalteinbettung: **{planned_with_content}**")
    lines.append(f"- Gesamtgröße der Quellen: **{human_size(total_size)}**")
    if any(fi.size > max_bytes for fi in text_files):
        lines.append(
            "- Hinweis: Textdateien größer als {} werden abhängig von der Detailstufe "
            "gekürzt oder nur im Manifest aufgeführt.".format(human_size(max_bytes))
        )
    lines.append("")

    if cat_stats:
        lines.append("**Dateien nach Kategorien:**")
        lines.append("")
        lines.append("| Kategorie | Dateien | Gesamtgröße |")
        lines.append("| --- | ---: | ---: |")
        for cat in sorted(cat_stats.keys()):
            cnt, sz = cat_stats[cat]
            lines.append(
                "| `{}` | {} | {} |".format(cat, cnt, human_size(sz))
            )
        lines.append("")

    if ext_counts:
        lines.append("**Grobe Statistik nach Dateiendungen:**")
        lines.append("")
        lines.append("| Ext | Dateien | Gesamtgröße |")
        lines.append("| --- | ---: | ---: |")
        for ext in sorted(ext_counts.keys()):
            lines.append(
                "| `{}` | {} | {} |".format(
                    ext, ext_counts[ext], human_size(ext_sizes[ext])
                )
            )
        lines.append("")

    lines.append(
        "Jeder wc-merge-Lauf ist ein eigenständiger Schnappschuss – "
        "keine Diffs zu früheren Läufen."
    )
    lines.append("")

    if plan_only:
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return

    # Struktur
    lines.append("## 📁 Struktur")
    lines.append("")
    lines.append(build_tree(files))
    lines.append("")

    # Manifest
    lines.append("## 🧾 Manifest")
    lines.append("")
    lines.append("| Root | Pfad | Kategorie | Text | Größe | MD5 |")
    lines.append("| --- | --- | --- | --- | ---: | --- |")
    for fi in files:
        root_label = getattr(fi, "root_label", "?")
        lines.append(
            "| `{}` | `{}` | `{}` | {} | {} | `{}` |".format(
                root_label,
                fi.rel_path,
                fi.category,
                "ja" if fi.is_text else "nein",
                human_size(fi.size),
                fi.md5,
            )
        )
    lines.append("")

    # Inhalte
    if level != "overview":
        lines.append("## 📄 Dateiinhalte")
        lines.append("")
        # Nach Root + Pfad gruppiert, damit es halbwegs sortiert aussieht
        files_sorted = sorted(
            files, key=lambda fi: (getattr(fi, "root_label", ""), fi.rel_path)
        )
        for fi in files_sorted:
            if not fi.is_text:
                continue

            if level == "summary" and fi.size > max_bytes:
                continue

            root_label = getattr(fi, "root_label", "?")
            root_path: Path = getattr(fi, "root_path")
            abs_path = root_path / fi.rel_path

            lines.append(f"### `{root_label}/{fi.rel_path}`")
            lines.append("")
            if fi.size > max_bytes and level == "full":
                lines.append(
                    "**Hinweis:** Datei ist größer als {} – es wird nur ein Ausschnitt "
                    "bis zu dieser Grenze gezeigt.".format(human_size(max_bytes))
                )
                lines.append("")

            try:
                if fi.size > max_bytes and level == "full":
                    # begrenztes Einlesen
                    remaining = max_bytes
                    collected: List[str] = []
                    with abs_path.open("r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            encoded = line.encode("utf-8", errors="replace")
                            if remaining <= 0:
                                break
                            if len(encoded) > remaining:
                                part = encoded[:remaining].decode(
                                    "utf-8", errors="replace"
                                )
                                collected.append(part + "\n[... gekürzt ...]\n")
                                remaining = 0
                                break
                            collected.append(line)
                            remaining -= len(encoded)
                    content = "".join(collected)
                else:
                    content = abs_path.read_text(
                        encoding="utf-8", errors="replace"
                    )
            except OSError as e:
                lines.append(f"_Fehler beim Lesen der Datei: {e}_")
                lines.append("")
                continue

            lang = lang_for(fi.ext)
            lines.append(f"```{lang}")
            lines.append(content.rstrip("\n"))
            lines.append("```")
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_reports(
    merges_dir: Path,
    hub: Path,
    repo_summaries: List[Dict],
    detail: str,
    mode: str,
    max_bytes: int,
    plan_only: bool,
) -> List[Path]:
    """
    Schreibt einen oder mehrere Markdown-Berichte und liefert die Pfade
    zu den erzeugten Dateien zurück.

    - mode == "gesamt"  -> ein kombinierter Bericht über alle Repos
    - mode == "pro-repo" -> ein Bericht pro Repo
    """
    if not repo_summaries:
        return []

    # Alle FileInfos mit Root-Infos anreichern
    all_files: List[FileInfo] = []
    for summary in repo_summaries:
        root_path: Path = summary["root"]
        repo_name = summary.get("name", root_path.name)
        for fi in summary["files"]:
            fi.root_label = repo_name
            fi.root_path = root_path
            all_files.append(fi)

    if not all_files:
        return []

    out_paths: List[Path] = []

    if mode == "gesamt":
        repo_names = sorted(
            {summary.get("name", summary["root"].name) for summary in repo_summaries}
        )
        out_path = make_output_filename(merges_dir, repo_names, mode, detail)
        _write_single_report(
            out_path=out_path,
            hub=hub,
            files=all_files,
            repo_names=repo_names,
            detail=detail,
            max_bytes=max_bytes,
            plan_only=plan_only,
        )
        out_paths.append(out_path)
        return out_paths

    # mode == "pro-repo"
    files_by_repo: Dict[str, List[FileInfo]] = {}
    for fi in all_files:
        repo_name = getattr(fi, "root_label", "?")
        files_by_repo.setdefault(repo_name, []).append(fi)

    for repo_name, files in sorted(files_by_repo.items(), key=lambda kv: kv[0]):
        out_path = make_output_filename(merges_dir, [repo_name], mode, detail)
        _write_single_report(
            out_path=out_path,
            hub=hub,
            files=files,
            repo_names=[repo_name],
            detail=detail,
            max_bytes=max_bytes,
            plan_only=plan_only,
        )
        out_paths.append(out_path)

    return out_paths
