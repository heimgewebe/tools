# -*- coding: utf-8 -*-

"""
merge_core – Core functions for wc-merger / wc-extractor.
Compatible with Pythonista and standard Python environments.
"""

import os
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set

# --- Configuration & Heuristics (from repomerger) ---

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
}

# Extensions considered text
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
    ".lock",   # e.g. Cargo.lock, pnpm-lock.yaml
    ".bats",   # added based on feedback
    ".properties",
    ".gradle",
    ".groovy",
    ".kt",
    ".kts",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".go",
    ".rb",
    ".php",
    ".pl",
    ".lua",
    ".sql",
    ".bat",
    ".cmd",
    ".ps1",
    ".make",
    "makefile",
    "justfile",
    ".tf",
    ".hcl",
    ".gitignore",
    ".gitattributes",
    ".editorconfig"
}

# Files typically considered configuration
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
    ".pre-commit-config.yaml",
    ".gitignore",
    ".gitmodules",
}

DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc"}

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
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".sh",
    ".bash"
}

LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "html": "html", "css": "css",
    "scss": "scss", "sass": "sass", "json": "json", "xml": "xml", "yaml": "yaml", "yml": "yaml",
    "md": "markdown", "sh": "bash", "bat": "batch", "sql": "sql", "php": "php", "cpp": "cpp",
    "c": "c", "java": "java", "cs": "csharp", "go": "go", "rs": "rust", "rb": "ruby",
    "swift": "swift", "kt": "kotlin", "svelte": "svelte", "toml": "toml", "ini": "ini",
    "dockerfile": "dockerfile", "tf": "hcl", "hcl": "hcl", "bats": "bash"
}

# Hardcoded path for Pythonista environment (wc-hub location)
HARDCODED_HUB_PATH = (
    "/private/var/mobile/Containers/Data/Application/"
    "B60D0157-973D-489A-AA59-464C3BF6D240/Documents/wc-hub"
)


class FileInfo(object):
    """Container for file metadata."""
    def __init__(self, root_label, abs_path, rel_path, size, is_text, md5, category, ext, skipped=False, reason=None, content=None):
        self.root_label = root_label
        self.abs_path = abs_path
        self.rel_path = rel_path
        self.size = size
        self.is_text = is_text
        self.md5 = md5
        self.category = category
        self.ext = ext
        self.skipped = skipped
        self.reason = reason
        self.content = content  # Can be pre-loaded or loaded on demand


# --- Utilities ---

def detect_hub_dir(script_path: Path, arg_base_dir: Optional[str] = None) -> Path:
    """
    Determines the base directory (Hub) for repos.
    Priority:
    1. ENV WC_MERGER_BASEDIR
    2. HARDCODED_HUB_PATH (Pythonista specific)
    3. CLI argument
    4. Fallback: Script's parent directory
    """
    # 1. ENV
    env_base = os.environ.get("WC_MERGER_BASEDIR")
    if env_base:
        p = Path(env_base).expanduser()
        try:
            p = p.resolve()
        except Exception:
            pass
        if p.is_dir():
            return p

    # 2. Hardcoded
    p = Path(HARDCODED_HUB_PATH)
    try:
        p = p.expanduser().resolve()
    except Exception:
        pass
    if p.is_dir():
        return p

    # 3. CLI Arg
    if arg_base_dir:
        p = Path(arg_base_dir).expanduser()
        try:
            p = p.resolve()
        except Exception:
            pass
        if p.is_dir():
            return p

    # 4. Fallback
    return script_path.parent


def get_merges_dir(hub: Path) -> Path:
    merges = hub / MERGES_DIR_NAME
    merges.mkdir(parents=True, exist_ok=True)
    return merges


def human_size(n):
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0 or unit == "GB":
            return "{0:.2f} {1}".format(size, unit)
        size /= 1024.0
    return "{0:.2f} GB".format(size)


def is_probably_text(path, size):
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


def compute_md5(path, limit_bytes=None):
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


def lang_for(ext):
    return LANG_MAP.get(ext.lower().lstrip("."), "")


def classify_category(rel_path, ext):
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

    # Enhanced categorization based on feedback
    if "contracts" in parts or "contract" in parts or "schemas" in parts:
        return "contract"
    if "scripts" in parts:
        return "source" # or 'script'? repomerger puts scripts in source if .sh
    if "tests" in parts or "test" in parts or name.endswith("_test.py") or name.startswith("test_"):
        return "test"

    return "other"


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

def scan_repo(repo_root: Path, extensions: Optional[List[str]], path_contains: Optional[str], max_bytes: int) -> Dict:
    repo_root = repo_root.resolve()
    root_label = repo_root.name
    files = []

    ext_filter = set(e.lower() for e in extensions) if extensions else None
    path_filter = path_contains.strip() if path_contains else None

    total_files = 0
    total_bytes = 0
    ext_hist: Dict[str, int] = {}
    max_file_size = 0
    max_file: Optional[str] = None

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

            # Skip .env except examples
            if fn.startswith(".env") and fn not in (".env.example", ".env.template", ".env.sample"):
                continue

            abs_path = Path(dirpath) / fn
            rel_path = abs_path.relative_to(repo_root)
            rel_path_str = rel_path.as_posix()

            # Path filter
            if path_filter and path_filter not in rel_path_str:
                continue

            # Extension filter
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

            if size > max_file_size:
                max_file_size = size
                max_file = rel_path_str

            is_text = is_probably_text(abs_path, size)
            category = classify_category(rel_path, ext)

            # MD5 calculation
            if is_text or size <= max_bytes:
                md5 = compute_md5(abs_path, max_bytes)
            else:
                md5 = ""

            skipped = False
            reason = None
            content = None

            if size > max_bytes and is_text:
                # We will handle truncation during reporting, but mark it here?
                # Actually repomerger logic handles content reading separately or on demand.
                # For compatibility with wc-merger provided logic which reads content immediately (in pythonista version),
                # we can choose strategy. But repomerger reads on demand in write_report to be cleaner.
                # HOWEVER, the pythonista `scan_repo` in the prompt read content eagerly.
                # "Inhalt laden" ...
                # Let's use lazy loading (store path) for efficiency unless we need it eagerly.
                # Given we are "merging" logic, let's stick to repomerger's robust style: store metadata, read later.
                pass

            fi = FileInfo(
                root_label=root_label,
                abs_path=abs_path,
                rel_path=rel_path,
                size=size,
                is_text=is_text,
                md5=md5,
                category=category,
                ext=ext
            )
            files.append(fi)

    files.sort(key=lambda fi: (fi.root_label.lower(), str(fi.rel_path).lower()))

    return {
        "root": repo_root,
        "name": root_label,
        "files": files,
        "total_files": total_files,
        "total_bytes": total_bytes,
        "ext_hist": ext_hist,
        "max_file": max_file,
        "max_file_size": max_file_size,
    }


# --- Reporting Logic (Repomerger Style) ---

def summarize_extensions(file_infos):
    counts = {}
    sizes = {}
    for fi in file_infos:
        ext = fi.ext or "<none>"
        counts[ext] = counts.get(ext, 0) + 1
        sizes[ext] = sizes.get(ext, 0) + fi.size
    return counts, sizes

def summarize_categories(file_infos):
    stats = {}
    for fi in file_infos:
        cat = fi.category or "other"
        if cat not in stats:
            stats[cat] = [0, 0]
        stats[cat][0] += 1
        stats[cat][1] += fi.size
    return stats

def build_tree(file_infos):
    by_root = {}
    for fi in file_infos:
        by_root.setdefault(fi.root_label, []).append(fi.rel_path)

    lines = ["```"]
    for root in sorted(by_root.keys()):
        rels = by_root[root]
        lines.append(f"📁 {root}/")

        tree = {}
        for r in rels:
            parts = list(r.parts)
            node = tree
            for p in parts:
                if p not in node:
                    node[p] = {}
                node = node[p]

        def walk(node, indent):
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

def make_output_filename(merges_dir: Path, repo_names: List[str], mode: str, detail: str) -> Path:
    ts = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    if not repo_names:
        base = "no-repos"
    else:
        base = "+".join(repo_names)
        if len(base) > 40:
            base = base[:37] + "..."
    # Sanitize base
    base = base.replace(" ", "-").replace("/", "_")

    fname = f"merge_{mode}_{base}_{detail}_{ts}.md"
    return merges_dir / fname

def generate_report_content(files: List[FileInfo], level: str, max_file_bytes: int, sources: List[Path], plan_only: bool, encoding="utf-8") -> str:
    now = datetime.datetime.now()

    total_size = sum(fi.size for fi in files)
    text_files = [fi for fi in files if fi.is_text]
    binary_files = [fi for fi in files if not fi.is_text]

    if level == "overview":
        planned_with_content = 0
    elif level == "summary":
        planned_with_content = sum(1 for fi in text_files if fi.size <= max_file_bytes)
    else:  # full / max
        planned_with_content = len(text_files)

    ext_counts, ext_sizes = summarize_extensions(files)
    cat_stats = summarize_categories(files)

    lines = []

    # Header
    lines.append("# WC-Merge Report")
    lines.append("")
    lines.append(f"**Date:** {now.strftime('%Y-%m-%d %H:%M:%S')}")
    if sources:
        lines.append("**Sources:**")
        for src in sources:
            lines.append(f"- `{src}`")
    lines.append(f"**Level:** `{level}`")
    lines.append(f"**Max File Bytes:** {human_size(max_file_bytes)}")
    lines.append("")

    lines.append("> Note for AIs:")
    lines.append("> - This is a file system snapshot.")
    lines.append("> - Tree: `## 📁 Structure`.")
    lines.append("> - Manifest: `## 🧾 Manifest`.")
    if level == "overview":
        lines.append("> - No file contents included.")
    elif level == "summary":
        lines.append("> - Includes content for small text files only.")
    else:
        lines.append("> - Includes content for all text files (truncated if too large).")
    lines.append("")

    # Plan
    lines.append("## 🧮 Plan")
    lines.append("")
    lines.append(f"- Total Files: **{len(files)}**")
    lines.append(f"- Text Files: **{len(text_files)}**")
    lines.append(f"- Binary Files: **{len(binary_files)}**")
    lines.append(f"- Files with content: **{planned_with_content}**")
    lines.append(f"- Total Size: **{human_size(total_size)}**")
    lines.append("")

    if cat_stats:
        lines.append("**Files by Category:**")
        lines.append("")
        lines.append("| Category | Files | Size |")
        lines.append("| --- | ---: | ---: |")
        for cat in sorted(cat_stats.keys()):
            cnt, sz = cat_stats[cat]
            lines.append(f"| `{cat}` | {cnt} | {human_size(sz)} |")
        lines.append("")

    if ext_counts:
        lines.append("**Extensions:**")
        lines.append("")
        lines.append("| Ext | Files | Size |")
        lines.append("| --- | ---: | ---: |")
        for ext in sorted(ext_counts.keys()):
            lines.append(f"| `{ext}` | {ext_counts[ext]} | {human_size(ext_sizes[ext])} |")
        lines.append("")

    if plan_only:
        return "\n".join(lines)

    # Structure
    lines.append("## 📁 Structure")
    lines.append("")
    lines.append(build_tree(files))
    lines.append("")

    # Manifest
    lines.append("## 🧾 Manifest")
    lines.append("")
    lines.append("| Root | Path | Category | Text | Size | MD5 |")
    lines.append("| --- | --- | --- | --- | ---: | --- |")
    for fi in files:
        lines.append(
            f"| `{fi.root_label}` | `{fi.rel_path}` | `{fi.category}` | {'yes' if fi.is_text else 'no'} | {human_size(fi.size)} | `{fi.md5}` |"
        )
    lines.append("")

    # Content
    if level != "overview":
        lines.append("## 📄 Content")
        lines.append("")
        for fi in files:
            if not fi.is_text:
                continue

            if level == "summary" and fi.size > max_file_bytes:
                continue

            lines.append(f"### `{fi.root_label}/{fi.rel_path}`")
            lines.append("")

            truncated = False
            content = ""

            # If content was preloaded (Pythonista style from prompt), use it
            if fi.content is not None:
                content = fi.content
                # Check length if we need to simulate truncation?
                # The prompt logic had truncation in 'scan_repo' via max_bytes.
                # Here we handle it display-side if possible.
            else:
                # Lazy load
                try:
                    with fi.abs_path.open("r", encoding=encoding, errors="replace") as f:
                        if fi.size > max_file_bytes:
                            # If level is full/max, we show up to limit.
                            content = f.read(max_file_bytes)
                            truncated = True
                        else:
                            content = f.read()
                except OSError as e:
                    lines.append(f"_Error reading file: {e}_")
                    lines.append("")
                    continue

            if truncated:
                 lines.append(f"**Note:** File > {human_size(max_file_bytes)}, content truncated.")
                 lines.append("")

            lang = lang_for(fi.ext)
            lines.append(f"```{lang}")
            lines.append(content.rstrip("\n"))
            if truncated:
                lines.append("\n[... truncated ...]")
            lines.append("```")
            lines.append("")

    return "\n".join(lines)

def write_reports(merges_dir: Path, hub: Path, repo_summaries: List[Dict], detail: str, mode: str, max_bytes: int, plan_only: bool) -> List[Path]:
    """
    Generates report files.
    """
    out_paths = []

    # Flatten all files for 'gesamt' mode
    all_files = []
    repo_names = []

    for s in repo_summaries:
        all_files.extend(s["files"])
        repo_names.append(s["name"])

    sources = [s["root"] for s in repo_summaries]

    if mode == "gesamt":
        out_path = make_output_filename(merges_dir, repo_names, mode, detail)
        content = generate_report_content(all_files, detail, max_bytes, sources, plan_only)
        out_path.write_text(content, encoding="utf-8")
        out_paths.append(out_path)

    else: # pro-repo
        for s in repo_summaries:
            s_name = s["name"]
            s_files = s["files"]
            s_root = s["root"]
            out_path = make_output_filename(merges_dir, [s_name], "repo", detail)
            content = generate_report_content(s_files, detail, max_bytes, [s_root], plan_only)
            out_path.write_text(content, encoding="utf-8")
            out_paths.append(out_path)

    return out_paths
