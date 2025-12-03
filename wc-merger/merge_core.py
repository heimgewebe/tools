# -*- coding: utf-8 -*-
import os
import datetime
import hashlib
import fnmatch
from pathlib import Path

# --- Constants & Configuration ---

SKIP_DIRS = {
    ".git", ".idea", ".vscode", "node_modules", ".svelte-kit", ".next",
    "dist", "build", "target", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".DS_Store", "coverage", ".tox", ".mypy_cache", "site-packages"
}

SKIP_FILES = {
    ".DS_Store", "Thumbs.db", ".directory"
}

# Files that should be treated as sensitive and NOT embedded in content
SENSITIVE_PATTERNS = {
    ".env", ".env.*", "*.key", "*.pem", "*.p12", "id_rsa", "id_dsa",
    "secrets.*", "*.kdbx", "*.pfx", ".npmrc", ".pypirc",
    "credentials", "token", "api_key"
}

# Whitelist for .env files that are safe
SAFE_ENV_FILES = {
    ".env.example", ".env.template", ".env.sample", ".env.defaults"
}

TEXT_EXTENSIONS = {
    ".md", ".txt", ".rst", ".py", ".rs", ".ts", ".tsx", ".js", ".jsx",
    ".json", ".jsonl", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".sh", ".bash", ".zsh", ".fish", ".dockerfile", "dockerfile",
    ".svelte", ".css", ".scss", ".less", ".html", ".htm", ".xml", ".csv",
    ".log", ".lock", ".properties", ".gradle", ".groovy", ".kt", ".kts",
    ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rb", ".php", ".pl",
    ".lua", ".sql", ".bat", ".cmd", ".ps1", ".make", "makefile", "justfile",
    ".tf", ".hcl", ".gitignore", ".gitattributes", ".editorconfig"
}

# Mapping extensions to Markdown language identifiers
LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "html": "html",
    "css": "css", "scss": "scss", "sass": "sass", "json": "json", "xml": "xml",
    "yaml": "yaml", "yml": "yaml", "md": "markdown", "sh": "bash", "bat": "batch",
    "sql": "sql", "php": "php", "cpp": "cpp", "c": "c", "java": "java",
    "cs": "csharp", "go": "go", "rs": "rust", "rb": "ruby", "swift": "swift",
    "kt": "kotlin", "svelte": "svelte", "toml": "toml", "ini": "ini",
    "dockerfile": "dockerfile", "tf": "hcl", "hcl": "hcl"
}

# --- Data Structures ---

class FileInfo:
    def __init__(self, root_label, abs_path, rel_path, size, is_text, md5, category, ext, flags=None):
        self.root_label = root_label
        self.abs_path = abs_path
        self.rel_path = rel_path
        self.size = size
        self.is_text = is_text
        self.md5 = md5
        self.category = category
        self.ext = ext
        self.flags = flags or []

# --- Core Logic ---

def human_size(n):
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0 or unit == "GB":
            return "{0:.2f} {1}".format(size, unit)
        size /= 1024.0
    return "{0:.2f} GB".format(size)

def is_sensitive(filename):
    if filename in SAFE_ENV_FILES:
        return False
    for pattern in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False

def is_probably_text(path, size):
    name = path.name.lower()
    if is_sensitive(name):
        # Sensitive files are text-like usually, but handled separately.
        # Here we just want to know if it's binary or text for classification.
        pass

    if path.suffix.lower() in TEXT_EXTENSIONS or name in TEXT_EXTENSIONS:
        return True

    # Large unknown files -> binary
    if size > 10 * 1024 * 1024:
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

def classify_category(rel_path):
    parts = [p.lower() for p in rel_path.parts]
    name = rel_path.name.lower()
    ext = rel_path.suffix.lower()

    # CI
    if ".github" in parts or ".gitlab" in parts or ".circleci" in parts:
        return "ci"
    if name in ("dockerfile", "docker-compose.yml", "docker-compose.yaml", "justfile", "makefile"):
        return "ci"

    # Config
    if name in ("package.json", "package-lock.json", "pyproject.toml", "cargo.toml", "go.mod", "pom.xml", "requirements.txt"):
        return "config"
    if ext in (".ini", ".cfg", ".conf", ".toml", ".yaml", ".yml", ".json"):
        # Could be config or data. If in 'config' dir, definitely config.
        if "config" in parts or "conf" in parts or "settings" in parts:
            return "config"
        # Otherwise, keep looking or default to config for now?
        # Let's say generic json/yaml is config unless other heuristic applies.
        return "config"

    # Doc
    if "docs" in parts or "doc" in parts:
        return "doc"
    if ext in (".md", ".rst", ".adoc", ".txt") or name.startswith("readme"):
        return "doc"

    # Test
    if "test" in parts or "tests" in parts or "spec" in parts or "specs" in parts:
        return "test"
    if name.startswith("test_") or name.endswith("_test.py") or name.endswith(".test.ts") or name.endswith(".spec.ts"):
        return "test"

    # Contract
    if "contracts" in parts or "contract" in parts or "proto" in parts or "schemas" in parts:
        return "contract"
    if ext in (".proto", ".graphql", ".gql"):
        return "contract"

    # Source
    if ext in (".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt", ".sh"):
        return "source"

    return "other"

def is_compact_match(rel_path, category):
    """
    Determines if a file should be included in 'Compact' mode.
    Focus: Core artifacts, READMEs, Docs, Contracts, central scripts/tests.
    """
    parts = rel_path.parts
    name = rel_path.name.lower()
    path_str = str(rel_path).lower()

    # Always include READMEs and key root files
    if name.startswith("readme") or name in ("changelog.md", "contributing.md", "license"):
        return True

    # Always include CI workflows
    if ".github/workflows" in path_str:
        return True

    # Always include Contracts/Schemas
    if category == "contract":
        return True
    if "contracts" in parts or "schemas" in parts:
        return True

    # Include key package definitions
    if name in ("package.json", "cargo.toml", "pyproject.toml", "go.mod", "pom.xml"):
        return True

    # Include central scripts (but not everything)
    if "scripts" in parts and len(parts) <= 3: # heuristics for top-level scripts
        return True

    # Runbooks / ADRs
    if "runbook" in path_str or "adr" in path_str:
        return True

    # Entry points for tests (heuristics)
    if category == "test":
        if name in ("run_tests.sh", "conftest.py"):
            return True

    return False

def scan_repo(repo_path, root_label, max_file_bytes):
    repo_path = Path(repo_path).resolve()
    files = []

    for dirpath, dirnames, filenames in os.walk(str(repo_path)):
        # Filter directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]

        for fn in filenames:
            if fn in SKIP_FILES:
                continue

            abs_path = Path(dirpath) / fn
            rel_path = abs_path.relative_to(repo_path)

            try:
                st = abs_path.stat()
                size = st.st_size
            except OSError:
                continue

            flags = []

            if is_sensitive(fn):
                flags.append("sensitive")

            is_text = is_probably_text(abs_path, size)
            if not is_text:
                flags.append("binary")

            # Checkmd5 for all files? For large files, maybe skip or limit?
            # repomerger limits md5 to limit_bytes if text or small enough.
            if is_text or size <= max_file_bytes:
                md5 = compute_md5(abs_path, max_file_bytes)
            else:
                md5 = ""

            category = classify_category(rel_path)
            ext = abs_path.suffix.lower()

            files.append(FileInfo(
                root_label=root_label,
                abs_path=abs_path,
                rel_path=rel_path,
                size=size,
                is_text=is_text,
                md5=md5,
                category=category,
                ext=ext,
                flags=flags
            ))

    files.sort(key=lambda x: (x.root_label, str(x.rel_path)))
    return files

def build_tree_text(file_infos):
    by_root = {}
    for fi in file_infos:
        by_root.setdefault(fi.root_label, []).append(fi.rel_path)

    lines = []
    for root in sorted(by_root.keys()):
        rels = by_root[root]
        lines.append(f"📁 {root}/")

        # Build a nested dict tree
        tree = {}
        for r in rels:
            parts = r.parts
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

    return "\n".join(lines)

def generate_report(sources, file_infos, level, max_file_bytes, encoding="utf-8"):
    now = datetime.datetime.now()
    lines = []

    # Filter logic for content inclusion
    # Plan: No content
    # Compact: Content for specific important files
    # Max: Content for all text files (truncated if too large)

    files_with_content = []
    if level != "plan":
        for fi in file_infos:
            if not fi.is_text:
                continue
            if "sensitive" in fi.flags:
                continue

            if level == "compact":
                if is_compact_match(fi.rel_path, fi.category):
                    files_with_content.append(fi)
            elif level == "max":
                files_with_content.append(fi)

    # Statistics
    total_files = len(file_infos)
    text_files_count = sum(1 for f in file_infos if f.is_text)
    binary_files_count = total_files - text_files_count
    total_size = sum(f.size for f in file_infos)

    cat_stats = {}
    for fi in file_infos:
        c = fi.category
        if c not in cat_stats:
            cat_stats[c] = [0, 0] # count, size
        cat_stats[c][0] += 1
        cat_stats[c][1] += fi.size

    # --- Header ---
    lines.append("# wc-merge Report")
    lines.append("")
    lines.append(f"**Date:** {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("**Sources:**")
    for s in sources:
        lines.append(f"- `{s}`")
    lines.append(f"**Level:** `{level}`")
    lines.append(f"**Max File Bytes:** {human_size(max_file_bytes)}")
    lines.append("")

    # --- Plan ---
    lines.append("## 🧮 Plan")
    lines.append("")
    lines.append(f"- **Total Files:** {total_files}")
    lines.append(f"- **Text Files:** {text_files_count}")
    lines.append(f"- **Binary Files:** {binary_files_count}")
    lines.append(f"- **Total Size:** {human_size(total_size)}")
    lines.append(f"- **Files with Content:** {len(files_with_content)}")
    lines.append("")

    lines.append("| Category | Files | Size |")
    lines.append("| --- | ---: | ---: |")
    for cat in sorted(cat_stats.keys()):
        cnt, sz = cat_stats[cat]
        lines.append(f"| `{cat}` | {cnt} | {human_size(sz)} |")
    lines.append("")

    # --- Structure ---
    lines.append("## 📁 Structure")
    lines.append("")
    lines.append("```")
    lines.append(build_tree_text(file_infos))
    lines.append("```")
    lines.append("")

    # --- Manifest ---
    lines.append("## 🧾 Manifest")
    lines.append("")
    lines.append("| Root | Path | Category | Type | Size | Hash | Flags |")
    lines.append("| --- | --- | --- | --- | ---: | --- | --- |")
    for fi in file_infos:
        ftype = "text" if fi.is_text else "bin"
        flag_str = ", ".join(fi.flags) if fi.flags else "-"
        lines.append(f"| `{fi.root_label}` | `{fi.rel_path}` | `{fi.category}` | {ftype} | {human_size(fi.size)} | `{fi.md5}` | {flag_str} |")
    lines.append("")

    # --- Content ---
    if level != "plan":
        lines.append("## 📄 Content")
        lines.append("")
        for fi in files_with_content:
            lines.append(f"### `{fi.root_label}/{fi.rel_path}`")
            lines.append("")

            truncated = False
            content = ""
            try:
                with fi.abs_path.open("r", encoding=encoding, errors="replace") as f:
                    if fi.size > max_file_bytes:
                        content = f.read(max_file_bytes)
                        truncated = True
                    else:
                        content = f.read()
            except Exception as e:
                lines.append(f"_Error reading file: {e}_")
                lines.append("")
                continue

            if truncated:
                lines.append(f"> ⚠️ **Truncated**: File size ({human_size(fi.size)}) exceeds limit ({human_size(max_file_bytes)}). Content is cut off.")
                lines.append("")

            ext_key = fi.ext.lstrip(".").lower()
            lang = LANG_MAP.get(ext_key, "")

            lines.append(f"```{lang}")
            lines.append(content)
            if truncated:
                lines.append("\n[... truncated ...]")
            lines.append("```")
            lines.append("")

    return "\n".join(lines)
