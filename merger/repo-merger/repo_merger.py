#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repo-merger – Repository/Code Merger for AI Context

Text-based repository merger that creates AI-friendly Markdown snapshots.
Focused on code, documentation, and configuration files.

Features:
- Level logic (overview, summary, dev, max)
- Split mechanics for large outputs (Part 1/N, 2/N, ...)
- Meta-blocks in output
- Strict text file processing only
- Heimgewebe-compatible structure

Based on wc-merger core functionality but simplified for general repository use.
"""

from __future__ import annotations

import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

# ========= Configuration =========

ENCODING = "utf-8"
SPEC_VERSION = "1.0"

# Directories to skip
SKIP_DIRS = {
    ".git", ".hg", ".svn",
    "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", "dist", "build", "target",
    ".venv", "venv",
    ".idea", ".vscode", ".DS_Store",
    ".cargo", ".gradle", ".ruff_cache", ".cache",
    ".next", ".svelte-kit",
    "coverage", "htmlcov",
}

# Files to skip
SKIP_FILES = {
    ".DS_Store", "thumbs.db",
}

# Text extensions (code, config, documentation)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".rst", ".py", ".rs", ".ts", ".tsx", ".js", ".jsx",
    ".json", ".jsonl", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".sh", ".bash", ".zsh", ".fish", ".dockerfile", "dockerfile",
    ".svelte", ".css", ".scss", ".html", ".htm", ".xml", ".csv",
    ".lock", ".bats", ".properties", ".gradle", ".groovy", ".kt", ".kts",
    ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rb", ".php", ".pl",
    ".lua", ".sql", ".bat", ".cmd", ".ps1", ".make", "makefile", "justfile",
    ".tf", ".hcl", ".gitignore", ".gitattributes", ".editorconfig", ".cs",
    ".swift", ".adoc",
}

# Level configurations
LEVEL_CONFIG = {
    "overview": {
        "description": "High-level overview with README and main docs",
        "max_files": 10,
        "include_patterns": {"README.md", "readme.md", "README", "LICENSE", "CHANGELOG.md"},
    },
    "summary": {
        "description": "Documentation and configuration",
        "max_files": 50,
        "include_categories": {"doc", "config"},
    },
    "dev": {
        "description": "Source code and tests",
        "max_files": 200,
        "include_categories": {"doc", "config", "source", "test"},
    },
    "max": {
        "description": "Complete repository snapshot",
        "max_files": -1,  # no limit
        "include_categories": {"doc", "config", "source", "test", "other"},
    },
}

# Language mapping for syntax highlighting
LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "tsx": "typescript",
    "jsx": "javascript", "html": "html", "css": "css", "scss": "scss",
    "json": "json", "xml": "xml", "yaml": "yaml", "yml": "yaml",
    "md": "markdown", "rst": "markdown", "sh": "bash", "bash": "bash",
    "sql": "sql", "toml": "toml", "ini": "ini", "cfg": "ini",
    "rs": "rust", "go": "go", "c": "c", "h": "c",
    "cpp": "cpp", "hpp": "cpp", "cc": "cpp", "cxx": "cpp",
    "java": "java", "kt": "kotlin", "swift": "swift",
    "cs": "csharp", "rb": "ruby", "php": "php",
    "svelte": "svelte", "vue": "vue", "txt": "text",
}


# ========= Utils =========

def human_size(n: int) -> str:
    """Convert bytes to human-readable format."""
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024
        i += 1
    return f"{f:.1f} {units[i]}"


def file_md5(path: Path) -> str:
    """Calculate MD5 hash of file."""
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def is_text_file(path: Path) -> bool:
    """Check if file is a text file based on extension."""
    ext = path.suffix.lower()
    name_lower = path.name.lower()
    
    # Check extension
    if ext in TEXT_EXTENSIONS:
        return True
    
    # Check special files without extension (case-insensitive)
    if name_lower in {"dockerfile", "makefile", "justfile"}:
        return True
    
    # Sniff for text content
    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
        if not chunk:
            return True
        if b"\x00" in chunk:
            return False
        # Try decode as UTF-8
        try:
            chunk.decode(ENCODING)
            return True
        except UnicodeDecodeError:
            return False
    except Exception:
        return False


def categorize_file(path: Path) -> str:
    """
    Categorize file into: doc, config, source, test, other
    """
    ext = path.suffix.lower()
    name = path.name.lower()
    
    # Documentation
    if ext in {".md", ".rst", ".txt", ".adoc"}:
        return "doc"
    
    # Configuration
    if ext in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}:
        return "config"
    if name in {"package.json", "pyproject.toml", "cargo.toml", "poetry.lock", "package-lock.json"}:
        return "config"
    
    # Tests
    if "test" in str(path).lower() or name.startswith("test_"):
        return "test"
    
    # Source code
    if ext in {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go",
        ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
        ".java", ".kt", ".swift", ".cs",
        ".rb", ".php", ".svelte", ".vue"
    }:
        return "source"
    
    return "other"


def language_for(path: Path) -> str:
    """Get language identifier for syntax highlighting."""
    ext = path.suffix.lower().lstrip(".")
    return LANG_MAP.get(ext, "")


# ========= File Collection =========

def gather_files(root: Path, level: str) -> List[Tuple[Path, Path]]:
    """
    Gather files based on level configuration.
    Returns list of (absolute_path, relative_path) tuples.
    """
    config = LEVEL_CONFIG.get(level, LEVEL_CONFIG["max"])
    files: List[Tuple[Path, Path]] = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        
        # Filter directories (keep .github as it's often important)
        dirnames[:] = [
            dn for dn in dirnames
            if dn not in SKIP_DIRS and (not dn.startswith(".") or dn == ".github")
        ]
        
        for fn in filenames:
            p = d / fn
            if not p.is_file():
                continue
            if fn in SKIP_FILES:
                continue
            
            # Only include text files
            if not is_text_file(p):
                continue
            
            rel = p.relative_to(root)
            
            # Level-specific filtering
            if level == "overview":
                # Only specific important files (case-insensitive match)
                if fn.lower() not in {p.lower() for p in config["include_patterns"]}:
                    continue
            else:
                # Category-based filtering
                cat = categorize_file(p)
                if "include_categories" in config:
                    if cat not in config["include_categories"]:
                        continue
            
            files.append((p, rel))
    
    # Sort by path
    files.sort(key=lambda t: str(t[1]).lower())
    
    # Apply max_files limit
    max_files = config.get("max_files", -1)
    if max_files > 0 and len(files) > max_files:
        files = files[:max_files]
    
    return files


# ========= Output Generation =========

def write_meta_block(out, root: Path, level: str, total_files: int, total_bytes: int) -> None:
    """Write meta information block."""
    out.write("```yaml\n")
    out.write("merge:\n")
    out.write(f"  tool: repo-merger\n")
    out.write(f"  version: {SPEC_VERSION}\n")
    out.write(f"  created_at: {datetime.now().isoformat(timespec='seconds')}\n")
    out.write(f"  level: {level}\n")
    out.write(f"  root: {root}\n")
    out.write(f"  stats:\n")
    out.write(f"    file_count: {total_files}\n")
    out.write(f"    total_bytes: {total_bytes}\n")
    out.write("```\n\n")


def write_structure(out, root: Path, files: List[Tuple[Path, Path]]) -> None:
    """Write directory structure."""
    out.write("## 📁 Structure\n\n")
    out.write("```tree\n")
    out.write(f"{root.name}/\n")
    
    # Build tree structure
    dirs_seen = set()
    for _, rel_path in files:
        parts = rel_path.parts
        for i in range(len(parts)):
            dir_path = Path(*parts[:i+1])
            if dir_path not in dirs_seen:
                depth = len(parts[:i+1]) - 1
                indent = "  " * depth
                if i < len(parts) - 1:
                    out.write(f"{indent}├── {parts[i]}/\n")
                else:
                    out.write(f"{indent}├── {parts[i]}\n")
                dirs_seen.add(dir_path)
    
    out.write("```\n\n")


def write_manifest(out, files: List[Tuple[Path, Path]]) -> None:
    """Write file manifest."""
    out.write("## 🧾 Manifest\n\n")
    out.write("| Path | Category | Size |\n")
    out.write("|------|----------|------|\n")
    
    for abs_path, rel_path in files:
        try:
            size = abs_path.stat().st_size
        except Exception:
            size = 0
        cat = categorize_file(abs_path)
        out.write(f"| `{rel_path}` | {cat} | {human_size(size)} |\n")
    
    out.write("\n")


def write_content(out, files: List[Tuple[Path, Path]]) -> None:
    """Write file contents."""
    out.write("## 📄 Content\n\n")
    
    for abs_path, rel_path in files:
        lang = language_for(abs_path)
        cat = categorize_file(abs_path)
        
        out.write(f"### {rel_path}\n\n")
        out.write(f"**Category:** {cat}  \n")
        
        # Read file content
        try:
            content = abs_path.read_text(encoding=ENCODING, errors="replace")
        except Exception as e:
            out.write(f"```\n<<Error reading file: {e}>>\n```\n\n")
            continue
        
        # Write content with syntax highlighting
        out.write(f"```{lang}\n")
        out.write(content)
        if not content.endswith("\n"):
            out.write("\n")
        out.write("```\n\n")


def split_output(content: str, max_bytes: int) -> List[str]:
    """Split content into multiple parts if needed."""
    if max_bytes <= 0:
        return [content]
    
    content_bytes = content.encode(ENCODING)
    if len(content_bytes) <= max_bytes:
        return [content]
    
    # Simple line-based splitting
    lines = content.split("\n")
    parts = []
    current_part = []
    current_size = 0
    
    for line in lines:
        line_bytes = len(line.encode(ENCODING)) + 1  # +1 for newline
        if current_size + line_bytes > max_bytes and current_part:
            parts.append("\n".join(current_part))
            current_part = [line]
            current_size = line_bytes
        else:
            current_part.append(line)
            current_size += line_bytes
    
    if current_part:
        parts.append("\n".join(current_part))
    
    return parts


def generate_merge(root: Path, level: str, output_path: Path, split_size: int = 0) -> None:
    """Generate repository merge."""
    # Gather files
    files = gather_files(root, level)
    
    if not files:
        print(f"⚠️  No files found for level '{level}'")
        return
    
    # Calculate stats
    total_bytes = sum(p.stat().st_size for p, _ in files)
    
    # Generate content
    from io import StringIO
    buffer = StringIO()
    
    # Header
    config = LEVEL_CONFIG[level]
    buffer.write(f"# Repo-Merger: {root.name}\n\n")
    buffer.write(f"**Level:** {level} – {config['description']}  \n")
    buffer.write(f"**Files:** {len(files)}  \n")
    buffer.write(f"**Total Size:** {human_size(total_bytes)}  \n\n")
    
    # Meta block
    write_meta_block(buffer, root, level, len(files), total_bytes)
    
    # Structure
    write_structure(buffer, root, files)
    
    # Manifest
    write_manifest(buffer, files)
    
    # Content
    write_content(buffer, files)
    
    content = buffer.getvalue()
    
    # Split if needed
    parts = split_output(content, split_size) if split_size > 0 else [content]
    
    # Write output files
    if len(parts) == 1:
        output_path.write_text(content, encoding=ENCODING)
        print(f"✅ Merge created: {output_path}")
    else:
        stem = output_path.stem
        parent = output_path.parent
        suffix = output_path.suffix
        
        for i, part in enumerate(parts, 1):
            part_path = parent / f"{stem}_part{i}{suffix}"
            
            # Add part header
            part_content = f"# Repo-Merger: {root.name} (Part {i}/{len(parts)})\n\n"
            part_content += part
            
            part_path.write_text(part_content, encoding=ENCODING)
            print(f"✅ Part {i}/{len(parts)} created: {part_path}")


# ========= CLI =========

def parse_args(argv: List[str]) -> Dict[str, Any]:
    """Parse command line arguments."""
    args = {
        "root": None,
        "level": "max",
        "out": None,
        "split_size": 0,
    }
    
    it = iter(argv)
    for token in it:
        if token in ("--root", "-r"):
            args["root"] = next(it, None)
        elif token in ("--level", "-l"):
            args["level"] = next(it, "max")
        elif token in ("--out", "-o"):
            args["out"] = next(it, None)
        elif token == "--split-size":
            try:
                args["split_size"] = int(next(it, "0"))
            except ValueError:
                pass
        elif token in ("--help", "-h"):
            print_help()
            sys.exit(0)
        elif not token.startswith("-") and args["root"] is None:
            args["root"] = token
    
    return args


def print_help() -> None:
    """Print help message."""
    print("""
repo-merger – Repository/Code Merger for AI Context

Usage:
  repo-merger [options] [root]
  
Options:
  --root, -r PATH      Repository root directory (default: current directory)
  --level, -l LEVEL    Merge level: overview, summary, dev, max (default: max)
  --out, -o PATH       Output file path (default: auto-generated)
  --split-size BYTES   Split output into multiple files if larger than BYTES
  --help, -h           Show this help message

Levels:
  overview  - High-level overview with README and main docs
  summary   - Documentation and configuration
  dev       - Source code and tests
  max       - Complete repository snapshot (default)

Examples:
  repo-merger --root . --level max --out merged_repo_max.md
  repo-merger --level dev
  repo-merger . --level overview --out overview.md
""")


def main() -> None:
    """Main entry point."""
    args = parse_args(sys.argv[1:])
    
    # Determine root
    root_str = args["root"] or "."
    root = Path(root_str).expanduser().resolve()
    
    if not root.is_dir():
        print(f"❌ Error: Not a directory: {root}", file=sys.stderr)
        sys.exit(1)
    
    # Validate level
    level = args["level"]
    if level not in LEVEL_CONFIG:
        print(f"❌ Error: Unknown level '{level}'", file=sys.stderr)
        print(f"   Valid levels: {', '.join(LEVEL_CONFIG.keys())}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output path
    if args["out"]:
        output_path = Path(args["out"]).expanduser().resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        output_path = root / f"{root.name}_repo_merge_{level}_{timestamp}.md"
    
    # Generate merge
    try:
        generate_merge(root, level, output_path, args["split_size"])
    except Exception as e:
        print(f"❌ Error generating merge: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
