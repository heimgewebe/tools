from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
from merger_model import FileInfo
from merger_config import DebugConfig
from merger_debug import DebugCollector

DEBUG_CONFIG = DebugConfig() # Default instance

@dataclass
class RepoHealth:
    """Stores health status for a single repository."""
    status: str = "ok"  # "ok", "warning", "critical"
    missing: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    unknown_category_ratio: float = 0.0

class HealthCollector:
    """Collects health checks for repositories (Stage 1: Repo Doctor)."""

    def __init__(self) -> None:
        self._repo_health: Dict[str, RepoHealth] = {}

    def analyze_repo(self, root_label: str, files: List[FileInfo]) -> RepoHealth:
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

        # Determine status
        missing = []
        if not has_readme: missing.append("readme")
        if not has_wgx_profile: missing.append("wgx-profile")
        if not has_ci_workflows: missing.append("ci-workflows")
        if not has_contracts: missing.append("contracts")
        if not has_ai_context: missing.append("ai-context")

        status = "ok"
        if not has_readme or not has_wgx_profile:
            status = "warning"

        # If too many unknowns, warn
        if unknown_category_ratio > 0.5:
             status = "warning"
             warnings.append(f"High unknown category ratio: {unknown_category_ratio:.0%}")

        health = RepoHealth(
            status=status,
            missing=missing,
            warnings=warnings,
            recommendations=recommendations,
            unknown_category_ratio=unknown_category_ratio
        )
        self._repo_health[root_label] = health
        return health

    def get_repo_health(self, root_label: str) -> Optional[RepoHealth]:
        return self._repo_health.get(root_label)


class HeatmapCollector:
    """
    Collects metrics for the AI Heatmap (Code Hotspots).
    Identifies largest files, largest directories, and complex modules.
    """
    def __init__(self, top_n: int = 5):
        self.top_n = top_n

    def generate_heatmap(self, file_infos: List[FileInfo]) -> Dict:
        """Generates heatmap data structure."""
        # 1. Top Largest Files (Source only)
        # Filter for source code to avoid skewing by huge lockfiles/json/assets
        source_files = [
            f for f in file_infos
            if f.category in ("source", "test", "config") and f.is_text
        ]

        sorted_by_size = sorted(source_files, key=lambda f: f.size_bytes, reverse=True)
        top_files = []
        for f in sorted_by_size[:self.top_n]:
            top_files.append({
                "path": str(f.rel_path),
                "size": f.size_bytes,
                "category": f.category
            })

        # 2. Largest Directories (by total size)
        dir_sizes: Dict[str, int] = {}
        for f in file_infos:
             # Use parent dir as key.
             # For 'src/utils/helper.py', we might want 'src/utils' or just top-level 'src'.
             # Let's use the full directory path relative to repo root.
             if len(f.rel_path.parts) > 1:
                 parent = str(f.rel_path.parent)
                 dir_sizes[parent] = dir_sizes.get(parent, 0) + f.size_bytes

        sorted_dirs = sorted(dir_sizes.items(), key=lambda item: item[1], reverse=True)
        top_dirs = []
        for d, size in sorted_dirs[:self.top_n]:
            top_dirs.append({
                "path": d,
                "size": size
            })

        return {
            "top_files": top_files,
            "top_directories": top_dirs
        }
