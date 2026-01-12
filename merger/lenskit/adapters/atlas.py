import os
import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import fnmatch

# Attempt to import is_probably_text from core to avoid duplication
try:
    from ..core.merge import is_probably_text
except ImportError:
    # Fallback implementation if core is not accessible
    # Configurable text detection limit (aligned with core's 20MB)
    TEXT_DETECTION_MAX_BYTES = 20 * 1024 * 1024

    def is_probably_text(path: Path, size: int) -> bool:
        TEXT_EXTENSIONS = {
            ".md", ".txt", ".py", ".rs", ".ts", ".js", ".json", ".yml", ".yaml",
            ".sh", ".html", ".css", ".xml", ".csv", ".log", ".lock", ".gitignore",
            ".toml", ".ini", ".conf", ".dockerfile", "dockerfile", ".bat", ".cmd"
        }
        if path.suffix.lower() in TEXT_EXTENSIONS or path.name.lower() in TEXT_EXTENSIONS:
            return True
        if size > TEXT_DETECTION_MAX_BYTES:
            return False
        try:
            with path.open("rb") as f:
                chunk = f.read(4096)
                if not chunk: return True
                return b"\x00" not in chunk
        except OSError:
            return False

logger = logging.getLogger(__name__)

class AtlasScanner:
    def __init__(self, root: Path, max_depth: int = 6, max_entries: int = 200000,
                 exclude_globs: List[str] = None, inventory_strict: bool = False):
        self.root = root
        self.max_depth = max_depth
        self.max_entries = max_entries
        self.inventory_strict = inventory_strict

        if self.inventory_strict:
            # Minimal excludes for strict inventory: only git and venv
            default_excludes = ["**/.git/**", "**/.venv/**"]
        else:
            default_excludes = ["**/.git/**", "**/node_modules/**", "**/.venv/**", "**/__pycache__/**", "**/.cache/**"]

        self.exclude_globs = exclude_globs if exclude_globs is not None else default_excludes
        self._exclude_patterns = self._build_exclude_patterns(self.exclude_globs)
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
            "active_excludes": self.exclude_globs, # Transparency: list active excludes
        }
        self.tree = {} # Nested dict structure representing the tree

    @staticmethod
    def _build_exclude_patterns(globs: List[str]) -> List[str]:
        patterns = []
        seen = set()
        for glob in globs:
            normalized = str(glob).replace("\\", "/")
            candidates = [normalized]
            if normalized.startswith("**/"):
                candidates.append(normalized[3:])
            if normalized.endswith("/**"):
                candidates.append(normalized[:-3])
            if normalized.startswith("**/") and normalized.endswith("/**"):
                candidates.append(normalized[3:-3])
            for candidate in candidates:
                if candidate and candidate not in seen:
                    seen.add(candidate)
                    patterns.append(candidate)
        return patterns

    def _is_excluded(self, path: Path) -> bool:
        # Check against globs
        # We match relative path from root
        try:
            rel_path = path.relative_to(self.root)
        except ValueError:
            return True # Should not happen if walking from root

        str_path = rel_path.as_posix()
        for pattern in self._exclude_patterns:
            if fnmatch.fnmatch(str_path, pattern):
                return True
        return False

    def scan(self, inventory_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Scans the directory structure.

        Args:
            inventory_file: Optional path to write a JSONL inventory of all files.
        """
        self.stats["start_time"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        start_ts = time.time()

        current_entries = 0

        # Prepare inventory writer if needed
        inv_f = None
        if inventory_file:
            try:
                inv_f = inventory_file.open("w", encoding="utf-8")
            except OSError as e:
                logger.error(f"Failed to open inventory file {inventory_file}: {e}")

        # Root node for stats tree
        self.tree = {
            "name": self.root.name,
            "path": ".",
            "type": "dir",
            "children": [],
            "stats": {"files": 0, "bytes": 0}
        }

        dir_sizes = {} # path -> size

        try:
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
                    if ".git" in dirs:
                        dirs.remove(".git")

                # Filter dirs in-place
                dirs[:] = [d for d in dirs if not self._is_excluded(current_root / d)]

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
                        mtime = stat.st_mtime
                        ext = f_path.suffix.lower()
                        is_sym = f_path.is_symlink()

                        self.stats["total_files"] += 1
                        self.stats["total_bytes"] += size
                        self.stats["extensions"][ext] = self.stats["extensions"].get(ext, 0) + 1

                        dir_bytes += size

                        # Inventory Output
                        if inv_f:
                            is_txt = is_probably_text(f_path, size)
                            file_rel = f_path.relative_to(self.root).as_posix()
                            entry = {
                                "rel_path": file_rel,
                                "name": f,
                                "ext": ext,
                                "size_bytes": size,
                                "mtime": datetime.fromtimestamp(mtime, timezone.utc).isoformat().replace('+00:00', 'Z'),
                                "is_text": is_txt,
                                "is_symlink": is_sym
                            }
                            # Unicode-friendly and deterministic JSON
                            inv_f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

                    except OSError:
                        continue

                if current_entries > self.max_entries:
                    break

                self.stats["total_dirs"] += 1
                dir_sizes[str(rel_path)] = dir_bytes
        finally:
            if inv_f:
                inv_f.close()

        # Calculate Duration
        self.stats["end_time"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        self.stats["duration_seconds"] = time.time() - start_ts

        # Find Top Dirs (Hotspots) - simplistic aggregation
        all_paths = sorted(dir_sizes.keys(), key=lambda p: len(Path(p).parts), reverse=True)
        recursive_sizes = dir_sizes.copy()

        for p_str in all_paths:
            if p_str == ".":
                continue
            p = Path(p_str)
            parent = str(p.parent)
            if parent == ".":
                # For path "foo", parent is "."
                # For path ".", parent is "." but we skip "." in loop above
                pass

            if parent in recursive_sizes:
                recursive_sizes[parent] += recursive_sizes[p_str]

        sorted_dirs = sorted(recursive_sizes.items(), key=lambda x: x[1], reverse=True)
        self.stats["top_dirs"] = [{"path": p, "bytes": s} for p, s in sorted_dirs[:50]]

        # Add inventory metadata to stats if file was generated
        if inventory_file:
            # Store full absolute path for robustness, as requested
            self.stats["inventory_file"] = str(inventory_file.resolve())
            self.stats["inventory_strict"] = self.inventory_strict

        return {
            "root": str(self.root),
            "stats": self.stats,
        }

    def merge_folder(self, folder_rel_path: str, output_file: Path) -> Dict[str, Any]:
        """
        Situative Folder Merge: Merges all text files in a specific folder into one file.
        Non-recursive.
        """
        target_dir = (self.root / folder_rel_path).resolve()

        # Security check: ensure target_dir is inside root
        try:
            target_dir.relative_to(self.root.resolve())
        except ValueError:
             raise ValueError(f"Target folder {folder_rel_path} is outside of atlas root.")

        if not target_dir.exists() or not target_dir.is_dir():
            raise ValueError(f"Folder not found: {folder_rel_path}")

        files_merged = []
        files_skipped = []

        # Gather candidates (shallow)
        candidates = []
        for item in target_dir.iterdir():
            if item.is_file():
                candidates.append(item)

        # Deterministic sort
        candidates.sort(key=lambda p: p.name.lower())

        with output_file.open("w", encoding="utf-8") as out:
            out.write(f"# Atlas Folder Merge: {folder_rel_path}\n")
            out.write(f"# Generated: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}\n\n")

            for f_path in candidates:
                rel_path = f_path.relative_to(self.root).as_posix()
                try:
                    size = f_path.stat().st_size
                    if is_probably_text(f_path, size):
                        out.write(f"===== FILE: {rel_path} =====\n")
                        try:
                            content = f_path.read_text(encoding="utf-8", errors="replace")
                            out.write(content)
                        except Exception as e:
                            out.write(f"[Error reading file: {e}]\n")
                        out.write("\n\n")
                        files_merged.append(rel_path)
                    else:
                        files_skipped.append({"path": rel_path, "reason": "binary/non-text"})
                except OSError as e:
                    files_skipped.append({"path": rel_path, "reason": f"fs_error: {e}"})

            if files_skipped:
                out.write("===== SKIPPED FILES =====\n")
                for item in files_skipped:
                    out.write(f"- {item['path']} ({item['reason']})\n")

        return {
            "merged": files_merged,
            "skipped": files_skipped,
            "output_file": str(output_file)
        }

def render_atlas_md(atlas_data: Dict[str, Any]) -> str:
    stats = atlas_data["stats"]
    root = atlas_data.get("root", "Unknown")

    lines = []
    lines.append(f"# 🗺️ Atlas: {root}")
    lines.append(f"Generated: {stats.get('end_time')} (Duration: {stats.get('duration_seconds'):.2f}s)")
    lines.append("")

    if stats.get("inventory_file"):
        lines.append(f"**Inventory:** `{stats.get('inventory_file')}` generated.")
        if stats.get("inventory_strict"):
            lines.append("**Mode:** Strict Inventory (minimal excludes).")
        lines.append("")

    # Transparency on Excludes
    if stats.get("active_excludes"):
        lines.append("**Active Excludes:**")
        for ex in sorted(stats["active_excludes"]):
            lines.append(f"- `{ex}`")
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
