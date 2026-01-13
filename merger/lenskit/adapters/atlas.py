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
            default_excludes = ["**/.git", "**/.venv"]
        else:
            default_excludes = ["**/.git", "**/node_modules", "**/.venv", "**/__pycache__", "**/.cache"]

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
            "active_excludes": self.exclude_globs,
            "truncated": {
                "max_entries": self.max_entries,
                "hit": False,
                "files_seen": 0,
                "dirs_seen": 0,
                "depth_limit_hit": False,
                "reason": None
            }
        }
        self.tree = {} # Nested dict structure representing the tree

    @staticmethod
    def _build_exclude_patterns(globs: List[str]) -> List[str]:
        patterns = []
        seen = set()
        for glob in globs:
            # Normalize globs
            normalized = str(glob).replace("\\", "/")

            # 1. The original pattern (robust normalization)
            candidates = [normalized]

            # 2. If it DOES NOT end with "/**", add it to match contents recursively
            #    e.g. "**/node_modules" -> also exclude "**/node_modules/**"
            if not normalized.endswith("/**"):
                candidates.append(f"{normalized}/**")

            # 3. If it DOES end with "/**", add the base directory to prune traversal
            #    e.g. "**/node_modules/**" -> also exclude "**/node_modules"
            if normalized.endswith("/**"):
                candidates.append(normalized[:-3])

            # 4. FIX: If it starts with "**/", add the suffix to match root-level directories
            #    fnmatch('node_modules', '**/node_modules') is False.
            #    So we need 'node_modules' as a pattern.
            if normalized.startswith("**/"):
                candidates.append(normalized[3:])

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

    def scan(self, inventory_file: Optional[Path] = None, dirs_inventory_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Scans the directory structure.

        Args:
            inventory_file: Optional path to write a JSONL inventory of all files.
            dirs_inventory_file: Optional path to write a JSONL inventory of all directories.
        """
        self.stats["start_time"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        start_ts = time.time()

        current_entries = 0
        depth_limit_hit = False

        # Prepare inventory writers
        inv_f = None
        dirs_inv_f = None
        try:
            if inventory_file:
                inv_f = inventory_file.open("w", encoding="utf-8")
            if dirs_inventory_file:
                dirs_inv_f = dirs_inventory_file.open("w", encoding="utf-8")
        except OSError as e:
            logger.error(f"Failed to open inventory files: {e}")

        dir_sizes = {} # path -> size

        try:
            for root, dirs, files in os.walk(self.root, topdown=True):
                current_root = Path(root)

                # Check exclusions for current root (prune traversal)
                if self._is_excluded(current_root):
                    dirs[:] = []
                    continue

                rel_path = current_root.relative_to(self.root)
                depth = len(rel_path.parts) if str(rel_path) != "." else 0

                if depth > self.max_depth:
                    dirs[:] = []
                    depth_limit_hit = True
                    continue

                # Check for .git to mark repo node
                if ".git" in dirs:
                    self.stats["repo_nodes"].append(str(rel_path))
                    dirs.remove(".git")

                # Filter dirs in-place (Pruning)
                # We must check if the dir ITSELF is excluded to prune it from walk
                kept_dirs = []
                for d in dirs:
                    d_path = current_root / d
                    # Note: We check exclusion of the CHILD directory here.
                    # This relies on pattern matching relative path from ROOT.
                    if self._is_excluded(d_path):
                        continue
                    kept_dirs.append(d)
                dirs[:] = kept_dirs

                dir_bytes = 0

                # Directory Inventory
                if dirs_inv_f:
                    # Robustness: try-catch stat calls to avoid crashing on permission errors
                    try:
                        st_mtime = current_root.stat().st_mtime
                        mtime_iso = datetime.fromtimestamp(st_mtime, timezone.utc).isoformat().replace('+00:00', 'Z')
                    except OSError:
                        mtime_iso = None

                    entry = {
                        "rel_path": rel_path.as_posix(),
                        "depth": depth,
                        "n_files": len(files),
                        "n_dirs": len(dirs),
                        "mtime": mtime_iso
                    }
                    try:
                        dirs_inv_f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
                    except OSError:
                        pass # Ignore write errors

                self.stats["truncated"]["dirs_seen"] += 1

                for f in files:
                    f_path = current_root / f
                    if self._is_excluded(f_path):
                        continue

                    current_entries += 1
                    self.stats["truncated"]["files_seen"] = current_entries

                    if current_entries > self.max_entries:
                        self.stats["truncated"]["hit"] = True
                        self.stats["truncated"]["reason"] = "max_entries"
                        # Reset files_seen to max_entries to reflect "stop at limit" contract
                        self.stats["truncated"]["files_seen"] = self.max_entries
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
                            inv_f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

                    except OSError:
                        continue

                if self.stats["truncated"]["hit"]:
                    break

                self.stats["total_dirs"] += 1
                dir_sizes[str(rel_path)] = dir_bytes

        finally:
            if inv_f: inv_f.close()
            if dirs_inv_f: dirs_inv_f.close()

        # Update stats
        if depth_limit_hit:
             self.stats["truncated"]["depth_limit_hit"] = True
             if not self.stats["truncated"]["hit"]:
                 self.stats["truncated"]["hit"] = True
                 self.stats["truncated"]["reason"] = "max_depth"

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
                pass

            if parent in recursive_sizes:
                recursive_sizes[parent] += recursive_sizes[p_str]

        sorted_dirs = sorted(recursive_sizes.items(), key=lambda x: x[1], reverse=True)
        self.stats["top_dirs"] = [{"path": p, "bytes": s} for p, s in sorted_dirs[:50]]

        # Add inventory metadata to stats if file was generated
        if inventory_file:
            self.stats["inventory_file"] = str(inventory_file.resolve())
        if dirs_inventory_file:
            self.stats["dirs_inventory_file"] = str(dirs_inventory_file.resolve())

        self.stats["inventory_strict"] = self.inventory_strict

        return {
            "root": str(self.root),
            "stats": self.stats,
        }

    def merge_folder(self, folder_rel_path: str, output_file: Path,
                     recursive: bool = False, max_files: int = 1000, max_bytes: int = 10 * 1024 * 1024) -> Dict[str, Any]:
        """
        Situative Folder Merge: Merges all text files in a specific folder into one file.

        Args:
            folder_rel_path: Relative path to folder to merge.
            output_file: Path to write merged content.
            recursive: Whether to include subdirectories.
            max_files: Safety limit for number of files.
            max_bytes: Safety limit for total merged size.
        """
        target_dir = (self.root / folder_rel_path).resolve()

        try:
            target_dir.relative_to(self.root.resolve())
        except ValueError:
            raise ValueError(f"Target folder {folder_rel_path} is outside of atlas root.")

        if not target_dir.exists() or not target_dir.is_dir():
            raise ValueError(f"Folder not found: {folder_rel_path}")

        files_merged = []
        files_skipped = []
        total_merged_bytes = 0
        file_count = 0

        # Gather candidates
        candidates = []
        if recursive:
            for root, dirs, files in os.walk(target_dir):
                # Apply same excludes? Or raw merge?
                # User said "situative folder merge... roh...".
                # Usually explicit merge implies "I want this folder".
                # But we should probably respect excludes to avoid merging .git etc.

                # Exclude directories from traversal
                # Similar logic to scan() pruning
                current_root = Path(root)
                if self._is_excluded(current_root):
                    dirs[:] = []
                    continue

                kept_dirs = []
                for d in dirs:
                    d_path = current_root / d
                    if not self._is_excluded(d_path):
                        kept_dirs.append(d)
                dirs[:] = kept_dirs

                for f in files:
                    candidates.append(Path(root) / f)
        else:
            for item in target_dir.iterdir():
                if item.is_file():
                    candidates.append(item)

        # Deterministic sort
        # Sort by relative path to target_dir for stability
        candidates.sort(key=lambda p: str(p.relative_to(target_dir)).lower())

        limit_hit_reason = None

        with output_file.open("w", encoding="utf-8") as out:
            out.write(f"# Atlas Folder Merge: {folder_rel_path}\n")
            out.write(f"# Generated: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}\n")
            out.write(f"# Recursive: {recursive}\n\n")

            for f_path in candidates:
                # Check exclusion again for the file path
                if self._is_excluded(f_path):
                    continue

                if file_count >= max_files:
                    limit_hit_reason = "max_files"
                    break

                if total_merged_bytes >= max_bytes:
                    limit_hit_reason = "max_bytes"
                    break

                rel_path = f_path.relative_to(self.root).as_posix()
                try:
                    # Check size BEFORE reading
                    size = f_path.stat().st_size

                    # Hard limit check: if adding this file would definitely exceed max_bytes
                    if total_merged_bytes + size > max_bytes:
                        limit_hit_reason = "max_bytes"
                        break

                    if is_probably_text(f_path, size):
                        out.write(f"===== FILE: {rel_path} =====\n")
                        try:
                            content = f_path.read_text(encoding="utf-8", errors="replace")
                            out.write(content)
                            total_merged_bytes += len(content.encode("utf-8")) # Rough estimate
                        except Exception as e:
                            out.write(f"[Error reading file: {e}]\n")
                        out.write("\n\n")
                        files_merged.append(rel_path)
                        file_count += 1
                    else:
                        files_skipped.append({"path": rel_path, "reason": "binary/non-text"})
                except OSError as e:
                    files_skipped.append({"path": rel_path, "reason": f"fs_error: {e}"})

            if limit_hit_reason:
                out.write(f"\n===== MERGE TRUNCATED: {limit_hit_reason} reached =====\n")

            if files_skipped:
                out.write("\n===== SKIPPED FILES =====\n")
                for item in files_skipped:
                    out.write(f"- {item['path']} ({item['reason']})\n")

        return {
            "merged": files_merged,
            "skipped": files_skipped,
            "output_file": str(output_file),
            "truncated": limit_hit_reason
        }

def render_atlas_md(atlas_data: Dict[str, Any]) -> str:
    stats = atlas_data["stats"]
    root = atlas_data.get("root", "Unknown")

    lines = []
    lines.append(f"# 🗺️ Atlas: {root}")
    lines.append(f"Generated: {stats.get('end_time')} (Duration: {stats.get('duration_seconds'):.2f}s)")
    lines.append("")

    if stats.get("inventory_file"):
        lines.append(f"**Inventory (Files):** `{Path(stats.get('inventory_file')).name}`")
    if stats.get("dirs_inventory_file"):
        lines.append(f"**Inventory (Dirs):** `{Path(stats.get('dirs_inventory_file')).name}`")

    if stats.get("inventory_strict"):
        lines.append("**Mode:** Strict Inventory (minimal excludes).")
    lines.append("")

    # Truncation Warning
    trunc = stats.get("truncated", {})
    if trunc.get("hit"):
        lines.append(f"⚠️ **SCAN TRUNCATED**: {trunc.get('reason')}")
        lines.append(f"  - Files seen: {trunc.get('files_seen')}")
        lines.append(f"  - Limit: {trunc.get('max_entries')}")
        if trunc.get("depth_limit_hit"):
            lines.append("  - Depth limit hit: Yes")
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
