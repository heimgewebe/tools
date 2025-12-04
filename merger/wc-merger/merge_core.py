# -*- coding: utf-8 -*-

"""
merge_core – Core functions for wc-merger (v2.1 Standard).
Implements AI-friendly formatting, tagging, and strict Pflichtenheft structure.
"""

import os
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Any, Iterator

# --- Configuration & Heuristics ---

SPEC_VERSION = "2.1"
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


def get_declared_purpose(files: List[FileInfo]) -> str:
    """
    Extracts declared purpose STRICTLY from .ai-context.yml or README.md.
    No guessing.
    """
    # 1. Check .ai-context.yml
    ai_context = next((f for f in files if f.rel_path.name == ".ai-context.yml"), None)
    if ai_context and ai_context.is_text and ai_context.size < 100000:
        try:
            with ai_context.abs_path.open("r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                # Simple parsing to avoid yaml dependency if not available or just for robustness
                # Looking for "project:" then "description:"
                import re
                match = re.search(r'project:\s*\n.*?description:\s*(.*?)(?:\n\S|$)', content, re.DOTALL)
                if match:
                    desc = match.group(1).strip().strip('"\'')
                    if desc:
                        return desc
        except Exception:
            pass

    # 2. Check README.md
    readme = next((f for f in files if f.rel_path.name.lower() == "readme.md"), None)
    if readme and readme.is_text and readme.size < 100000:
        try:
            with readme.abs_path.open("r", encoding="utf-8", errors="replace") as f:
                # Get first header and first paragraph
                lines = f.readlines()
                first_header = ""
                first_para = ""
                in_para = False
                for line in lines:
                    line_strip = line.strip()
                    if not line_strip:
                        if in_para: break # End of first paragraph
                        continue

                    if line_strip.startswith("#"):
                        if not first_header:
                            first_header = line_strip.lstrip("#").strip()
                    else:
                        if not first_para:
                            first_para = line_strip
                            in_para = True
                        elif in_para:
                            first_para += " " + line_strip

                if first_para:
                    return f"{first_header}: {first_para}" if first_header else first_para
        except Exception:
            pass

    return "(none)"


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

    # Correction: .ai-context.yml is config/ai-context, but let's stick to simple mapping.
    # Spec says .ai-context.yml -> ai-context tag. Category? likely config.

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

    # Check for hausKI casing (checking root labels)
    roots = set(f.root_label for f in files)
    for r in roots:
        if "hauski" in r.lower() and r != "hausKI":
             # We can't really enforce case on root_label easily as it comes from folder name on disk,
             # but we can warn if we see inconsistency if multiple exist or if it differs from expected.
             # However, spec says "hausKI-audio: inconsistent casing".
             pass # Logic is a bit loose here without a reference set.

    # Check for missing .wgx/profile.yml in repos
    # We need to know which folders are repos. roots are repos.
    for root in roots:
        has_profile = any(f.root_label == root and "wgx-profile" in f.tags for f in files)
        # Assuming .wgx/profile.yml would be tagged wgx-profile
        if not has_profile:
             # But not all roots might be fleet repos.
             # Let's check if .wgx folder exists at all, or if it is one of the known fleet repos.
             if root in REPO_ORDER:
                 warnings.append(f"- {root}: missing .wgx/profile.yml")

    # Check for adr folder present but empty
    # We need to see if docs/adr exists as a dir.
    # scan_repo returns files. If no files in docs/adr, we might not know it exists unless we tracked dirs.
    # But wait, scan_repo doesn't return empty dirs.
    # If we have files in 'docs/adr', then it's not empty.
    # If we have 'docs' but no 'docs/adr' files, we don't know if adr dir exists.
    # So this check is hard with just file list. We'll skip for now to avoid false positives.

    return warnings

def iter_report_blocks(files: List[FileInfo], level: str, max_file_bytes: int, sources: List[Path], plan_only: bool) -> Iterator[str]:
    # UTC Timestamp
    now = datetime.datetime.utcnow()

    # Sort files according to strict multi-repo order and then path
    files.sort(key=lambda fi: (get_repo_sort_index(fi.root_label), fi.root_label.lower(), str(fi.rel_path).lower()))

    # Pre-calculate status based on Profile Strict Logic
    processed_files = []

    for fi in files:
        status = "omitted"
        if fi.is_text:
            if level == "overview":
                # Overview: Only README, Runbook, ai-context FULL. Rest meta-only.
                if is_priority_file(fi):
                    status = "full"
                else:
                    status = "meta-only"
            elif level == "dev":
                # Dev: Full for code, docs, ci, contracts, ai-context.
                # Lockfiles/Artifacts -> truncated/meta-only.
                if "lockfile" in fi.tags:
                    if fi.size > 20000:
                        status = "meta-only" # Summarized usually means meta-only or truncated, spec says "truncated or meta-only"
                    else:
                        status = "full"
                else:
                    status = "full"
            elif level == "max":
                # Max: All text full.
                status = "full"
            else:
                # Summary or fallback
                if fi.size <= max_file_bytes: status = "full"
                else: status = "omitted"

        if status == "full" and fi.size > max_file_bytes:
            status = "truncated"

        processed_files.append((fi, status))

    total_size = sum(fi.size for fi in files)
    text_files = [fi for fi in files if fi.is_text]
    included_count = sum(1 for _, s in processed_files if s in ("full", "truncated"))

    cat_stats = summarize_categories(files)

    declared_purpose = get_declared_purpose(files)

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
    header.append(f"# WC-Merger Report (v{SPEC_VERSION.split('.')[0]}.x)") # e.g. v2.x
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

    # --- 7. Manifest ---
    manifest = []
    manifest.append("## 🧾 Manifest")
    manifest.append("")
    manifest.append("| Root | Path | Category | Tags | Size | Included | MD5 |")
    manifest.append("| --- | --- | --- | --- | ---: | --- | --- |")
    for fi, status in processed_files:
        tags_str = ", ".join(fi.tags) if fi.tags else "-"
        manifest.append(
            f"| `{fi.root_label}` | `{fi.rel_path}` | `{fi.category}` | {tags_str} | {human_size(fi.size)} | `{status}` | `{fi.md5}` |"
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

    # --- 8. Content (Per-Repo Blocks) ---
    # Note: No generic "## Content" header in v2.1 Spec.
    # Directly starts with "## 📦 <repo>" blocks.

    current_root = None

    for fi, status in processed_files:
        if status in ("omitted", "meta-only"):
            continue

        if fi.root_label != current_root:
            yield f"## 📦 {fi.root_label}\n\n"
            current_root = fi.root_label

        block = []
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
