# WC-Merge Report (Part 2/3)

<a id="file-test-f2-py"></a>
### `f2.py`
- Category: source
- Tags: -
- Size: 48.59 KB
- Included: full
- MD5: md5

```python
# -*- coding: utf-8 -*-

"""
merge_core – Core functions for wc-merger (v2.3 Standard).
Implements AI-friendly formatting, tagging, and strict Pflichtenheft structure.
"""

import os
import sys
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Iterator, NamedTuple
from dataclasses import dataclass, asdict

# --- Configuration & Heuristics ---

SPEC_VERSION = "2.3"
MERGES_DIR_NAME = "merges"

# Formale Contract-Deklaration für alle wc-merger-Reports.
# Name/Version können von nachgelagerten Tools verwendet werden,
# um das Format eindeutig zu erkennen.
MERGE_CONTRACT_NAME = "wc-merge-report"
MERGE_CONTRACT_VERSION = SPEC_VERSION

# Ab v2.3+: 0 = "kein Limit pro Datei".
# max_file_bytes wirkt nur noch als optionales Soft-Limit / Hint,
# nicht mehr als harte Abschneide-Grenze. Große Dateien werden
# vollständig gelesen und nur über die Split-Logik in Parts verteilt.
DEFAULT_MAX_BYTES = 0

# Debug-Config (kann später bei Bedarf erweitert werden)
ALLOWED_CATEGORIES = {"source", "test", "doc", "config", "contract", "other"}
ALLOWED_TAGS = {
    "ai-context",
    "runbook",
    "lockfile",
    "script",
    "ci",
    "adr",
    "feed",
    "wgx-profile",
}

# Directories to ignore
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
    ".mypy_cache",
    "coverage",
}

# Top-level roots to skip in auto-discovery
SKIP_ROOTS = {
    MERGES_DIR_NAME,
    "merge",
    "output",
    "out",
}

# Individual files to ignore
SKIP_FILES = {
    ".DS_Store",
    "thumbs.db",
}

# Extensions considered text (broadened)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".rst", ".py", ".rs", ".ts", ".tsx", ".js", ".jsx",
    ".json", ".jsonl", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".sh", ".bash", ".zsh", ".fish", ".dockerfile", "dockerfile",
    ".svelte", ".css", ".scss", ".html", ".htm", ".xml", ".csv", ".log",
    ".lock", ".bats", ".properties", ".gradle", ".groovy", ".kt", ".kts",
    ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rb", ".php", ".pl",
    ".lua", ".sql", ".bat", ".cmd", ".ps1", ".make", "makefile", "justfile",
    ".tf", ".hcl", ".gitignore", ".gitattributes", ".editorconfig", ".cs",
    ".swift", ".adoc", ".ai-context"
}


# --- Debug-Kollektor -------------------------------------------------------

class DebugItem(NamedTuple):
    level: str   # "info", "warn", "error"
    code: str    # z. B. "tag-unknown"
    context: str # kurzer Pfad oder Repo-Name
    message: str # Menschentext


@dataclass
class ExtrasConfig:
    health: bool = False
    organism_index: bool = False
    fleet_panorama: bool = False
    augment_sidecar: bool = False
    delta_reports: bool = False

    @classmethod
    def none(cls):
        return cls()


class DebugCollector:
    """Sammelt Debug-Infos für optionale Report-Sektionen."""

    def __init__(self) -> None:
        self._items: List[DebugItem] = []

    @property
    def items(self) -> List[DebugItem]:
        return list(self._items)

    def info(self, code: str, context: str, msg: str) -> None:
        self._items.append(DebugItem("info", code, context, msg))

    def warn(self, code: str, context: str, msg: str) -> None:
        self._items.append(DebugItem("warn", code, context, msg))

    def error(self, code: str, context: str, msg: str) -> None:
        self._items.append(DebugItem("error", code, context, msg))

    def has_items(self) -> bool:
        return bool(self._items)

    def render_markdown(self) -> str:
        """Erzeugt eine optionale ## Debug-Sektion als Markdown-Tabelle."""
        if not self._items:
            return ""
        lines: List[str] = []
        lines.append("<!-- @debug:start -->")
        lines.append("## Debug")
        lines.append("")
        lines.append("| Level | Code | Kontext | Hinweis |")
        lines.append("|-------|------|---------|---------|")
        for it in self._items:
            lines.append(
                f"| {it.level} | `{it.code}` | `{it.context}` | {it.message} |"
            )
        lines.append("")
        lines.append("<!-- @debug:end -->")
        lines.append("")
        return "\n".join(lines)


def run_debug_checks(file_infos: List["FileInfo"], debug: DebugCollector) -> None:
    """
    Leichte, rein lesende Debug-Checks auf Basis der FileInfos.
    Verändert keine Merge-Logik, liefert nur Hinweise.
    """
    # 1. Unbekannte Kategorien / Tags
    for fi in file_infos:
        ctx = f"{fi.root_label}/{fi.rel_path.as_posix()}"
        cat = fi.category or "other"
        if cat not in ALLOWED_CATEGORIES:
            debug.warn(
                "category-unknown",
                ctx,
                f"Unbekannte Kategorie '{cat}' – erwartet sind {sorted(ALLOWED_CATEGORIES)}.",
            )
        for tag in getattr(fi, "tags", []) or []:
            if tag not in ALLOWED_TAGS:
                debug.warn(
                    "tag-unknown",
                    ctx,
                    f"Tag '{tag}' ist nicht im v2.3-Schema registriert.",
                )

    # 2. Fleet-/Heimgewebe-Checks pro Repo
    per_root: Dict[str, List["FileInfo"]] = {}
    for fi in file_infos:
        per_root.setdefault(fi.root_label, []).append(fi)

    for root, fis in per_root.items():
        # README-Check
        if not any(f.rel_path.name.lower() == "readme.md" for f in fis):
            debug.info(
                "repo-no-readme",
                root,
                "README.md fehlt – Repo ist für KIs schwerer einzuordnen.",
            )
        # WGX-Profil-Check
        if not any(
            ".wgx" in f.rel_path.parts and str(f.rel_path).endswith("profile.yml")
            for f in fis
        ):
            debug.info(
                "repo-no-wgx-profile",
                root,
                "`.wgx/profile.yml` nicht gefunden – Repo ist nicht vollständig Fleet-konform.",
            )


# Directories considered "noise" (build artifacts etc.)
NOISY_DIRECTORIES = ("node_modules/", "dist/", "build/", "target/")

# Standard lockfile names
LOCKFILE_NAMES = {
    "Cargo.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
}

# Files typically considered configuration
CONFIG_FILENAMES = {
    "pyproject.toml", "package.json", "package-lock.json", "pnpm-lock.yaml",
    "Cargo.toml", "Cargo.lock", "requirements.txt", "Pipfile", "Pipfile.lock",
    "poetry.lock", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "Justfile", "Makefile", "toolchain.versions.yml", ".editorconfig",
    ".markdownlint.jsonc", ".markdownlint.yaml", ".yamllint", ".yamllint.yml",
    ".lychee.toml", ".vale.ini", ".pre-commit-config.yaml", ".gitignore",
    ".gitmodules", "tsconfig.json", "babel.config.js", "webpack.config.js",
    "rollup.config.js", "vite.config.js", "vite.config.ts", ".ai-context.yml"
}

# Large generated files or lockfiles that should be summarized in 'dev' profile
SUMMARIZE_FILES = {
    "package-lock.json", "pnpm-lock.yaml", "Cargo.lock", "yarn.lock", "Pipfile.lock", "poetry.lock"
}

DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc"}
SOURCE_EXTENSIONS = {
    ".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".svelte", ".c", ".cpp",
    ".h", ".hpp", ".go", ".java", ".cs", ".rb", ".php", ".swift", ".kt",
    ".sh", ".bash", ".pl", ".lua"
}

LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "html": "html", "css": "css",
    "scss": "scss", "sass": "sass", "json": "json", "xml": "xml", "yaml": "yaml", "yml": "yaml",
    "md": "markdown", "sh": "bash", "bat": "batch", "sql": "sql", "php": "php", "cpp": "cpp",
    "c": "c", "java": "java", "cs": "csharp", "go": "go", "rs": "rust", "rb": "ruby",
    "swift": "swift", "kt": "kotlin", "svelte": "svelte", "toml": "toml", "ini": "ini",
    "dockerfile": "dockerfile", "tf": "hcl", "hcl": "hcl", "bats": "bash", "pl": "perl", "lua": "lua",
    "ai-context": "yaml"
}

HARDCODED_HUB_PATH = (
    "/private/var/mobile/Containers/Data/Application/"
    "B60D0157-973D-489A-AA59-464C3BF6D240/Documents/wc-hub"
)

# Semantische Use-Case-Beschreibung pro Profil.
# Wichtig: das ersetzt NICHT den Repo-Zweck (Declared Purpose),
# sondern ergänzt ihn um die Rolle des aktuellen Merges.
PROFILE_USECASE = {
    "overview": "Tools – Index",
    "summary": "Tools – Doku/Kontext",
    "dev": "Tools – Code/Review Snapshot",
    "max": "Tools – Vollsnapshot",
}

# Mandatory Repository Order for Multi-Repo Merges (v2.1 Spec)
REPO_ORDER = [
    "metarepo",
    "wgx",
    "hausKI",
    "hausKI-audio",
    "heimgeist",
    "chronik",
    "aussensensor",
    "semantAH",
    "leitstand",
    "heimlern",
    "tools",
    "weltgewebe",
    "vault-gewebe",
]

class FileInfo(object):
    """Container for file metadata."""
    def __init__(self, root_label, abs_path, rel_path, size, is_text, md5, category, tags, ext, skipped=False, reason=None, content=None):
        self.root_label = root_label
        self.abs_path = abs_path
        self.rel_path = rel_path
        self.size = size
        self.is_text = is_text
        self.md5 = md5
        self.category = category
        self.tags = tags
        self.ext = ext
        self.skipped = skipped
        self.reason = reason
        self.content = content
        self.anchor = "" # Will be set during report generation


# --- Utilities ---

def is_noise_file(fi: "FileInfo") -> bool:
    """
    Heuristik für 'Noise'-Dateien:
    - offensichtliche Lockfiles / Paketmanager-Artefakte
    - typische Build-/Vendor-Verzeichnisse
    ohne das Manifest-Schema zu verändern – nur das Included-Label wird erweitert.
    """
    try:
        path_str = str(fi.rel_path).replace("\\", "/").lower()
        name = fi.rel_path.name.lower()
    except Exception:
        return False

    noisy_dirs = (
        "node_modules/",
        "dist/",
        "build/",
        "target/",
        "venv/",
        ".venv/",
        "__pycache__/",
    )
    if any(seg in path_str for seg in noisy_dirs):
        return True

    lock_names = {
        "cargo.lock",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "poetry.lock",
        "pipfile.lock",
        "composer.lock",
    }
    if name in lock_names or name.endswith(".lock"):
        return True

    tags_lower = {t.lower() for t in (fi.tags or [])}
    if "lockfile" in tags_lower or "deps" in tags_lower or "vendor" in tags_lower:
        return True

    return False

def detect_hub_dir(script_path: Path, arg_base_dir: Optional[str] = None) -> Path:
    env_base = os.environ.get("WC_MERGER_BASEDIR")
    if env_base:
        p = Path(env_base).expanduser()
        if p.is_dir(): return p

    p = Path(HARDCODED_HUB_PATH)
    try:
        if p.expanduser().is_dir(): return p
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to check hub dir {p}: {e}\n")

    if arg_base_dir:
        p = Path(arg_base_dir).expanduser()
        if p.is_dir(): return p

    return script_path.parent


def get_merges_dir(hub: Path) -> Path:
    merges = hub / MERGES_DIR_NAME
    merges.mkdir(parents=True, exist_ok=True)
    return merges


def human_size(n: float) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0 or unit == "GB":
            return "{0:.2f} {1}".format(size, unit)
        size /= 1024.0
    return "{0:.2f} GB".format(size)


def is_probably_text(path: Path, size: int) -> bool:
    name = path.name.lower()
    base, ext = os.path.splitext(name)
    if ext in TEXT_EXTENSIONS or name in TEXT_EXTENSIONS:
        return True
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


def compute_md5(path: Path, limit_bytes: Optional[int] = None) -> str:
    h = hashlib.md5()
    try:
        with path.open("rb") as f:
            remaining = limit_bytes
            while True:
                if remaining is None:
                    chunk = f.read(65536)
                else:
                    chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                h.update(chunk)
                if remaining is not None:
                    remaining -= len(chunk)
                    if remaining <= 0:
                        break
        return h.hexdigest()
    except OSError:
        return "ERROR"


def lang_for(ext: str) -> str:
    return LANG_MAP.get(ext.lower().lstrip("."), "")


def get_repo_sort_index(repo_name: str) -> int:
    """Returns sort index for repo based on REPO_ORDER."""
    try:
        return REPO_ORDER.index(repo_name)
    except ValueError:
        return 999  # Put undefined repos at the end

def extract_purpose(repo_root: Path) -> str:
    """Safe purpose extraction from README or docs/intro.md. No guessing."""
    candidates = ["README.md", "README", "docs/intro.md"]
    for c in candidates:
        p = repo_root / c
        if p.exists():
            try:
                # Read text safely
                with p.open("r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read().strip()
                    # First paragraph is content until double newline
                    first = txt.split("\n\n")[0].strip()
                    # Markdown-Überschrift (#, ##, …) vorne abschneiden
                    first = first.lstrip("#").strip()
                    return first
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to extract purpose from {p}: {e}\n")
                return ""
    return ""

def get_declared_purpose(files: List[FileInfo]) -> str:
    # Deprecated in favor of extract_purpose for consistency with Spec v2.3 patch D logic
    # But kept as fallback or to support .ai-context which spec patch D didn't mention explicitly
    # but patch D implemented it as:
    # try: purpose = extract_purpose(sources[0]); ...
    return "(none)" # Handled in iter_report_blocks via extract_purpose


def classify_file_v2(rel_path: Path, ext: str) -> Tuple[str, List[str]]:
    """
    Returns (category, tags).
    Strict Pattern Matching based on v2.1 Spec.
    """
    parts = list(rel_path.parts)
    name = rel_path.name.lower()
    tags = []

    # Tag Patterns - Strict match
    # KI-Kontext-Dateien
    if name.endswith(".ai-context.yml"):
        tags.append("ai-context")

    # CI-Workflows
    if ".github" in parts and "workflows" in parts and ext in [".yml", ".yaml"]:
        tags.append("ci")

    # Contracts:
    # Nur als Kategorie, nicht mehr als Tag – Spec sieht kein 'contract'-Tag vor.
    # (Die Zuordnung passiert weiter unten über die Category-Logik.)

    if "docs" in parts and "adr" in parts and ext == ".md":
        tags.append("adr")
    if name.startswith("runbook") and ext == ".md":
        tags.append("runbook")

    # Skripte: Shell und Python unter scripts/ oder bin/ als 'script' markieren
    if (("scripts" in parts) or ("bin" in parts)) and ext in (".sh", ".py"):
        tags.append("script")

    if "export" in parts and ext == ".jsonl":
        tags.append("feed")

    # Lockfiles (package-lock, Cargo.lock, pnpm-lock, etc.)
    if "lock" in name:
        tags.append("lockfile")

    # README: Spec-konform als KI-Kontext markieren, kein eigener 'readme'-Tag
    if name == "readme.md":
        tags.append("ai-context")

    # WGX-Profile
    if ".wgx" in parts and name.startswith("profile"):
        tags.append("wgx-profile")


    # Determine Category - Strict Logic
    # Category ∈ {source, test, doc, config, contract, other}
    category = "other"

    # Order matters: check more specific first
    if name in CONFIG_FILENAMES or "config" in parts or ".github" in parts or ".wgx" in parts or ext in [".toml", ".yaml", ".yml", ".json", ".lock"]:
         # Note: .json could be contract or config, check contract path
         if "contracts" in parts:
             category = "contract"
         else:
             category = "config"
    elif ext in DOC_EXTENSIONS or "docs" in parts:
        category = "doc"
    elif "contracts" in parts: # Fallback if not caught above
        category = "contract"
    elif "tests" in parts or "test" in parts or name.endswith("_test.py") or name.startswith("test_"):
        category = "test"
    elif ext in SOURCE_EXTENSIONS or "src" in parts or "crates" in parts or "scripts" in parts:
        category = "source"

    return category, tags


def _normalize_ext_list(ext_text: str) -> List[str]:
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


# --- Repo Scan Logic ---

def scan_repo(repo_root: Path, extensions: Optional[List[str]] = None, path_contains: Optional[str] = None, max_bytes: int = DEFAULT_MAX_BYTES) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    root_label = repo_root.name
    files = []

    ext_filter = set(e.lower() for e in extensions) if extensions else None
    path_filter = path_contains.strip() if path_contains else None

    total_files = 0
    total_bytes = 0
    ext_hist: Dict[str, int] = {}

    for dirpath, dirnames, filenames in os.walk(str(repo_root)):
        # Filter directories
        keep_dirs = []
        for d in dirnames:
            if d in SKIP_DIRS:
                continue
            keep_dirs.append(d)
        dirnames[:] = keep_dirs

        for fn in filenames:
            if fn in SKIP_FILES:
                continue
            if fn.startswith(".env") and fn not in (".env.example", ".env.template", ".env.sample"):
                continue

            abs_path = Path(dirpath) / fn
            try:
                rel_path = abs_path.relative_to(repo_root)
            except ValueError:
                continue

            rel_path_str = rel_path.as_posix()
            if path_filter and path_filter not in rel_path_str:
                continue

            ext = abs_path.suffix.lower()
            if ext_filter is not None and ext not in ext_filter:
                continue

            try:
                st = abs_path.stat()
            except OSError:
                continue

            size = st.st_size
            total_files += 1
            total_bytes += size
            ext_hist[ext] = ext_hist.get(ext, 0) + 1

            is_text = is_probably_text(abs_path, size)
            category, tags = classify_file_v2(rel_path, ext)

            # MD5 calculation:
            # - Textdateien: immer kompletter MD5
            # - Binärdateien: nur, falls ein positives Limit gesetzt ist
            #   und die Datei kleiner/gleich diesem Limit ist.
            md5 = ""
            # 0 oder <0 = "kein Limit" → komplette Textdateien hashen
            limit_bytes: Optional[int] = max_bytes if max_bytes and max_bytes > 0 else None
            if is_text:
                md5 = compute_md5(abs_path, limit_bytes)
            else:
                if limit_bytes is not None and size <= limit_bytes:
                    md5 = compute_md5(abs_path, limit_bytes)

            fi = FileInfo(
                root_label=root_label,
                abs_path=abs_path,
                rel_path=rel_path,
                size=size,
                is_text=is_text,
                md5=md5,
                category=category,
                tags=tags,
                ext=ext
            )
            files.append(fi)

    # Sort files: first by repo order (if multi-repo context handled outside,
    # but here root_label is constant per scan_repo call unless we merge lists later),
    # then by path.
    files.sort(key=lambda fi: str(fi.rel_path).lower())

    return {
        "root": repo_root,
        "name": root_label,
        "files": files,
        "total_files": total_files,
        "total_bytes": total_bytes,
        "ext_hist": ext_hist,
    }

def get_repo_snapshot(repo_root: Path) -> Dict[str, Tuple[int, str, str]]:
    """
    Liefert einen Snapshot des Repos für Diff-Zwecke.

    Rückgabe:
      Dict[rel_path] -> (size, md5, category)

    Wichtig:
      - nutzt scan_repo, d. h. dieselben Ignore-Regeln wie der Merger
      - Category stammt direkt aus classify_file_v2 und ist damit
        kompatibel zum Manifest (source/doc/config/test/contract/ci/other)
    """
    snapshot: Dict[str, Tuple[int, str, str]] = {}
    summary = scan_repo(
        repo_root, extensions=None, path_contains=None, max_bytes=100_000_000
    )  # großes Limit, damit wir verlässliche MD5s haben
    for fi in summary["files"]:
        snapshot[fi.rel_path.as_posix()] = (fi.size, fi.md5, fi.category or "other")
    return snapshot


# --- Reporting Logic V2 ---

def summarize_categories(file_infos: List[FileInfo]) -> Dict[str, List[int]]:
    stats: Dict[str, List[int]] = {}
    for fi in file_infos:
        cat = fi.category or "other"
        if cat not in stats:
            stats[cat] = [0, 0]
        stats[cat][0] += 1
        stats[cat][1] += fi.size
    return stats

def build_tree(file_infos: List[FileInfo]) -> str:
    by_root: Dict[str, List[Path]] = {}

    # Sort roots first
    sorted_files = sorted(file_infos, key=lambda fi: (get_repo_sort_index(fi.root_label), fi.root_label.lower()))

    for fi in sorted_files:
        by_root.setdefault(fi.root_label, []).append(fi.rel_path)

    lines = ["```"]
    # Keys are already sorted by insertion order in py3.7+, which matches our sorted_files loop,
    # but let's be safe and sort keys based on REPO_ORDER.
    sorted_roots = sorted(by_root.keys(), key=lambda r: (get_repo_sort_index(r), r.lower()))

    for root in sorted_roots:
        rels = by_root[root]
        lines.append(f"📁 {root}/")

        tree: Dict[str, Any] = {}
        for r in rels:
            parts = list(r.parts)
            node = tree
            for p in parts:
                if p not in node:
                    node[p] = {}
                node = node[p]

        def walk(node, indent, root_lbl):
            dirs = []
            files = []
            for k, v in node.items():
                if v:
                    dirs.append(k)
                else:
                    files.append(k)
            for d in sorted(dirs):
                lines.append(f"{indent}📁 {d}/")
                walk(node[d], indent + "    ", root_lbl)
            for f in sorted(files):
                # Optional: Hyperlinking in Tree
                # Needs rel path reconstruction which is tricky in this recursive walk without passing it down
                # For v2.3 Spec 6.3: 📄 [filename](#file-…)
                # We need to construct the full relative path to generate the anchor.
                # Since we don't pass the path down easily here, let's skip tree linking for this iteration
                # to keep it robust, or do a simple approximation if needed.
                # Actually, we can use a lookup if we want, but "optional" in spec allows skipping.
                # Let's stick to plain text for now to avoid complexity in build_tree.
                lines.append(f"{indent}📄 {f}")

        walk(tree, "    ", root)
    lines.append("```")
    return "\n".join(lines)

def make_output_filename(merges_dir: Path, repo_names: List[str], mode: str, detail: str, part: Optional[int] = None) -> Path:
    # Zeitstempel ohne Sekunden, damit die Namen ruhiger werden
    ts = datetime.datetime.now().strftime("%y%m%d-%H%M")
    base = "+".join(repo_names) if repo_names else "no-repos"
    if len(base) > 40:
        base = base[:37] + "..."
    base = base.replace(" ", "-").replace("/", "_")

    part_suffix = f"_part{part}" if part else ""
    # Neues Schema:
    #   <repos>_<detail>_<mode>_<YYMMDD-HHMM>[_partX]_merge.md
    # Beispiel:
    #   hausKI+wgx_dev_multi_251205-1457_merge.md
    return merges_dir / f"{base}_{detail}_{mode}_{ts}{part_suffix}_merge.md"

def read_smart_content(fi: FileInfo, max_bytes: int, encoding="utf-8") -> Tuple[str, bool, str]:
    """
    Reads content.
    Returns (content, truncated, truncation_msg).
    Truncation is disabled in v2.3+ per user request (files are split across parts if needed).
    max_bytes is ignored here, effectively reading the full file.
    """
    try:
        with fi.abs_path.open("r", encoding=encoding, errors="replace") as f:
            return f.read(), False, ""
    except OSError as e:
        return f"_Error reading file: {e}_", False, ""

def is_priority_file(fi: FileInfo) -> bool:
    if "ai-context" in fi.tags: return True
    if "runbook" in fi.tags: return True
    if fi.rel_path.name.lower() == "readme.md": return True
    return False

def check_fleet_consistency(files: List[FileInfo]) -> List[str]:
    """
    Checks for objective inconsistencies specified in the spec.
    """
    warnings = []

    # Check for hausKI casing
    roots = set(f.root_label for f in files)

    # Check for missing .wgx/profile.yml in repos
    for root in roots:
        has_profile = any(f.root_label == root and "wgx-profile" in f.tags for f in files)
        if not has_profile:
             if root in REPO_ORDER:
                 warnings.append(f"- {root}: missing .wgx/profile.yml")

    return warnings

def validate_report_structure(report: str):
    """Checks if report follows Spec v2.3 structure."""
    required = [
        "## Source & Profile",
        "## Profile Description",
        "## Reading Plan",
        "## Plan",
        "## 📁 Structure",
        "## 🧾 Manifest",
        "## 📄 Content",
    ]

    positions = []
    for sec in required:
        pos = report.find(sec)
        if pos == -1:
            raise ValueError(f"Missing section: {sec}")
        positions.append(pos)

    # enforce ordering
    if positions != sorted(positions):
        raise ValueError("Section ordering does not match Spec v2.3")

    # ensure Manifest has anchor
    if "{#manifest}" not in report:
        raise ValueError("Manifest missing required anchor {#manifest}")

def iter_report_blocks(
    files: List[FileInfo],
    level: str,
    max_file_bytes: int,
    sources: List[Path],
    plan_only: bool,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
) -> Iterator[str]:
    if extras is None:
        extras = ExtrasConfig.none()

    # UTC Timestamp
    now = datetime.datetime.utcnow()

    # Sort files according to strict multi-repo order and then path
    files.sort(key=lambda fi: (get_repo_sort_index(fi.root_label), fi.root_label.lower(), str(fi.rel_path).lower()))

    # Pre-calculate status based on Profile Strict Logic
    processed_files = []

    unknown_categories = set()
    unknown_tags = set()
    files_missing_anchor = []

    for fi in files:
        # Generate deterministic anchor
        rel_id = fi.rel_path.as_posix().replace("/", "-").replace(".", "-")
        anchor = f"file-{fi.root_label}-{rel_id}"
        fi.anchor = anchor

        # Debug checks
        # Kategorien strikt gemäß Spec v2.3:
        # {source, doc, config, test, contract, other}
        if fi.category == "other" or fi.category not in ["source", "doc", "config", "test", "contract", "other"]:
            unknown_categories.add(fi.category)

        status = "omitted"
        if fi.is_text:
            if level == "overview":
                if is_priority_file(fi):
                    status = "full"
                else:
                    status = "meta-only"
            elif level == "summary":
                # Summary: Dokumentation und Konfiguration voll,
                # Code/Test eher manifest-orientiert – außer Prioritätsdateien.
                if fi.category in ["doc", "config", "contract", "ci"] or "ai-context" in fi.tags or "wgx-profile" in fi.tags:
                    status = "full"
                elif fi.category in ["source", "test"]:
                    if is_priority_file(fi):
                        status = "full"
                    else:
                        status = "meta-only"
                else:
                    # Fallback: wie overview – wichtiges voll, Rest meta-only
                    if is_priority_file(fi):
                        status = "full"
                    else:
                        status = "meta-only"
            elif level == "dev":
                # Dev-Profil: Fokus auf arbeitsrelevante Dateien.
                # - Source/Tests/Config/CI/Contracts → voll
                # - Lockfiles: ab bestimmter Größe nur Manifest
                # - Doku: nur Prioritätsdateien (README, Runbooks, ai-context) voll,
                #         Rest Manifest
                # - Sonstiges: Manifest
                if "lockfile" in fi.tags:
                    if fi.size > 20_000:
                        status = "meta-only"
                    else:
                        status = "full"
                elif fi.category in ["source", "test", "config", "ci", "contract"]:
                    status = "full"
                elif fi.category == "doc":
                    if is_priority_file(fi):
                        status = "full"
                    else:
                        status = "meta-only"
                else:
                    status = "meta-only"
            elif level == "max":
                status = "full"
            else:
                if fi.size <= max_file_bytes: status = "full"
                else: status = "omitted"

        # Explicitly removed: automatic downgrade from "full" to "truncated"
        # if status == "full" and fi.size > max_file_bytes:
        #    status = "truncated"

        processed_files.append((fi, status))

    if debug:
        print("DEBUG: total files:", len(files))
        print("DEBUG: unknown categories:", unknown_categories)
        # print("DEBUG: unknown tags:", unknown_tags) # Tags logic is simple, skipping for now
        print("DEBUG: files without anchors:", [fi.rel_path for fi in files if not hasattr(fi, "anchor")])

    total_size = sum(fi.size for fi in files)
    text_files = [fi for fi in files if fi.is_text]
    included_count = sum(1 for _, s in processed_files if s in ("full", "truncated"))

    cat_stats = summarize_categories(files)

    # pro-Repo-Statistik für "mit Inhalt" (full/truncated),
    # um später im Plan pro Repo eine Coverage-Zeile auszugeben
    included_by_root: Dict[str, int] = {}

    # Declared Purpose (Patch C)
    declared_purpose = ""
    try:
        if sources:
            declared_purpose = extract_purpose(sources[0])
    except Exception:
        pass

    if not declared_purpose:
        declared_purpose = "(none)"

    infra_folders = set()
    code_folders = set()
    doc_folders = set()

    # Organismus-Rollen (ohne neue Tags/Kategorien):
    organism_ai_ctx: List[FileInfo] = []
    organism_contracts: List[FileInfo] = []
    organism_pipelines: List[FileInfo] = []
    organism_wgx_profiles: List[FileInfo] = []

    for fi in files:
        parts = fi.rel_path.parts
        if ".github" in parts or ".wgx" in parts or "contracts" in parts:
            infra_folders.add(parts[0])
        if "src" in parts or "scripts" in parts:
            code_folders.add(parts[0])
        if "docs" in parts:
            doc_folders.add("docs")

        # Organismus-Rollen:
        if fi.category == "contract":
            organism_contracts.append(fi)
        if "ai-context" in (fi.tags or []):
            organism_ai_ctx.append(fi)
        if "ci" in (fi.tags or []):
            organism_pipelines.append(fi)
        if "wgx-profile" in (fi.tags or []):
            organism_wgx_profiles.append(fi)

    # jetzt, nachdem processed_files existiert, die Coverage pro Root berechnen
    for fi, status in processed_files:
        if status in ("full", "truncated"):
            included_by_root[fi.root_label] = included_by_root.get(fi.root_label, 0) + 1

    # --- 1. Header ---
    header = []
    header.append(f"# WC-Merger Report (v{SPEC_VERSION.split('.')[0]}.x)")
    header.append("")

    # --- 2. Source & Profile ---
    header.append("## Source & Profile")
    source_names = sorted([s.name for s in sources])
    header.append(f"- **Source:** {', '.join(source_names)}")
    header.append(f"- **Profile:** `{level}`")
    header.append(f"- **Generated At:** {now.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
    if max_file_bytes and max_file_bytes > 0:
        header.append(f"- **Max File Bytes:** {human_size(max_file_bytes)}")
    else:
        # 0 / None = kein per-File-Limit – alles wird vollständig gelesen
        header.append("- **Max File Bytes:** unlimited")
    header.append(f"- **Spec-Version:** {SPEC_VERSION}")
    header.append(f"- **Contract:** {MERGE_CONTRACT_NAME}")
    header.append(f"- **Contract-Version:** {MERGE_CONTRACT_VERSION}")

    # Semantische Use-Case-Zeile pro Profil (ergänzend zum Repo-Zweck)
    profile_usecase = PROFILE_USECASE.get(level)
    if profile_usecase:
        header.append(f"- **Profile Use-Case:** {profile_usecase}")

    header.append(f"- **Declared Purpose:** {declared_purpose}")

    # Scope-Zeile: welche Roots/Repos sind beteiligt?
    roots = sorted({fi.root_label for fi in files})
    if not roots:
        scope_desc = "empty (no matching files)"
    elif len(roots) == 1:
        scope_desc = f"single repo `{roots[0]}`"
    else:
        preview = ", ".join(f"`{r}`" for r in roots[:5])
        if len(roots) > 5:
            preview += ", …"
        scope_desc = f"{len(roots)} repos: {preview}"
    header.append(f"- **Scope:** {scope_desc}")

    # Neue, explizite Filterangaben
    if path_filter:
        header.append(f"- **Path Filter:** `{path_filter}`")
    else:
        header.append("- **Path Filter:** `none (full tree)`")

    if ext_filter:
        header.append(
            "- **Extension Filter:** "
            + ", ".join(f"`{e}`" for e in sorted(ext_filter))
        )
    else:
        header.append("- **Extension Filter:** `none (all text types)`")
    header.append("")

    # --- 3. Machine-readable Meta Block (für KIs) ---
    meta: List[str] = []
    meta.append("<!-- @meta:start -->")
    meta.append("```yaml")
    meta.append("merge:")
    meta.append(f"  spec_version: \"{SPEC_VERSION}\"")
    meta.append(f"  profile: \"{level}\"")
    meta.append(f"  contract: \"{MERGE_CONTRACT_NAME}\"")
    meta.append(f"  contract_version: \"{MERGE_CONTRACT_VERSION}\"")
    meta.append(f"  plan_only: {str(plan_only).lower()}")
    meta.append(f"  max_file_bytes: {max_file_bytes}")
    meta.append(f"  scope: \"{scope_desc}\"")
    if roots:
        roots_list = ", ".join(repr(r) for r in roots)
        meta.append(f"  source_repos: [{roots_list}]")
    else:
        meta.append("  source_repos: []")
    if path_filter:
        meta.append(f"  path_filter: {path_filter!r}")
    else:
        meta.append("  path_filter: null")
    if ext_filter:
        exts_list = ", ".join(repr(e) for e in sorted(ext_filter))
        meta.append(f"  ext_filter: [{exts_list}]")
    else:
        meta.append("  ext_filter: null")

    # Extras Configuration (optional)
    if extras and any(asdict(extras).values()):
        meta.append("  extras:")
        for k, v in asdict(extras).items():
            meta.append(f"    {k}: {str(v).lower()}")

    meta.append("```")
    meta.append("<!-- @meta:end -->")
    meta.append("")
    header.extend(meta)

    # --- 4. Profile Description ---
    header.append("## Profile Description")
    if level == "overview":
        header.append("`overview`")
        header.append("- Nur: README (voll), Runbook (voll), ai-context (voll)")
        header.append("- Andere Dateien: Included = meta-only")
    elif level == "summary":
        header.append("`summary`")
        header.append("- Voll: README, Runbooks, ai-context, docs/, .wgx/, .github/workflows/, zentrale Config, Contracts")
        header.append("- Code & Tests: Manifest + Struktur; nur Prioritätsdateien (README, Runbooks, ai-context) voll")
    elif level == "dev":
        header.append("`dev`")
        header.append("- Code, Tests, Config, CI, Contracts, ai-context, wgx-profile → voll")
        header.append("- Doku nur für Prioritätsdateien voll (README, Runbooks, ai-context), sonst Manifest")
        header.append("- Lockfiles / Artefakte: ab bestimmter Größe meta-only")
    elif level == "max":
        header.append("`max`")
        header.append("- alle Textdateien → voll")
        header.append("- keine Kürzung (Dateien werden ggf. gesplittet)")
    else:
        header.append(f"`{level}` (custom)")
    header.append("")

    # --- 4. Reading Plan ---
    header.append("## Reading Plan")
    header.append("1. Lies zuerst: `README.md`, `docs/runbook*.md`, `*.ai-context.yml`")
    header.append("2. Danach: `Structure` -> `Manifest` -> `Content`")
    header.append("3. Hinweis: „Multi-Repo-Merges: jeder Repo hat eigenen Block 📦“")
    header.append("")

    yield "\n".join(header) + "\n"

    # --- 5. Plan ---
    plan: List[str] = []
    plan.append("## Plan")
    plan.append("")
    plan.append(f"- **Total Files:** {len(files)} (Text: {len(text_files)})")
    plan.append(f"- **Total Size:** {human_size(total_size)}")
    plan.append(f"- **Included Content:** {included_count} files (full)")
    if text_files:
        plan.append(
            f"- **Coverage:** {included_count}/{len(text_files)} Textdateien mit Inhalt (`full`/`truncated`)"
        )
    plan.append("")

    # Mini-Summary pro Repo – damit KIs schnell die Lastverteilung sehen
    files_by_root: Dict[str, List[FileInfo]] = {}
    for fi in files:
        files_by_root.setdefault(fi.root_label, []).append(fi)

    if files_by_root:
        plan.append("### Repo Snapshots")
        plan.append("")
        for root in sorted(files_by_root.keys()):
            root_files = files_by_root[root]
            root_total = len(root_files)
            # „relevante Textdateien“: Code, Docs, Config, Tests, CI, Contracts
            root_text = sum(
                1
                for f in root_files
                if f.is_text
                and f.category in {"source", "doc", "config", "test", "ci", "contract"}
            )
            root_bytes = sum(f.size for f in root_files)
            root_included = included_by_root.get(root, 0)
            plan.append(
                f"- `{root}` → {root_total} files "
                f"({root_text} relevant text, {human_size(root_bytes)}, {root_included} with content)"
            )
        plan.append("")
    plan.append("**Folder Highlights:**")
    if code_folders: plan.append(f"- Code: `{', '.join(sorted(code_folders))}`")
    if doc_folders: plan.append(f"- Docs: `{', '.join(sorted(doc_folders))}`")
    if infra_folders: plan.append(f"- Infra: `{', '.join(sorted(infra_folders))}`")
    plan.append("")

    # Organismus-Overview (im Plan, ohne Spec-Reihenfolge zu brechen)
    plan.append("### Organism Overview")
    plan.append("")
    plan.append(
        f"- AI-Kontext-Organe: {len(organism_ai_ctx)} Datei(en) (`ai-context`)"
    )
    plan.append(
        f"- Contracts: {len(organism_contracts)} Datei(en) (category = `contract`)"
    )
    plan.append(
        f"- Pipelines (CI/CD): {len(organism_pipelines)} Datei(en) (Tag `ci`)"
    )
    plan.append(
        f"- Fleet-/WGX-Profile: {len(organism_wgx_profiles)} Datei(en) (Tag `wgx-profile`)"
    )
    plan.append("")

    yield "\n".join(plan) + "\n"

    if plan_only:
        return

    # --- 6. Structure ---
    structure = []
    structure.append("## 📁 Structure")
    structure.append("")
    structure.append(build_tree(files))
    structure.append("")
    yield "\n".join(structure) + "\n"

    # --- Index (Patch B) ---
    # Generated Categories Index
    index_blocks = []
    index_blocks.append("## Index")

    # List of categories to index
    # CI ist ein Tag, keine eigene Kategorie – wird separat indiziert.
    cats_to_idx = ["source", "doc", "config", "contract", "test"]
    for c in cats_to_idx:
        index_blocks.append(f"- [{c.capitalize()}](#cat-{c})")

    # Tags can be indexed too if needed, e.g. wgx-profile
    index_blocks.append("- [CI Pipelines](#tag-ci)")
    index_blocks.append("- [WGX Profiles](#tag-wgx-profile)")
    index_blocks.append("")

    # Category Lists
    for c in cats_to_idx:
        cat_files = [f for f in files if f.category == c]
        if cat_files:
            index_blocks.append(f"## Category: {c} {{#cat-{c}}}")
            for f in cat_files:
                index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
            index_blocks.append("")

    # Tag Lists – CI-Pipelines
    ci_files = [f for f in files if "ci" in (f.tags or [])]
    if ci_files:
        index_blocks.append("## Tag: ci {#tag-ci}")
        for f in ci_files:
            index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
        index_blocks.append("")

    # Tag Lists (example)
    wgx_files = [f for f in files if "wgx-profile" in f.tags]
    if wgx_files:
        index_blocks.append("## Tag: wgx-profile {#tag-wgx-profile}")
        for f in wgx_files:
             index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
        index_blocks.append("")

    yield "\n".join(index_blocks) + "\n"

    # --- 7. Manifest (Patch A) ---
    manifest: List[str] = []
    manifest.append("## 🧾 Manifest {#manifest}")
    manifest.append("")
    manifest.append("| Root | Path | Category | Tags | Size | Included | MD5 |")
    manifest.append("| --- | --- | --- | --- | ---: | --- | --- |")
    for fi, status in processed_files:
        tags_str = ", ".join(fi.tags) if fi.tags else "-"
        # Noise kennzeichnen, ohne das Schema zu ändern
        included_label = status
        if is_noise_file(fi):
            included_label = f"{status} (noise)"

        # Link in Manifest
        path_str = f"[`{fi.rel_path}`](#{fi.anchor})"
        manifest.append(
            f"| `{fi.root_label}` | {path_str} | `{fi.category}` | {tags_str} | "
            f"{human_size(fi.size)} | `{included_label}` | `{fi.md5}` |"
        )
    manifest.append("")
    yield "\n".join(manifest) + "\n"

    # --- Optional: Fleet Consistency ---
    consistency_warnings = check_fleet_consistency(files)
    if consistency_warnings:
        cons = []
        cons.append("## Fleet Consistency")
        cons.append("")
        for w in consistency_warnings:
            cons.append(w)
        cons.append("")
        yield "\n".join(cons) + "\n"

    # --- 8. Content ---
    # Per Spec v2.3 / Validator requirements
    yield "## 📄 Content\n\n"

    current_root = None

    for fi, status in processed_files:
        if status in ("omitted", "meta-only"):
            continue

        if fi.root_label != current_root:
            yield f"## 📦 {fi.root_label} {{#repo-{fi.root_label}}}\n\n"
            current_root = fi.root_label

        block = []
        block.append(f'<a id="{fi.anchor}"></a>')
        block.append(f"### `{fi.rel_path}`")
        block.append(f"- Category: {fi.category}")
        if fi.tags:
            block.append(f"- Tags: {', '.join(fi.tags)}")
        else:
            block.append(f"- Tags: -")
        block.append(f"- Size: {human_size(fi.size)}")
        block.append(f"- Included: {status}")
        block.append(f"- MD5: {fi.md5}")

        content, truncated, trunc_msg = read_smart_content(fi, max_file_bytes)

        lang = lang_for(fi.ext)
        block.append("")
        block.append(f"```{lang}")
        block.append(content)
        block.append("```")
        block.append("")
        block.append("[↑ Zurück zum Manifest](#manifest)")
        yield "\n".join(block) + "\n\n"

def generate_report_content(
    files: List[FileInfo],
    level: str,
    max_file_bytes: int,
    sources: List[Path],
    plan_only: bool,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
) -> str:
    report = "".join(iter_report_blocks(files, level, max_file_bytes, sources, plan_only, debug, path_filter, ext_filter, extras))
    if plan_only:
        return report
    try:
        validate_report_structure(report)
    except ValueError as e:
        if debug:
            print(f"DEBUG: Validation Error: {e}")
        # In strict mode, we might want to raise, but for now let's just warn or allow passing if debug
        # User said "Fehler -> kein Merge wird geschrieben." in Spec.
        # So we should probably re-raise.
        raise
    return report

def write_reports_v2(
    merges_dir: Path,
    hub: Path,
    repo_summaries: List[Dict],
    detail: str,
    mode: str,
    max_bytes: int,
    plan_only: bool,
    split_size: int = 0,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
) -> List[Path]:
    out_paths = []

    # Helper for writing logic
    def process_and_write(target_files, target_sources, output_filename_base_func):
        if split_size > 0:
            local_out_paths = []
            part_num = 1
            current_size = 0
            current_lines = []

            # Helper to flush
            def flush_part(is_last=False):
                nonlocal part_num, current_size, current_lines
                if not current_lines:
                    return

                out_path = output_filename_base_func(part=part_num)
                out_path.write_text("".join(current_lines), encoding="utf-8")
                local_out_paths.append(out_path)

                part_num += 1
                current_lines = []
                # Add continuation header for next part
                if not is_last:
                    header = f"# WC-Merge Report (Part {part_num})\n\n"
                    current_lines.append(header)
                    current_size = len(header.encode('utf-8'))
                else:
                    current_size = 0

            iterator = iter_report_blocks(target_files, detail, max_bytes, target_sources, plan_only, debug, path_filter, ext_filter, extras)

            for block in iterator:
                block_len = len(block.encode('utf-8'))

                if current_size + block_len > split_size and len(current_lines) > 1:
                    flush_part()

                current_lines.append(block)
                current_size += block_len

            flush_part(is_last=True)

            # Nachlauf: Header aller Teile auf "Part N/M" normalisieren.
            # Hintergrund:
            # - Während des Schreibens kennen wir die Gesamtzahl der Teile noch nicht.
            # - Jetzt (nach allen flushes) können wir die Header 1/1, 1/3, 2/3, … sauber setzen.
            total_parts = len(local_out_paths)
            if total_parts >= 1:
                for idx, path in enumerate(local_out_paths, start=1):
                    try:
                        text = path.read_text(encoding="utf-8")
                    except Exception:
                        # Wenn das Lesen fehlschlägt, diesen Part überspringen.
                        continue

                    lines = text.splitlines(True)
                    if not lines:
                        continue

                    # Anpassung: Auch den Standard-Header (Part 1) erkennen
                    prefix_part = "# WC-Merge Report (Part "
                    prefix_main = "# WC-Merger Report"

                    if lines[0].startswith(prefix_part) or lines[0].startswith(prefix_main):
                        # Nur die erste Zeile ersetzen, Rest unverändert lassen.
                        lines[0] = f"# WC-Merge Report (Part {idx}/{total_parts})\n"
                        try:
                            path.write_text("".join(lines), encoding="utf-8")
                        except Exception:
                            # Schreibfehler nicht fatal machen.
                            pass

            out_paths.extend(local_out_paths)

        else:
            # Standard single file
            content = generate_report_content(target_files, detail, max_bytes, target_sources, plan_only, debug, path_filter, ext_filter, extras)
            out_path = output_filename_base_func(part=None)
            out_path.write_text(content, encoding="utf-8")
            out_paths.append(out_path)

    if mode == "gesamt":
        all_files = []
        repo_names = []
        sources = []
        for s in repo_summaries:
            all_files.extend(s["files"])
            repo_names.append(s["name"])
            sources.append(s["root"])

        # kosmetisches Label im Dateinamen:
        # nur ein Repo → "single", mehrere → "multi"
        mode_label = "single" if len(repo_names) == 1 else "multi"
        process_and_write(
            all_files,
            sources,
            lambda part=None: make_output_filename(merges_dir, repo_names, mode_label, detail, part),
        )

    else:
        for s in repo_summaries:
            s_name = s["name"]
            s_files = s["files"]
            s_root = s["root"]

            process_and_write(s_files, [s_root], lambda part=None: make_output_filename(merges_dir, [s_name], "repo", detail, part))

    return out_paths

```

[↑ Zurück zum Manifest](#manifest)
