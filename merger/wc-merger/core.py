# -*- coding: utf-8 -*-

"""
merge_core – Core functions for wc-merger (v2.4 Standard).
Implements AI-friendly formatting, tagging, and strict Pflichtenheft structure.
"""

import os
import sys
import json
import hashlib
import datetime
import re
from pathlib import Path
from typing import Iterable, List, Dict, Optional, Tuple, Any, Iterator, NamedTuple, Set
from dataclasses import dataclass

try:
    import yaml
except ImportError:
    pass


# Default-Config (Dec 2025)
DEFAULT_LEVEL = "dev"
DEFAULT_MODE = "gesamt"  # combined
DEFAULT_SPLIT_SIZE = "25MB"
# Ab v2.3+: 0 = "kein Limit pro Datei".
DEFAULT_MAX_BYTES = 0
DEFAULT_MAX_FILE_BYTES = 0 # Alias for consistency
DEFAULT_EXTRAS = "health,augment_sidecar,organism_index,fleet_panorama,json_sidecar,ai_heatmap"


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _slug_token(s: str) -> str:
    """Deterministic ASCII token suitable for heading ids across renderers."""

    s = s.lower()
    s = s.replace("/", "-").replace(".", "-")
    s = _NON_ALNUM.sub("-", s).strip("-")
    return s


@dataclass(frozen=True)
class NavStyle:
    """
    Controls how much navigation noise is emitted into the report.
    - emit_search_markers: show '§§ token' lines for fallback search
    """

    emit_search_markers: bool = False


def _heading_block(level: int, token: str, title: Optional[str] = None, nav: Optional[NavStyle] = None) -> List[str]:
    """
    Return heading lines with stable token-based ids and optional title.
    """

    nav = nav or NavStyle()
    lines: List[str] = []
    if nav.emit_search_markers:
        lines.append(f"§§ {token}")
    lines.extend([f'<a id="{token}"></a>', "#" * level + " " + token, ""])
    if title:
        lines.append(f"**{title}**")
        lines.append("")
    return lines

# --- Configuration & Heuristics ---

SPEC_VERSION = "2.4"
MERGES_DIR_NAME = "merges"

MERGE_CONTRACT_NAME = "wc-merge-report"
MERGE_CONTRACT_VERSION = SPEC_VERSION

def _debug_log_func(debug: "DebugCollector", level: str):
    """
    Map configured severity levels to DebugCollector methods.
    """
    lvl = (level or "warn").strip().lower()
    if lvl in ("warn", "warning"):
        return debug.warn
    if lvl in ("error", "err"):
        return getattr(debug, "error", debug.warn)
    if lvl in ("info",):
        return getattr(debug, "info", debug.warn)

    debug.warn(
        "debug-config-invalid",
        "merge_core",
        f"Unbekannter severity-level '{level}'. Erlaubt: info|warn|error. Fallback: warn.",
    )
    return debug.warn

# Debug-Config (erweitert für v2.4)
@dataclass
class DebugConfig:
    """
    Zentralisiert Debug- und Validierungs-Einstellungen.
    """
    allowed_categories: Set[str]
    allowed_tags: Set[str]
    code_only_categories: Set[str]

    unknown_category_level: str = "warn"
    unknown_tag_level: str = "warn"

    @classmethod
    def defaults(cls) -> "DebugConfig":
        return cls(
            allowed_categories={"source", "test", "doc", "config", "contract", "other"},
            allowed_tags={
                "ai-context", "runbook", "lockfile", "script", "ci",
                "adr", "feed", "wgx-profile"
            },
            code_only_categories={"source", "test", "config", "contract"}
        )

DEBUG_CONFIG = DebugConfig.defaults()

AGENT_CONTRACT_NAME = "wc-merge-agent"
AGENT_CONTRACT_VERSION = "v1"

# Delta Report configuration
MAX_DELTA_FILES = 10  # Maximum number of files to show in each delta section

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


def _stable_file_id(fi: "FileInfo") -> str:
    """
    Stable across runs as long as repo + rel-path stay the same.
    """

    repo = (
        getattr(fi, "root_label", None)
        or getattr(fi, "repo", None)
        or getattr(fi, "repo_name", None)
        or ""
    )
    path = str(
        getattr(fi, "rel_path", None)
        or getattr(fi, "path", None)
        or getattr(fi, "abs_path", None)
        or ""
    )
    raw = f"{repo}:{path}".encode("utf-8", errors="ignore")
    return "f_" + hashlib.sha1(raw).hexdigest()[:12]


def _validate_agent_json_dict(d: Dict[str, Any], allow_empty_primary: bool = False) -> None:
    """
    Minimal, dependency-free validation.
    """

    if not isinstance(d, dict):
        raise ValueError("agent-json: top-level is not an object")
    meta = d.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("agent-json: missing/invalid meta")
    if meta.get("contract") != AGENT_CONTRACT_NAME:
        raise ValueError(f"agent-json: meta.contract must be {AGENT_CONTRACT_NAME}")
    if meta.get("contract_version") != AGENT_CONTRACT_VERSION:
        raise ValueError(
            f"agent-json: meta.contract_version must be {AGENT_CONTRACT_VERSION}"
        )
    artifacts = d.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("agent-json: missing/invalid artifacts")
    if "primary_json" not in artifacts:
        raise ValueError("agent-json: artifacts.primary_json missing")
    if not allow_empty_primary and not artifacts.get("primary_json"):
        raise ValueError("agent-json: artifacts.primary_json missing")
    files = d.get("files")
    if not isinstance(files, list):
        raise ValueError("agent-json: missing/invalid files[]")


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
    heatmap: bool = False
    json_sidecar: bool = False  # NEW: Enable JSON sidecar output

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


@dataclass
class MergeArtifacts:
    """
    Result object for write_reports_v2() containing all generated artifacts.
    Makes it explicit which artifact is the primary (JSON or Markdown).
    """
    primary_json: Optional[Path] = None
    human_md: Optional[Path] = None
    md_parts: List[Path] = None
    other: List[Path] = None

    def __post_init__(self):
        if self.md_parts is None:
            self.md_parts = []
        if self.other is None:
            self.other = []

    def get_all_paths(self) -> List[Path]:
        """Return all paths in deterministic order: primary first, then others."""
        paths = []
        if self.primary_json:
            paths.append(self.primary_json)
        if self.human_md and self.human_md not in paths:
            paths.append(self.human_md)
        for p in self.md_parts:
            if p not in paths:
                paths.append(p)
        for p in self.other:
            if p not in paths:
                paths.append(p)
        return paths

    def get_primary_path(self) -> Optional[Path]:
        """Return the primary artifact path (JSON if exists, otherwise Markdown)."""
        return self.primary_json or self.human_md


@dataclass
class RepoHealth:
    """Health status for a single repository."""
    repo_name: str
    status: str  # "ok", "warn", "critical"
    total_files: int
    category_counts: Dict[str, int]
    has_readme: bool
    has_wgx_profile: bool
    has_ci_workflows: bool
    has_contracts: bool
    has_ai_context: bool
    unknown_category_ratio: float
    unknown_categories: List[str]
    unknown_tags: List[str]
    warnings: List[str]
    recommendations: List[str]


class HealthCollector:
    """Collects health checks for repositories (Stage 1: Repo Doctor)."""

    def __init__(self) -> None:
        self._repo_health: Dict[str, RepoHealth] = {}

    def analyze_repo(self, root_label: str, files: List["FileInfo"]) -> RepoHealth:
        """Analyze health of a single repository."""
        # Count files per category
        category_counts: Dict[str, int] = {}
        for fi in files:
            cat = fi.category or "other"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Check for key files
        has_readme = any(f.rel_path.name.lower() == "readme.md" for f in files)
        has_wgx_profile = any(
            ".wgx" in f.rel_path.parts and str(f.rel_path).endswith("profile.yml")
            for f in files
        )
        has_ci_workflows = any("ci" in (f.tags or []) for f in files)
        has_contracts = any(f.category == "contract" for f in files)
        # Enhanced AI context detection: check tags and file paths (cached to avoid repeated conversions)
        has_ai_context = False
        for f in files:
            if "ai-context" in (f.tags or []):
                has_ai_context = True
                break
            path_lower = str(f.rel_path).lower()
            if "ai-context" in path_lower or path_lower.endswith(".ai-context.yml") or "ai-context" in f.rel_path.parts:
                has_ai_context = True
                break

        # Check for unknown categories/tags
        unknown_categories = []
        unknown_tags = []
        unknown_cat_count = 0
        other_count = 0

        for fi in files:
            cat = fi.category or "other"
            if cat not in DEBUG_CONFIG.allowed_categories:
                if cat not in unknown_categories:
                    unknown_categories.append(cat)
                unknown_cat_count += 1
            if cat == "other":
                other_count += 1

            for tag in fi.tags or []:
                if tag not in DEBUG_CONFIG.allowed_tags:
                    if tag not in unknown_tags:
                        unknown_tags.append(tag)

        unknown_category_ratio = 0.0
        if len(files) > 0:
            unknown_category_ratio = unknown_cat_count / len(files)

        # Generate warnings and recommendations
        warnings = []
        recommendations = []

        if not has_readme:
            warnings.append("No README.md found")
            recommendations.append("Add README.md for better AI/human navigation")

        if not has_wgx_profile:
            warnings.append("No .wgx/profile.yml found")
            recommendations.append("Create .wgx/profile.yml for Fleet conformance")

        if not has_ci_workflows:
            warnings.append("No CI workflows found")
            recommendations.append("Add .github/workflows for CI/CD")

        if not has_contracts:
            warnings.append("No contracts found")
            recommendations.append("Consider adding contract schemas")

        if not has_ai_context:
            warnings.append("No AI context files found")
            recommendations.append("Add .ai-context.yml files for better AI understanding")

        if unknown_categories:
            warnings.append(f"Unknown categories: {', '.join(unknown_categories)}")

        if unknown_tags:
            warnings.append(f"Unknown tags: {', '.join(unknown_tags)}")

        # Determine overall status
        if len(warnings) >= 4:
            status = "critical"
        elif len(warnings) >= 2:
            status = "warn"
        else:
            status = "ok"

        health = RepoHealth(
            repo_name=root_label,
            status=status,
            total_files=len(files),
            category_counts=category_counts,
            has_readme=has_readme,
            has_wgx_profile=has_wgx_profile,
            has_ci_workflows=has_ci_workflows,
            has_contracts=has_contracts,
            has_ai_context=has_ai_context,
            unknown_category_ratio=unknown_category_ratio,
            unknown_categories=unknown_categories,
            unknown_tags=unknown_tags,
            warnings=warnings,
            recommendations=recommendations,
        )

        try:
            health.other_count = other_count
        except AttributeError:
            pass

        self._repo_health[root_label] = health
        return health

    def get_all_health(self) -> List[RepoHealth]:
        """Get all repo health reports."""
        return list(self._repo_health.values())

    def render_markdown(self) -> str:
        """Render health report as markdown."""
        if not self._repo_health:
            return ""

        lines: List[str] = []
        lines.append("<!-- @health:start -->")
        lines.append("## 🩺 Repo Health")
        lines.append("")

        # 1. Repo Feindynamiken (Global)
        total_repos = len(self._repo_health)
        no_ci = sum(1 for h in self._repo_health.values() if not h.has_ci_workflows)
        no_contracts = sum(1 for h in self._repo_health.values() if not h.has_contracts)
        no_wgx = sum(1 for h in self._repo_health.values() if not h.has_wgx_profile)

        if no_ci > 0 or no_contracts > 0 or no_wgx > 0:
            lines.append("### ⚔ Repo Feindynamiken (Global Risks)")
            lines.append("")
            if no_ci > 0:
                lines.append(f"- {no_ci} Repos ohne CI-Workflows")
            if no_contracts > 0:
                lines.append(f"- {no_contracts} Repos ohne Contracts")
            if no_wgx > 0:
                lines.append(f"- {no_wgx} Repos ohne WGX-Profil")
            lines.append("")

        # 2. Per-Repo Report
        for health in sorted(self._repo_health.values(), key=lambda h: h.repo_name):
            # Status emoji
            status_emoji = {
                "ok": "✅",
                "warn": "⚠️",
                "critical": "🔴",
            }.get(health.status, "❓")

            lines.append(f"### {status_emoji} `{health.repo_name}` – {health.status.upper()}")
            lines.append("")
            lines.append(f"- **Total Files:** {health.total_files}")
            
            # Category breakdown
            if health.category_counts:
                cat_parts = [f"{cat}={count}" for cat, count in sorted(health.category_counts.items())]
                lines.append(f"- **Categories:** {', '.join(cat_parts)}")

            # Key indicators
            indicators = []
            indicators.append(f"README: {'yes' if health.has_readme else 'no'}")
            indicators.append(f"WGX Profile: {'yes' if health.has_wgx_profile else 'no'}")
            indicators.append(f"CI: {'yes' if health.has_ci_workflows else 'no'}")
            indicators.append(f"Contracts: {'yes' if health.has_contracts else 'no'}")
            indicators.append(f"AI Context: {'yes' if health.has_ai_context else 'no'}")
            lines.append(f"- **Indicators:** {', '.join(indicators)}")

            # Feindynamik-Scanner (Risiken)
            risks = []
            if not health.has_contracts:
                risks.append("❌ Keine Contracts gefunden → Änderungen nicht formal prüfbar.")
            else:
                risks.append("✅ Contracts vorhanden")

            if not health.has_ci_workflows:
                risks.append("❌ Keine CI-Workflows → Keine automatische Qualitätssicherung.")
            else:
                risks.append("✅ CI-Workflows vorhanden")

            if not health.has_wgx_profile:
                risks.append("❌ Kein WGX-Profil → Organismus kennt Standard-Jobs nicht.")
            else:
                risks.append("✅ WGX-Profil vorhanden")

            lines.append("")
            lines.append("**Risiko-Check (Feindynamik):**")
            for r in risks:
                lines.append(f"- {r}")

            if health.warnings:
                lines.append("")
                lines.append("**Detailed Warnings:**")
                for warning in health.warnings:
                    lines.append(f"  - {warning}")

            if health.recommendations:
                lines.append("")
                lines.append("**Recommendations:**")
                for rec in health.recommendations:
                    lines.append(f"  - {rec}")

            lines.append("")

        lines.append("<!-- @health:end -->")
        lines.append("")
        return "\n".join(lines)


class HeatmapCollector:
    """
    Identifies code hotspots and complexity clusters.
    """
    def __init__(self, files: List["FileInfo"]):
        self.files = files

    def render_markdown(self) -> str:
        if not self.files:
            return ""

        lines = []
        lines.append("<!-- @heatmap:start -->")
        lines.append("## 🔥 AI Heatmap – Code Hotspots")
        lines.append("")

        # 1. Top Files (Size & Complexity proxy)
        relevant = [f for f in self.files if f.category in ("source", "config", "contract", "test")]
        top_files = sorted(relevant, key=lambda f: f.size, reverse=True)[:5]

        lines.append("### Top-Level Hotspots (Files by Size)")
        for i, f in enumerate(top_files, 1):
            lines.append(f"{i}. `{f.rel_path}`")
            lines.append(f"   - Size: {human_size(f.size)}")
            lines.append(f"   - Category: {f.category}")
            if f.tags:
                lines.append(f"   - Tags: {', '.join(f.tags)}")
            lines.append("")

        # 2. Top Folders
        folder_stats = {}
        for f in self.files:
            parent = f.rel_path.parent
            if parent == Path("."):
                continue
            path_str = str(parent)
            if path_str not in folder_stats:
                folder_stats[path_str] = {"count": 0, "size": 0}
            folder_stats[path_str]["count"] += 1
            folder_stats[path_str]["size"] += f.size

        sorted_folders = sorted(folder_stats.items(), key=lambda x: x[1]["size"], reverse=True)[:5]

        lines.append("### Top Folder Hotspots")
        for path, stats in sorted_folders:
            lines.append(f"- `{path}/` → {stats['count']} Files, {human_size(stats['size'])}")

        lines.append("")
        lines.append("<!-- @heatmap:end -->")
        lines.append("")
        return "\n".join(lines)


def _build_extras_meta(extras: "ExtrasConfig", num_repos: int) -> Dict[str, bool]:
    """
    Hilfsfunktion: baut den extras-Block für den @meta-Contract.
    """
    extras_meta: Dict[str, bool] = {}
    if extras.health:
        extras_meta["health"] = True
    if extras.organism_index:
        extras_meta["organism_index"] = True
    if extras.fleet_panorama and num_repos > 1:
        extras_meta["fleet_panorama"] = True
    if extras.augment_sidecar:
        extras_meta["augment_sidecar"] = True
    if extras.delta_reports:
        extras_meta["delta_reports"] = True
    if extras.json_sidecar:
        extras_meta["json_sidecar"] = True
    if extras.heatmap:
        extras_meta["heatmap"] = True
    return extras_meta


def _build_augment_meta(sources: List[Path]) -> Optional[Dict[str, Any]]:
    """
    Nutzt dieselbe Logik wie der Augment-Block, um das Sidecar im Meta zu verlinken.
    """
    sidecar = _find_augment_file_for_sources(sources)
    return {"sidecar": sidecar.name} if sidecar else None


def _render_fleet_panorama(sources: List[Path], files: List["FileInfo"]) -> Optional[str]:
    """
    Render the Fleet Panorama block.
    """
    if len(sources) < 2:
        return None

    grouped: Dict[str, List["FileInfo"]] = {}
    for fi in files:
        grouped.setdefault(fi.root_label, []).append(fi)

    lines: List[str] = []
    lines.append("<!-- @fleet-panorama:start -->")
    lines.append("## 🛰 Fleet Panorama")
    lines.append("")

    total_files = sum(len(v) for v in grouped.values())
    total_bytes = sum(f.size for f in files)
    lines.append(f"**Summary:** {len(grouped)} repos, {total_bytes} bytes, {total_files} files")
    lines.append("")

    for repo, repo_files in grouped.items():
        repo_bytes = sum(f.size for f in repo_files)
        lines.append(f"### `{repo}`")
        lines.append(f"- Files: {len(repo_files)}")
        lines.append(f"- Size: {repo_bytes} bytes")
        lines.append("")

    lines.append("<!-- @fleet-panorama:end -->")
    return "\n".join(lines) + "\n"


def _find_augment_file_for_sources(sources: List[Path]) -> Optional[Path]:
    """
    Locate an augment sidecar YAML file for the given sources.
    """
    for source in sources:
        try:
            candidate = source / f"{source.name}_augment.yml"
            if candidate.exists():
                return candidate

            candidate_parent = source.parent / f"{source.name}_augment.yml"
            if candidate_parent.exists():
                return candidate_parent
        except (OSError, PermissionError):
            continue
    return None


def _render_augment_block(sources: List[Path]) -> str:
    """
    Render the Augment Intelligence block based on an augment sidecar, if present.
    """
    augment_path = _find_augment_file_for_sources(sources)
    if not augment_path:
        return ""

    try:
        yaml  # type: ignore[name-defined]
    except NameError:
        lines = []
        lines.append("<!-- @augment:start -->")
        lines.append("## 🧩 Augment Intelligence")
        lines.append("")
        lines.append(f"**Sidecar:** `{augment_path.name}`")
        lines.append("")
        lines.append("_Hinweis: PyYAML nicht verfügbar – Details aus dem Sidecar können nicht automatisch geparst werden._")
        lines.append("")
        lines.append("<!-- @augment:end -->")
        lines.append("")
        return "\n".join(lines)

    try:
        raw = augment_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""

    try:
        data = yaml.safe_load(raw)  # type: ignore[name-defined]
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to parse augment sidecar {augment_path}: {e}\n")
        return ""

    if not isinstance(data, dict):
        return ""

    augment = data.get("augment") or {}
    if not isinstance(augment, dict):
        return ""

    lines: List[str] = []
    lines.append("<!-- @augment:start -->")
    lines.append("## 🧩 Augment Intelligence")
    lines.append("")
    lines.append(f"**Sidecar:** `{augment_path.name}`")
    lines.append("")

    hotspots = augment.get("hotspots") or []
    if isinstance(hotspots, list) and hotspots:
        lines.append("### Hotspots")
        for hs in hotspots:
            if not isinstance(hs, dict):
                continue
            path = hs.get("path") or "?"
            reason = hs.get("reason") or ""
            severity = hs.get("severity") or ""
            line_range = hs.get("lines")
            details = []
            if severity:
                details.append(f"Severity: {severity}")
            if line_range:
                details.append(f"Lines: {line_range}")
            suffix = f" ({'; '.join(details)})" if details else ""
            if reason:
                lines.append(f"- `{path}` – {reason}{suffix}")
            else:
                lines.append(f"- `{path}`{suffix}")
        lines.append("")

    suggestions = augment.get("suggestions") or []
    if isinstance(suggestions, list) and suggestions:
        lines.append("### Suggestions")
        for s in suggestions:
            if isinstance(s, str):
                lines.append(f"- {s}")
        lines.append("")

    risks = augment.get("risks") or []
    if isinstance(risks, list) and risks:
        lines.append("### Risks")
        for r in risks:
            if isinstance(r, str):
                lines.append(f"- {r}")
        lines.append("")

    dependencies = augment.get("dependencies") or []
    if isinstance(dependencies, list) and dependencies:
        lines.append("### Dependencies")
        for dep in dependencies:
            if not isinstance(dep, dict):
                continue
            name = dep.get("name") or "unknown"
            required = dep.get("required")
            purpose = dep.get("purpose") or ""
            req_txt = ""
            if isinstance(required, bool):
                req_txt = "required" if required else "optional"
            parts = [name]
            if req_txt:
                parts.append(f"({req_txt})")
            if purpose:
                parts.append(f"– {purpose}")
            lines.append(f"- {' '.join(parts)}")
        lines.append("")

    priorities = augment.get("priorities") or []
    if isinstance(priorities, list) and priorities:
        lines.append("### Priorities")
        for pr in priorities:
            if not isinstance(pr, dict):
                continue
            prio = pr.get("priority")
            task = pr.get("task") or ""
            status = pr.get("status") or ""
            head = f"P{prio}: {task}" if prio is not None else task
            if status:
                lines.append(f"- {head} ({status})")
            else:
                lines.append(f"- {head}")
        lines.append("")

    context = augment.get("context") or {}
    if isinstance(context, dict) and context:
        lines.append("### Context")
        for key, value in context.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    lines.append("<!-- @augment:end -->")
    lines.append("")
    return "\n".join(lines)


def run_debug_checks(file_infos: List["FileInfo"], debug: DebugCollector) -> None:
    """
    Leichte, rein lesende Debug-Checks auf Basis der FileInfos.
    """
    # 1. Unbekannte Kategorien / Tags
    for fi in file_infos:
        ctx = f"{fi.root_label}/{fi.rel_path.as_posix()}"
        cat = fi.category or "other"

        if cat not in DEBUG_CONFIG.allowed_categories:
            # Use configured severity
            log_func = _debug_log_func(debug, DEBUG_CONFIG.unknown_category_level)
            log_func(
                "category-unknown",
                ctx,
                f"Unbekannte Kategorie '{cat}' – erwartet sind {sorted(DEBUG_CONFIG.allowed_categories)}.",
            )

        for tag in getattr(fi, "tags", []) or []:
            if tag not in DEBUG_CONFIG.allowed_tags:
                log_func = _debug_log_func(debug, DEBUG_CONFIG.unknown_tag_level)
                log_func(
                    "tag-unknown",
                    ctx,
                    f"Tag '{tag}' ist nicht im v2.4-Schema registriert.",
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


NOISY_DIRECTORIES = ("node_modules/", "dist/", "build/", "target/")

LOCKFILE_NAMES = {
    "Cargo.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
}

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

PROFILE_USECASE = {
    "overview": "Tools – Index",
    "summary": "Tools – Doku/Kontext",
    "dev": "Tools – Code/Review Snapshot",
    "machine-lean": "Tools – Machine-Lean",
    "max": "Tools – Vollsnapshot",
}

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
        self.anchor = ""
        self.anchor_alias = ""
        self.roles = []


# --- Utilities ---

def infer_repo_role(root_label: str, files: List["FileInfo"]) -> str:
    """
    Infers the high-level semantic role of the repository within the organism.
    """
    roles = []
    root = root_label.lower()

    if "tool" in root or "merger" in root: roles.append("tooling")
    if "contract" in root or "schema" in root: roles.append("contracts")
    if "meta" in root: roles.append("governance")
    if "lern" in root: roles.append("education")
    if "geist" in root: roles.append("knowledge-base")
    if "haus" in root: roles.append("logic-core")
    if "sensor" in root: roles.append("ingestion")
    if "ui" in root or "app" in root or "leitstand" in root: roles.append("ui")
    if "wgx" in root: roles.append("fleet-management")

    has_contracts = any(f.category == "contract" for f in files)

    if has_contracts and "contracts" not in roles:
        roles.append("contracts")

    if not roles:
        roles.append("service")

    return " / ".join(roles)


def summarize_repo(files: List["FileInfo"], included_count: int) -> Dict[str, Any]:
    """
    Build a compact stats dict for a repository.
    """
    total = len(files)
    text_files = sum(
        1
        for f in files
        if f.is_text and f.category in {"source", "doc", "config", "test", "ci", "contract"}
    )
    total_bytes = sum(f.size for f in files)

    return {
        "total": total,
        "text_files": text_files,
        "bytes": total_bytes,
        "included": included_count,
    }


def compute_file_roles(fi: "FileInfo") -> List[str]:
    """
    Compute semantic roles with a lean, high-signal heuristic.
    """
    roles: List[str] = []

    path_str = fi.rel_path.as_posix().lower()
    filename = fi.rel_path.name.lower()

    if fi.category == "doc" and "readme" in filename:
        roles.append("doc-essential")

    if "config" in path_str or filename.endswith((".yml", ".yaml", ".toml")):
        roles.append("config")

    if filename.startswith(("run_", "main", "index")):
        roles.append("entrypoint")

    if "ai" in path_str or "context" in path_str or "ai-context" in (fi.tags or []):
        roles.append("ai-context")

    seen = set()
    deduped = []
    for r in roles:
        if r not in seen:
            deduped.append(r)
            seen.add(r)

    return deduped


def build_hotspots(processed_files: List[Tuple["FileInfo", str]], limit: int = 8) -> List[str]:
    """
    Build a concise hotspot list for quick navigation.
    """
    candidates: List[Tuple[float, FileInfo]] = []

    for fi, status in processed_files:
        if status not in ("full", "truncated"):
            continue

        score = 0.0

        if "entrypoint" in fi.roles:
            score += 5.0
        if fi.category == "contract":
            score += 3.0
        if "ai-context" in (fi.tags or []):
            score += 2.5
        if "ci" in (fi.tags or []):
            score += 1.5
        if fi.category == "config":
            score += 1.0

        score += min(fi.size / 1024.0, 50) / 50.0

        candidates.append((score, fi))

    if not candidates:
        return []

    candidates.sort(key=lambda item: (-item[0], -item[1].size, str(item[1].rel_path)))
    top = candidates[:limit]

    lines = ["### Hotspots (Einstiegspunkte)"]
    for _, fi in top:
        link = f"[`{fi.rel_path}`](#{fi.anchor})"
        role_hint = f"roles: {', '.join(fi.roles)}" if fi.roles else "roles: -"
        tag_hint = f"tags: {', '.join(fi.tags)}" if fi.tags else "tags: -"
        lines.append(
            f"- {link} — repo `{fi.root_label}`, {fi.category}; {role_hint}, {tag_hint}"
        )

    return lines


def describe_scope(files: List["FileInfo"]) -> str:
    """Build a human-readable scope string from the involved roots."""
    roots = sorted({fi.root_label for fi in files})
    if not roots:
        return "empty (no matching files)"
    if len(roots) == 1:
        return f"single repo `{roots[0]}`"

    preview = ", ".join(f"`{r}`" for r in roots[:5])
    if len(roots) > 5:
        preview += ", …"
    return f"{len(roots)} repos: {preview}"


def determine_inclusion_status(fi: "FileInfo", level: str, max_file_bytes: int) -> str:
    """
    Determine whether a file is included with content based on profile settings.
    """
    if not fi.is_text:
        return "omitted"

    tags = fi.tags or []

    if level == "overview":
        return "full" if is_priority_file(fi) else "meta-only"

    if level == "summary":
        if fi.category in ["doc", "config", "contract", "ci"] or "ai-context" in tags or "wgx-profile" in tags:
            return "full"
        if fi.category in ["source", "test"]:
            return "full" if is_priority_file(fi) else "meta-only"
        return "full" if is_priority_file(fi) else "meta-only"

    if level in ("dev", "machine-lean"):
        if "lockfile" in tags:
            return "meta-only" if fi.size > 20_000 else "full"
        if fi.category in ["source", "test", "config", "ci", "contract"]:
            return "full"
        if fi.category == "doc":
            return "full" if is_priority_file(fi) else "meta-only"
        return "meta-only"

    if level == "max":
        return "full"

    return "full" if fi.size <= max_file_bytes else "omitted"

def is_noise_file(fi: "FileInfo") -> bool:
    """
    Heuristik für 'Noise'-Dateien.
    """
    try:
        path_str = str(fi.rel_path).replace("\\", "/").lower()
        name = fi.rel_path.name.lower()
    except Exception as e:
        sys.stderr.write(f"Warning: is_noise_file failed for {fi.rel_path}: {e}\n")
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

def _parse_extras_csv(extras_csv: str) -> List[str]:
    items = [x.strip().lower() for x in (extras_csv or "").split(",") if x.strip()]
    normalized = []
    for item in items:
        if item == "ai_heatmap":
            item = "heatmap"
        normalized.append(item)
    return normalized

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
    # MD5 is used for file integrity checking, not cryptographic security
    try:
        h = hashlib.md5(usedforsecurity=False)
    except TypeError:
        # Fallback for Python < 3.9
        h = hashlib.md5()  # nosec B303
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
    return "(none)"


def classify_file_v2(rel_path: Path, ext: str) -> Tuple[str, List[str]]:
    """
    Returns (category, tags).
    Strict Pattern Matching based on v2.1 Spec.
    """
    parts = list(rel_path.parts)
    name = rel_path.name.lower()
    tags = []

    if name.endswith(".ai-context.yml"):
        tags.append("ai-context")

    if ".github" in parts and "workflows" in parts and ext in [".yml", ".yaml"]:
        tags.append("ci")

    if "docs" in parts and "adr" in parts and ext == ".md":
        tags.append("adr")
    if name.startswith("runbook") and ext == ".md":
        tags.append("runbook")

    if (("scripts" in parts) or ("bin" in parts)) and ext in (".sh", ".py"):
        tags.append("script")

    if "export" in parts and ext == ".jsonl":
        tags.append("feed")

    if "lock" in name:
        tags.append("lockfile")

    if name == "readme.md":
        tags.append("ai-context")

    if ".wgx" in parts and name.startswith("profile"):
        tags.append("wgx-profile")

    category = "other"

    if name in CONFIG_FILENAMES or "config" in parts or ".github" in parts or ".wgx" in parts or ext in [".toml", ".yaml", ".yml", ".json", ".lock"]:
         if "contracts" in parts:
             category = "contract"
         else:
             category = "config"
    elif ext in DOC_EXTENSIONS or "docs" in parts:
        category = "doc"
    elif "contracts" in parts:
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

def _pick_primary_artifact(paths):
    for p in paths:
        try:
            if str(p).lower().endswith(".json"):
                return p
        except Exception:
            pass
    for p in paths:
        try:
            if str(p).lower().endswith(".md"):
                return p
        except Exception:
            pass
    return paths[0] if paths else None

def _pick_human_md(paths) -> Optional[Path]:
    for p in paths:
        try:
            if str(p).lower().endswith(".md"):
                return p
        except Exception:
            pass
    return None

def _load_wc_extractor_module(script_path: Path):
    """Dynamically load wc-extractor.py from the same directory."""
    from importlib.machinery import SourceFileLoader
    import types

    extractor_path = script_path.with_name("wc-extractor.py")
    if not extractor_path.exists():
        return None
    try:
        loader = SourceFileLoader("wc_extractor", str(extractor_path))
        mod = types.ModuleType(loader.name)
        loader.exec_module(mod)
        return mod
    except Exception as exc:
        print(f"[wc-merger] could not load wc-extractor: {exc}")
        return None

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

            md5 = ""
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
    """
    snapshot: Dict[str, Tuple[int, str, str]] = {}
    summary = scan_repo(
        repo_root, extensions=None, path_contains=None, max_bytes=100_000_000
    )
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


def _effective_render_mode(plan_only: bool, code_only: bool) -> str:
    """Return the effective render mode based on plan/code switches."""

    plan_only = bool(plan_only)
    code_only = bool(code_only)

    if plan_only:
        return "plan-only"
    if code_only:
        return "code-only"
    return "full"


def _normalize_mode_flags(plan_only: bool, code_only: bool) -> Tuple[bool, bool, Dict[str, bool]]:
    """Normalize plan/code flags and retain the original user request."""

    requested_flags = {"plan_only": bool(plan_only), "code_only": bool(code_only)}

    plan_only = requested_flags["plan_only"]
    code_only = False if plan_only else requested_flags["code_only"]

    return plan_only, code_only, requested_flags


def _generate_run_id(
    repo_names: List[str],
    detail: str,
    path_filter: Optional[str],
    ext_filter: Optional[str],
    plan_only: bool = False,
    code_only: bool = False,
    timestamp: Optional[str] = None,
) -> str:
    """
    Generate a deterministic run_id for consistent primary artifact naming.
    """
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%y%m%d-%H%M")

    components: List[str] = []

    plan_only, code_only, _ = _normalize_mode_flags(plan_only, code_only)

    if path_filter:
        path_slug = path_filter.strip().strip("/").replace("/", "-")
        if path_slug:
            components.append(path_slug)

    if not repo_names:
        components.append("no-repo")
    elif len(repo_names) == 1:
        components.append(repo_names[0].replace("/", "-"))
    else:
        repo_str = "-".join(sorted(repo_names))
        repo_hash = hashlib.md5(repo_str.encode("utf-8")).hexdigest()[:6]
        components.append(f"multi-{repo_hash}")

    components.append(_effective_render_mode(plan_only, code_only))
    components.append(detail)

    if ext_filter:
        ext_clean = ext_filter.replace(".", "").replace(",", "+").replace(" ", "")
        if ext_clean:
            components.append(f"ext-{ext_clean}")

    components.append(timestamp)

    return "-".join(components)


def build_tree(file_infos: List[FileInfo]) -> str:
    by_root: Dict[str, List[Path]] = {}

    sorted_files = sorted(file_infos, key=lambda fi: (get_repo_sort_index(fi.root_label), fi.root_label.lower()))

    for fi in sorted_files:
        by_root.setdefault(fi.root_label, []).append(fi.rel_path)

    lines = ["```"]
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
                lines.append(f"{indent}📄 {f}")

        walk(tree, "    ", root)
    lines.append("```")
    return "\n".join(lines)

def make_output_filename(
    merges_dir: Path,
    repo_names: List[str],
    detail: str,
    part_suffix: str,
    path_filter: Optional[str],
    ext_filter: Optional[str],
    run_id: Optional[str] = None,
    plan_only: bool = False,
    code_only: bool = False,
) -> Path:
    """
    Erzeugt den endgültigen Dateinamen für den Merge-Report.
    """
    
    plan_only, code_only, _ = _normalize_mode_flags(plan_only, code_only)
    render_mode = _effective_render_mode(plan_only, code_only)

    if isinstance(path_filter, str):
        pf = path_filter.strip()
        if pf in ("", "root", "/"):
            path_filter = None

    ts = datetime.datetime.now().strftime("%y%m%d-%H%M")

    if not repo_names:
        repo_block = "no-repo"
    elif len(repo_names) == 1:
        repo_block = repo_names[0]
    else:
        repo_block = "multi"
    repo_block = repo_block.replace("/", "-")

    detail_block = detail

    path_block = None
    if path_filter:
        slug = path_filter.strip().strip("/")
        if slug:
            path_block = slug.replace("/", "-")

    mode_block = render_mode

    ext_block = None
    if ext_filter:
        cleaned = ext_filter.replace(" ", "").replace(".", "").replace(",", "+")
        if cleaned:
            ext_block = f"ext-{cleaned}"

    part_block = part_suffix.lstrip("_") if part_suffix else ""

    parts: List[str] = []

    if path_block:
        parts.append(path_block)

    parts.append(repo_block)
    parts.append(mode_block)
    parts.append(detail_block)

    if ext_block:
        parts.append(ext_block)

    if part_block:
        parts.append(part_block)

    parts.append(ts)

    filename = "-".join(parts) + "_merge.md"
    return merges_dir / filename

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

def _render_delta_block(delta_meta: Dict[str, Any]) -> str:
    """
    Render Delta Report block from delta metadata.
    """
    lines = []
    lines.append("<!-- @delta:start -->")
    lines.append("## ♻ Delta Report")
    lines.append("")
    
    base_ts = delta_meta.get("base_import") or delta_meta.get("base_timestamp", "unknown")
    current_ts = delta_meta.get("current_timestamp", "unknown")
    
    lines.append(f"- **Base Import:** {base_ts}")
    lines.append(f"- **Current:** {current_ts}")
    lines.append("")
    
    def _safe_list_len(val):
        return len(val) if isinstance(val, list) else 0
    
    summary = delta_meta.get("summary", {})
    if summary and isinstance(summary, dict):
        added_count = summary.get("files_added", 0)
        removed_count = summary.get("files_removed", 0)
        changed_count = summary.get("files_changed", 0)
        
        lines.append("**Summary:**")
        lines.append(f"- Files added: {added_count}")
        lines.append(f"- Files removed: {removed_count}")
        lines.append(f"- Files changed: {changed_count}")
        lines.append("")
        
        added = delta_meta.get("files_added", [])
        removed = delta_meta.get("files_removed", [])
        changed = delta_meta.get("files_changed", [])
    else:
        added = delta_meta.get("files_added", [])
        removed = delta_meta.get("files_removed", [])
        changed = delta_meta.get("files_changed", [])
        
        lines.append("**Summary:**")
        lines.append(f"- Files added: {_safe_list_len(added)}")
        lines.append(f"- Files removed: {_safe_list_len(removed)}")
        lines.append(f"- Files changed: {_safe_list_len(changed)}")
        lines.append("")
    
    if isinstance(added, list) and added:
        lines.append("### Added Files")
        for f in added[:MAX_DELTA_FILES]:
            lines.append(f"- `{f}`")
        if len(added) > MAX_DELTA_FILES:
            lines.append(f"- _(and {len(added) - MAX_DELTA_FILES} more)_")
        lines.append("")
    
    if isinstance(removed, list) and removed:
        lines.append("### Removed Files")
        for f in removed[:MAX_DELTA_FILES]:
            lines.append(f"- `{f}`")
        if len(removed) > MAX_DELTA_FILES:
            lines.append(f"- _(and {len(removed) - MAX_DELTA_FILES} more)_")
        lines.append("")
    
    if isinstance(changed, list) and changed:
        lines.append("### Changed Files")
        for f in changed[:MAX_DELTA_FILES]:
            if isinstance(f, dict):
                path = f.get("path", "unknown")
                size_delta = f.get("size_delta", 0)
                if size_delta > 0:
                    lines.append(f"- `{path}` (+{size_delta} bytes)")
                elif size_delta < 0:
                    lines.append(f"- `{path}` ({size_delta} bytes)")
                else:
                    lines.append(f"- `{path}`")
            else:
                lines.append(f"- `{f}`")
        if len(changed) > MAX_DELTA_FILES:
            lines.append(f"- _(and {len(changed) - MAX_DELTA_FILES} more)_")
        lines.append("")
    
    lines.append("<!-- @delta:end -->")
    lines.append("")
    return "\n".join(lines)

def check_fleet_consistency(files: List[FileInfo]) -> List[str]:
    """
    Checks for objective inconsistencies specified in the spec.
    """
    warnings = []

    roots = set(f.root_label for f in files)

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
        "## manifest",
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


def iter_report_blocks(
    files: List[FileInfo],
    level: str,
    max_file_bytes: int,
    sources: List[Path],
    plan_only: bool,
    code_only: bool = False,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
    delta_meta: Optional[Dict[str, Any]] = None,
) -> Iterator[str]:
    if extras is None:
        extras = ExtrasConfig.none()

    nav = NavStyle(emit_search_markers=False)

    now = datetime.datetime.utcnow()

    files.sort(key=lambda fi: (get_repo_sort_index(fi.root_label), fi.root_label.lower(), str(fi.rel_path).lower()))

    if code_only:
        files = [fi for fi in files if fi.category in DEBUG_CONFIG.code_only_categories]

    processed_files = []

    unknown_categories = set()
    unknown_tags = set()
    roots = set(f.root_label for f in files)

    for fi in files:
        rel_id = _slug_token(fi.rel_path.as_posix())
        repo_slug = _slug_token(fi.root_label)
        base_anchor = f"file-{repo_slug}-{rel_id}"
        suffix = (fi.md5 or "")[:6] if getattr(fi, "md5", None) else ""
        fi.anchor_alias = base_anchor
        fi.anchor = f"{base_anchor}-{suffix}" if suffix else base_anchor
        
        fi.roles = compute_file_roles(fi)

        if fi.category not in DEBUG_CONFIG.allowed_categories:
            unknown_categories.add(fi.category)

        for tag in (fi.tags or []):
            if tag not in DEBUG_CONFIG.allowed_tags:
                unknown_tags.add(tag)

        status = determine_inclusion_status(fi, level, max_file_bytes)

        processed_files.append((fi, status))

    if debug:
        print("DEBUG: total files:", len(files))
        print("DEBUG: unknown categories:", unknown_categories)
        print("DEBUG: unknown tags:", unknown_tags)
        print("DEBUG: files without anchors:", [fi.rel_path for fi in files if not hasattr(fi, "anchor")])

    total_size = sum(fi.size for fi in files)
    text_files = [fi for fi in files if fi.is_text]
    included_count = sum(1 for _, s in processed_files if s in ("full", "truncated"))

    included_by_root: Dict[str, int] = {}

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

        if fi.category == "contract":
            organism_contracts.append(fi)
        if "ai-context" in (fi.tags or []):
            organism_ai_ctx.append(fi)
        if "ci" in (fi.tags or []):
            organism_pipelines.append(fi)
        if "wgx-profile" in (fi.tags or []):
            organism_wgx_profiles.append(fi)

    files_by_root: Dict[str, List[FileInfo]] = {}
    for fi in files:
        files_by_root.setdefault(fi.root_label, []).append(fi)

    for fi, status in processed_files:
        if status in ("full", "truncated"):
            included_by_root[fi.root_label] = included_by_root.get(fi.root_label, 0) + 1

    repo_stats: Dict[str, Dict[str, Any]] = {}
    for root, root_files in files_by_root.items():
        repo_stats[root] = summarize_repo(root_files, included_by_root.get(root, 0))

    health_collector = None
    if extras.health:
        health_collector = HealthCollector()
        for root in sorted(files_by_root.keys()):
            root_files = files_by_root[root]
            health_collector.analyze_repo(root, root_files)

    # --- 1. Header ---
    header = []
    header.append(f"# WC-Merge Report (v{SPEC_VERSION.split('.')[0]}.x)")
    header.append("")

    header.append("**Human Contract:** `wc-merge-report` (v2.4)")
    header.append(f"**Primary Contract (Agent):** `{AGENT_CONTRACT_NAME}` ({AGENT_CONTRACT_VERSION}) — siehe `artifacts.primary_json`")
    header.append("")

    render_mode = _effective_render_mode(plan_only, code_only)

    if render_mode == "meta-only":
        header.append("**META-ONLY Modus:** Dieser Merge enthält ausschließlich Meta-, Struktur-, Index- und Analyse-Informationen.")
        header.append("**Kein Code, keine Planinhalte. Gedacht als Entscheidungs- und Steuerungsartefakt für Agenten.**")
        header.append("")
    else:
        if code_only:
            header.append("**Profil: CODE-ONLY – dieser Merge enthält bewusst nur Source-Code, Tests, technische Configs und Contracts.**")
            header.append("**Keine Beschreibungs-Dokus; nutze Manifest, Roles und Hotspots als Einstiegspunkte.**")
            header.append("")
        if plan_only:
            header.append("**Profil: PLAN-ONLY – dieser Merge enthält nur Plan-/Doku-/Struktur-Kontext (kein Code, keine Tests).**")
            header.append("**Nutze ihn als Token-sparenden Vorab-Scan; fehlender Code ist Absicht (Modus), nicht „vergessen“.**")
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
        header.append("- **Max File Bytes:** unlimited")
    header.append(f"- **Spec-Version:** {SPEC_VERSION}")
    header.append(f"- **Contract:** {MERGE_CONTRACT_NAME}")
    header.append(f"- **Contract-Version:** {MERGE_CONTRACT_VERSION}")
    header.append(f"- **Plan Only:** {str(bool(plan_only)).lower()}")
    header.append(f"- **Code Only:** {str(bool(code_only)).lower()}")
    header.append(f"- **Render Mode:** `{render_mode}`")

    header.append("### Navigation")
    header.append("- **Index:** [#index](#index) · **Manifest:** [#manifest](#manifest)")
    header.append("- Wenn dein Viewer nicht springt: nutze die Suche nach `manifest`, `index` oder `file-...`.")
    header.append("")

    profile_usecase = PROFILE_USECASE.get(level)
    if profile_usecase:
        header.append(f"- **Profile Use-Case:** {profile_usecase}")

    header.append(f"- **Declared Purpose:** {declared_purpose}")

    scope_desc = describe_scope(files)
    header.append(f"- **Scope:** {scope_desc}")

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
    
    if text_files:
        coverage_pct = int((included_count / len(text_files)) * 100)
        header.append(f"- **Coverage:** {coverage_pct}% ({included_count}/{len(text_files)} text files with content)")
    
    header.append("")
    
    # --- 3. Machine-readable Meta Block (für KIs) ---
    if not plan_only:
        meta_lines: List[str] = []
        meta_lines.append("<!-- @meta:start -->")
        meta_lines.append("```yaml")

        total_files = len(files)
        text_files_count = len(text_files)
        if text_files_count:
            coverage_raw = (included_count / text_files_count) * 100.0
            coverage_pct = round(coverage_raw, 1)
        else:
            coverage_pct = 0.0

        meta_dict: Dict[str, Any] = {
            "merge": {
                "spec_version": SPEC_VERSION,
                "profile": level,
                "contract": MERGE_CONTRACT_NAME,
                "contract_version": MERGE_CONTRACT_VERSION,
                "plan_only": plan_only,
                "code_only": code_only,
                "render_mode": render_mode,
                "max_file_bytes": max_file_bytes,
                "scope": scope_desc,
                "source_repos": sorted([s.name for s in sources]) if sources else [],
                "path_filter": path_filter,
                "ext_filter": sorted(ext_filter) if ext_filter else None,
                "generated_at": now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "total_files": total_files,
                "total_size_bytes": total_size,
                "coverage": {
                    "included_files": included_count,
                    "text_files": text_files_count,
                    "coverage_pct": coverage_pct,
                },
            }
        }

        if extras:
            extras_meta = _build_extras_meta(extras, len(roots))
            if extras_meta:
                meta_dict["merge"]["extras"] = extras_meta

        if extras and extras.health and health_collector:
            all_health = health_collector.get_all_health()
            if any(h.status == "critical" for h in all_health):
                overall = "critical"
            elif any(h.status == "warn" for h in all_health):
                overall = "warning"
            else:
                overall = "ok"

            missing_set = set()
            for h in all_health:
                if not h.has_contracts: missing_set.add("contracts")
                if not h.has_ci_workflows: missing_set.add("ci")
                if not h.has_wgx_profile: missing_set.add("wgx-profile")

            meta_dict["merge"]["health"] = {
                "status": overall,
                "missing": sorted(list(missing_set)),
            }

        if extras and extras.delta_reports:
            if delta_meta:
                meta_dict["merge"]["delta"] = delta_meta
            else:
                meta_dict["merge"]["delta"] = {
                    "enabled": True
                }

        if extras and extras.augment_sidecar:
            augment_meta = _build_augment_meta(sources)
            if augment_meta:
                meta_dict["merge"]["augment"] = augment_meta

        if "yaml" in globals():
            meta_yaml = yaml.safe_dump(meta_dict)
            for line in meta_yaml.rstrip("\n").splitlines():
                meta_lines.append(line)
        else:
             meta_lines.append("# YAML support missing")

        meta_lines.append("```")
        meta_lines.append("<!-- @meta:end -->")
        meta_lines.append("")
        header.extend(meta_lines)

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
    elif level == "machine-lean":
        header.append("`machine-lean`")
        header.append("- Lean Snapshot: volle Inhalte, reduzierter Baum/Decorations")
        header.append("- Manifest + Index + Content für Maschinen-Parsing optimiert")
    elif level == "max":
        header.append("`max`")
        header.append("- alle Textdateien → voll")
        header.append("- keine Kürzung (Dateien werden ggf. gesplittet)")
    else:
        header.append(f"`{level}` (custom)")
    header.append("")

    # --- 4. Reading Plan ---
    header.append("## Reading Plan")
    header.append("")
    if plan_only:
        header.append("1. Hinweis: Dieser Merge wurde im **PLAN-ONLY** Modus erzeugt.")
        header.append("   - Enthält nur: Profilbeschreibung, Plan und Meta (`@meta`).")
        header.append("   - Enthält **nicht**: `Structure`, `Manifest` oder `Content`-Blöcke.")
        header.append("")
        header.append("2. Nutze diesen Merge, um schnell zu entscheiden, ob sich ein Voll-Merge lohnt,")
        header.append("   ohne Tokens für Dateiinhalte zu verbrauchen.")
    else:
        header.append("1. Lies zuerst: `README.md`, `docs/runbook*.md`, `*.ai-context.yml`")
        if level == "machine-lean":
            header.append("2. Danach: `Manifest` -> `Content`")
        else:
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
    
    if extras.delta_reports and delta_meta and isinstance(delta_meta, dict):
        summary = delta_meta.get("summary", {})
        if isinstance(summary, dict):
            plan.append("### Delta Summary")
            plan.append("")
            files_added = summary.get("files_added", 0)
            files_removed = summary.get("files_removed", 0)
            files_changed = summary.get("files_changed", 0)
            plan.append(f"- Files added: {files_added}")
            plan.append(f"- Files removed: {files_removed}")
            plan.append(f"- Files changed: {files_changed}")
            plan.append("")

    if files_by_root:
        plan.append("### Repo Snapshots")
        plan.append("")
        for root in sorted(files_by_root.keys()):
            root_files = files_by_root[root]
            root_total = len(root_files)
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

    hotspots = build_hotspots(processed_files)
    if hotspots:
        plan.extend(hotspots)
        plan.append("")
    plan.append("**Folder Highlights:**")
    if code_folders: plan.append(f"- Code: `{', '.join(sorted(code_folders))}`")
    if doc_folders: plan.append(f"- Docs: `{', '.join(sorted(doc_folders))}`")
    if infra_folders: plan.append(f"- Infra: `{', '.join(sorted(infra_folders))}`")
    plan.append("")

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

    # --- Health Report ---
    if extras.health and health_collector:
        health_report = health_collector.render_markdown()
        if health_report:
            yield health_report

    # --- Delta Report Block ---
    if extras.delta_reports and delta_meta:
        try:
            delta_block = _render_delta_block(delta_meta)
            if delta_block:
                yield delta_block
        except Exception as e:
            yield f"\n<!-- delta-error: {e} -->\n"

    # --- Fleet Panorama ---
    if extras.fleet_panorama:
        fleet_block = _render_fleet_panorama(sources, files)
        if fleet_block:
            yield fleet_block

    # --- Organism Index ---
    if extras.organism_index and len(roots) == 1:
        repo_name = list(roots)[0]
        repo_role = infer_repo_role(repo_name, files)

        organism_index: List[str] = []
        organism_index.append("<!-- @organism-index:start -->")
        organism_index.append("## 🧬 Organism Index")
        organism_index.append("")
        organism_index.append(f"**Repo:** `{repo_name}`")
        organism_index.append(f"**Rolle:** {repo_role}")
        organism_index.append("")
        organism_index.append("**Organ-Status:**")
        organism_index.append(f"- AI-Kontext: {len(organism_ai_ctx)} Datei(en)")
        organism_index.append(f"- Verträge (Contracts): {len(organism_contracts)} Datei(en)")
        organism_index.append(f"- Pipelines (CI/CD): {len(organism_pipelines)} Workflow(s)")
        organism_index.append(f"- WGX / Fleet-Profile: {len(organism_wgx_profiles)} Profil(e)")
        organism_index.append("")

        if organism_ai_ctx:
            organism_index.append("### AI-Kontext")
            for fi in organism_ai_ctx:
                organism_index.append(f"- `{fi.rel_path}`")
            organism_index.append("")
        else:
            organism_index.append("### AI-Kontext")
            organism_index.append("_Keine AI-Kontext-Dateien gefunden._")
            organism_index.append("")

        if organism_contracts:
            organism_index.append("### Verträge (Contracts)")
            for fi in organism_contracts:
                organism_index.append(f"- `{fi.rel_path}`")
            organism_index.append("")
        else:
            organism_index.append("### Verträge (Contracts)")
            organism_index.append("_Keine Contract-Dateien gefunden._")
            organism_index.append("")

        if organism_pipelines:
            organism_index.append("### Pipelines (CI/CD)")
            for fi in organism_pipelines:
                organism_index.append(f"- `{fi.rel_path}`")
            organism_index.append("")
        else:
            organism_index.append("### Pipelines (CI/CD)")
            organism_index.append("_Keine CI/CD-Workflows gefunden._")
            organism_index.append("")

        if organism_wgx_profiles:
            organism_index.append("### WGX / Fleet-Profile")
            for fi in organism_wgx_profiles:
                organism_index.append(f"- `{fi.rel_path}`")
            organism_index.append("")
        else:
            organism_index.append("### WGX / Fleet-Profile")
            organism_index.append("_Kein WGX-/Fleet-Profil gefunden._")
            organism_index.append("")

        organism_index.append("<!-- @organism-index:end -->")
        organism_index.append("")
        yield "\n".join(organism_index)

    # --- AI Heatmap ---
    if extras.heatmap:
        heatmap_collector = HeatmapCollector(files)
        hm_report = heatmap_collector.render_markdown()
        if hm_report:
            yield hm_report

    # --- Augment Intelligence ---
    if extras.augment_sidecar:
        augment_block = _render_augment_block(sources)
        if augment_block:
            yield augment_block

    if plan_only:
        return

    # --- 6. Structure ---
    if level != "machine-lean":
        structure = []
        structure.append("## 📁 Structure")
        structure.append("")
        structure.append(build_tree(files))
        structure.append("")
        yield "\n".join(structure) + "\n"

    # --- Index ---
    index_blocks = []
    index_blocks.extend(_heading_block(2, "index", "🧭 Index", nav=nav))

    cats_to_idx = ["source", "doc", "config", "contract", "test"]
    non_empty_cats = []
    for c in cats_to_idx:
        cat_files = [f for f in files if f.category == c]
        if cat_files:
            non_empty_cats.append(c)
    
    ci_files = [f for f in files if "ci" in (f.tags or [])]
    wgx_files = [f for f in files if "wgx-profile" in f.tags]
    
    for c in non_empty_cats:
        index_blocks.append(f"- [{c.capitalize()}](#cat-{_slug_token(c)})")
    
    if ci_files:
        index_blocks.append("- [CI Pipelines](#tag-ci)")
    if wgx_files:
        index_blocks.append("- [WGX Profiles](#tag-wgx-profile)")
    
    index_blocks.append("")

    for c in non_empty_cats:
        cat_files = [f for f in files if f.category == c]
        index_blocks.extend(_heading_block(2, f"cat-{_slug_token(c)}", f"Category: {c}", nav=nav))
        for f in cat_files:
            index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
        index_blocks.append("")

    if ci_files:
        index_blocks.extend(_heading_block(2, "tag-ci", "Tag: ci", nav=nav))
        for f in ci_files:
            index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
        index_blocks.append("")

    if wgx_files:
        index_blocks.extend(_heading_block(2, "tag-wgx-profile", "Tag: wgx-profile", nav=nav))
        for f in wgx_files:
            index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
        index_blocks.append("")

    yield "\n".join(index_blocks) + "\n"

    # --- 7. Manifest ---
    manifest: List[str] = []
    manifest.extend(_heading_block(2, "manifest", "🧾 Manifest" if not code_only else "🧾 Manifest (Code-Only)", nav=nav))

    roots_sorted = sorted(files_by_root.keys())
    if roots_sorted:
        manifest_nav = " · ".join(
            f"[{r}](#manifest-{_slug_token(r)})" for r in roots_sorted
        )
        manifest.append(f"**Repos im Merge:** {manifest_nav}")
        manifest.append("")

    if code_only:
        manifest.append(
            "_Profil: CODE-ONLY – nur Source/Tests/Config/Contracts. Rollen-Shortcut: "
            "`entrypoint`=CLIs/Starts, `config`=zentral, `ci`=Workflows, `test`=Tests._"
        )
        manifest.append("")

    if not roots_sorted:
        manifest.append("_Keine Dateien im Manifest._")
        manifest.append("")
        yield "\n".join(manifest) + "\n"
    else:
        for root in roots_sorted:
            root_files = files_by_root[root]
            stats = repo_stats.get(root, {})
            repo_role = infer_repo_role(root, root_files)

            manifest.extend(_heading_block(3, f"manifest-{_slug_token(root)}", f"Repo `{root}`", nav=nav))
            manifest.append(
                f"- Rolle: {repo_role}"
            )
            if stats:
                manifest.append(
                    f"- Umfang: {stats.get('total', 0)} Dateien "
                    f"({stats.get('text_files', 0)} Text), {human_size(stats.get('bytes', 0))}; "
                    f"Inhalt: {stats.get('included', 0)} mit Content"
                )
            manifest.append("")
            manifest.append("| Path | Category | Tags | Roles | Size | Included | MD5 |")
            manifest.append("| --- | --- | --- | --- | ---: | --- | --- |")

            for fi, status in processed_files:
                if fi.root_label != root:
                    continue

                tags_str = ", ".join(fi.tags) if fi.tags else "-"
                roles_str = ", ".join(fi.roles) if fi.roles else "-"
                included_label = status
                if is_noise_file(fi):
                    included_label = f"{status} (noise)"

                path_str = f"[`{fi.rel_path}`](#{fi.anchor})"
                manifest.append(
                    f"| {path_str} | `{fi.category}` | {tags_str} | {roles_str} | "
                    f"{human_size(fi.size)} | `{included_label}` | `{fi.md5}` |"
                )
            manifest.append("")

        yield "\n".join(manifest) + "\n"

    # --- Fleet Consistency ---
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
    content_header: List[str] = ["# Content", ""]
    content_roots = [fi.root_label for fi, status in processed_files if status in ("full", "truncated", "meta-only", "omitted")]
    if content_roots:
        nav_links = " · ".join(
            f"[{root}](#repo-{_slug_token(root)})" for root in sorted(set(content_roots))
        )
        content_header.append(f"**Repos im Merge:** {nav_links}")
        content_header.append("")

    yield "\n".join(content_header)

    current_root = None

    for fi, status in processed_files:
        if status in ("omitted", "meta-only"):
            continue

        if fi.root_label != current_root:
            repo_slug = _slug_token(fi.root_label)
            yield "\n".join(_heading_block(2, f"repo-{repo_slug}", fi.root_label, nav=nav)) + "\n"
            current_root = fi.root_label

        block = ["---"]
        if getattr(fi, "anchor_alias", "") and fi.anchor_alias != fi.anchor:
            block.append(f'<a id="{fi.anchor_alias}"></a>')
            block.append("")
        block.extend(_heading_block(3, fi.anchor, nav=nav))
        block.append(f"**Path:** `{fi.rel_path}`")
        block.append(f"- Category: {fi.category}")
        if fi.tags:
            block.append(f"- Tags: {', '.join(fi.tags)}")
        else:
            block.append("- Tags: -")
        block.append(f"- Size: {human_size(fi.size)}")
        block.append(f"- Included: {status}")
        block.append(f"- MD5: {fi.md5}")

        content, truncated, trunc_msg = read_smart_content(fi, max_file_bytes)
        block.append(f"<!-- FILE:{_stable_file_id(fi)} -->")

        lang = lang_for(fi.ext)
        block.append("")
        block.append(f"```{lang}")
        block.append(content)
        block.append("```")
        block.append("")
        block.append("[↑ Manifest](#manifest) · [↑ Index](#index)")
        yield "\n".join(block) + "\n\n"

def generate_report_content(
    files: List[FileInfo],
    level: str,
    max_file_bytes: int,
    sources: List[Path],
    plan_only: bool,
    code_only: bool = False,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
    delta_meta: Optional[Dict[str, Any]] = None,
) -> str:
    report = "".join(
        iter_report_blocks(
            files,
            level,
            max_file_bytes,
            sources,
            plan_only,
            code_only,
            debug,
            path_filter,
            ext_filter,
            extras,
            delta_meta,
        )
    )
    if plan_only:
        return "<!-- MODE:PLAN_ONLY -->\n" + report
    try:
        validate_report_structure(report)
    except ValueError as e:
        if debug:
            print(f"DEBUG: Validation Error: {e}")
        raise
    return report

def generate_json_sidecar(
    files: List[FileInfo],
    level: str,
    max_file_bytes: int,
    sources: List[Path],
    plan_only: bool,
    code_only: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    total_size: int = 0,
    delta_meta: Optional[Dict[str, Any]] = None,
    requested_flags: Optional[Dict[str, bool]] = None,
) -> Dict[str, Any]:
    """
    Generate a JSON sidecar structure for machine consumption.
    """
    now = datetime.datetime.utcnow()
    requested_flags = requested_flags or {"plan_only": plan_only, "code_only": code_only}
    plan_only, code_only, normalized_requested = _normalize_mode_flags(
        requested_flags.get("plan_only", False),
        requested_flags.get("code_only", False),
    )
    render_mode = _effective_render_mode(plan_only, code_only)

    requested_flags = {
        "plan_only": bool(normalized_requested["plan_only"]),
        "code_only": bool(normalized_requested["code_only"]),
    }

    if code_only:
        files = [fi for fi in files if fi.category in DEBUG_CONFIG.code_only_categories]

    scope_desc = describe_scope(files)

    total_size = sum(fi.size for fi in files)

    processed = []
    included_count = 0
    text_files = [f for f in files if f.is_text]

    for fi in files:
        status = determine_inclusion_status(fi, level, max_file_bytes)
        if status in ("full", "truncated"):
            included_count += 1
        processed.append((fi, status))

    coverage_pct = round((included_count / len(text_files)) * 100, 1) if text_files else 0.0

    meta = {
        "contract": AGENT_CONTRACT_NAME,
        "contract_version": AGENT_CONTRACT_VERSION,
        "spec_version": SPEC_VERSION,
        "profile": level,
        "generated_at": now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "plan_only": plan_only,
        "code_only": code_only,
        "requested_flags": {
            "plan_only": bool(requested_flags["plan_only"]),
            "code_only": bool(requested_flags["code_only"]),
        },
        "max_file_bytes": max_file_bytes,
        "total_files": len(files),
        "total_size_bytes": total_size,
        "source_repos": sorted([s.name for s in sources]) if sources else [],
        "filters": {
            "path_filter": (path_filter or "").strip(),
            "ext_filter": ",".join(sorted(ext_filter)) if ext_filter else "",
            "included_categories": sorted(list(DEBUG_CONFIG.code_only_categories)) if code_only else [],
            "excluded_categories": [],
            "included_globs": [],
            "excluded_globs": [],
            "binary_policy": "ignore",
            "content_policy": render_mode,
        },
    }

    files_out = []
    for fi, status in processed:
        fid = _stable_file_id(fi)
        file_obj = {
            "id": fid,
            "path": fi.rel_path.as_posix(),
            "repo": fi.root_label,
            "size_bytes": fi.size,
            "is_text": fi.is_text,
            "category": fi.category,
            "tags": fi.tags or [],
            "included": status in ("full", "truncated"),
            "inclusion_status": status,
            "content_ref": {
                "marker": f"FILE:{fid}",
            },
        }
        files_out.append(file_obj)

    out = {
        "meta": meta,
        "artifacts": {
            "primary_json": None,
            "human_md": None,
            "md_parts": [],
        },
        "coverage": {
            "included_text_files": included_count,
            "total_text_files": len(text_files),
            "coverage_pct": coverage_pct,
        },
        "scope": scope_desc,
        "files": files_out,
        "delta": delta_meta or None,
    }
    _validate_agent_json_dict(out, allow_empty_primary=True)
    return out

def write_reports_v2(
    merges_dir: Path,
    hub: Path,
    repo_summaries: List[Dict],
    detail: str,
    mode: str,
    max_bytes: int,
    plan_only: bool,
    code_only: bool = False,
    split_size: int = 0,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
    delta_meta: Optional[Dict[str, Any]] = None,
) -> MergeArtifacts:
    out_paths = []

    plan_only, code_only, requested_flags = _normalize_mode_flags(plan_only, code_only)

    ext_filter_str = ",".join(sorted(ext_filter)) if ext_filter else None
    
    repo_names = [s["name"] for s in repo_summaries]
    run_id = _generate_run_id(repo_names, detail, path_filter, ext_filter_str, plan_only=plan_only, code_only=code_only)

    def process_and_write(target_files, target_sources, output_filename_base_func):
        if split_size > 0:
            # Better approach:
            # 1. Collect all blocks into a list.
            # 2. Join them to validate structure.
            # 3. If valid, iterate the list to write parts.

            iterator = iter_report_blocks(
                target_files,
                detail,
                max_bytes,
                target_sources,
                plan_only,
                code_only,
                debug,
                path_filter,
                ext_filter,
                extras,
                delta_meta,
            )

            all_blocks = list(iterator)
            full_report = "".join(all_blocks)
            if plan_only:
                 full_report = "<!-- MODE:PLAN_ONLY -->\n" + full_report

            if not plan_only:
                try:
                    validate_report_structure(full_report)
                except ValueError as e:
                    if debug:
                        print(f"DEBUG: Validation Error: {e}")
                    raise

            # Now write parts
            local_out_paths = []
            part_num = 1
            current_size = 0
            current_lines = []

            parts_meta = []
            current_part_paths = []

            def flush_part(is_last=False):
                nonlocal part_num, current_size, current_lines, current_part_paths
                if not current_lines:
                    return

                first = current_part_paths[0] if current_part_paths else None
                last = current_part_paths[-1] if current_part_paths else None
                parts_meta.append({"first": first, "last": last})
                current_part_paths = []

                out_path = output_filename_base_func(part_suffix=f"_tmp_part{part_num}")
                out_path.write_text("".join(current_lines), encoding="utf-8")
                local_out_paths.append(out_path)

                part_num += 1
                current_lines = []
                if not is_last:
                    header = f"# WC-Merge Report (Part {part_num})\n\n"
                    current_lines.append(header)
                    current_size = len(header.encode('utf-8'))
                else:
                    current_size = 0

            for block in all_blocks:
                block_len = len(block.encode('utf-8'))
                m = re.search(r"\*\*Path:\*\* `(.+?)`", block)
                block_path = m.group(1) if m else None

                if current_size + block_len > split_size and len(current_lines) > 1:
                    flush_part()

                current_lines.append(block)
                current_size += block_len
                if block_path:
                    current_part_paths.append(block_path)

            flush_part(is_last=True)

            total_parts = len(local_out_paths)
            final_paths = []

            for idx, path in enumerate(local_out_paths, start=1):
                try:
                    text = path.read_text(encoding="utf-8")
                    lines = text.splitlines(True)
                    if lines:
                        prefix_part = "# WC-Merge Report (Part "
                        prefix_main = "# WC-Merge Report"
                        for i, line in enumerate(lines):
                            stripped = line.lstrip("\ufeff")
                            if stripped.startswith(prefix_part) or stripped.startswith(prefix_main):
                                lines[i] = f"# WC-Merge Report (Part {idx}/{total_parts})\n"

                                if total_parts > 1:
                                    meta = parts_meta[idx - 1]
                                    p_start = meta["first"]
                                    p_end = meta["last"]
                                    range_str = f"{p_start} ... {p_end}" if p_start else "Meta/Structure/Index"

                                    prev_name = "none"
                                    if idx > 1:
                                        prev_suffix = f"_part{idx - 1}of{total_parts}"
                                        prev_path_obj = output_filename_base_func(part_suffix=prev_suffix)
                                        prev_name = prev_path_obj.name

                                    sig_block = (
                                        f"<!-- part_signature:\n"
                                        f"  part_index: {idx}\n"
                                        f"  part_total: {total_parts}\n"
                                        f"  continuation_of: \"{prev_name}\"\n"
                                        f"  range: \"{range_str}\"\n"
                                        f"-->\n"
                                        f"**[Part {idx}/{total_parts}]** continuation_of: `{prev_name}` · range: `{range_str}`\n\n"
                                    )
                                    lines.insert(i + 1, sig_block)
                                break
                    text = "".join(lines)
                except Exception:
                    text = None

                if total_parts == 1:
                    new_suffix = ""
                else:
                    new_suffix = f"_part{idx}of{total_parts}"

                new_path = output_filename_base_func(part_suffix=new_suffix)

                if text is not None:
                    new_path.write_text(text, encoding="utf-8")
                    try:
                        path.unlink()
                    except OSError:
                        pass
                else:
                    try:
                        path.rename(new_path)
                    except OSError as e:
                        sys.stderr.write(f"Error renaming {path} to {new_path}: {e}\n")

                final_paths.append(new_path)

            out_paths.extend(final_paths)

        else:
            # Standard single file
            content = generate_report_content(
                target_files,
                detail,
                max_bytes,
                target_sources,
                plan_only,
                code_only,
                debug,
                path_filter,
                ext_filter,
                extras,
                delta_meta,
            )
            out_path = output_filename_base_func(part_suffix="")
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

        process_and_write(
            all_files,
            sources,
            lambda part_suffix="": make_output_filename(
                merges_dir,
                repo_names,
                detail,
                part_suffix,
                path_filter,
                ext_filter_str,
                run_id,
                plan_only=plan_only,
                code_only=code_only,
            ),
        )
        
        if extras and extras.json_sidecar:
            total_size = sum(
                f.size for f in all_files if (not code_only or f.category in DEBUG_CONFIG.code_only_categories)
            )
            json_data = generate_json_sidecar(
                all_files,
                detail,
                max_bytes,
                sources,
                plan_only,
                code_only,
                path_filter,
                ext_filter,
                total_size,
                delta_meta,
                requested_flags=requested_flags,
            )
            if out_paths:
                json_path = out_paths[0].with_suffix('.json')
            else:
                json_path = make_output_filename(
                    merges_dir,
                    repo_names,
                    detail,
                    "",
                    path_filter,
                    ext_filter_str,
                    run_id,
                    plan_only=plan_only,
                    code_only=code_only,
                ).with_suffix('.json')
            
            json_data["artifacts"]["primary_json"] = str(json_path)
            md_parts = [p for p in out_paths if p.suffix.lower() == ".md"]
            json_data["artifacts"]["md_parts"] = [str(p) for p in md_parts]
            json_data["artifacts"]["human_md"] = str(md_parts[0]) if md_parts else None
            _validate_agent_json_dict(json_data)
            json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
            out_paths.append(json_path)

    else:
        for s in repo_summaries:
            s_name = s["name"]
            s_files = s["files"]
            s_root = s["root"]
            
            repo_run_id = _generate_run_id([s_name], detail, path_filter, ext_filter_str, plan_only=plan_only, code_only=code_only)

            process_and_write(
                s_files,
                [s_root],
                lambda part_suffix="": make_output_filename(
                    merges_dir,
                    [s_name],
                    detail,
                    part_suffix,
                    path_filter,
                    ext_filter_str,
                    repo_run_id,
                    plan_only=plan_only,
                    code_only=code_only,
                ),
            )
            
            if extras and extras.json_sidecar:
                total_size = sum(
                    f.size for f in s_files if (not code_only or f.category in DEBUG_CONFIG.code_only_categories)
                )
                json_data = generate_json_sidecar(
                    s_files,
                    detail,
                    max_bytes,
                    [s_root],
                    plan_only,
                    code_only,
                    path_filter,
                    ext_filter,
                    total_size,
                    delta_meta,
                    requested_flags=requested_flags,
                )
                if out_paths:
                    json_path = out_paths[-1].with_suffix('.json')
                else:
                    json_path = make_output_filename(
                        merges_dir,
                        [s_name],
                        detail,
                        "",
                        path_filter,
                        ext_filter_str,
                        repo_run_id,
                        plan_only=plan_only,
                        code_only=code_only,
                    ).with_suffix('.json')
                
                json_data["artifacts"]["primary_json"] = str(json_path)
                md_parts = [p for p in out_paths if p.suffix.lower() == ".md"]
                json_data["artifacts"]["md_parts"] = [str(p) for p in md_parts]
                json_data["artifacts"]["human_md"] = (
                    str(out_paths[-1]) if out_paths[-1].suffix.lower() == ".md" else (str(md_parts[-1]) if md_parts else None)
                )
                _validate_agent_json_dict(json_data)
                json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
                out_paths.append(json_path)

    md_paths = [p for p in out_paths if p.suffix.lower() == ".md"]
    json_paths = [p for p in out_paths if p.suffix.lower() == ".json"]
    other_paths = [p for p in out_paths if p.suffix.lower() not in (".md", ".json")]

    verified_md: List[Path] = []
    for p in md_paths:
        try:
            if p.exists() and p.is_file() and p.stat().st_size > 0:
                verified_md.append(p)
        except Exception:
            pass

    if md_paths and not verified_md:
        raise RuntimeError(
            "wc-merger: Report was announced as written, but no non-empty .md output exists on disk. "
            "Check merges_dir / permissions / rename logic."
        )

    verified_json: List[Path] = []
    if extras and extras.json_sidecar:
        for p in json_paths:
            try:
                if p.exists() and p.is_file() and p.stat().st_size > 0:
                    d = json.loads(p.read_text(encoding="utf-8"))
                    _validate_agent_json_dict(d)
                    verified_json.append(p)
            except Exception:
                pass
        if json_paths and not verified_json:
            raise RuntimeError(
                "wc-merger: JSON primary artifact was announced as written, but no valid non-empty .json exists on disk."
            )

    if extras and extras.json_sidecar:
        return MergeArtifacts(
            primary_json=verified_json[0] if verified_json else None,
            human_md=verified_md[0] if verified_md else None,
            md_parts=verified_md,
            other=other_paths
        )
    else:
        return MergeArtifacts(
            primary_json=None,
            human_md=verified_md[0] if verified_md else None,
            md_parts=verified_md,
            other=other_paths
        )
