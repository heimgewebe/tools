# repo-merger

Repository/Code Merger for AI Context

## Overview

`repo-merger` is a text-based tool that creates AI-friendly Markdown snapshots of code repositories. It focuses exclusively on text files (code, documentation, configuration) and produces structured, deterministic output suitable for AI consumption and Heimgewebe workflows.

## Features

- **Level-based filtering**: Choose from `overview`, `summary`, `dev`, or `max` levels
- **Structured output**: Consistent sections (Meta, Structure, Manifest, Content)
- **Split mechanics**: Automatically split large outputs into multiple files
- **Text-only**: Strictly processes text files, no binary/media handling
- **Heimgewebe-compatible**: Follows merge-contract structure

## Installation

No external dependencies required. Pure Python 3.7+.

```bash
# Make executable
chmod +x repo_merger.py

# Optional: Create symlink for easier access
ln -s "$(pwd)/repo_merger.py" /usr/local/bin/repo-merger
```

## Usage

### Basic Usage

```bash
# Merge current directory at max level
./repo_merger.py

# Merge specific directory
./repo_merger.py --root /path/to/repo --level dev

# Custom output path
./repo_merger.py --out snapshot.md
```

### Levels

- **overview**: High-level overview with README and main documentation
  - Includes: README.md, LICENSE, CHANGELOG.md
  - Best for: Quick repository overview

- **summary**: Documentation and configuration
  - Includes: All doc and config files
  - Best for: Understanding project structure and setup

- **dev**: Source code and tests
  - Includes: Doc, config, source, and test files
  - Best for: Code review and development context

- **max**: Complete repository snapshot (default)
  - Includes: Everything (doc, config, source, test, other)
  - Best for: Full AI context

### Options

```
--root, -r PATH      Repository root directory (default: current directory)
--level, -l LEVEL    Merge level: overview, summary, dev, max (default: max)
--out, -o PATH       Output file path (default: auto-generated)
--split-size BYTES   Split output into multiple files if larger than BYTES
--help, -h           Show this help message
```

### Examples

```bash
# Create overview
repo-merger --level overview --out overview.md

# Full snapshot with splitting
repo-merger --level max --split-size 5000000

# Development snapshot
repo-merger --root ~/projects/myapp --level dev
```

## Output Format

Each merge contains:

1. **Header**: Repository name, level, statistics
2. **Meta Block**: YAML metadata (tool, version, timestamp, stats)
3. **Structure**: Tree view of included files
4. **Manifest**: Table of files with categories and sizes
5. **Content**: Full content of each file with syntax highlighting

Example output structure:

```markdown
# Repo-Merger: myproject

**Level:** dev – Source code and tests
**Files:** 42
**Total Size:** 156.3 KB

```yaml
merge:
  tool: repo-merger
  version: 1.0
  created_at: 2025-12-09T10:30:00
  level: dev
  ...
```

## 📁 Structure
...

## 🧾 Manifest
...

## 📄 Content
...
```

## File Categorization

Files are automatically categorized:

- **doc**: `.md`, `.rst`, `.txt`, `.adoc`
- **config**: `.json`, `.yaml`, `.toml`, `.ini`, `package.json`, etc.
- **source**: `.py`, `.js`, `.ts`, `.rs`, `.go`, `.c`, `.cpp`, `.java`, etc.
- **test**: Files in test directories or starting with `test_`
- **other**: Everything else

## Ignored Directories

The following directories are automatically skipped:

- `.git`, `.hg`, `.svn`
- `__pycache__`, `.mypy_cache`, `.pytest_cache`
- `node_modules`, `dist`, `build`, `target`
- `.venv`, `venv`
- `.idea`, `.vscode`
- `.cargo`, `.gradle`, `.cache`

## Comparison with Other Tools

### vs. wc-merger

`wc-merger` is the full-featured Heimgewebe tool with:
- Advanced organism integration
- Health checks
- Delta reports
- Fleet panorama
- Strict contract compliance

`repo-merger` is a simplified, standalone tool for:
- General repository merging
- Simpler use cases
- No Heimgewebe dependencies

### vs. folder-extractor

`repo-merger` is for **code repositories** (text only).

`folder-extractor` is for **any folder** (PDFs, images, Office docs).

Use `repo-merger` for code projects, `folder-extractor` for mixed content.

## License

Part of the Heimgewebe tools collection.
