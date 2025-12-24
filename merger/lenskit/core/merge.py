from __future__ import annotations
# -*- coding: utf-8 -*-

"""
merge_core – Core functions for repoLens (v2.4 Standard).
Implements AI-friendly formatting, tagging, and strict Pflichtenheft structure.
"""

import os
import sys
import json
import hashlib
import datetime
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Iterator, NamedTuple, Set
from dataclasses import dataclass

try:
    import yaml  # PyYAML
except Exception:  # pragma: no cover
    yaml = None

from .fs_scan import (
    FileInfo,
    scan_repo,
    compute_md5,
    compute_sha256,
    is_probably_text,
    classify_file,
    is_critical_file,
    is_noise_file,
    human_size,
    TEXT_EXTENSIONS,
    SKIP_DIRS,
    SKIP_FILES,
    CONFIG_FILENAMES,
    DOC_EXTENSIONS,
    SOURCE_EXTENSIONS,
    DEFAULT_MAX_BYTES,
    lang_for,
    get_repo_sort_index,
    extract_purpose,
    get_declared_purpose
)

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

EPISTEMIC_HUMILITY_WARNING = "⚠️ **Hinweis:** Dieses Profil/Filter erlaubt keine Aussagen über das Nicht-Vorhandensein von Dateien im Repository. Fehlende Einträge bedeuten lediglich „nicht im Ausschnitt enthalten“."

def _slug_token(s: str) -> str:
    """Deterministic ASCII token suitable for heading ids across renderers."""

    s = s.lower()
    s = s.replace("/", "-").replace(".", "-")
    s = _NON_ALNUM.sub("-", s).strip("-")
    return s


READING_POLICY_BANNER = (
    "**READING POLICY (verbindlich):**\n"
    "- Dieses Markdown ist die kanonische Quelle und vollständig zu lesen.\n"
    "- Die JSON-Datei ist nur Index/Metadaten/Einstieg und enthält NICHT die volle Information.\n"
    "\n"
)


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

    Many Markdown renderers (especially on iOS) fail to emit heading IDs, and
    some ignore the `{#id}` syntax. To maximize compatibility for links like
    `#manifest` or `#file-tools-...`, we emit an explicit HTML anchor before the
    tokenized heading. This keeps links working when either heading IDs *or*
    HTML anchors are supported by the renderer.
    """

    # NOTE:
    # - Some renderers do not generate heading IDs.
    # - Some renderers strip HTML anchors.
    # We therefore provide three layers:
    #   (1) visible search marker: "§§ <token>" (works even if links are dead)
    #   (2) HTML anchor: <a id="token"></a> (works if HTML allowed)
    #   (3) tokenized heading: "## token" (works if heading IDs generated)
    nav = nav or NavStyle()
    lines: List[str] = []
    if nav.emit_search_markers:
        lines.append(f"§§ {token}")

    # Correction for readable headers (Spec v2.4):
    # Instead of "## token", we use "## Title" if available, keeping the anchor for linking.
    lines.append(f'<a id="{token}"></a>')

    if title:
        lines.append("#" * level + " " + title)
    else:
        lines.append("#" * level + " " + token)

    lines.append("")
    return lines

# --- Configuration & Heuristics ---

SPEC_VERSION = "2.4"
MERGES_DIR_NAME = "merges"

# Formale Contract-Deklaration für alle repoLens-Reports.
# Name/Version können von nachgelagerten Tools verwendet werden,
# um das Format eindeutig zu erkennen.
MERGE_CONTRACT_NAME = "repolens-report"
MERGE_CONTRACT_VERSION = SPEC_VERSION

def _debug_log_func(debug: "DebugCollector", level: str):
    """
    Map configured severity levels to DebugCollector methods.
    If misconfigured, warn once (per call) and fall back to warn.
    """
    lvl = (level or "warn").strip().lower()
    if lvl in ("warn", "warning"):
        return debug.warn
    if lvl in ("error", "err"):
        return getattr(debug, "error", debug.warn)
    if lvl in ("info",):
        return getattr(debug, "info", debug.warn)

    # Misconfiguration: make it visible, then fall back.
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
    Ermöglicht spätere Erweiterung (Severity-Levels, neue Tags) ohne API-Break.
    """
    allowed_categories: Set[str]
    allowed_tags: Set[str]
    code_only_categories: Set[str]

    # Severity levels for checks (extensions)
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

AGENT_CONTRACT_NAME = "repolens-agent"
AGENT_CONTRACT_VERSION = "v1"

# Delta Report configuration
MAX_DELTA_FILES = 10  # Maximum number of files to show in each delta section

# Top-level roots to skip in auto-discovery
SKIP_ROOTS = {
    MERGES_DIR_NAME,
    "merge",
    "output",
    "out",
}

def _stable_file_id(fi: "FileInfo") -> str:
    """
    Stable across runs as long as repo + rel-path stay the same.
    Avoids relying on Markdown heading anchors or renderer-specific IDs.
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
    Minimal, dependency-free validation. Purpose: prevent "success but nothing usable".
    (Full JSON-Schema validation can be added later; this is the hard safety belt.)
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
    if "index_json" not in artifacts:
        raise ValueError("agent-json: artifacts.index_json missing")
    if not allow_empty_primary and not artifacts.get("index_json"):
        raise ValueError("agent-json: artifacts.index_json missing")
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
    Result object for write_reports() containing all generated artifacts.
    Makes it explicit which artifact is the primary (JSON or Markdown).
    """
    index_json: Optional[Path] = None
    canonical_md: Optional[Path] = None
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
        if self.index_json:
            paths.append(self.index_json)
        if self.canonical_md and self.canonical_md not in paths:
            paths.append(self.canonical_md)
        for p in self.md_parts:
            if p not in paths:
                paths.append(p)
        for p in self.other:
            if p not in paths:
                paths.append(p)
        return paths

    def get_primary_path(self) -> Optional[Path]:
        """Return the primary artifact path (JSON if exists, otherwise Markdown)."""
        return self.index_json or self.canonical_md


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
    wgx_profile_expected: Optional[bool]  # True/False if declared, else None
    unknown_category_ratio: float
    unknown_categories: List[str]
    unknown_tags: List[str]
    warnings: List[str]
    recommendations: List[str]
    meta_sync_status: str = "unknown"  # "ok"|"warn"|"unknown"
    meta_sync: Optional[Dict[str, Any]] = None


class HealthCollector:
    """Collects health checks for repositories (Stage 1: Repo Doctor)."""

    def __init__(self, hub_path: Optional[Path] = None) -> None:
        self._repo_health: Dict[str, RepoHealth] = {}
        self.hub_path = hub_path
        self.fleet_snapshot = self._read_fleet_snapshot()
        self.fleet_snapshot_outdated = self._is_fleet_snapshot_outdated(self.fleet_snapshot)

    def _parse_dt(self, s: str) -> Optional[datetime.datetime]:
        # Accept "Z" timestamps and full ISO
        try:
            if s.endswith("Z"):
                return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
            # fromisoformat handles offsets like +00:00
            return datetime.datetime.fromisoformat(s)
        except Exception:
            return None

    def _is_fleet_snapshot_outdated(self, snap: Optional[Dict[str, Any]]) -> bool:
        if not snap or not isinstance(snap, dict):
            return False
        try:
            validity = snap.get("validity") if isinstance(snap.get("validity"), dict) else {}
            ttl_hours = validity.get("ttl_hours")
            if not isinstance(ttl_hours, int) or ttl_hours < 1:
                return False
            gen = snap.get("generated_at")
            if not isinstance(gen, str) or not gen.strip():
                return False
            dt = self._parse_dt(gen.strip())
            if not dt:
                return True
            now = datetime.datetime.now(datetime.timezone.utc)
            # normalize naive datetimes to UTC to avoid crashes
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return (now - dt) > datetime.timedelta(hours=ttl_hours)
        except Exception:
            # Safer to assume outdated/invalid than fresh if parsing fails
            return True

    def _read_fleet_snapshot(self) -> Optional[Dict[str, Any]]:
        """Reads .gewebe/cache/fleet.snapshot.json if available."""
        if not self.hub_path:
            return None
        try:
            p = self.hub_path / ".gewebe/cache/fleet.snapshot.json"
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
        return None

    def _pick_ai_context_paths(self, files: List["FileInfo"]) -> List[Path]:
        """
        Return candidate .ai-context.yml paths, preferring repo-root (shortest rel_path).
        Deterministic ordering prevents 'first file wins' randomness.
        """
        candidates: List[Tuple[int, str, Path]] = []
        for f in files:
            rp = str(getattr(f, "rel_path", ""))
            name = getattr(getattr(f, "rel_path", None), "name", "")
            if name == ".ai-context.yml" or rp.endswith("/.ai-context.yml") or rp.endswith(".ai-context.yml"):
                ap = getattr(f, "abs_path", None)
                if ap:
                    depth = rp.count("/")  # root file tends to have smallest depth
                    candidates.append((depth, rp, Path(ap)))
        candidates.sort(key=lambda t: (t[0], t[1]))
        return [p for _, __, p in candidates]

    def _read_sync_report(self, repo_root: Optional[Path]) -> Optional[Dict[str, Any]]:
        """Reads .gewebe/out/sync.report.json if available."""
        if not repo_root:
            return None
        try:
            p = repo_root / ".gewebe/out/sync.report.json"
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
        return None

    def _eval_sync_status(self, report: Optional[Dict[str, Any]]) -> str:
        """Evaluates meta sync status: ok|warn|unknown."""
        if not report:
            return "unknown"

        # Immediate error check (Patch 1)
        if report.get("status") == "error":
            return "warn"

        # Safe access to fields
        summary = report.get("summary", {})
        mode = report.get("mode", "unknown")

        err_count = summary.get("error", 0)
        blocked_count = summary.get("blocked", 0)
        add_count = summary.get("add", 0)
        update_count = summary.get("update", 0)

        # Summary error check
        if err_count > 0:
            return "warn"

        if mode == "dry_run":
             # Pending changes in dry_run are a warning (not synced yet)
             if add_count > 0 or update_count > 0 or blocked_count > 0:
                 return "warn"
             return "ok" # Clean dry run means sync is up to date

        if mode == "apply":
            if blocked_count > 0:
                return "warn"
            # If applied successfully (error=0, blocked=0), status is ok.
            return "ok"

        return "unknown"

    def _read_wgx_profile_expected(self, files: List["FileInfo"], root_label: str) -> Optional[bool]:
        """
        Reads `profile_expected` from fleet snapshot (primary truth).
        """
        # T5: Fleet-Erwartungen nur aus fleet.snapshot.json
        if self.fleet_snapshot:
            repos = self.fleet_snapshot.get("data", {}).get("repos", {})
            repo_data = repos.get(root_label)
            if repo_data:
                wgx = repo_data.get("wgx") if isinstance(repo_data.get("wgx"), dict) else {}
                return wgx.get("profile_expected")
            # If repo not in snapshot, we assume unknown (None)
            return None

        # Fallback to local (deprecated by T5 but safe to keep as secondary?
        # T5 says "Fleet-Erwartungen ... NUR aus fleet.snapshot.json")
        # So we should probably return None if snapshot missing, or maybe
        # we check if we should strictly follow "NUR" (ONLY).
        # "wenn Snapshot fehlt/älter: WARN ... statt CRITICAL." implies we know it's missing.
        return None

    def analyze_repo(self, root_label: str, files: List["FileInfo"]) -> RepoHealth:
        """Analyze health of a single repository."""
        # Check if repo is known to fleet snapshot (completeness check)
        is_known_to_snapshot = True
        if self.fleet_snapshot:
            repos = self.fleet_snapshot.get("data", {}).get("repos", {})
            if root_label not in repos:
                is_known_to_snapshot = False

        # Try to determine repo root
        repo_root: Optional[Path] = None

        # Strategy A: Deterministic from Hub (Preferred)
        if self.hub_path:
            candidate = self.hub_path / root_label
            if candidate.exists() and candidate.is_dir():
                repo_root = candidate

        # Strategy B: Reconstruction from files (Fallback)
        if not repo_root and files:
            try:
                # Robust reconstruction: take abs path of first file, walk up by len(rel_path.parts) - 1
                f0 = files[0]
                if f0.abs_path and f0.rel_path:
                    # e.g. /a/b/c/d/file.txt, rel=d/file.txt -> len(parts)=2.
                    # parents[0] = /a/b/c/d
                    # parents[1] = /a/b/c <-- repo root
                    # Index should be len(f0.rel_path.parts) - 1
                    # Ensure index is within bounds of parents
                    idx = len(f0.rel_path.parts) - 1
                    if idx < len(f0.abs_path.parents):
                        repo_root = f0.abs_path.parents[idx]
            except Exception:
                pass

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
        wgx_profile_expected = self._read_wgx_profile_expected(files, root_label)
        has_ci_workflows = any("ci" in (f.tags or []) for f in files)
        # 4. Contracts (heuristic extended: contracts/ OR **/*.schema.json)
        def is_contract(f):
            if f.category == "contract":
                return True
            rel = str(getattr(f, "rel_path", "")).lower()
            if rel.endswith(".schema.json"):
                return True
            return False

        has_contracts = any(is_contract(f) for f in files)
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

        if not is_known_to_snapshot:
            # We don't add a per-repo warning to avoid spam if the user requested "incomplete snapshot warning".
            # But the requirement says: "Snapshot incomplete (unknown repos: X)" global warning.
            # So we track it via a flag on RepoHealth or just count it globally.
            # Let's add an info-level warning here so it is visible in the per-repo details if desired?
            # User said: "optional pro repo: unknown_to_snapshot als Info/Warn (nicht als CRITICAL)."
            warnings.append("Repo unknown to fleet snapshot")
            # We do NOT mark this as CRITICAL, only warn/info.

        if not has_readme:
            warnings.append("No README.md found")
            recommendations.append("Add README.md for better AI/human navigation")

        # WGX profile policy:
        # - If explicitly NOT expected -> do not warn.
        # - If expected -> warn.
        # - If unknown (e.g. no snapshot) -> do NOT warn about profile itself, but we warned about snapshot.
        if not has_wgx_profile:
            if wgx_profile_expected is True:
                warnings.append("No .wgx/profile.yml found (expected by fleet snapshot)")
                recommendations.append("Create .wgx/profile.yml for Fleet conformance")
            elif wgx_profile_expected is None:
                # If unknown, we don't warn about missing profile, because we don't know if it is required.
                # (Strict logic T3/T5).
                pass

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

        # Meta Sync Check
        meta_sync = self._read_sync_report(repo_root)
        meta_sync_status = self._eval_sync_status(meta_sync)

        if meta_sync_status == "warn":
             warnings.append("Meta Sync Issues (see details)")
             # We assume recommendation is handled by sync tool report

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
            wgx_profile_expected=wgx_profile_expected,
            unknown_category_ratio=unknown_category_ratio,
            unknown_categories=unknown_categories,
            unknown_tags=unknown_tags,
            warnings=warnings,
            recommendations=recommendations,
            meta_sync_status=meta_sync_status,
            meta_sync=meta_sync,
        )

        # Optional enrichment (keeps compatibility if RepoHealth doesn't define it)
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
        no_ci = sum(1 for h in self._repo_health.values() if not h.has_ci_workflows)
        no_contracts = sum(1 for h in self._repo_health.values() if not h.has_contracts)
        # Only count missing WGX profile as a "problem" if expected is True or unknown.
        no_wgx = sum(
            1 for h in self._repo_health.values()
            if (not h.has_wgx_profile) and (h.wgx_profile_expected is not False)
        )

        # Snapshot Warn Global: missing OR outdated OR incomplete
        snapshot_missing = not self.fleet_snapshot
        snapshot_outdated = bool(self.fleet_snapshot_outdated)

        # Check for incomplete snapshot (repos present locally but not in snapshot)
        unknown_repos_count = 0
        if self.fleet_snapshot:
            snapshot_repos = self.fleet_snapshot.get("data", {}).get("repos", {})
            for h in self._repo_health.values():
                if h.repo_name not in snapshot_repos:
                    unknown_repos_count += 1

        if no_ci > 0 or no_contracts > 0 or no_wgx > 0 or snapshot_missing or snapshot_outdated or unknown_repos_count > 0:
            lines.append("### ⚔ Repo Feindynamiken (Global Risks)")
            lines.append("")
            if snapshot_missing:
                lines.append("- ⚠️ **Fleet Snapshot missing** – policy checks skipped or may be inaccurate.")
            elif snapshot_outdated:
                lines.append("- ⚠️ **Fleet Snapshot outdated (TTL exceeded)** – policy checks skipped or may be inaccurate.")

            if unknown_repos_count > 0:
                lines.append(f"- ⚠️ **Snapshot incomplete** – {unknown_repos_count} repositories unknown to fleet snapshot.")

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
            if health.wgx_profile_expected is True:
                indicators.append("WGX Expected: yes")
            elif health.wgx_profile_expected is False:
                indicators.append("WGX Expected: no")
            else:
                indicators.append("WGX Expected: unknown")
            indicators.append(f"CI: {'yes' if health.has_ci_workflows else 'no'}")
            indicators.append(f"Contracts: {'yes' if health.has_contracts else 'no'}")
            indicators.append(f"AI Context: {'yes' if health.has_ai_context else 'no'}")
            lines.append(f"- **Indicators:** {', '.join(indicators)}")

            # Meta Sync
            if health.meta_sync:
                ms = health.meta_sync
                summ = ms.get("summary", {})
                mode = ms.get("mode", "?")
                sync_detail = f"mode={mode} add={summ.get('add',0)} upd={summ.get('update',0)} blk={summ.get('blocked',0)} err={summ.get('error',0)}"
                lines.append(f"- **Meta Sync:** {health.meta_sync_status} ({sync_detail})")
            else:
                 lines.append(f"- **Meta Sync:** unknown")

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

            # Warnings (Standard)
            if health.warnings:
                lines.append("")
                lines.append("**Detailed Warnings:**")
                for warning in health.warnings:
                    lines.append(f"  - {warning}")

            # Recommendations
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
        # Filter for relevant categories
        relevant = [f for f in self.files if f.category in ("source", "config", "contract", "test")]
        # Sort by size desc
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

        # Sort by size
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
    Nur aktivierte Flags werden gesetzt, damit das Schema schlank bleibt.

    Args:
        extras: ExtrasConfig mit den gewünschten Extras
        num_repos: Anzahl der Repos im Merge (für Fleet Panorama - muss explizit übergeben werden)
    """
    extras_meta: Dict[str, bool] = {}
    if extras.health:
        extras_meta["health"] = True
    if extras.organism_index:
        extras_meta["organism_index"] = True
    # Fleet Panorama nur bei Multi-Repo-Merges
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
    Only shown if:
      - extras.fleet_panorama is true
      - more than one repo is being merged
    """
    if len(sources) < 2:
        return None

    # Group files per repo
    grouped: Dict[str, List["FileInfo"]] = {}
    for fi in files:
        grouped.setdefault(fi.root_label, []).append(fi)

    lines: List[str] = []
    lines.append("<!-- @fleet-panorama:start -->")
    lines.append("## 🛰 Fleet Panorama")
    lines.append("")

    # Summary header
    total_files = sum(len(v) for v in grouped.values())
    total_bytes = sum(f.size for f in files)
    lines.append(f"**Summary:** {len(grouped)} repos, {total_bytes} bytes, {total_files} files")
    lines.append("")

    # Per-repo details
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
    Convention: {repo_name}_augment.yml either in the repo root or its parent.
    """
    for source in sources:
        try:
            # Try in the repo directory itself
            candidate = source / f"{source.name}_augment.yml"
            if candidate.exists():
                return candidate

            # Try in parent directory
            candidate_parent = source.parent / f"{source.name}_augment.yml"
            if candidate_parent.exists():
                return candidate_parent
        except (OSError, PermissionError):
            # If we cannot access this source, skip it
            continue
    return None


def _render_augment_block(sources: List[Path]) -> str:
    """
    Render the Augment Intelligence block based on an augment sidecar, if present.
    The expected structure matches tools_augment.yml (augment.hotspots, suggestions, risks, dependencies, priorities, context).
    """
    augment_path = _find_augment_file_for_sources(sources)
    if not augment_path:
        return ""

    # yaml is optional; if not available, render a basic block
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
        # If the augment file is malformed, log error and do not break the merge
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
    Verändert keine Merge-Logik, liefert nur Hinweise.
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


# Large generated files or lockfiles that should be summarized in 'dev' profile
SUMMARIZE_FILES = {
    "package-lock.json", "pnpm-lock.yaml", "Cargo.lock", "yarn.lock", "Pipfile.lock", "poetry.lock"
}

HARDCODED_HUB_PATH = (
    "/private/var/mobile/Containers/Data/Application/"
    "B60D0157-973D-489A-AA59-464C3BF6D240/Documents/wc-hub"
)

HUB_PATH_FILENAME = ".repolens-hub-path.txt"

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
    "aussensensor",
    "semantAH",
    "leitstand",
    "heimlern",
    "tools",
    "weltgewebe",
    "vault-gewebe",
]

# --- Utilities ---

def _hub_path_file(script_path: Path) -> Path:
    # liegt im repoLens-Skriptordner (neben repolens.py)
    return script_path.parent / HUB_PATH_FILENAME


def load_saved_hub_path(script_path: Path) -> Optional[Path]:
    f = _hub_path_file(script_path)
    try:
        if not f.is_file():
            return None
        raw = f.read_text(encoding="utf-8").strip()
        if not raw:
            return None
        p = Path(raw).expanduser()
        if p.is_dir():
            return p
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to load hub path from {f}: {e}\n")
        return None
    return None


def save_hub_path(script_path: Path, hub_dir: Path) -> bool:
    f = _hub_path_file(script_path)
    try:
        f.write_text(str(hub_dir.resolve()), encoding="utf-8")
        return True
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to save hub path to {f}: {e}\n")
        return False


def infer_repo_role(root_label: str, files: List["FileInfo"]) -> str:
    """
    Infers the high-level semantic role of the repository within the organism.
    """
    roles = []
    root = root_label.lower()

    # Name-based heuristics
    if "tool" in root or "merger" in root: roles.append("tooling")
    if "contract" in root or "schema" in root: roles.append("contracts")
    if "meta" in root: roles.append("governance")
    if "lern" in root: roles.append("education")
    if "geist" in root: roles.append("knowledge-base")
    if "haus" in root: roles.append("logic-core")
    if "sensor" in root: roles.append("ingestion")
    if "ui" in root or "app" in root or "leitstand" in root: roles.append("ui")
    if "wgx" in root: roles.append("fleet-management")

    # Content-based heuristics
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
        if f.is_text and f.category in {"source", "doc", "config", "test", "contract"}
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

    Only adds roles that meaningfully refine the category:
    - doc-essential: README-level docs
    - config: configuration/contract-style paths or config extensions
    - entrypoint: common entrypoint filenames
    - ai-context: AI/context-bearing paths or tags
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

    # Deduplicate while preserving order
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

    Focuses on included files and boosts likely entrypoints/configs.
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

        # Light size bias to surface substantial files without overwhelming the list
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
    Returns one of {"full", "meta-only", "omitted", "truncated"} (truncated unused today).
    """
    if not fi.is_text:
        return "omitted"

    tags = fi.tags or []

    if level == "overview":
        return "full" if is_priority_file(fi) else "meta-only"

    if level == "summary":
        if fi.category in ["doc", "config", "contract"] or "ci" in tags or "ai-context" in tags or "wgx-profile" in tags:
            return "full"
        if fi.category in ["source", "test"]:
            return "full" if is_priority_file(fi) else "meta-only"
        return "full" if is_priority_file(fi) else "meta-only"

    if level in ("dev", "machine-lean"):
        if "lockfile" in tags:
            return "meta-only" if fi.size > 20_000 else "full"
        if fi.category in ["source", "test", "config", "contract"] or "ci" in tags:
            return "full"
        if fi.category == "doc":
            return "full" if is_priority_file(fi) else "meta-only"
        return "meta-only"

    if level == "max":
        return "full"

    return "full" if fi.size <= max_file_bytes else "omitted"

def detect_hub_dir(script_path: Path, arg_base_dir: Optional[str] = None) -> Path:
    env_base = os.environ.get("REPOLENS_BASEDIR")
    if env_base:
        p = Path(env_base).expanduser()
        if p.is_dir():
            return p

    saved = load_saved_hub_path(script_path)
    if saved is not None:
        return saved

    p = Path(HARDCODED_HUB_PATH)
    try:
        if p.expanduser().is_dir():
            return p
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to check hub dir {p}: {e}\n")

    if arg_base_dir:
        p = Path(arg_base_dir).expanduser()
        if p.is_dir():
            return p

    return script_path.parent


def get_merges_dir(hub: Path) -> Path:
    merges = hub / MERGES_DIR_NAME
    merges.mkdir(parents=True, exist_ok=True)
    return merges

def parse_human_size(text: str) -> int:
    text = str(text).upper().strip()
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

def _effective_render_mode(plan_only: bool, code_only: bool) -> str:
    """Return the effective render mode based on plan/code switches."""

    plan_only = bool(plan_only)
    code_only = bool(code_only)

    # plan_only wins – avoid conflicting content policies.
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

    Args:
        repo_names: List of repository names
        detail: Profile level (dev, max, summary, etc.)
        path_filter: Optional path filter
        ext_filter: Optional extension filter
        timestamp: Optional timestamp string (if None, uses current time)

    Returns:
        A deterministic run_id string
    """
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%y%m%d-%H%M")

    components: List[str] = []

    plan_only, code_only, _ = _normalize_mode_flags(plan_only, code_only)

    # Path block first (stable anchor).
    if path_filter:
        path_slug = path_filter.strip().strip("/").replace("/", "-")
        if path_slug:
            components.append(path_slug)

    # Repo block
    if not repo_names:
        components.append("no-repo")
    elif len(repo_names) == 1:
        components.append(repo_names[0].replace("/", "-"))
    else:
        repo_str = "-".join(sorted(repo_names))
        repo_hash = hashlib.md5(repo_str.encode("utf-8")).hexdigest()[:6]
        components.append(f"multi-{repo_hash}")

    # Mode + profile blocks
    components.append(_effective_render_mode(plan_only, code_only))
    components.append(detail)

    # Optional filters (makes run_id unique per filter combination)
    if ext_filter:
        ext_clean = ext_filter.replace(".", "").replace(",", "+").replace(" ", "")
        if ext_clean:
            components.append(f"ext-{ext_clean}")

    # Timestamp always last
    components.append(timestamp)

    return "-".join(components)


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
    timestamp: Optional[str] = None,
) -> Path:
    """
    Erzeugt den endgültigen Dateinamen für den Merge-Report.

    If run_id is provided, uses it as the base stem (deterministic).
    Otherwise, generates filename from components (legacy behavior).

    Neuer Wunsch:
    - Zuerst der Block aus dem Pfad-Filter (ohne 'path-'-Präfix)
    - Danach der bisherige Rest (Repo-Block, Detail, Timestamp, evtl. Filter/Part)
    """

    plan_only, code_only, _ = _normalize_mode_flags(plan_only, code_only)
    render_mode = _effective_render_mode(plan_only, code_only)

    # Normalize "no path filter" sentinels coming from UI/config.
    # If the UI stores "root" (or "/") to mean "no specific subpath selected",
    # we must *not* leak that into the filename.
    if isinstance(path_filter, str):
        pf = path_filter.strip()
        if pf in ("", "root", "/"):
            path_filter = None

    # Phase 1.3: If run_id is provided and mode != single, use simple filename:
    # <run_id>[_partxofy]_merge.md
    #
    # NOTE: We intentionally *disable* the run_id-as-filename shortcut.
    # Reason: it produces opaque stems like "9f75ad" which are bad for humans,
    # and it also hides useful context (mode/detail/timestamp).
    # The run_id can still live in metadata; filenames stay descriptive.

    # Legacy behavior: build filename from components
    # 1. Timestamp (jetzt immer am Ende)
    ts = timestamp if timestamp else datetime.datetime.now().strftime("%y%m%d-%H%M")

    # 2. Repo-Block
    if not repo_names:
        repo_block = "no-repo"
    elif len(repo_names) == 1:
        repo_block = repo_names[0]
    else:
        repo_block = "multi"
    repo_block = repo_block.replace("/", "-")

    # 3. Detail-Block (overview/summary/dev/max)
    detail_block = detail

    # 4. Pfad-Block: aus path_filter, aber OHNE 'path-' Präfix
    # Wichtig: Wenn KEIN spezifischer Pfad gewählt ist, soll hier gar nichts stehen.
    path_block = None
    if path_filter:
        slug = path_filter.strip().strip("/")
        if slug:
            path_block = slug.replace("/", "-")

    # 5. Mode-Block (Kollisionen vermeiden)
    mode_block = render_mode

    # 6. Optional: Extension-Filter-Block (nur, wenn bewusst gesetzt)
    ext_block = None
    if ext_filter:
        cleaned = ext_filter.replace(" ", "").replace(".", "").replace(",", "+")
        if cleaned:
            ext_block = f"ext-{cleaned}"

    # 7. Optional: Part-Suffix (_partXofY o. ä.) – kommt schon fertig rein
    part_block = part_suffix.lstrip("_") if part_suffix else ""

    # 8. Reihenfolge bauen:
    #    1. path_block
    #    2. repo_block
    #    3. mode_block
    #    4. detail_block
    #    5. ext_block (falls vorhanden)
    #    6. part_block (falls vorhanden)
    #    7. ts (am Ende)
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
    Shows what changed between base and current import.

    Supports both formats:
    1. Schema-compliant (base_import, current_timestamp, summary.files_*)
    2. Detailed format (base_timestamp, files_added/removed/changed as arrays)
    """
    lines = []
    lines.append("<!-- @delta:start -->")
    lines.append("## ♻ Delta Report")
    lines.append("")

    # Extract timestamps - support both schema (base_import) and legacy (base_timestamp)
    base_ts = delta_meta.get("base_import") or delta_meta.get("base_timestamp", "unknown")
    current_ts = delta_meta.get("current_timestamp", "unknown")

    lines.append(f"- **Base Import:** {base_ts}")
    lines.append(f"- **Current:** {current_ts}")
    lines.append("")

    def _safe_list_len(val):
        """Helper: safely get length of value if it's a list, else 0."""
        return len(val) if isinstance(val, list) else 0

    # Check for schema-compliant summary object
    summary = delta_meta.get("summary", {})
    if summary and isinstance(summary, dict):
        # Schema-compliant format with counts
        added_count = summary.get("files_added", 0)
        removed_count = summary.get("files_removed", 0)
        changed_count = summary.get("files_changed", 0)

        lines.append("**Summary:**")
        lines.append(f"- Files added: {added_count}")
        lines.append(f"- Files removed: {removed_count}")
        lines.append(f"- Files changed: {changed_count}")
        lines.append("")

        # Check for detailed lists (optional extension to schema)
        added = delta_meta.get("files_added", [])
        removed = delta_meta.get("files_removed", [])
        changed = delta_meta.get("files_changed", [])
    else:
        # Legacy detailed format with arrays
        added = delta_meta.get("files_added", [])
        removed = delta_meta.get("files_removed", [])
        changed = delta_meta.get("files_changed", [])

        lines.append("**Summary:**")
        lines.append(f"- Files added: {_safe_list_len(added)}")
        lines.append(f"- Files removed: {_safe_list_len(removed)}")
        lines.append(f"- Files changed: {_safe_list_len(changed)}")
        lines.append("")

    # Detail sections (only if we have lists)
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

    # Use new Validator
    validator = ReportValidator(plan_only=plan_only, code_only=code_only, machine_lean=(level=="machine-lean"))
    validator.validate_full(report)

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
    Contains meta, files array, and minimal verification guards.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
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

    # Build meta block (agent-first contract)
    meta = {
        "contract": AGENT_CONTRACT_NAME,
        "contract_version": AGENT_CONTRACT_VERSION,
        # keep existing useful fields for compatibility/traceability
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
        # explicit include/exclude semantics (negation available even if None)
        "filters": {
            "path_filter": (path_filter or "").strip(),
            "ext_filter": ",".join(sorted(ext_filter)) if ext_filter else "",
            # explicit negation sets (agent-safe): empty list means "no restriction" / "none excluded"
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
                # Markdown marker search is more robust than anchors/links.
                "marker": f"FILE:{fid}",
            },
        }
        files_out.append(file_obj)

    out = {
        "meta": meta,
        "reading_policy": {
            "canonical_source": "md",
            "md_required": True,
            "json_role": "index_and_metadata_only",
            "md_contains_full_information": True,
        },
        "artifacts": {
            # filled by writer (paths)
            "index_json": None,
            "canonical_md": None,
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

def write_reports(
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

    # Global consistent timestamp for this run (all parts/formats must share it)
    global_ts = datetime.datetime.now().strftime("%y%m%d-%H%M")

    # Phase 1.3: Generate deterministic run_id once for this merge
    repo_names = [s["name"] for s in repo_summaries]
    run_id = _generate_run_id(
        repo_names, detail, path_filter, ext_filter_str,
        plan_only=plan_only, code_only=code_only, timestamp=global_ts
    )

    # Helper for writing logic
    def process_and_write(target_files, target_sources, output_filename_base_func):
        # Instantiate stream validator
        validator = ReportValidator(plan_only=plan_only, code_only=code_only, machine_lean=(detail=="machine-lean"))

        if split_size > 0:
            local_out_paths = []
            part_num = 1
            current_size = 0
            current_lines = []

            # --- Metadata tracking for parts (NEW) ---
            parts_meta = []  # List of dicts: {first, last}
            current_part_paths = []  # Paths in current buffer

            # Helper to flush
            def flush_part(is_last=False):
                nonlocal part_num, current_size, current_lines, current_part_paths
                if not current_lines:
                    return

                # Record metadata for this part
                first = current_part_paths[0] if current_part_paths else None
                last = current_part_paths[-1] if current_part_paths else None
                parts_meta.append({"first": first, "last": last})
                current_part_paths = []

                # Temporärer Name während der Generierung
                # Wir nutzen _tmp_partX, um es später sauber umzubenennen
                out_path = output_filename_base_func(part_suffix=f"_tmp_part{part_num}")
                out_path.write_text("".join(current_lines), encoding="utf-8")
                local_out_paths.append(out_path)

                part_num += 1
                current_lines = []
                # Add continuation header for next part
                if not is_last:
                    header = f"# repoLens Report (Part {part_num})\n\n"
                    # Note: we don't feed continuation headers to validator as they are technical split artifacts,
                    # not part of the logical report structure.
                    current_lines.append(header)
                    current_size = len(header.encode('utf-8'))
                else:
                    current_size = 0

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

            for block in iterator:
                # Validate the block before writing
                validator.feed(block)

                block_len = len(block.encode('utf-8'))

                # --- Path detection (NEW) ---
                # Detect path in block using regex to track range for signatures
                m = re.search(r"\*\*Path:\*\* `(.+?)`", block)
                block_path = m.group(1) if m else None

                if current_size + block_len > split_size and len(current_lines) > 1:
                    flush_part()
                    # After flush, block belongs to next part.
                    # current_part_paths was cleared in flush_part.

                current_lines.append(block)
                current_size += block_len
                if block_path:
                    current_part_paths.append(block_path)

            flush_part(is_last=True)
            validator.close()

            # Nachlauf: Header normalisieren UND Dateien umbenennen (Part X of Y)
            total_parts = len(local_out_paths)
            final_paths = []

            for idx, path in enumerate(local_out_paths, start=1):
                # 1. Header Rewrite
                try:
                    text = path.read_text(encoding="utf-8")
                    lines = text.splitlines(True)
                    if lines:
                        prefix_part = "# repoLens Report (Part "
                        prefix_main = "# repoLens Report"
                        for i, line in enumerate(lines):
                            stripped = line.lstrip("\ufeff")
                            if stripped.startswith(prefix_part) or stripped.startswith(prefix_main):
                                lines[i] = f"# repoLens Report (Part {idx}/{total_parts})\n"

                                # --- Inject Signature (NEW) ---
                                if total_parts > 1:
                                    meta = parts_meta[idx - 1]
                                    p_start = meta["first"]
                                    p_end = meta["last"]
                                    range_str = f"{p_start} ... {p_end}" if p_start else "Meta/Structure/Index"

                                    prev_name = "none"
                                    if idx > 1:
                                        # calculate name of part idx-1
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
                    text = None  # Skip rewrite if read fails, but still rename

                # 2. Rename File
                # If total_parts == 1, no part suffix.
                # If total_parts > 1, _partXofY.
                if total_parts == 1:
                    new_suffix = ""
                else:
                    new_suffix = f"_part{idx}of{total_parts}"

                new_path = output_filename_base_func(part_suffix=new_suffix)

                if text is not None:
                    new_path.write_text(text, encoding="utf-8")
                    # Delete old tmp file
                    try:
                        path.unlink()
                    except OSError:
                        pass
                else:
                    # Just rename if we couldn't read/edit content
                    try:
                        path.rename(new_path)
                    except OSError as e:
                        sys.stderr.write(f"Error renaming {path} to {new_path}: {e}\n")

                final_paths.append(new_path)

            out_paths.extend(final_paths)

        else:
            # Standard single file (no split logic active, e.g. split_size=0)
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

            # Spec v2.4: Always enforce Part N/M header, even for single files (1/1)
            lines = content.splitlines(True)
            if lines:
                prefix_ver = "# repoLens Report (v"
                prefix_main = "# repoLens Report"
                for i, line in enumerate(lines):
                    stripped = line.lstrip("\ufeff")
                    if stripped.startswith(prefix_ver) or stripped.startswith(prefix_main):
                        lines[i] = "# repoLens Report (Part 1/1)\n"
                        break
            content = "".join(lines)

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
                timestamp=global_ts,
            ),
        )

        # Write JSON sidecar if enabled (agent-first: also for plan_only)
        # JSON must be written when json_sidecar is active - no conditions like "and not plan_only"
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
            # Generate JSON filename: use first MD file for name, or fallback to deterministic name
            if out_paths:
                json_path = out_paths[0].with_suffix('.json')
            else:
                # Fallback: generate JSON even if no MD files (shouldn't happen, but be defensive)
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
                        timestamp=global_ts,
                ).with_suffix('.json')

            json_data["artifacts"]["index_json"] = str(json_path)
            md_parts = [p for p in out_paths if p.suffix.lower() == ".md"]
            json_data["artifacts"]["md_parts"] = [str(p) for p in md_parts]
            json_data["artifacts"]["canonical_md"] = str(md_parts[0]) if md_parts else None
            _validate_agent_json_dict(json_data)
            json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
            out_paths.append(json_path)

    else:
        for s in repo_summaries:
            s_name = s["name"]
            s_files = s["files"]
            s_root = s["root"]

            # Generate per-repo run_id for deterministic naming
            repo_run_id = _generate_run_id(
                [s_name], detail, path_filter, ext_filter_str,
                plan_only=plan_only, code_only=code_only, timestamp=global_ts
            )

            # Fix: Explicitly capture loop variables (s_name, repo_run_id) as default args
            # to avoid lazy binding issues in the lambda.
            process_and_write(
                s_files,
                [s_root],
                lambda part_suffix="", _name=s_name, _rid=repo_run_id: make_output_filename(
                    merges_dir,
                    [_name],
                    detail,
                    part_suffix,
                    path_filter,
                    ext_filter_str,
                    _rid,
                    plan_only=plan_only,
                    code_only=code_only,
                    timestamp=global_ts,
                ),
            )

            # Write JSON sidecar if enabled (agent-first: also for plan_only)
            # JSON must be written when json_sidecar is active - no conditions like "and not plan_only"
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
                # Generate JSON filename: use last MD file for name, or fallback to deterministic name
                if out_paths:
                    json_path = out_paths[-1].with_suffix('.json')
                else:
                    # Fallback: generate JSON even if no MD files (shouldn't happen, but be defensive)
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
                        timestamp=global_ts,
                    ).with_suffix('.json')

                json_data["artifacts"]["index_json"] = str(json_path)
                md_parts = [p for p in out_paths if p.suffix.lower() == ".md"]
                # for per-repo mode, md_parts typically ends with this repo's report; we still record all md parts.
                json_data["artifacts"]["md_parts"] = [str(p) for p in md_parts]
                json_data["artifacts"]["canonical_md"] = (
                    str(out_paths[-1]) if out_paths[-1].suffix.lower() == ".md" else (str(md_parts[-1]) if md_parts else None)
                )
                _validate_agent_json_dict(json_data)
                json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
                out_paths.append(json_path)

    # --- Post-check & deterministic ordering (primary artifact first) ---
    md_paths = [p for p in out_paths if p.suffix.lower() == ".md"]
    json_paths = [p for p in out_paths if p.suffix.lower() == ".json"]
    other_paths = [p for p in out_paths if p.suffix.lower() not in (".md", ".json")]

    # Verify that reported .md outputs really exist and are non-empty.
    # This prevents "generated" messages when the file did not land where expected.
    verified_md: List[Path] = []
    for p in md_paths:
        try:
            if p.exists() and p.is_file() and p.stat().st_size > 0:
                verified_md.append(p)
        except Exception:
            # treat as missing
            pass

    if md_paths and not verified_md:
        # We *expected* at least one markdown output, but none is actually usable.
        # Make this a hard error so callers don't display a success message.
        raise RuntimeError(
            "repoLens: Report was announced as written, but no non-empty .md output exists on disk. "
            "Check merges_dir / permissions / rename logic."
        )

    # If json_sidecar is enabled, JSON is the primary artifact: verify it exists & is non-empty.
    verified_json: List[Path] = []
    if extras and extras.json_sidecar:
        for p in json_paths:
            try:
                if p.exists() and p.is_file() and p.stat().st_size > 0:
                    # sanity: load + minimal validate
                    d = json.loads(p.read_text(encoding="utf-8"))
                    _validate_agent_json_dict(d)
                    verified_json.append(p)
            except Exception:
                pass
        if json_paths and not verified_json:
            raise RuntimeError(
                "repoLens: JSON primary artifact was announced as written, but no valid non-empty .json exists on disk."
            )

    # Primary ordering: JSON (if enabled) first, then Markdown, then other artifacts.
    # Return structured MergeArtifacts object instead of flat list
    if extras and extras.json_sidecar:
        # JSON is primary when json_sidecar is enabled
        return MergeArtifacts(
            index_json=verified_json[0] if verified_json else None,
            canonical_md=verified_md[0] if verified_md else None,
            md_parts=verified_md,
            other=other_paths
        )
    else:
        # Markdown is primary when json_sidecar is disabled
        return MergeArtifacts(
            index_json=None,
            canonical_md=verified_md[0] if verified_md else None,
            md_parts=verified_md,
            other=other_paths
        )


# --- Review Bundle Renderer (v2.4 Extension) ---

REVIEW_BLOCKLIST = {
    ".env",
    "id_rsa",
    "id_dsa",
    "id_ed25519",
    "id_ecdsa",
    "secrets.yaml",
    "secrets.yml",
    "secrets.json",
    "tokens.json",
    "tokens.yaml",
}

REVIEW_BLOCKLIST_PATTERNS = [
    re.compile(r".*\.key$"),
    re.compile(r".*\.pem$"),
    re.compile(r".*\.p12$"),
    re.compile(r".*\.pfx$"),
    re.compile(r".*\.ovpn$"),
    re.compile(r"id_rsa.*"),
]

def is_blocked_file(filename: str) -> bool:
    if filename in REVIEW_BLOCKLIST:
        return True
    for p in REVIEW_BLOCKLIST_PATTERNS:
        if p.match(filename):
            return True
    return False

def render_review_bundle(
    source_dir: Path,
    output_dir: Path,
    delta: Dict[str, Any],
    base_dir: Optional[Path] = None
) -> None:
    """
    Generates a full AI-ready review bundle.

    Structure:
      bundle/
        review.md
        delta.json
        bundle.json
        evidence/
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(exist_ok=True)

    # 1. Write delta.json
    delta_path = output_dir / "delta.json"
    delta_path.write_text(json.dumps(delta, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Write review.md
    review_lines = []

    # Header
    review_lines.append("# PR Review")
    review_lines.append("")

    # Summary
    summary = delta.get("summary", {})
    review_lines.append("## Summary")
    review_lines.append(f"- added: {summary.get('added', 0)}")
    review_lines.append(f"- changed: {summary.get('changed', 0)}")
    review_lines.append(f"- removed: {summary.get('removed', 0)}")

    # Hotspots (simple heuristic based on categories in delta)
    hotspots = set()
    for f in delta.get("files", []):
        path = f.get("path", "")
        # Hotspots: path-based only (Fix 4)
        if "contracts/" in path:
            hotspots.add("contracts/")
        if "schemas/" in path:
            hotspots.add("schemas/")
        if ".github/" in path:
            hotspots.add(".github/")

    if hotspots:
        review_lines.append(f"- hotspots: {', '.join(sorted(hotspots))}")

    review_lines.append("")
    review_lines.append("---")
    review_lines.append("")

    # Files
    files = delta.get("files", [])

    for f in files:
        path = f.get("path")
        status = f.get("status")
        category = f.get("category")
        size = f.get("size_bytes", 0)

        review_lines.append(f"## File: {path}")
        review_lines.append(f"status: {status}")
        review_lines.append(f"category: {category}")
        review_lines.append(f"size_bytes: {size}")
        review_lines.append("")

        # Determine if we show content
        if status == "removed":
            review_lines.append("(removed)")
            review_lines.append("")
            review_lines.append("---")
            review_lines.append("")
            continue

        # Security Check
        filename = Path(path).name
        if is_blocked_file(filename):
            review_lines.append("```markdown")
            review_lines.append("[REDACTED: security rule]")
            review_lines.append("```")
            review_lines.append("")
            review_lines.append("---")
            review_lines.append("")
            continue

        # Size Check (200KB)
        if size > 200 * 1024:
            review_lines.append("```markdown")
            review_lines.append(f"[OMITTED: file size {human_size(size)} > 200KB]")
            review_lines.append("```")
            review_lines.append("")
            review_lines.append("---")
            review_lines.append("")
            continue

        # Read Content
        src_file = source_dir / path
        content = ""
        try:
            if src_file.exists():
                # Check for binary
                if is_probably_text(src_file, size):
                    content = src_file.read_text(encoding="utf-8", errors="replace")
                else:
                    content = "[BINARY CONTENT]"
            else:
                content = "[FILE NOT FOUND]"
        except Exception as e:
            content = f"[ERROR READING FILE: {e}]"

        # Optional BEFORE context for changed files
        before_content = None
        if status == "changed" and base_dir:
            base_file = base_dir / path
            try:
                if base_file.exists():
                     if is_probably_text(base_file, base_file.stat().st_size):
                         before_content = base_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        # Render Content (Fix 2: No nested fences & dynamic length)
        # We need to scan content for backticks to ensure the fence is long enough.
        # This is critical for robustness.

        # Calculate fence length for content
        max_ticks = 0
        if "```" in content:
            ticks = re.findall(r"`{3,}", content)
            if ticks:
                max_ticks = max(len(t) for t in ticks)
        fence_len = max(3, max_ticks + 1)
        fence = "`" * fence_len

        # Calculate fence length for before_content (if present)
        before_fence = "```"
        if before_content is not None:
            max_ticks_before = 0
            if "```" in before_content:
                ticks_b = re.findall(r"`{3,}", before_content)
                if ticks_b:
                    max_ticks_before = max(len(t) for t in ticks_b)
            before_fence_len = max(3, max_ticks_before + 1)
            before_fence = "`" * before_fence_len

        if before_content is not None:
             review_lines.append("### BEFORE")
             review_lines.append(f"{before_fence}text")
             review_lines.append(before_content)
             review_lines.append(f"{before_fence}")
             review_lines.append("")
             review_lines.append("AFTER")
             review_lines.append("")

        review_lines.append(f"{fence}text")
        review_lines.append(content)
        review_lines.append(f"{fence}")
        review_lines.append("")
        review_lines.append("---")
        review_lines.append("")

    review_path = output_dir / "review.md"
    review_path.write_text("\n".join(review_lines), encoding="utf-8")

    # 3. Write bundle.json
    bundle_meta = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": str(source_dir),
        "base": str(base_dir) if base_dir else None,
        "delta_version": delta.get("version"),
        "files_count": len(files)
    }

    bundle_path = output_dir / "bundle.json"
    bundle_path.write_text(json.dumps(bundle_meta, indent=2), encoding="utf-8")
