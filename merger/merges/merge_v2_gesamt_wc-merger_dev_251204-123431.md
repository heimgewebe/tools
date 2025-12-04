# WC-Merger Report (v2.x)

## Source & Profile
- **Source:** wc-merger
- **Profile:** `dev`
- **Generated At:** 2025-12-04 12:34:31 (UTC)
- **Max File Bytes:** 9.54 MB
- **Spec-Version:** 2.3
- **Declared Purpose:** # wc-merger (Working Copy Merger)

## Profile Description
`dev`
- Alles relevante (Code, Tests, CI, Contracts, ai-context, wgx-profile) → voll
- Lockfiles / Artefakte: truncated oder meta-only

## Reading Plan
1. Lies zuerst: `README.md`, `docs/runbook*.md`, `*.ai-context.yml`
2. Danach: `Structure` -> `Manifest` -> `Content`
3. Hinweis: „Multi-Repo-Merges: jeder Repo hat eigenen Block 📦“

## Plan

- **Total Files:** 5 (Text: 5)
- **Total Size:** 58.47 KB
- **Included Content:** 5 files (full/truncated)

**Folder Highlights:**

## 📁 Structure

```
📁 wc-merger/
    📄 README.md
    📄 merge_core.py
    📄 wc-extractor.py
    📄 wc-merger-spec.md
    📄 wc-merger.py
```

## Index
- [Source](#cat-source)
- [Doc](#cat-doc)
- [Config](#cat-config)
- [Contract](#cat-contract)
- [Test](#cat-test)
- [Ci](#cat-ci)
- [WGX Profiles](#tag-wgx-profile)

## Category: source {#cat-source}
- [`merge_core.py`](#file-wc-merger-merge_core-py)
- [`wc-extractor.py`](#file-wc-merger-wc-extractor-py)
- [`wc-merger.py`](#file-wc-merger-wc-merger-py)

## Category: doc {#cat-doc}
- [`README.md`](#file-wc-merger-README-md)
- [`wc-merger-spec.md`](#file-wc-merger-wc-merger-spec-md)

## 🧾 Manifest {#manifest}

| Root | Path | Category | Tags | Size | Included | MD5 |
| --- | --- | --- | --- | ---: | --- | --- |
| `wc-merger` | [`merge_core.py`](#file-wc-merger-merge_core-py) | `source` | - | 31.25 KB | `full` | `ac436f1e124e3c8e07787120a0632a24` |
| `wc-merger` | [`README.md`](#file-wc-merger-README-md) | `doc` | readme | 3.05 KB | `full` | `278783c979e9940805f907308555b5ba` |
| `wc-merger` | [`wc-extractor.py`](#file-wc-merger-wc-extractor-py) | `source` | - | 6.67 KB | `full` | `74b11f9852b25112e2616847f7171f54` |
| `wc-merger` | [`wc-merger-spec.md`](#file-wc-merger-wc-merger-spec-md) | `doc` | - | 2.92 KB | `full` | `6b42b59949e5bd76e7850baa3e3f184d` |
| `wc-merger` | [`wc-merger.py`](#file-wc-merger-wc-merger-py) | `source` | - | 14.58 KB | `full` | `7a66edb867a6a2cd792fb5d4ead99c2a` |

## 📄 Content

## 📦 wc-merger {#repo-wc-merger}

<a id="file-wc-merger-merge_core-py"></a>
### `merge_core.py`
- Category: source
- Tags: -
- Size: 31.25 KB
- Included: full
- MD5: ac436f1e124e3c8e07787120a0632a24

```python
# -*- coding: utf-8 -*-

"""
merge_core – Core functions for wc-merger (v2.3 Standard).
Implements AI-friendly formatting, tagging, and strict Pflichtenheft structure.
"""

import os
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Any, Iterator

# --- Configuration & Heuristics ---

SPEC_VERSION = "2.3"
MERGES_DIR_NAME = "merges"
DEFAULT_MAX_BYTES = 10_000_000  # 10 MB

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

def detect_hub_dir(script_path: Path, arg_base_dir: Optional[str] = None) -> Path:
    env_base = os.environ.get("WC_MERGER_BASEDIR")
    if env_base:
        p = Path(env_base).expanduser()
        if p.is_dir(): return p

    p = Path(HARDCODED_HUB_PATH)
    try:
        if p.expanduser().is_dir(): return p
    except Exception:
        pass

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
                    return first
            except Exception:
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
    if name.endswith(".ai-context.yml"):
        tags.append("ai-context")
    if ".github" in parts and "workflows" in parts and ext in [".yml", ".yaml"]:
        tags.append("ci")
    if "contracts" in parts and ext == ".json":
        tags.append("contract")
    if "docs" in parts and "adr" in parts and ext == ".md":
        tags.append("adr")
    if name.startswith("runbook") and ext == ".md":
        tags.append("runbook")
    if "scripts" in parts and ext == ".sh":
        tags.append("script")
    if "export" in parts and ext == ".jsonl":
        tags.append("feed")
    if "lock" in name: # *lock* pattern
        tags.append("lockfile")
    if "tools" in parts and "src" in parts:
        tags.append("cli")
    if name == "readme.md":
        tags.append("readme")
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

            # MD5 calculation
            md5 = ""
            if is_text or size <= max_bytes:
                md5 = compute_md5(abs_path, max_bytes)

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

def get_repo_snapshot(repo_root: Path) -> Dict[str, Tuple[int, str]]:
    """
    Returns a dictionary mapping relative paths to (size, md5).
    Uses the same ignoring logic as scan_repo to ensure clean diffs.
    """
    snapshot = {}
    summary = scan_repo(repo_root, extensions=None, path_contains=None, max_bytes=100_000_000) # Large limit for diffs
    for fi in summary["files"]:
        snapshot[fi.rel_path.as_posix()] = (fi.size, fi.md5)
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
    ts = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    base = "+".join(repo_names) if repo_names else "no-repos"
    if len(base) > 40:
        base = base[:37] + "..."
    base = base.replace(" ", "-").replace("/", "_")

    part_suffix = f"_part{part}" if part else ""
    return merges_dir / f"merge_v2_{mode}_{base}_{detail}_{ts}{part_suffix}.md"

def read_smart_content(fi: FileInfo, max_bytes: int, encoding="utf-8") -> Tuple[str, bool, str]:
    """
    Reads content.
    Returns (content, truncated, truncation_msg).
    If truncated, returns head + tail logic.
    """
    try:
        if fi.size <= max_bytes:
            with fi.abs_path.open("r", encoding=encoding, errors="replace") as f:
                return f.read(), False, ""

        # Truncation logic: Head + Tail
        head_size = max_bytes // 2
        tail_size = 4096 # Keep reasonably small tail to catch recent changes/end blocks
        if tail_size > max_bytes // 4:
            tail_size = max_bytes // 4

        with fi.abs_path.open("r", encoding=encoding, errors="replace") as f:
            head = f.read(head_size)
            f.seek(0, 2)
            f_size = f.tell()
            if f_size > head_size + tail_size:
                f.seek(f_size - tail_size)
                tail = f.read(tail_size)
                return (
                    head + f"\n\n> [TRUNCATED] Original size: {human_size(fi.size)}. Included: first {human_size(head_size)} and last {human_size(tail_size)}.\n\n" + tail,
                    True,
                    f"Included: first {human_size(head_size)} and last {human_size(tail_size)}."
                )
            else:
                f.seek(0)
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

def iter_report_blocks(files: List[FileInfo], level: str, max_file_bytes: int, sources: List[Path], plan_only: bool, debug: bool = False) -> Iterator[str]:
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
        if fi.category == "other" or fi.category not in ["source", "doc", "config", "test", "contract", "ci", "other"]:
             unknown_categories.add(fi.category)

        status = "omitted"
        if fi.is_text:
            if level == "overview":
                if is_priority_file(fi): status = "full"
                else: status = "meta-only"
            elif level == "dev":
                if "lockfile" in fi.tags:
                    if fi.size > 20000:
                        status = "meta-only"
                    else:
                        status = "full"
                else:
                    status = "full"
            elif level == "max":
                status = "full"
            else:
                if fi.size <= max_file_bytes: status = "full"
                else: status = "omitted"

        if status == "full" and fi.size > max_file_bytes:
            status = "truncated"

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

    for fi in files:
        parts = fi.rel_path.parts
        if ".github" in parts or ".wgx" in parts or "contracts" in parts:
            infra_folders.add(parts[0])
        if "src" in parts or "scripts" in parts:
            code_folders.add(parts[0])
        if "docs" in parts:
            doc_folders.add("docs")

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
    header.append(f"- **Max File Bytes:** {human_size(max_file_bytes)}")
    header.append(f"- **Spec-Version:** {SPEC_VERSION}")
    header.append(f"- **Declared Purpose:** {declared_purpose}")
    header.append("")

    # --- 3. Profile Description ---
    header.append("## Profile Description")
    if level == "overview":
        header.append("`overview`")
        header.append("- Nur: README (voll), Runbook (voll), ai-context (voll)")
        header.append("- Andere Dateien: Included = meta-only")
    elif level == "dev":
        header.append("`dev`")
        header.append("- Alles relevante (Code, Tests, CI, Contracts, ai-context, wgx-profile) → voll")
        header.append("- Lockfiles / Artefakte: truncated oder meta-only")
    elif level == "max":
        header.append("`max`")
        header.append("- alle Textdateien → voll")
        header.append("- nur > Max Bytes → BITECHT truncated")
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
    plan = []
    plan.append("## Plan")
    plan.append("")
    plan.append(f"- **Total Files:** {len(files)} (Text: {len(text_files)})")
    plan.append(f"- **Total Size:** {human_size(total_size)}")
    plan.append(f"- **Included Content:** {included_count} files (full/truncated)")
    plan.append("")
    plan.append("**Folder Highlights:**")
    if code_folders: plan.append(f"- Code: `{', '.join(sorted(code_folders))}`")
    if doc_folders: plan.append(f"- Docs: `{', '.join(sorted(doc_folders))}`")
    if infra_folders: plan.append(f"- Infra: `{', '.join(sorted(infra_folders))}`")
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
    cats_to_idx = ["source", "doc", "config", "contract", "test", "ci"]
    for c in cats_to_idx:
        index_blocks.append(f"- [{c.capitalize()}](#cat-{c})")

    # Tags can be indexed too if needed, e.g. wgx-profile
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

    # Tag Lists (example)
    wgx_files = [f for f in files if "wgx-profile" in f.tags]
    if wgx_files:
        index_blocks.append("## Tag: wgx-profile {#tag-wgx-profile}")
        for f in wgx_files:
             index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
        index_blocks.append("")

    yield "\n".join(index_blocks) + "\n"

    # --- 7. Manifest (Patch A) ---
    manifest = []
    manifest.append("## 🧾 Manifest {#manifest}")
    manifest.append("")
    manifest.append("| Root | Path | Category | Tags | Size | Included | MD5 |")
    manifest.append("| --- | --- | --- | --- | ---: | --- | --- |")
    for fi, status in processed_files:
        tags_str = ", ".join(fi.tags) if fi.tags else "-"
        # Link in Manifest
        path_str = f"[`{fi.rel_path}`](#{fi.anchor})"
        manifest.append(
            f"| `{fi.root_label}` | {path_str} | `{fi.category}` | {tags_str} | {human_size(fi.size)} | `{status}` | `{fi.md5}` |"
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

def generate_report_content(files: List[FileInfo], level: str, max_file_bytes: int, sources: List[Path], plan_only: bool, debug: bool = False) -> str:
    report = "".join(iter_report_blocks(files, level, max_file_bytes, sources, plan_only, debug))
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

def write_reports_v2(merges_dir: Path, hub: Path, repo_summaries: List[Dict], detail: str, mode: str, max_bytes: int, plan_only: bool, split_size: int = 0, debug: bool = False) -> List[Path]:
    out_paths = []

    # Helper for writing logic
    def process_and_write(target_files, target_sources, output_filename_base_func):
        if split_size > 0:
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
                out_paths.append(out_path)

                part_num += 1
                current_lines = []
                # Add continuation header for next part
                if not is_last:
                    header = f"# WC-Merge Report (Part {part_num})\n\n"
                    current_lines.append(header)
                    current_size = len(header.encode('utf-8'))
                else:
                    current_size = 0

            iterator = iter_report_blocks(target_files, detail, max_bytes, target_sources, plan_only, debug)

            for block in iterator:
                block_len = len(block.encode('utf-8'))

                if current_size + block_len > split_size and len(current_lines) > 1:
                    flush_part()

                current_lines.append(block)
                current_size += block_len

            flush_part(is_last=True)

        else:
            # Standard single file
            content = generate_report_content(target_files, detail, max_bytes, target_sources, plan_only, debug)
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

        process_and_write(all_files, sources, lambda part=None: make_output_filename(merges_dir, repo_names, mode, detail, part))

    else:
        for s in repo_summaries:
            s_name = s["name"]
            s_files = s["files"]
            s_root = s["root"]

            process_and_write(s_files, [s_root], lambda part=None: make_output_filename(merges_dir, [s_name], "repo", detail, part))

    return out_paths

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-wc-merger-README-md"></a>
### `README.md`
- Category: doc
- Tags: readme
- Size: 3.05 KB
- Included: full
- MD5: 278783c979e9940805f907308555b5ba

```markdown
# wc-merger (Working Copy Merger)

Der `wc-merger` erzeugt aus lokalen Working-Copy-Checkouts strukturierte „Merge-Berichte“ im Markdown-Format.

Hauptziel: **KIs einen möglichst vollständigen Blick auf ein oder mehrere Repositories geben**, damit sie

- Code verstehen,
- Reviews erstellen,
- Refactorings vorschlagen,
- Dokumentation prüfen,
- CI- und Contract-Setups analysieren können.

**⚠️ WICHTIG: Verbindliche Spezifikation**

Ab Version 2.1 folgt dieses Tool einer strikten, unverhandelbaren Spezifikation.
Jede Änderung am Code muss diese Regeln einhalten.

👉 [**wc-merger-spec.md**](./wc-merger-spec.md) (Die Single Source of Truth)

---

## 🏗️ Jules Guidelines (Strict Mode)

Für die Weiterentwicklung (und speziell für Agenten wie Jules) gelten folgende **Meta-Regeln**:

1.  **Strict Compliance Check:**
    *   Verstößt der Patch gegen die festgelegte Abschnittsreihenfolge?
    *   Werden neue Kategorien/Tags eingeführt? → **VERBOTEN**
    *   Werden bestehende Tags verändert? → **VERBOTEN**
    *   Wird irgendwo neue Logik eingeführt, die „intelligent“ ist? → **VERBOTEN**
    *   Verändert der Patch einen optionalen Abschnitt so, dass er verpflichtend wird? → **VERBOTEN**
    *   Entsteht eine neue potenzielle Halluzinationsquelle? → **SOFORT ABBRECHEN**

2.  **Explicit Non-Interpretation:**
    *   `if some_field_unsure: do NOT fill it, NOT invent fallback, leave as (none)`
    *   Keine „kleinen automatischen Schlauheiten“.

3.  **Strict Sorting:**
    *   Multi-Repo-Merges müssen der in der Spec definierten Reihenfolge folgen (`metarepo` -> `wgx` -> `hausKI` ...).
    *   Dateien alphabetisch nach Pfad.

4.  **KI-Safety:**
    *   Timestamps immer in UTC (`YYYY-MM-DD HH:MM:SS (UTC)`).
    *   `Spec-Version: 2.1` Header immer setzen.

---

## Zielbild

Ein idealer wc-merge erfüllt:

- bildet **den gesamten relevanten Textinhalt** eines Repos ab (Code, Skripte, Configs, Tests, Docs),
- macht die **Struktur** des Repos sichtbar,
- zeigt **Zusammenhänge** (Workflows, Contracts, Tools, Tests),
- ermöglicht KIs, auf Basis des Merges so zu arbeiten, als hätten sie das Repo lokal ausgecheckt – nur ohne Binärmüll und ohne sensible Daten.

---

## Detailgrade (Profile)

Der wc-merger v2 kennt drei optimierte Profile:

### 1. Overview (`overview`)
- Kopf, Plan, Strukturbaum, Manifest.
- **Inhalte nur für Prioritätsdateien:** `README.*`, `docs/runbook.*`, `.ai-context.yml`
- Alle anderen Dateien nur als Metadaten im Manifest (`meta-only`).

### 2. Dev (`dev`)
- **Vollständig:** Source-Code, Docs, CI/CD, Contracts, Configs.
- **Zusammengefasst:** Große Lockfiles.

### 3. Max (`max`)
- Inhalte **aller Textdateien** (bis zum Limit).
- Maximale Tiefe.

---

## Nutzung

### CLI-Nutzung:

```bash
# Overview-Profil
python3 wc-merger.py --cli --repos repo1,repo2 --detail overview

# Dev-Profil
python3 wc-merger.py --cli --repos myrepo --detail dev --mode batch

# Max-Profil mit Split
python3 wc-merger.py --cli --repos myrepo --detail max --split-size 20
```

Weitere Details siehe [wc-merger-spec.md](./wc-merger-spec.md).

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-wc-merger-wc-extractor-py"></a>
### `wc-extractor.py`
- Category: source
- Tags: -
- Size: 6.67 KB
- Included: full
- MD5: 74b11f9852b25112e2616847f7171f54

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc_extractor – ZIPs im wc-hub entpacken und Repos aktualisieren.
Verwendet merge_core.

Funktion:
- Suche alle *.zip im Hub (wc-hub).
- Für jede ZIP:
  - Entpacke in temporären Ordner.
  - Wenn es bereits einen Zielordner mit gleichem Namen gibt:
    - Erzeuge einfachen Diff-Bericht (Markdown) alt vs. neu.
    - Lösche den alten Ordner.
  - Benenne Temp-Ordner in Zielordner um.
  - Lösche die ZIP-Datei.

Diff-Berichte:
- Liegen direkt im merges-Verzeichnis des Hubs.
"""

import sys
import shutil
import zipfile
import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional, List

try:
    import console  # type: ignore
except ImportError:
    console = None  # type: ignore

# Import from core
try:
    from merge_core import (
        detect_hub_dir,
        get_merges_dir,
        get_repo_snapshot,
    )
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from merge_core import (
        detect_hub_dir,
        get_merges_dir,
        get_repo_snapshot,
    )


def detect_hub() -> Path:
    script_path = Path(__file__).resolve()
    return detect_hub_dir(script_path)


def diff_trees(
    old: Path,
    new: Path,
    repo_name: str,
    merges_dir: Path,
) -> Path:
    """
    Vergleicht zwei Repo-Verzeichnisse und schreibt einen Markdown-Diff-Bericht.
    Rückgabe: Pfad zur Diff-Datei.
    """
    # Use scan_repo / get_repo_snapshot via merge_core to respect ignores
    old_map = get_repo_snapshot(old)
    new_map = get_repo_snapshot(new)

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    only_old = sorted(old_keys - new_keys)
    only_new = sorted(new_keys - old_keys)
    common = sorted(old_keys & new_keys)

    changed = []
    for rel in common:
        size_old, md5_old = old_map[rel]
        size_new, md5_new = new_map[rel]
        if size_old != size_new or md5_old != md5_new:
            changed.append((rel, size_old, size_new))

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    fname = "{}-import-diff-{}.md".format(repo_name, ts)
    out_path = merges_dir / fname

    lines = []
    lines.append("# Import-Diff `{}`".format(repo_name))
    lines.append("")
    lines.append("- Zeitpunkt: `{}`".format(now))
    lines.append("- Alter Pfad: `{}`".format(old))
    lines.append("- Neuer Pfad (Temp): `{}`".format(new))
    lines.append("")
    lines.append("- Dateien nur im alten Repo: **{}**".format(len(only_old)))
    lines.append("- Dateien nur im neuen Repo: **{}**".format(len(only_new)))
    lines.append("- Dateien mit geändertem Inhalt: **{}**".format(len(changed)))
    lines.append("")

    if only_old:
        lines.append("## Nur im alten Repo")
        lines.append("")
        for rel in only_old:
            lines.append("- `{}`".format(rel))
        lines.append("")

    if only_new:
        lines.append("## Nur im neuen Repo")
        lines.append("")
        for rel in only_new:
            lines.append("- `{}`".format(rel))
        lines.append("")

    if changed:
        lines.append("## Geänderte Dateien")
        lines.append("")
        lines.append("| Pfad | Größe alt | Größe neu |")
        lines.append("| --- | ---: | ---: |")
        for rel, s_old, s_new in changed:
            lines.append(
                "| `{}` | {} | {} |".format(rel, s_old, s_new)
            )
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def import_zip(zip_path: Path, hub: Path, merges_dir: Path) -> Optional[Path]:
    """
    Entpackt eine einzelne ZIP-Datei in den Hub, behandelt Konflikte,
    schreibt ggf. Diff und ersetzt das alte Repo.

    Rückgabe:
      Pfad zum Diff-Bericht oder None.
    """
    repo_name = zip_path.stem
    target_dir = hub / repo_name
    tmp_dir = hub / ("__extract_tmp_" + repo_name)

    print("Verarbeite ZIP:", zip_path.name, "-> Repo", repo_name)

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    tmp_dir.mkdir(parents=True, exist_ok=True)

    # ZIP entpacken
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp_dir)

    diff_path = None  # type: Optional[Path]

    # Wenn es schon ein Repo mit diesem Namen gibt -> Diff + löschen
    if target_dir.exists():
        print("  Zielordner existiert bereits:", target_dir)
        try:
            diff_path = diff_trees(target_dir, tmp_dir, repo_name, merges_dir)
            print("  Diff-Bericht:", diff_path)
        except Exception as e:
            print(f"  Warnung: Fehler beim Diff-Erstellen ({e}). Fahre fort.")

        shutil.rmtree(target_dir)
        print("  Alter Ordner gelöscht:", target_dir)
    else:
        print("  Kein vorhandenes Repo – frischer Import.")

    # Temp-Ordner ins Ziel verschieben
    tmp_dir.rename(target_dir)
    print("  Neuer Repo-Ordner:", target_dir)

    # ZIP nach erfolgreichem Import löschen
    try:
        zip_path.unlink()
        print("  ZIP gelöscht:", zip_path.name)
    except OSError as e:
        print(f"  Warnung: Konnte ZIP nicht löschen ({e})")
    print("")

    return diff_path


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="wc-extractor-v2: Import ZIPs to hub.")
    parser.add_argument("--hub", help="Hub directory override.")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    hub = detect_hub_dir(script_path, args.hub)

    if not hub.exists():
         print(f"Hub directory not found: {hub}")
         return 1

    merges_dir = get_merges_dir(hub)

    print("wc_extractor-v2 – Hub:", hub)
    zips = sorted(hub.glob("*.zip"))

    if not zips:
        msg = "Keine ZIP-Dateien im Hub gefunden."
        print(msg)
        if console:
            console.alert("wc_extractor-v2", msg, "OK", hide_cancel_button=True)
        return 0

    diff_paths = []

    for zp in zips:
        try:
            diff = import_zip(zp, hub, merges_dir)
            if diff is not None:
                diff_paths.append(diff)
        except Exception as e:
            print("Fehler bei {}: {}".format(zp, e), file=sys.stderr)

    summary_lines = []
    summary_lines.append("Import fertig.")
    summary_lines.append("Hub: {}".format(hub))
    if diff_paths:
        summary_lines.append(
            "Diff-Berichte ({}):".format(len(diff_paths))
        )
        for p in diff_paths:
            summary_lines.append("  - {}".format(p))
    else:
        summary_lines.append("Keine Diff-Berichte erzeugt.")

    summary = "\n".join(summary_lines)
    print(summary)

    if console:
        console.alert("wc_extractor-v2", summary, "OK", hide_cancel_button=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-wc-merger-wc-merger-spec-md"></a>
### `wc-merger-spec.md`
- Category: doc
- Tags: -
- Size: 2.92 KB
- Included: full
- MD5: 6b42b59949e5bd76e7850baa3e3f184d

```markdown
# WC-MERGER SPEC v2.3

(Normative Spezifikation)

## 1. Zweck

Der wc-merger erzeugt aus Working-Copy-Repositories KI-optimierte, strukturierte Hyper-Merges.
Diese dienen KIs als Navigations- und Arbeitsfläche, ähnlich einer Mini-IDE.

---

## 2. Invariante Struktur des Merges (strict ordering)

Jeder Merge folgt exakt dieser Reihenfolge:
1.  Source & Profile
2.  Profile Description
3.  Reading Plan
4.  Plan
5.  📁 Structure
6.  🧾 Manifest
7.  📄 Content

Fehlt ein Abschnitt → Fehler.

Reihenfolge falsch → Fehler.

---

## 3. Spec-Version-Pinning

Header muss enthalten:

- Spec-Version: 2.3

Optional:

- Spec-Checksum: <sha256>

---

## 4. Kategorien

Erlaubte Werte:
- source
- doc
- config
- test
- contract
- ci
- other

Neue Kategorien dürfen nicht entstehen.

---

## 5. Tags

Erlaubte Tags:
- ai-context
- runbook
- lockfile
- script
- ci
- adr
- feed
- wgx-profile

Jede Datei darf 0–n Tags haben.
Neue Tags sind verboten, außer Spec wird geändert.

---

## 6. Hyperlink-Schema (Pflicht)

### 6.1 Datei-Anchor (Pflicht)

Jede Datei im Content-Bereich erhält einen Anchor:

`<a id="file-<root>-<path-without-slashes>"></a>`

Regeln:
- `/` → `-`
- `.` → `-`

Beispiel:

`tools/merger/merge_core.py`
→ `file-tools-merger-merge_core-py`

---

### 6.2 Manifest-Link (Pflicht)

Pfadspalte:

[`<path>`](#file-<root>-<path>)

---

### 6.3 Strukturbaum-Link (optional)

📄 [filename](#file-…)

---

### 6.4 Repo-Anchor (Pflicht bei Multi-Repo)

`## 📦 tools {#repo-tools}`

---

### 6.5 Backlink (Pflicht)

Jeder Datei-Contentblock endet mit:

`[↑ Zurück zum Manifest](#manifest)`

---

## 7. Manifest-Anker

Oberhalb Manifest:

`## 🧾 Manifest {#manifest}`

---

## 8. Navigation-Indexe

Vor dem Manifest:

```markdown
## Index
- [Source Files](#cat-source)
- [Docs](#cat-doc)
- [Config](#cat-config)
- [Contracts](#cat-contract)
- [Tests](#cat-test)
- [CI](#cat-ci)
- [WGX Profiles](#tag-wgx-profile)
```

Für jede Kategorie:

```markdown
## Category: source {#cat-source}
- [file](#file-...)
```

---

## 9. Non-Interpretation Guard

Regeln:
- Keine Rateversuche.
- Unklare Klassifikation → other.
- Unklare Tags → keine Tags.
- Unklare Repo-Beschreibung → leer.

---

## 10. Repo-Zweck-Auslesung (safe)

Der Merger liest nur:
1.  README.md (erster Absatz)
2.  docs/intro.md (erster Absatz)

Keine weiteren Quellen. Keine Interpretation.

Output:

`- Declared Purpose: <ausgelesener Absatz>`

---

## 11. Debug Mode

CLI: `--debug`

Mindestinformationen:
- unbekannte Kategorien
- unbekannte Tags
- Dateien ohne Anchor
- Dateien ohne Manifest-Eintrag
- Dateien ohne Tags
- kollidierende Anchors
- Section-Ordering-Check-Report

---

## 12. Strict Validator

Jede Ausgabe wird geprüft:
- Abschnittsreihenfolge
- vollständige Manifest-Anker
- vollständige Content-Anker
- nur erlaubte Kategorien
- nur erlaubte Tags
- Spec-Version vorhanden
- keine verbotenen Schlüsselwörter oder Strukturen

Fehler → kein Merge wird geschrieben.

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-wc-merger-wc-merger-py"></a>
### `wc-merger.py`
- Category: source
- Tags: -
- Size: 14.58 KB
- Included: full
- MD5: 7a66edb867a6a2cd792fb5d4ead99c2a

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc-merger – Working-Copy Merger.
Enhanced AI-optimized reports with strict Pflichtenheft structure.
"""

import sys
import traceback
from pathlib import Path
from typing import List

# Try importing Pythonista modules
try:
    import ui        # type: ignore
    import console   # type: ignore
    import editor    # type: ignore
except ImportError:
    ui = None        # type: ignore
    console = None   # type: ignore
    editor = None    # type: ignore

# Import core logic
try:
    from merge_core import (
        MERGES_DIR_NAME,
        DEFAULT_MAX_BYTES,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
    )
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from merge_core import (
        MERGES_DIR_NAME,
        DEFAULT_MAX_BYTES,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
    )


# --- Helper ---

def find_repos_in_hub(hub: Path) -> List[str]:
    repos: List[str] = []
    if not hub.exists():
        return []
    for child in sorted(hub.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name in SKIP_ROOTS:
            continue
        if child.name == MERGES_DIR_NAME:
            continue
        if child.name.startswith("."):
            continue
        repos.append(child.name)
    return repos

def parse_human_size(text: str) -> int:
    text = text.upper().strip()
    if not text: return 0
    if text.isdigit(): return int(text)

    units = {"K": 1024, "M": 1024**2, "G": 1024**3}
    for u, m in units.items():
        if text.endswith(u) or text.endswith(u+"B"):
            val = text.rstrip(u+"B").rstrip(u)
            try:
                return int(float(val) * m)
            except ValueError:
                return 0
    return 0


# --- UI Class (Pythonista) ---

class MergerUI(object):
    def __init__(self, hub: Path) -> None:
        self.hub = hub
        self.repos = find_repos_in_hub(hub)

        v = ui.View()
        v.name = "WC-Merger"
        # Dark background, accent color in classic iOS blue for good contrast
        v.background_color = "#111111"
        v.frame = (0, 0, 540, 660) # Increased height
        self.view = v

        y = 10

        base_label = ui.Label()
        base_label.frame = (10, y, v.width - 20, 34)
        base_label.flex = "W"
        base_label.number_of_lines = 2
        base_label.text = f"Base-Dir: {hub}"
        base_label.text_color = "white"
        base_label.background_color = "#111111"
        base_label.font = ("<System>", 11)
        v.add_subview(base_label)
        self.base_label = base_label
        y += 40

        repo_label = ui.Label()
        repo_label.frame = (10, y, v.width - 20, 20)
        repo_label.flex = "W"
        repo_label.text = "Repos (Tap to select – None = All):"
        repo_label.text_color = "white"
        repo_label.background_color = "#111111"
        repo_label.font = ("<System>", 13)
        v.add_subview(repo_label)
        y += 22

        tv = ui.TableView()
        tv.frame = (10, y, v.width - 20, 160)
        tv.flex = "W"
        tv.background_color = "#111111"
        tv.separator_color = "#333333"
        tv.row_height = 32
        tv.allows_multiple_selection = True
        # Improve readability on dark background
        tv.tint_color = "#007aff"

        ds = ui.ListDataSource(self.repos)
        ds.text_color = "white"
        ds.highlight_color = "#333333"
        ds.tableview_cell_for_row = self._tableview_cell
        tv.data_source = ds
        tv.delegate = ds
        v.add_subview(tv)
        self.tv = tv
        self.ds = ds

        y += 170

        ext_field = ui.TextField()
        ext_field.frame = (10, y, v.width - 20, 28)
        ext_field.flex = "W"
        ext_field.placeholder = ".md,.yml,.rs (empty = all)"
        ext_field.text = ""
        ext_field.background_color = "#222222"
        ext_field.text_color = "white"
        ext_field.tint_color = "white"
        v.add_subview(ext_field)
        self.ext_field = ext_field

        y += 34

        path_field = ui.TextField()
        path_field.frame = (10, y, v.width - 20, 28)
        path_field.flex = "W"
        path_field.placeholder = "Path contains (e.g. docs/ or .github/)"
        path_field.background_color = "#222222"
        path_field.text_color = "white"
        path_field.tint_color = "white"
        path_field.autocorrection_type = False
        path_field.spellchecking_type = False
        v.add_subview(path_field)
        self.path_field = path_field

        y += 36

        detail_label = ui.Label()
        detail_label.text = "Detail:"
        detail_label.text_color = "white"
        detail_label.background_color = "#111111"
        detail_label.frame = (10, y, 60, 22)
        v.add_subview(detail_label)

        seg_detail = ui.SegmentedControl()
        seg_detail.segments = ["overview", "summary", "dev", "max"]
        seg_detail.selected_index = 2
        seg_detail.frame = (70, y - 2, 220, 28)
        seg_detail.flex = "W"
        # Use standard iOS blue instead of white for better contrast
        seg_detail.tint_color = "#007aff"
        v.add_subview(seg_detail)
        self.seg_detail = seg_detail

        mode_label = ui.Label()
        mode_label.text = "Mode:"
        mode_label.text_color = "white"
        mode_label.background_color = "#111111"
        mode_label.frame = (300, y, 60, 22)
        v.add_subview(mode_label)

        seg_mode = ui.SegmentedControl()
        seg_mode.segments = ["combined", "per repo"]
        seg_mode.selected_index = 0
        seg_mode.frame = (360, y - 2, v.width - 370, 28)
        seg_mode.flex = "W"
        # Same accent color as detail segmented control
        seg_mode.tint_color = "#007aff"
        v.add_subview(seg_mode)
        self.seg_mode = seg_mode

        y += 36

        max_label = ui.Label()
        max_label.text = "Max Bytes/File:"
        max_label.text_color = "white"
        max_label.background_color = "#111111"
        max_label.frame = (10, y, 120, 22)
        v.add_subview(max_label)

        max_field = ui.TextField()
        max_field.text = str(DEFAULT_MAX_BYTES)
        max_field.frame = (130, y - 2, 140, 28)
        max_field.flex = "W"
        max_field.background_color = "#222222"
        max_field.text_color = "white"
        max_field.tint_color = "white"
        max_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        v.add_subview(max_field)
        self.max_field = max_field

        y += 36

        split_label = ui.Label()
        split_label.text = "Split Size (MB):"
        split_label.text_color = "white"
        split_label.background_color = "#111111"
        split_label.frame = (10, y, 120, 22)
        v.add_subview(split_label)

        split_field = ui.TextField()
        split_field.placeholder = "0 = No Split"
        split_field.text = ""
        split_field.frame = (130, y - 2, 140, 28)
        split_field.flex = "W"
        split_field.background_color = "#222222"
        split_field.text_color = "white"
        split_field.tint_color = "white"
        split_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        v.add_subview(split_field)
        self.split_field = split_field

        y += 36

        info_label = ui.Label()
        info_label.text_color = "white"
        info_label.background_color = "#111111"
        info_label.font = ("<System>", 11)
        info_label.number_of_lines = 1
        info_label.frame = (10, y, v.width - 20, 18)
        info_label.flex = "W"
        v.add_subview(info_label)
        self.info_label = info_label
        self._update_repo_info()

        y += 26

        btn = ui.Button()
        btn.title = "Run Merge"
        btn.frame = (10, y, v.width - 20, 40)
        btn.flex = "W"
        btn.background_color = "#007aff"
        btn.tint_color = "white"
        btn.corner_radius = 6.0
        btn.action = self.run_merge
        v.add_subview(btn)
        self.run_button = btn

    def _update_repo_info(self) -> None:
        if not self.repos:
            self.info_label.text = "No repos found in Hub."
        else:
            self.info_label.text = f"{len(self.repos)} Repos found."

    def _tableview_cell(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.background_color = "#111111"
        if 0 <= row < len(self.repos):
            cell.text_label.text = self.repos[row]
        cell.text_label.text_color = "white"
        cell.text_label.background_color = "#111111"

        selected_bg = ui.View()
        selected_bg.background_color = "#333333"
        cell.selected_background_view = selected_bg
        return cell

    def _get_selected_repos(self) -> List[str]:
        tv = self.tv
        rows = tv.selected_rows or []
        if not rows:
            return list(self.repos)
        names: List[str] = []
        for section, row in rows:
            if 0 <= row < len(self.repos):
                names.append(self.repos[row])
        return names

    def _parse_max_bytes(self) -> int:
        txt = (self.max_field.text or "").strip()
        if not txt:
            return DEFAULT_MAX_BYTES
        try:
            val = int(txt)
            if val <= 0:
                raise ValueError()
            return val
        except Exception:
            return DEFAULT_MAX_BYTES

    def _parse_split_size(self) -> int:
        txt = (self.split_field.text or "").strip()
        if not txt:
            return 0
        try:
            # Assume MB if plain number in UI, or allow "1GB"
            if txt.isdigit():
                return int(txt) * 1024 * 1024
            return parse_human_size(txt)
        except Exception:
            return 0

    def run_merge(self, sender) -> None:
        try:
            self._run_merge_inner()
        except Exception as e:
            traceback.print_exc()
            msg = f"Error: {e}"
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(msg, file=sys.stderr)

    def _run_merge_inner(self) -> None:
        selected = self._get_selected_repos()
        if not selected:
            if console:
                console.alert("wc-merger", "No repos selected.", "OK", hide_cancel_button=True)
            return

        ext_text = (self.ext_field.text or "").strip()
        extensions = _normalize_ext_list(ext_text)

        path_contains = (self.path_field.text or "").strip() or None

        detail_idx = self.seg_detail.selected_index
        detail = ["overview", "summary", "dev", "max"][detail_idx]

        mode_idx = self.seg_mode.selected_index
        mode = ["gesamt", "pro-repo"][mode_idx]

        max_bytes = self._parse_max_bytes()
        split_size = self._parse_split_size()
        plan_only = False

        summaries = []
        for name in selected:
            root = self.hub / name
            if not root.is_dir():
                continue
            summary = scan_repo(root, extensions or None, path_contains, max_bytes)
            summaries.append(summary)

        if not summaries:
            if console:
                console.alert("wc-merger", "No valid repos found.", "OK", hide_cancel_button=True)
            return

        merges_dir = get_merges_dir(self.hub)
        out_paths = write_reports_v2(
            merges_dir,
            self.hub,
            summaries,
            detail,
            mode,
            max_bytes,
            plan_only,
            split_size,
        )

        if not out_paths:
            if console:
                console.alert("wc-merger", "No report generated.", "OK", hide_cancel_button=True)
            else:
                print("No report generated.")
            return

        main_report = out_paths[0]
        if editor:
            try:
                editor.open_file(str(main_report))
            except Exception:
                pass

        msg = f"Generated {len(out_paths)} report(s)."
        if console:
            try:
                console.hud_alert(msg)
            except Exception:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
        else:
            print(f"wc-merger: OK ({msg})")
            for p in out_paths:
                print(f"  - {p.name}")


# --- CLI Mode ---

def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="wc-merger CLI")
    parser.add_argument("paths", nargs="*", help="Repositories to merge")
    parser.add_argument("--hub", help="Base directory (wc-hub)")
    parser.add_argument("--level", choices=["overview", "summary", "dev", "max"], default="dev")
    parser.add_argument("--mode", choices=["gesamt", "pro-repo"], default="gesamt")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--split-size", help="Split output into chunks (e.g. 50MB, 1GB)")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    hub = detect_hub_dir(script_path, args.hub)

    sources = []
    if args.paths:
        for p in args.paths:
            path = Path(p)
            if not path.exists():
                path = hub / p
            if path.exists() and path.is_dir():
                sources.append(path)
            else:
                print(f"Warning: {path} not found.")
    else:
        repos = find_repos_in_hub(hub)
        for r in repos:
            sources.append(hub / r)

    if not sources:
        cwd = Path.cwd()
        print(f"No sources in hub ({hub}). Scanning current directory: {cwd}")
        sources.append(cwd)

    print(f"Hub: {hub}")
    print(f"Sources: {[s.name for s in sources]}")

    summaries = []
    for src in sources:
        print(f"Scanning {src.name}...")
        summary = scan_repo(src, None, None, args.max_bytes)
        summaries.append(summary)

    split_size = 0
    if args.split_size:
        split_size = parse_human_size(args.split_size)
        print(f"Splitting at {split_size} bytes")

    merges_dir = get_merges_dir(hub)
    out_paths = write_reports_v2(merges_dir, hub, summaries, args.level, args.mode, args.max_bytes, args.plan_only, split_size, debug=args.debug)

    print(f"Generated {len(out_paths)} report(s):")
    for p in out_paths:
        print(f"  - {p}")


def main():
    if ui is not None:
        script_path = Path(__file__).resolve()
        hub = detect_hub_dir(script_path)
        ui_obj = MergerUI(hub)
        ui_obj.view.present("sheet")
    else:
        main_cli()

if __name__ == "__main__":
    main()

```

[↑ Zurück zum Manifest](#manifest)
