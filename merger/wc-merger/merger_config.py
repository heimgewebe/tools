from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, Dict, List, Optional, Tuple

SPEC_VERSION = "2.4"
MERGES_DIR_NAME = "merges"
MERGE_CONTRACT_NAME = "wc-merge-report"
MERGE_CONTRACT_VERSION = SPEC_VERSION
DEFAULT_MAX_BYTES = 0

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
    "machine-lean": "Tools – Machine-Lean",
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
]

# Top-level roots to skip in auto-discovery
SKIP_ROOTS = {
    MERGES_DIR_NAME,
    "merge",
    "output",
    "out",
}

SKIP_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "venv",
    ".mypy_cache",
    "coverage",
}

SKIP_FILES = {
    ".DS_Store",
    "thumbs.db",
}

class NavStyle:
    """Standardized navigation anchors for hyperlinking."""

    @staticmethod
    def file_anchor(rel_path: Path) -> str:
        """Sanitized anchor for file paths in Manifest/Structure/Content."""
        return f"file-{str(rel_path).replace('/', '-').replace('.', '-').lower()}"

    @staticmethod
    def repo_anchor(repo_name: str) -> str:
        """Anchor for repository section in Structure."""
        return f"repo-{repo_name.lower()}"

    @staticmethod
    def category_anchor(category: str) -> str:
        """Anchor for category in Index."""
        return f"cat-{category.lower()}"

    @staticmethod
    def tag_anchor(tag: str) -> str:
        """Anchor for tag in Index."""
        return f"tag-{tag.lower()}"


@dataclass
class DebugConfig:
    """Configuration for debug checks and severity levels."""

    # Severity levels: 'info', 'warning', 'error', 'ignore'
    unknown_category_level: str = "info"
    unknown_tag_level: str = "info"
    missing_readme_level: str = "info"

    allowed_categories: Set[str] = field(default_factory=lambda: {
        "source", "test", "doc", "config", "contract", "other"
    })

    code_only_categories: Set[str] = field(default_factory=lambda: {
        "source", "test", "config", "contract"
    })

    allowed_tags: Set[str] = field(default_factory=lambda: {
        "ai-context", "runbook", "lockfile", "script", "ci", "adr", "feed", "wgx-profile"
    })


@dataclass
class ExtrasConfig:
    """Configuration for optional report features (v2.3 Spec)."""
    health: bool = False
    organism_index: bool = False
    fleet_panorama: bool = False
    augment_sidecar: bool = False
    delta_reports: bool = False
    json_sidecar: bool = False
    heatmap: bool = False
