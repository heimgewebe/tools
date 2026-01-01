import os
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import fnmatch

logger = logging.getLogger(__name__)

class AtlasScanner:
    def __init__(self, root: Path, max_depth: int = 6, max_entries: int = 200000, exclude_globs: List[str] = None):
        self.root = root
        self.max_depth = max_depth
        self.max_entries = max_entries
        self.exclude_globs = exclude_globs or ["**/.git/**", "**/node_modules/**", "**/.venv/**", "**/__pycache__/**", "**/.cache/**"]
        self.stats = {
            "total_files": 0,
            "total_dirs": 0,
            "total_bytes": 0,
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "extensions": {},
            "top_dirs": [],  # List of {"path": str, "bytes": int}
            "repo_nodes": [], # List of paths that look like git repos
        }
        self.tree = {} # Nested dict structure representing the tree

    def _is_excluded(self, path: Path) -> bool:
        # Check against globs
        # We match relative path from root
        try:
            rel_path = path.relative_to(self.root)
        except ValueError:
            return True # Should not happen if walking from root

        str_path = str(rel_path)
        for glob in self.exclude_globs:
            if fnmatch.fnmatch(str_path, glob):
                return True
        return False

    def scan(self) -> Dict[str, Any]:
        self.stats["start_time"] = datetime.utcnow().isoformat()
        start_ts = time.time()

        # Iterative walk to handle depth and limits better than os.walk recursion might in some cases,
        # but os.walk is efficient. We'll use os.walk with manual depth check.

        # We need to build a tree and stats.
        # To avoid massive memory usage for "tree", we might simplify it.
        # The user wants "Kartografieren: Verzeichnisbaum + Kennzahlen".
        # Let's build a simplified tree: only directories, with file counts/sizes in them?
        # Or a full tree? With 200k entries, a full tree dict is manageable in memory (approx 100MB RAM).

        current_entries = 0

        # Use a stack for traversal to control depth and state
        # Stack items: (path: Path, depth: int, parent_node: dict)

        # Root node
        self.tree = {
            "name": self.root.name,
            "path": ".",
            "type": "dir",
            "children": [],
            "stats": {"files": 0, "bytes": 0}
        }

        # For top dirs, we need to aggregate size.
        # Since we traverse depth-first (stack), we can't easily aggregate up without post-processing or recursion.
        # Let's stick to os.walk for simplicity and performance, but we need to map it to our tree.
        # Actually, os.walk is bottom-up if topdown=False. That helps with size aggregation!

        # But we also need to respect exclude globs which prune branches.
        # So topdown=True is better for pruning.

        # Let's do a custom walk.

        dir_sizes = {} # path -> size

        for root, dirs, files in os.walk(self.root, topdown=True):
            current_root = Path(root)

            # Check exclusions for current root (double check)
            if self._is_excluded(current_root):
                dirs[:] = []
                continue

            rel_path = current_root.relative_to(self.root)
            depth = len(rel_path.parts) if str(rel_path) != "." else 0

            if depth > self.max_depth:
                dirs[:] = []
                continue

            # Check for .git to mark repo node
            if ".git" in dirs:
                self.stats["repo_nodes"].append(str(rel_path))
                # Don't recurse into .git
                if ".git" in dirs:
                    dirs.remove(".git")

            # Filter dirs in-place
            dirs[:] = [d for d in dirs if not self._is_excluded(current_root / d)]

            # Process files
            dir_bytes = 0

            for f in files:
                f_path = current_root / f
                if self._is_excluded(f_path):
                    continue

                current_entries += 1
                if current_entries > self.max_entries:
                    logger.warning("Max entries limit reached for Atlas scan.")
                    break

                try:
                    stat = f_path.stat()
                    size = stat.st_size
                    ext = f_path.suffix.lower()

                    self.stats["total_files"] += 1
                    self.stats["total_bytes"] += size
                    self.stats["extensions"][ext] = self.stats["extensions"].get(ext, 0) + 1

                    dir_bytes += size

                except OSError:
                    continue

            if current_entries > self.max_entries:
                break

            self.stats["total_dirs"] += 1
            # We store dir_sizes for "hotspots" (only direct file size or recursive? Usually recursive is more useful)
            # Calculating recursive size requires post-processing or bottom-up walk.
            # For now, let's track "direct size" and maybe later we can do recursive if needed.
            # But "Hotspots" usually implies large folders.
            # Let's allow a simple aggregation later if we build the tree.

            dir_sizes[str(rel_path)] = dir_bytes

        # Calculate Duration
        self.stats["end_time"] = datetime.utcnow().isoformat()
        self.stats["duration_seconds"] = time.time() - start_ts

        # Find Top Dirs (by direct size for now, as full recursive calc is expensive without graph)
        # Or better: aggregate sizes now that we have the map.
        # We can sort paths by length desc (deepest first) and propagate sizes up.

        all_paths = sorted(dir_sizes.keys(), key=lambda p: len(Path(p).parts), reverse=True)
        recursive_sizes = dir_sizes.copy()

        for p_str in all_paths:
            if p_str == ".":
                continue
            p = Path(p_str)
            parent = str(p.parent)
            if parent == ".":
                # p.parent of "foo" is ".", but our map keys use "." for root?
                # relative_to root: root is ".".
                # Path("foo").parent is ".". Path(".").parent is ".".
                pass

            if parent in recursive_sizes:
                recursive_sizes[parent] += recursive_sizes[p_str]

        # Now get top 50 dirs
        sorted_dirs = sorted(recursive_sizes.items(), key=lambda x: x[1], reverse=True)
        self.stats["top_dirs"] = [{"path": p, "bytes": s} for p, s in sorted_dirs[:50]]

        return {
            "root": str(self.root),
            "stats": self.stats,
            # We omit the full tree in the return dict if we just want stats/hotspots.
            # But the user asked for "Systemkarte".
            # For "atlas.json", maybe the full tree is too big if 200k files.
            # Let's return a "flat atlas" (list of dirs with stats) or just the stats and hotspots.
            # "Kartografie ... dient als Orientierungs-Atlas".
            # Providing the "Top Dirs" and "Repo Nodes" is a good abstraction.
            # Detailed file list might be too much for the "Atlas" (Abstract) vs "File Browser" (Concrete).
            # Synthese: "Kartografie ist abstrakt". So file list is NOT included. Good.
        }

def render_atlas_md(atlas_data: Dict[str, Any]) -> str:
    stats = atlas_data["stats"]
    root = atlas_data.get("root", "Unknown")

    lines = []
    lines.append(f"# 🗺️ Atlas: {root}")
    lines.append(f"Generated: {stats.get('end_time')} (Duration: {stats.get('duration_seconds'):.2f}s)")
    lines.append("")

    lines.append("## 📊 Overview")
    lines.append(f"- **Total Directories:** {stats.get('total_dirs')}")
    lines.append(f"- **Total Files:** {stats.get('total_files')}")
    lines.append(f"- **Total Size:** {stats.get('total_bytes') / (1024*1024):.2f} MB")
    lines.append("")

    lines.append("## 📁 Top Folders (Hotspots)")
    lines.append("| Path | Size (MB) |")
    lines.append("|---|---|")
    for d in stats.get("top_dirs", [])[:20]:
        mb = d['bytes'] / (1024*1024)
        lines.append(f"| `{d['path']}` | {mb:.2f} |")
    lines.append("")

    lines.append("## 🏷️ File Types")
    lines.append("| Extension | Count |")
    lines.append("|---|---|")
    # Sort extensions by count
    sorted_exts = sorted(stats.get("extensions", {}).items(), key=lambda x: x[1], reverse=True)
    for ext, count in sorted_exts[:20]:
        lines.append(f"| `{ext or '(no ext)'}` | {count} |")
    lines.append("")

    lines.append("## 📍 Git Repositories")
    repos = stats.get("repo_nodes", [])
    if repos:
        for r in sorted(repos):
            lines.append(f"- `{r}`")
    else:
        lines.append("_No git repositories found in scan scope._")

    return "\n".join(lines)
