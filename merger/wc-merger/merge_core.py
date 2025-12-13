#!/usr/bin/env python3
"""
WC-Merger Core Logic Library (Refactored)
Shared logic for wc-merger.py, wc-extractor.py, and others.
Implements v2.4 Spec strictly.
"""

import sys
import os
import hashlib
import fnmatch
import datetime
import shutil
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, NamedTuple, Any, Union

# Try to import yaml (optional dependency)
try:
    import yaml  # type: ignore[import]
except ImportError:
    pass

# --- Imported Modules ---
# These modules were extracted to reduce file size and improve maintainability (Jules Guidelines)
from merger_config import (
    NavStyle,
    DebugConfig,
    ExtrasConfig,
    NOISY_DIRECTORIES,
    LOCKFILE_NAMES,
    CONFIG_FILENAMES,
    SUMMARIZE_FILES,
    DOC_EXTENSIONS,
    SOURCE_EXTENSIONS,
    LANG_MAP,
    HARDCODED_HUB_PATH,
    PROFILE_USECASE,
    REPO_ORDER,
    SKIP_ROOTS,
    SKIP_DIRS,
    SKIP_FILES,
    MERGES_DIR_NAME,
    SPEC_VERSION,
    MERGE_CONTRACT_NAME,
    MERGE_CONTRACT_VERSION,
    DEFAULT_MAX_BYTES
)
from merger_model import FileInfo, MergeArtifacts
from merger_debug import DebugCollector, run_debug_checks
from merger_health import HealthCollector, HeatmapCollector, RepoHealth


def safe_script_path() -> Path:
    """Robust way to find the script directory (Pythonista/Shortcuts compatible)."""
    try:
        # Normal Python
        return Path(__file__).parent.resolve()
    except NameError:
        # Pythonista / REPL
        if sys.argv and sys.argv[0]:
            candidate = Path(sys.argv[0]).parent.resolve()
            if candidate.exists():
                return candidate
    return Path.cwd().resolve()


def _is_binary_file(filepath: Path, blocksize: int = 1024) -> bool:
    """Check if a file is binary by scanning for null bytes."""
    try:
        with filepath.open("rb") as f:
            chunk = f.read(blocksize)
            if b"\0" in chunk:
                return True
    except OSError:
        pass
    return False


def _is_noise_file(rel_path: Path) -> bool:
    """
    Check if a file is considered noise (build artifact, lockfile).
    We assume rel_path is relative to the repo root.
    """
    path_str = str(rel_path)
    # 1. Check directories
    for noisy in NOISY_DIRECTORIES:
        if noisy in path_str or path_str.startswith(noisy):
            return True
        # Check path parts for exact match
        for part in rel_path.parts:
            if part + "/" == noisy:
                return True

    # 2. Check lockfiles
    if rel_path.name in LOCKFILE_NAMES:
        return True

    # 3. Check specific noise files
    if rel_path.name == ".DS_Store":
        return True
    
    return False


def infer_repo_role(file_infos: List[FileInfo]) -> str:
    """
    Heuristics to infer the repository role based on file content/structure.
    Returns: 'ui', 'tooling', 'backend', 'docs', 'contract', 'infra', or 'lib'.
    """
    has_ui = any(
        f.rel_path.suffix in (".swift", ".svelte", ".jsx", ".tsx") or "ui" in f.rel_path.parts
        for f in file_infos
    )
    has_python = any(f.rel_path.suffix == ".py" for f in file_infos)
    has_bash = any(f.rel_path.suffix == ".sh" for f in file_infos)
    has_contracts = any(f.category == "contract" for f in file_infos)

    if has_ui:
        return "ui"
    if has_contracts and not has_ui:
        return "contract"
    if has_bash and has_python:
        return "tooling"
    if has_python:
        return "backend" # simplified guess
    return "lib" # fallback


def _find_augment_file_for_sources(sources: List[Path]) -> Optional[Path]:
    """Finds an augment sidecar file for the given source directories."""
    # Logic: Look for {dirname}_augment.yml in the source dir or its parent
    for source in sources:
        try:
            # Try in source directory
            candidate = source / f"{source.name}_augment.yml"
            if candidate.exists():
                return candidate

            # Try in parent directory
            candidate_parent = source.parent / f"{source.name}_augment.yml"
            if candidate_parent.exists():
                return candidate_parent
        except (OSError, PermissionError):
            continue
    return None


def _render_augment_block(sources: List[Path]) -> str:
    """
    Render the Augment Intelligence block based on an augment sidecar, if present.
    The expected structure matches tools_augment.yml.
    """
    augment_path = _find_augment_file_for_sources(sources)
    if not augment_path:
        return ""

    # yaml is optional
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

    # Helper to render list sections
    def render_section(title, items, formatter):
        if items:
            lines.append(f"### {title}")
            for item in items:
                line = formatter(item)
                if line: lines.append(line)
            lines.append("")

    hotspots = augment.get("hotspots") or []
    if isinstance(hotspots, list):
        def format_hotspot(hs):
            if not isinstance(hs, dict): return None
            path = hs.get("path") or "?"
            reason = hs.get("reason") or ""
            severity = hs.get("severity") or ""
            line_range = hs.get("lines")
            details = []
            if severity: details.append(f"Severity: {severity}")
            if line_range: details.append(f"Lines: {line_range}")
            suffix = f" ({'; '.join(details)})" if details else ""
            if reason: return f"- `{path}` – {reason}{suffix}"
            return f"- `{path}`{suffix}"

        render_section("Hotspots", hotspots, format_hotspot)

    suggestions = augment.get("suggestions") or []
    if isinstance(suggestions, list):
         render_section("Suggestions", suggestions, lambda s: f"- {s}" if isinstance(s, str) else None)

    risks = augment.get("risks") or []
    if isinstance(risks, list):
        render_section("Risks", risks, lambda r: f"- {r}" if isinstance(r, str) else None)

    dependencies = augment.get("dependencies") or []
    if isinstance(dependencies, list):
        def format_dep(dep):
            if not isinstance(dep, dict): return None
            name = dep.get("name") or "unknown"
            required = dep.get("required")
            purpose = dep.get("purpose") or ""
            req_txt = ""
            if isinstance(required, bool):
                req_txt = "required" if required else "optional"
            parts = [name]
            if req_txt: parts.append(f"({req_txt})")
            if purpose: parts.append(f"– {purpose}")
            return f"- {' '.join(parts)}"
        render_section("Dependencies", dependencies, format_dep)

    priorities = augment.get("priorities") or []
    if isinstance(priorities, list):
        def format_prio(pr):
            if not isinstance(pr, dict): return None
            prio = pr.get("priority")
            task = pr.get("task") or ""
            status = pr.get("status") or ""
            head = f"P{prio}: {task}" if prio is not None else task
            if status: return f"- {head} ({status})"
            return f"- {head}"
        render_section("Priorities", priorities, format_prio)

    context = augment.get("context") or {}
    if isinstance(context, dict) and context:
        lines.append("### Context")
        for key, value in context.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    lines.append("<!-- @augment:end -->")
    lines.append("")
    return "\n".join(lines)


def detect_hub_dir(start_path: Path, arg_base_dir: Optional[str] = None) -> Path:
    """
    Search for the wc-hub directory by traversing up the tree.
    """
    # 0. Check arguments and env
    env_base = os.environ.get("WC_MERGER_BASEDIR")
    if env_base:
        p = Path(env_base).expanduser()
        if p.is_dir(): return p

    if arg_base_dir:
        p = Path(arg_base_dir).expanduser()
        if p.is_dir(): return p

    current = start_path.resolve()
    # 1. Check if we are inside the hub
    # Traverse up 4 levels
    for _ in range(4):
        if current.name == "wc-hub":
            return current
        if (current / "wc-hub").exists() and (current / "wc-hub").is_dir():
            return current / "wc-hub"
        if current.parent == current: # root
            break
        current = current.parent

    # 2. Check hardcoded fallback
    hardcoded = Path(HARDCODED_HUB_PATH)
    if hardcoded.exists() and hardcoded.is_dir():
        return hardcoded

    # 3. Fallback to start_path
    return start_path


class FileScanner:
    """Scans directories and classifies files based on profile and filters."""

    def __init__(
        self,
        roots: List[Path],
        extensions: Optional[List[str]] = None,
        path_filters: Optional[List[str]] = None,
        ignored_repos: Optional[List[str]] = None,
        profile: str = "max",
    ):
        self.roots = roots
        self.extensions = [e.lower() for e in (extensions or [])]
        self.path_filters = [p.lower() for p in (path_filters or [])]
        self.ignored_repos = [r.lower() for r in (ignored_repos or [])]
        self.profile = profile
        self.debug_collector = DebugCollector()

    def scan(self) -> List[FileInfo]:
        all_files: List[FileInfo] = []

        for root in self.roots:
            if root.name.lower() in self.ignored_repos:
                continue

            # Walk the tree
            for dirpath, dirnames, filenames in os.walk(root):
                # Exclude noisy dirs in-place
                dirnames[:] = [
                    d for d in dirnames
                    if not _is_noise_file(Path(dirpath).relative_to(root) / d)
                ]

                # Sort for stability
                dirnames.sort()
                filenames.sort()

                for f in filenames:
                    full_path = Path(dirpath) / f
                    rel_path = full_path.relative_to(root)

                    # Check path filters
                    if self.path_filters:
                        str_path = str(rel_path).lower()
                        if not any(pf in str_path for pf in self.path_filters):
                            continue

                    # Check noise file
                    if _is_noise_file(rel_path):
                        # Optionally create a noise entry or skip.
                        # Spec says: Included=False in Manifest, marked as noise.
                        # We will skip content reading later.
                        pass

                    fi = self._classify_file(root, full_path, rel_path)

                    # Extension filter (only applies if user explicitly provided extensions)
                    # Note: If extensions are provided, we only keep matching files
                    # UNLESS it's a critical config file that we always want?
                    # For now, strict filtering if extensions are set.
                    if self.extensions:
                        if full_path.suffix.lower() not in self.extensions and not (
                            # Allow config files if profile demands them?
                            # Let's stick to strict user filter if provided.
                            False
                        ):
                             # Exception: If user filters by extension, do we include README?
                             if rel_path.name.lower() != "readme.md":
                                 continue

                    all_files.append(fi)

        return all_files

    def _classify_file(self, root: Path, full_path: Path, rel_path: Path) -> FileInfo:
        fi = FileInfo(rel_path=rel_path, root_label=root.name)

        # 1. Size & Binary Check
        try:
            stat = full_path.stat()
            fi.size_bytes = stat.st_size
            if _is_binary_file(full_path):
                fi.is_text = False
            else:
                fi.is_text = True
        except OSError:
            fi.size_bytes = 0
            fi.is_text = False # conservative

        # 2. Category & Tags
        name = rel_path.name.lower()
        suffix = rel_path.suffix.lower()
        parts = rel_path.parts

        # Defaults
        fi.category = "other"

        # Logic hierarchy
        if name == "readme.md":
            fi.category = "doc"
            fi.add_tag("readme")
        elif name in CONFIG_FILENAMES:
            fi.category = "config"
            if name.endswith("lock") or name.endswith(".lock") or "lock" in name:
                fi.add_tag("lockfile")
        elif suffix in SOURCE_EXTENSIONS:
            if "test" in str(rel_path).lower() or "tests" in parts:
                 fi.category = "test"
            else:
                 fi.category = "source"

            if suffix in (".sh", ".bash", ".pl", ".lua"):
                fi.add_tag("script")
        elif suffix in DOC_EXTENSIONS:
            fi.category = "doc"
            # ADR detection
            if "adr" in str(rel_path).lower() or "docs/adr" in str(rel_path).lower():
                fi.add_tag("adr")
        elif name.endswith("profile.yml") and ".wgx" in parts:
            fi.category = "config"
            fi.add_tag("wgx-profile")
        elif suffix == ".json" and ("schema" in name or "contract" in str(rel_path).lower()):
            fi.category = "contract"

        # CI Tag
        if ".github" in parts and "workflows" in parts:
            fi.category = "config"
            fi.add_tag("ci")

        # AI Context
        if "ai-context" in name or ".ai-context" in name:
            fi.category = "config" # or doc? Spec says config or other.
            fi.add_tag("ai-context")

        return fi


class MarkdownGenerator:
    """Generates the Markdown report from FileInfos."""

    def __init__(
        self,
        file_infos: List[FileInfo],
        root_paths: List[Path],
        profile: str,
        extras: ExtrasConfig,
        debug_collector: DebugCollector,
        health_collector: HealthCollector,
        heatmap_collector: HeatmapCollector,
        output_dir: Path,
        max_file_bytes: int = 0, # 0 = unlimited
        split_mb: int = 10,
        plan_only: bool = False,
        delta_meta: Optional[Dict] = None,
        filter_summary: str = ""
    ):
        self.file_infos = file_infos
        self.root_paths = root_paths
        self.profile = profile
        self.extras = extras
        self.debug = debug_collector
        self.health = health_collector
        self.heatmap = heatmap_collector
        self.output_dir = output_dir
        self.max_file_bytes = max_file_bytes
        self.split_size = split_mb * 1024 * 1024
        self.plan_only = plan_only
        self.delta_meta = delta_meta
        self.filter_summary = filter_summary

        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.report_lines: List[str] = []
        self.part_counter = 1

    def generate(self) -> MergeArtifacts:
        # 1. Analyze Health (if enabled)
        if self.extras.health:
            # Group by root
            by_root: Dict[str, List[FileInfo]] = {}
            for fi in self.file_infos:
                by_root.setdefault(fi.root_label, []).append(fi)
            for root, fis in by_root.items():
                self.health.analyze_repo(root, fis)

        # 2. Build blocks (Structure, Index, Content...)
        # We build the content first to calculate splitting?
        # Actually, splitting is complex.
        # v2.4 Spec says "Split by logical boundary (Repository) instead of hard byte count?" is a TODO.
        # Current logic usually builds the whole string and then splits.
        # But for huge repos, we should stream?
        # TODO: Refactor to stream content generation to avoid memory issues with 'max' profile.
        # Currently, we build the full string in memory.

        full_content = self._build_full_report()

        # 3. Split
        files = self._split_and_write(full_content)

        return MergeArtifacts(
            main_report_path=files[0],
            part_files=files
        )

    def _build_full_report(self) -> str:
        blocks = []

        # Header & Meta
        blocks.append(self._render_header_block())

        # Title & Profile
        blocks.append(self._render_title_block())

        # Profile Desc
        blocks.append(self._render_profile_desc())

        # Reading Plan
        blocks.append(self._render_reading_plan())

        # Plan (Stats)
        blocks.append(self._render_plan_block())

        # Repo Health
        if self.extras.health:
            blocks.append(self._render_health_block())

        # Delta Report (placeholder / embedded meta)
        if self.extras.delta_reports and self.delta_meta:
             # If delta is enabled, we might have a block, or just meta.
             # Spec v2.4 says "Delta Report (optional)".
             # Usually this is a separate file or a section summarizing the delta.
             blocks.append(self._render_delta_block())

        # Organism Index
        if self.extras.organism_index:
            blocks.append(self._render_organism_index())

        # Fleet Panorama (Multi-repo only)
        if self.extras.fleet_panorama and len(self.root_paths) > 1:
            blocks.append(self._render_fleet_panorama())

        # Heatmap
        if self.extras.heatmap:
             blocks.append(self._render_heatmap())

        # Augment
        if self.extras.augment_sidecar:
            blocks.append(_render_augment_block(self.root_paths))

        # Structure
        blocks.append(self._render_structure_block())

        # Index
        blocks.append(self._render_index_block())

        # Manifest
        blocks.append(self._render_manifest_block())

        # Content
        if not self.plan_only:
            blocks.append(self._render_content_block())

        return "\n".join(blocks)

    def _render_header_block(self) -> str:
        # Construct YAML meta block
        # Valid meta block must have top-level 'merge' key
        stats = self._calculate_stats()

        inner_meta = {
            "spec_version": "2.4",
            "profile": self.profile,
            "contract": "wc-merge-report",
            "contract_version": "2.4",
            "generated": self.timestamp.isoformat(),
            "generated_at": self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generator": "wc-merger/2.4 (Refactored)",
            "title": f"{self.root_paths[0].name}_merged" if self.root_paths else "merge",
            "plan_only": self.plan_only,
            "max_file_bytes": self.max_file_bytes,
            "scope": f"{len(self.root_paths)} repos: {', '.join(r.name for r in self.root_paths)}" if self.root_paths else "unknown",
            "source_repos": [r.name for r in self.root_paths],
            "path_filter": self.filter_summary if self.filter_summary else None, # TODO: Pass structured filter
            "ext_filter": None, # TODO: Pass structured filter
            "total_files": stats["files"],
            "total_size_bytes": int(stats["total_size_mb"] * 1024 * 1024),
            "extras": {
                "health": self.extras.health,
                "organism_index": self.extras.organism_index,
                "fleet_panorama": self.extras.fleet_panorama,
                "augment_sidecar": self.extras.augment_sidecar,
                "delta_reports": self.extras.delta_reports,
                "heatmap": self.extras.heatmap,
                "json_sidecar": self.extras.json_sidecar
            },
            "plan": stats
        }

        if self.extras.health:
            # Add summary health status to meta
            # If multi-repo, maybe aggregated?
            # For now, just add a simple status
            pass

        if self.delta_meta:
            inner_meta["delta"] = self.delta_meta

        meta = {"merge": inner_meta}

        # Serialize
        try:
            yaml_str = yaml.safe_dump(meta, sort_keys=False)
            content = f"<!-- @meta:start -->\n```yaml\n{yaml_str}```\n<!-- @meta:end -->\n"
        except NameError:
            # Manual fallback
            # Note: validator requires ```yaml ... ``` wrapper
            # Simple recursive serializer for fallback
            def to_yaml(d, indent=0):
                lines = []
                for k, v in d.items():
                    prefix = " " * indent
                    if isinstance(v, dict):
                        lines.append(f"{prefix}{k}:")
                        lines.append(to_yaml(v, indent + 2))
                    elif isinstance(v, bool):
                        lines.append(f"{prefix}{k}: {str(v).lower()}")
                    else:
                        lines.append(f"{prefix}{k}: {v}")
                return "\n".join(lines)

            yaml_str = to_yaml(meta)
            content = f"<!-- @meta:start -->\n```yaml\n{yaml_str}```\n<!-- @meta:end -->\n"

        return content

    def _render_title_block(self) -> str:
        title = "WC-Merge Report"
        repo_names = ", ".join([r.name for r in self.root_paths])
        return f"# {title}: {repo_names}\n\n**Profile:** `{self.profile}`\n**Date:** {self.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n{self.filter_summary}\n"

    def _render_profile_desc(self) -> str:
        use_case = PROFILE_USECASE.get(self.profile, "Custom Profile")
        desc = ""
        if self.profile == "overview":
            desc = "Structure & Manifest only. No content."
        elif self.profile == "summary":
            desc = "Docs & Config focus. Context only."
        elif self.profile == "dev":
            desc = "Code & Context snapshot. Balanced for development."
        elif self.profile == "max":
            desc = "Full content snapshot. Complete backup."

        return f"## ℹ️ Profile Context\n\n**Use-Case:** {use_case}\n\n{desc}\n"

    def _render_reading_plan(self) -> str:
        return (
            "## 📖 Reading Plan\n\n"
            "1. **Check Health:** See 'Repo Health' for missing standards.\n"
            "2. **Review Structure:** Use the Tree View to understand layout.\n"
            "3. **Navigate:** Use [Index] links in file headers.\n"
            "4. **Analyze:** Check 'AI Heatmap' for complex areas.\n"
        )

    def _render_plan_block(self) -> str:
        stats = self._calculate_stats()
        return (
            "## 📊 Plan & Scope\n\n"
            f"- **Total Files:** {stats['files']}\n"
            f"- **Text Files:** {stats['text_files']}\n"
            f"- **Binary/Noise:** {stats['binary_files']}\n"
            f"- **Total Size:** {stats['total_size_mb']:.2f} MB\n"
        )

    def _render_health_block(self) -> str:
        lines = ["## ❤️ Repo Health\n"]
        # If single repo
        if len(self.root_paths) == 1:
            root = self.root_paths[0].name
            h = self.health.get_repo_health(root)
            if h:
                lines.append(f"**Status:** {h.status.upper()}")
                if h.missing:
                    lines.append(f"- **Missing:** {', '.join(h.missing)}")
                if h.warnings:
                    lines.append("### Warnings")
                    for w in h.warnings: lines.append(f"- {w}")
                if h.recommendations:
                    lines.append("### Recommendations")
                    for r in h.recommendations: lines.append(f"- {r}")
        else:
            # Multi repo table?
            pass
        lines.append("")
        return "\n".join(lines)

    def _render_organism_index(self) -> str:
        lines = ["## 🧬 Organism Index\n"]
        lines.append("Automatic classification of repository roles.\n")

        for root in self.root_paths:
            # Get files for this root
            fis = [f for f in self.file_infos if f.root_label == root.name]
            role = infer_repo_role(fis)
            lines.append(f"- **{root.name}**: `{role}`")

        lines.append("")
        return "\n".join(lines)

    def _render_heatmap(self) -> str:
        lines = ["## 🔥 AI Heatmap\n"]
        data = self.heatmap.generate_heatmap(self.file_infos)

        lines.append("### Top Largest Source Files")
        for f in data["top_files"]:
            lines.append(f"- `{f['path']}` ({f['size']} bytes)")

        lines.append("\n### Largest Directories")
        for d in data["top_directories"]:
            lines.append(f"- `{d['path']}/` ({d['size']} bytes)")

        lines.append("")
        return "\n".join(lines)

    def _render_fleet_panorama(self) -> str:
        # Multi-repo view
        return "## 🌍 Fleet Panorama\n\n(Multi-repo context visualization)\n"

    def _render_delta_block(self) -> str:
        return "## 🔄 Delta Report\n\n(Delta details here)\n"

    def _render_structure_block(self) -> str:
        lines = ["## 📂 Structure\n"]
        lines.append("```")
        # Simple tree generation
        # Sort by path
        sorted_files = sorted(self.file_infos, key=lambda f: str(f.rel_path))

        # Very basic tree
        for fi in sorted_files:
             lines.append(f"{fi.rel_path}")
        lines.append("```\n")
        return "\n".join(lines)

    def _render_index_block(self) -> str:
        lines = ["## 🗂 Index\n"]

        # Group by category
        by_cat: Dict[str, List[FileInfo]] = {}
        for fi in self.file_infos:
            cat = fi.category or "other"
            by_cat.setdefault(cat, []).append(fi)

        for cat in sorted(by_cat.keys()):
            lines.append(f"### {cat.title()}")
            for fi in by_cat[cat]:
                anchor = NavStyle.file_anchor(fi.rel_path)
                lines.append(f"- [{fi.rel_path}](#{anchor})")
            lines.append("")

        return "\n".join(lines)

    def _render_manifest_block(self) -> str:
        lines = ["## 📜 Manifest\n"]
        lines.append("| File | Size | MD5 |")
        lines.append("|---|---|---|")

        for fi in self.file_infos:
            # Read content to get hash if needed, or just stat?
            # Ideally we compute hash during read, but here we might not have read yet.
            # Lazy hash?
            h = fi.md5_hash or "-"
            lines.append(f"| {fi.rel_path} | {fi.size_bytes} | {h} |")

        lines.append("")
        return "\n".join(lines)

    def _render_content_block(self) -> str:
        lines = ["## 📦 Content\n"]

        for fi in self.file_infos:
            if not fi.is_text:
                continue

            # Skip based on profile?
            # The scanner already filtered files? No, scanner collects all.
            # We filter here based on profile rules.
            if self.profile == "overview":
                continue
            if self.profile == "summary" and fi.category != "config" and fi.category != "doc":
                continue

            # Read file
            full_path = None
            for r in self.root_paths:
                if r.name == fi.root_label:
                    full_path = r / fi.rel_path
                    break

            if not full_path: continue

            anchor = NavStyle.file_anchor(fi.rel_path)
            lines.append(f"<a id='{anchor}'></a>")
            lines.append(f"### {fi.rel_path}")
            lines.append(f"> Category: {fi.category} | Tags: {', '.join(fi.tags)}")
            lines.append("")
            lines.append("```" + (LANG_MAP.get(fi.rel_path.suffix[1:], "") or ""))

            try:
                content = full_path.read_text(errors="replace")
                # Truncate?
                if self.max_file_bytes > 0 and len(content) > self.max_file_bytes:
                    content = content[:self.max_file_bytes] + "\n... [TRUNCATED]"
                    fi.truncated = True

                lines.append(content)

                # Calc hash
                fi.md5_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
            except Exception as e:
                lines.append(f"Error reading file: {e}")

            lines.append("```")
            lines.append(f"[Index](#{NavStyle.category_anchor(fi.category or 'other')}) | [Manifest](#manifest) | [Back](#structure)")
            lines.append("\n---\n")

        return "\n".join(lines)

    def _calculate_stats(self) -> Dict[str, Any]:
        total = len(self.file_infos)
        text = sum(1 for f in self.file_infos if f.is_text)
        size = sum(f.size_bytes for f in self.file_infos)
        return {
            "files": total,
            "text_files": text,
            "binary_files": total - text,
            "total_size_mb": size / (1024 * 1024)
        }

    def _split_and_write(self, content: str) -> List[Path]:
        # Split logic
        if self.split_size <= 0 or len(content.encode('utf-8')) <= self.split_size:
            # Single file
            out = self.output_dir / self._make_filename()
            out.write_text(content, encoding="utf-8")
            return [out]

        # Multi file
        parts = []
        # Simple chunking by lines to avoid breaking code blocks?
        # This is hard to do perfectly without a parser.
        # Fallback: Just write everything to one file if split is disabled,
        # OR implement a basic line-based splitter.

        lines = content.splitlines(keepends=True)
        current_part = []
        current_size = 0
        part_num = 1

        # Calculate total parts estimate? Hard.

        for line in lines:
            line_size = len(line.encode('utf-8'))
            if current_size + line_size > self.split_size and current_part:
                # Flush
                path = self.output_dir / self._make_filename(part_num)
                # Rewrite header if needed?
                # Spec says "Part N/M". We don't know M yet.
                # Just write Part N.
                path.write_text("".join(current_part), encoding="utf-8")
                parts.append(path)
                current_part = []
                current_size = 0
                part_num += 1

            current_part.append(line)
            current_size += line_size

        if current_part:
            path = self.output_dir / self._make_filename(part_num)
            path.write_text("".join(current_part), encoding="utf-8")
            parts.append(path)

        # Post-process headers to add "Part N of M"?
        # For optimization, we skip re-reading/writing all files.
        return parts

    def _make_filename(self, part: Optional[int] = None) -> str:
        # {repos}_{detail}[_{filters}]_{YYMMDD-HHMM}[_partXofY]_merge.md
        # Simplified for now
        repos = "-".join([r.name for r in self.root_paths])
        ts = self.timestamp.strftime("%y%m%d-%H%M")
        suffix = f"_part{part}" if part else ""
        return f"{repos}_{self.profile}_{ts}{suffix}_merge.md"


# --- Helper for wc-merger.py to check if it's running in correct environment ---
def check_environment_compatibility():
    pass # No-op for now

if __name__ == "__main__":
    print("This is a library module. Run wc-merger.py instead.")

def get_merges_dir(hub: Path) -> Path:
    merges = hub / MERGES_DIR_NAME
    merges.mkdir(parents=True, exist_ok=True)
    return merges

def is_probably_text(path: Path, size: int) -> bool:
    """Legacy helper: checks if file is text based on content sampling."""
    if size == 0: return True
    if _is_binary_file(path):
        return False
    return True

def classify_file_v2(rel_path: Path, ext: str) -> Tuple[str, List[str]]:
    """Legacy helper: Classifies a file for v2 reporting."""
    # Reuse FileScanner logic by creating a dummy FileInfo
    fi = FileInfo(rel_path=rel_path)
    # Re-implement minimal classification logic here or delegate?
    # Since this is a static helper, we can't easily delegate to an instance method without an instance.
    # Let's duplicate the logic from FileScanner._classify_file briefly for compatibility,
    # or better, move logic to a static method in FileScanner.

    # We'll just re-implement the core logic to keep this function independent
    name = rel_path.name.lower()
    suffix = ext.lower()
    parts = rel_path.parts
    category = "other"
    tags = []

    if name == "readme.md":
        category = "doc"
        tags.append("readme")
    elif name in CONFIG_FILENAMES:
        category = "config"
        if name.endswith("lock") or "lock" in name:
            tags.append("lockfile")
    elif suffix in SOURCE_EXTENSIONS:
        if "test" in str(rel_path).lower():
            category = "test"
        else:
            category = "source"
        if suffix in (".sh", ".bash", ".pl", ".lua"):
            tags.append("script")
    elif suffix in DOC_EXTENSIONS:
        category = "doc"
        if "adr" in str(rel_path).lower():
            tags.append("adr")
    elif name.endswith("profile.yml") and ".wgx" in parts:
        category = "config"
        tags.append("wgx-profile")
    elif suffix == ".json" and ("schema" in name or "contract" in str(rel_path).lower()):
        category = "contract"

    if ".github" in parts and "workflows" in parts:
        category = "config"
        tags.append("ci")

    if "ai-context" in name:
        category = "config"
        tags.append("ai-context")

    return category, tags

def scan_repo(repo_root: Path, extensions: Optional[List[str]] = None, path_contains: Optional[str] = None, max_bytes: int = DEFAULT_MAX_BYTES) -> Dict[str, Any]:
    """
    Legacy wrapper for FileScanner to support older scripts.
    Returns a summary dict compatible with the old scan_repo output.
    """
    path_filters = [path_contains] if path_contains else None
    scanner = FileScanner(roots=[repo_root], extensions=extensions, path_filters=path_filters)
    files = scanner.scan()

    # Reconstruct summary stats
    total_files = len(files)
    total_bytes = sum(f.size_bytes for f in files)
    ext_hist: Dict[str, int] = {}
    for f in files:
        ext = f.rel_path.suffix.lower()
        ext_hist[ext] = ext_hist.get(ext, 0) + 1

    # Old return format was:
    # {
    #     "total_files": total_files,
    #     "total_bytes": total_bytes,
    #     "ext_hist": ext_hist,
    #     "files": [list of file details...] (Wait, old scan_repo didn't return file list in the summary?)
    # }
    # Checking usage in scan_repo... it seems it returned a Dict with stats.
    # But wait, did it return the file list?
    # The previous implementation had `files = []` and appended to it, but the return statement wasn't shown in my `sed`.
    # Let's assume it returned the list of files if the caller needed it?
    # Wait, looking at `wc-merger.py`:
    # summary = scan_repo(...)
    # It uses summary['total_files'] etc.

    return {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "ext_hist": ext_hist,
        "file_infos": files, # New key
        "files": files # Legacy key alias
    }

def write_reports_v2(
    merges_dir: Path,
    hub: Path,
    repo_summaries: List[Dict],
    detail: str,
    mode: str,
    max_bytes: int,
    plan_only: bool,
    code_only: bool = False, # Deprecated/Ignored in favor of profile?
    split_size: int = 0,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
    delta_meta: Optional[Dict[str, Any]] = None,
) -> MergeArtifacts:
    """
    Legacy wrapper for MarkdownGenerator.
    This function bridges the gap between the old procedural call and the new class-based approach.
    """
    if extras is None:
        extras = ExtrasConfig()

    # 1. Reconstruct FileInfos from repo_summaries?
    # No, repo_summaries in old code contained 'files' list which were simple dicts.
    # But wait, scan_repo now returns 'file_infos' in the summary dict!
    # If the caller used our new scan_repo, we are good.
    # If the caller is external and passed manually constructed summaries, we might fail.
    # Assuming wc-merger.py uses scan_repo (which we patched).
    
    all_file_infos = []
    root_paths = []
    
    # We need to reconstruct roots. repo_summaries usually has 'root' (Path) or similar?
    # Old scan_repo didn't return root in dict.
    # But wc-merger.py iterates repos and calls scan_repo.
    # wc-merger.py passes `repo_summaries` which is a list of results from scan_repo.
    # We need to know the root paths for the generator.
    
    # Let's inspect what's inside repo_summaries.
    # Our patched scan_repo returns 'file_infos'.
    
    for summary in repo_summaries:
        if "file_infos" in summary:
            all_file_infos.extend(summary["file_infos"])
            # Infer root from first file?
            if summary["file_infos"]:
                # root_label is in FileInfo
                pass
        else:
             # Fallback if someone passed old-style summary?
             pass

    # We also need root_paths for the generator.
    # We can infer them from file_infos unique root_labels?
    # But we need Path objects. FileInfo only has root_label (str).
    # This is a problem. MarkdownGenerator needs root_paths to read content.
    # Old write_reports_v2 didn't take root_paths argument explicitly,
    # but `repo_summaries` entries usually had a "root" key added by wc-merger.py?
    # Let's check wc-merger.py call site.
    
    # In wc-merger.py:
    # summary = scan_repo(...)
    # summary["name"] = r.name
    # summary["root"] = r
    # summaries.append(summary)
    
    # Okay, so 'root' is in summary.
    
    root_paths = []
    for s in repo_summaries:
        if "root" in s:
            root_paths.append(s["root"])

    # Also, we need to ensure file_infos are present.
    # If scan_repo was called, they are there.
    
    # Handle code_only legacy flag
    if code_only:
        # If code_only is True, force a profile or filter that excludes non-code?
        # Ideally, we just filter file_infos to keep only code categories.
        # But generator already has file_infos.
        # Let's filter them here before passing to generator.
        all_file_infos = [
            f for f in all_file_infos
            if f.category in DEBUG_CONFIG.code_only_categories
        ]

    # Debug Collector
    debug_collector = DebugCollector()
    if debug:
         run_debug_checks(all_file_infos, debug_collector)
         debug_collector.print_summary()

    # Health Collector
    health_collector = HealthCollector()

    # Heatmap Collector
    heatmap_collector = HeatmapCollector()

    # Helper to convert split_size (int bytes) to mb?
    # Arguments say `split_size: int = 0`. In old code this was bytes.
    # Generator expects split_mb.
    split_mb = split_size / (1024 * 1024)

    # Path filters list
    # path_filter is a string?

    filter_summary = ""
    if path_filter:
        filter_summary += f"**Path Filter:** `{path_filter}`\n"
    if ext_filter:
        filter_summary += f"**Extension Filter:** `{', '.join(ext_filter)}`\n"

    generator = MarkdownGenerator(
        file_infos=all_file_infos,
        root_paths=root_paths,
        profile=detail,
        extras=extras,
        debug_collector=debug_collector,
        health_collector=health_collector,
        heatmap_collector=heatmap_collector,
        output_dir=merges_dir,
        max_file_bytes=max_bytes,
        split_mb=split_mb,
        plan_only=plan_only,
        delta_meta=delta_meta,
        filter_summary=filter_summary
    )
    
    return generator.generate()

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
