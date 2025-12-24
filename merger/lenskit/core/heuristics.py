from __future__ import annotations
# -*- coding: utf-8 -*-

"""
heuristics.py – Project-specific policies, lists, and classification logic.
"""

from pathlib import Path
from typing import Tuple, List

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

def classify_file(rel_path: Path, ext: str) -> Tuple[str, List[str]]:
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


def is_critical_file(rel_path_str: str) -> bool:
    """
    Checks if a file is critical and should be force-included regardless of filters.
    Rules:
    - README.md (any case)
    - .ai-context.yml
    - .wgx/profile.yml
    - .github/workflows/*guard*
    """
    lower = rel_path_str.lower()
    if lower == "readme.md" or lower.endswith("/readme.md"):
        return True
    if lower == ".ai-context.yml" or lower.endswith("/.ai-context.yml"):
        return True
    if ".wgx/profile.yml" in lower:
        return True
    if ".github/workflows/" in lower and "guard" in lower:
        return True
    return False


class FileInfo(object):
    """Container for file metadata."""
    def __init__(self, root_label, abs_path, rel_path, size, is_text, md5, category, tags, ext, skipped=False, reason=None, content=None, inclusion_reason="normal"):
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
        self.inclusion_reason = inclusion_reason
        self.anchor = "" # Will be set during report generation
        self.anchor_alias = "" # Backwards-compatible anchor (without hash suffix)
        self.roles = [] # Will be computed during report generation


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
