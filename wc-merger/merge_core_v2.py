# -*- coding: utf-8 -*-

"""
merge_core_v2 – Enhanced core functions for wc-merger.
Implements improved AI-friendly formatting, tagging, and structure.
"""

import os
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Any, Iterator

# --- Configuration & Heuristics ---

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


def classify_file_v2(rel_path: Path, ext: str) -> Tuple[str, List[str]]:
    """
    Returns (category, tags).
    Categories: config, doc, source, test, contract, other
    Tags: ai-context, ci, wgx-profile, script, adr, lockfile, etc.
    """
    parts = rel_path.parts
    name = rel_path.name.lower()
    tags = []

    # Identify specific tags first
    if name == ".ai-context.yml":
        tags.append("ai-context")
    if ".github" in parts and "workflows" in parts:
        tags.append("ci")
    if ".wgx" in parts and name.startswith("profile"):
        tags.append("wgx-profile")
    if "scripts" in parts:
        tags.append("script")
    if "docs" in parts and "adr" in parts:
        tags.append("adr")
    if name in SUMMARIZE_FILES:
        tags.append("lockfile")

    # Determine Category
    category = "other"

    if name in CONFIG_FILENAMES or "config" in parts or "configs" in parts or ".github" in parts or ".wgx" in parts:
        category = "config"
    elif ext in DOC_EXTENSIONS or "docs" in parts or "doc" in parts:
        category = "doc"
    elif "contracts" in parts or "contract" in parts or "schemas" in parts:
        category = "contract"
    elif "tests" in parts or "test" in parts or name.endswith("_test.py") or name.startswith("test_"):
        category = "test"
    elif ext in SOURCE_EXTENSIONS or "src" in parts or "crates" in parts:
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

    files.sort(key=lambda fi: (fi.root_label.lower(), str(fi.rel_path).lower()))

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
    for fi in file_infos:
        by_root.setdefault(fi.root_label, []).append(fi.rel_path)

    lines = ["```"]
    for root in sorted(by_root.keys()):
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
                    head + f"\n\n... [TRUNCATED {human_size(f_size - head_size - tail_size)}] ...\n\n" + tail,
                    True,
                    f"Original size: {human_size(fi.size)}. Included: First {human_size(head_size)} + Last {human_size(tail_size)}."
                )
            else:
                # Should have been caught by size check, but just in case
                f.seek(0)
                return f.read(), False, ""

    except OSError as e:
        return f"_Error reading file: {e}_", False, ""

def iter_report_blocks(files: List[FileInfo], level: str, max_file_bytes: int, sources: List[Path], plan_only: bool) -> Iterator[str]:
    now = datetime.datetime.now()
    total_size = sum(fi.size for fi in files)
    text_files = [fi for fi in files if fi.is_text]

    # Filter files based on level
    included_files = []

    for fi in text_files:
        if level == "overview":
            continue
        elif level == "summary":
            if fi.size <= max_file_bytes:
                included_files.append(fi)
        elif level == "dev":
             if "lockfile" in fi.tags and fi.size > 20000:
                 included_files.append(fi)
             else:
                 included_files.append(fi)
        else: # max
            included_files.append(fi)

    cat_stats = summarize_categories(files)

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

    # --- Header ---
    header = []
    header.append("# WC-Merge Report (v2)")
    header.append("")
    header.append(f"**Date:** {now.strftime('%Y-%m-%d %H:%M:%S')}")
    header.append(f"**Level:** `{level}`")
    header.append(f"**Max File Bytes:** {human_size(max_file_bytes)}")
    header.append("")
    header.append("> **Note for AIs:**")
    header.append("> 1. **Context:** Read `README.md`, `docs/runbook.md`, `*.ai-context.yml` first.")
    header.append("> 2. **Structure:** See `## 📁 Structure` and `## 🧾 Manifest`.")
    header.append("> 3. **Content:** Files are in `## 📄 Content`. Each file has a metadata block.")
    if level == "dev":
         header.append("> 4. **Profile:** `dev` - Focus on code, docs, CI. Large lockfiles are summarized.")
    elif level == "max":
         header.append("> 4. **Profile:** `max` - All text files included (large ones truncated).")
    header.append("")
    yield "\n".join(header) + "\n"

    # --- Plan ---
    plan = []
    plan.append("## 🧮 Plan")
    plan.append("")
    plan.append(f"- **Total Files:** {len(files)} (Text: {len(text_files)})")
    plan.append(f"- **Total Size:** {human_size(total_size)}")
    plan.append(f"- **Included Content:** {len(included_files)} files")
    plan.append("")
    plan.append("**Folder Highlights:**")
    if code_folders: plan.append(f"- Code: `{', '.join(sorted(code_folders))}`")
    if doc_folders: plan.append(f"- Docs: `{', '.join(sorted(doc_folders))}`")
    if infra_folders: plan.append(f"- Infra: `{', '.join(sorted(infra_folders))}`")
    plan.append("")
    if cat_stats:
        plan.append("| Category | Files | Size |")
        plan.append("| --- | ---: | ---: |")
        for cat in sorted(cat_stats.keys()):
            cnt, sz = cat_stats[cat]
            plan.append(f"| `{cat}` | {cnt} | {human_size(sz)} |")
    plan.append("")
    yield "\n".join(plan) + "\n"

    if plan_only:
        return

    # --- Structure ---
    structure = []
    structure.append("## 📁 Structure")
    structure.append("")
    structure.append(build_tree(files))
    structure.append("")
    yield "\n".join(structure) + "\n"

    # --- Manifest ---
    manifest = []
    manifest.append("## 🧾 Manifest")
    manifest.append("")
    manifest.append("| Path | Category | Tags | Size | MD5 |")
    manifest.append("| --- | --- | --- | ---: | --- |")
    for fi in files:
        tags_str = ", ".join(fi.tags) if fi.tags else "-"
        manifest.append(
            f"| `{fi.root_label}/{fi.rel_path}` | `{fi.category}` | {tags_str} | {human_size(fi.size)} | `{fi.md5}` |"
        )
    manifest.append("")
    yield "\n".join(manifest) + "\n"

    # --- Content ---
    if included_files:
        yield "## 📄 Content\n\n"

        for fi in included_files:
            block = []

            is_summary_only = False
            if level == "dev" and "lockfile" in fi.tags and fi.size > 20000:
                is_summary_only = True

            block.append(f"### 📄 {fi.root_label}/{fi.rel_path}")
            block.append(f"**Category:** {fi.category}")
            if fi.tags:
                block.append(f"**Tags:** `[{', '.join(fi.tags)}]`")
            block.append(f"**Size:** {human_size(fi.size)}")
            block.append(f"**MD5:** `{fi.md5}`")

            if is_summary_only:
                 block.append("")
                 block.append("> [SUMMARY ONLY] Large lockfile omitted in 'dev' profile.")
                 block.append("")
                 yield "\n".join(block) + "\n\n"
                 continue

            content, truncated, trunc_msg = read_smart_content(fi, max_file_bytes)

            if truncated:
                block.append(f"**Truncated:** {trunc_msg}")
            else:
                block.append("**Truncated:** No (Full content)")

            lang = lang_for(fi.ext)
            block.append("")
            block.append(f"```{lang}")
            block.append(content)
            block.append("```")
            block.append("")
            yield "\n".join(block) + "\n\n"

def generate_report_content(files: List[FileInfo], level: str, max_file_bytes: int, sources: List[Path], plan_only: bool) -> str:
    return "".join(iter_report_blocks(files, level, max_file_bytes, sources, plan_only))

def write_reports_v2(merges_dir: Path, hub: Path, repo_summaries: List[Dict], detail: str, mode: str, max_bytes: int, plan_only: bool, split_size: int = 0) -> List[Path]:
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

                # If we have only a header line and nothing else, and it's not the first part, maybe skip?
                # But safer to just write it.

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

            iterator = iter_report_blocks(target_files, detail, max_bytes, target_sources, plan_only)

            for block in iterator:
                block_len = len(block.encode('utf-8'))

                # If adding this block exceeds limit, flush first
                # But ensure we have at least something besides the header
                if current_size + block_len > split_size and len(current_lines) > 1:
                    flush_part()

                current_lines.append(block)
                current_size += block_len

            flush_part(is_last=True)

        else:
            # Standard single file
            content = generate_report_content(target_files, detail, max_bytes, target_sources, plan_only)
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
