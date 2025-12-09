#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
all-ein-wandler – Ordner → eine Markdown-Datei + JSON-Manifest

Optimiert für iOS (Pythonista) & Desktop.
Zweck: Konvertierung von generischen Ordnern (PDFs, Bilder, Docs) in KI-lesbares Markdown.

Features:
- "Hub Mode": Automatische Verarbeitung in ~/Documents/wandler-hub (iPad Standard)
- "Manual Mode": Explizite Pfadangabe (CLI / UI)
- OCR-Support: Integration mit iOS Shortcuts für Bilder/PDFs
- UI: Pythonista-UI für einfache Bedienung
"""

from __future__ import annotations

import sys
import os
import io
import json
import hashlib
import shutil
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Set

# --- Pythonista Imports (Safe) ---
try:
    import ui
except ImportError:
    ui = None

try:
    import console
except ImportError:
    console = None

try:
    import editor
except ImportError:
    editor = None

try:
    import clipboard
except ImportError:
    clipboard = None

try:
    import shortcuts
except ImportError:
    shortcuts = None

# --- Constants ---

ENCODING = "utf-8"
DEFAULT_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_SPLIT_SIZE = 10 * 1024 * 1024      # 10 MB Split

# Standard Ignorier-Listen (Noise)
IGNORE_DIR_NAMES = {
    ".git", ".hg", ".svn",
    "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", "dist", "build", ".next",
    ".venv", "venv", "env",
    ".idea", ".vscode", ".DS_Store",
    ".cargo", ".gradle", ".ruff_cache", ".cache"
}

IGNORE_FILE_SUFFIXES = {
    ".lock", ".log", ".pyc", ".DS_Store"
}

# Dateitypen
BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".ico",
    ".tif", ".tiff", ".pdf",
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
    ".mp4", ".mkv", ".mov", ".avi", ".webm",
    ".zip", ".gz", ".bz2", ".xz", ".7z", ".rar", ".zst",
    ".ttf", ".otf", ".woff", ".woff2",
    ".so", ".dylib", ".dll", ".exe",
    ".db", ".sqlite", ".sqlite3", ".realm", ".mdb", ".pack", ".idx",
    ".psd", ".ai", ".sketch", ".fig",
}

MEDIA_IMAGE_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".ico", ".tif", ".tiff"
}

LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "html": "html",
    "css": "css", "scss": "scss", "sass": "sass",
    "json": "json", "xml": "xml", "yaml": "yaml", "yml": "yaml",
    "md": "markdown", "rst": "markdown",
    "sh": "bash", "bat": "batch", "ps1": "powershell",
    "sql": "sql", "toml": "toml", "ini": "ini", "cfg": "ini",
    "rs": "rust", "go": "go", "c": "c", "h": "c",
    "cpp": "cpp", "hpp": "cpp", "cc": "cpp", "cxx": "cpp",
    "java": "java", "kt": "kotlin", "swift": "swift",
    "cs": "csharp", "rb": "ruby", "php": "php",
    "svelte": "svelte", "vue": "vue", "txt": ""
}


# --- Helpers ---

def safe_script_path() -> Path:
    """Robust script path detection."""
    try:
        return Path(__file__).resolve()
    except NameError:
        argv0 = sys.argv[0] if sys.argv else None
        if argv0:
            return Path(argv0).resolve()
        return Path.cwd().resolve()

def human_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024
        i += 1
    return f"{f:.1f} {units[i]}"

def file_md5(path: Path) -> str:
    h = hashlib.md5()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def is_probably_text(path: Path, sniff_bytes: int = 4096) -> bool:
    suf = path.suffix.lower()
    if suf in BINARY_EXTS:
        return False
    try:
        with path.open("rb") as f:
            chunk = f.read(sniff_bytes)
        if not chunk:
            return True
        if b"\x00" in chunk:
            return False
        try:
            chunk.decode(ENCODING)
            return True
        except UnicodeDecodeError:
            try:
                chunk.decode("latin-1")
                return True
            except Exception:
                return False
    except Exception:
        return False

# --- Config Class ---

class WandlerConfig:
    def __init__(self):
        self.max_file_bytes = DEFAULT_MAX_FILE_BYTES
        self.ocr_backend = "none"
        self.ocr_shortcut = "AllEin OCR"
        self.keep_last_n = 5
        self.auto_delete_source = True # Im Hub-Modus Standard

        self.load()

    def load(self):
        # 1. ~/.config
        cfg_path = Path.home() / ".config" / "all-ein-wandler" / "config.toml"
        if cfg_path.exists():
            try:
                # Basic parsing without toml lib dependency to avoid crashes
                # This is a hacky fallback if tomli is missing
                content = cfg_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if "max_file_bytes" in line and "=" in line:
                        self.max_file_bytes = int(line.split("=")[1].strip())
                    if "backend" in line and "=" in line:
                        val = line.split("=")[1].strip().strip('"').strip("'")
                        self.ocr_backend = val
                    if "shortcut_name" in line and "=" in line:
                        val = line.split("=")[1].strip().strip('"').strip("'")
                        self.ocr_shortcut = val
            except Exception:
                pass

# --- Core Logic ---

class WandlerCore:
    def __init__(self, config: WandlerConfig):
        self.config = config

    def ocr_via_shortcut(self, image_path: Path) -> Optional[str]:
        if not shortcuts:
            return None
        try:
            # Shortcut call blocked in main thread? In Pythonista usually ok.
            result = shortcuts.run(self.config.ocr_shortcut, input=str(image_path))
            if isinstance(result, str) and result.strip():
                return result
            return None
        except Exception:
            return None

    def gather_files(self, source: Path) -> List[Tuple[Path, Path]]:
        files = []
        for dirpath, dirnames, filenames in os.walk(source):
            d = Path(dirpath)
            # Filter directories
            dirnames[:] = [
                dn for dn in dirnames
                if dn not in IGNORE_DIR_NAMES and (not dn.startswith(".") or dn == ".github")
            ]
            for fn in filenames:
                p = d / fn
                if not p.is_file(): continue
                if any(p.name.endswith(s) for s in IGNORE_FILE_SUFFIXES): continue

                rel = p.relative_to(source)
                files.append((p, rel))

        files.sort(key=lambda t: str(t[1]).lower())
        return files

    def run(self, source: Path, dest_dir: Path, delete_source: bool = False) -> Tuple[Path, Path]:
        files = self.gather_files(source)

        ts = datetime.now().strftime("%Y%m%d-%H%M")
        stem = f"{source.name}_all-ein_{ts}"
        md_path = dest_dir / f"{stem}.md"
        json_path = dest_dir / f"{stem}.manifest.json"

        stats = {"total_bytes": 0, "categories": {}}
        manifest_files = []

        with md_path.open("w", encoding=ENCODING, errors="replace") as out:
            # Header matching wc-merger style roughly
            out.write(f"# All-Ein-Wandler Report: {source.name}\n\n")
            out.write(f"<!-- @meta:start -->\n")
            out.write(f"tool: all-ein-wandler\n")
            out.write(f"version: 2.0\n")
            out.write(f"source: {source.name}\n")
            out.write(f"timestamp: {datetime.now().isoformat()}\n")
            out.write(f"files: {len(files)}\n")
            out.write(f"<!-- @meta:end -->\n\n")

            out.write("## 🧭 Meta & Plan\n\n")
            out.write(f"- **Source:** `{source}`\n")
            out.write(f"- **Files:** {len(files)}\n\n")

            out.write("## 📁 Structure\n\n")
            out.write("```tree\n")
            # Simple tree gen
            for _, rel in files:
                out.write(f"{rel}\n")
            out.write("```\n\n")

            out.write("## 📦 Content\n\n")

            for abs_path, rel_path in files:
                size = abs_path.stat().st_size
                stats["total_bytes"] += size

                cat = self._categorize(abs_path)
                stats["categories"][cat] = stats["categories"].get(cat, 0) + 1

                md5 = file_md5(abs_path)

                out.write(f"### 📄 {rel_path}\n\n")
                out.write(f"- Category: `{cat}`\n")
                out.write(f"- Size: {human_size(size)}\n")
                out.write(f"- MD5: `{md5}`\n\n")

                is_text = cat != "media" and is_probably_text(abs_path)
                ocr_text = None
                ocr_status = "none"

                if cat == "media" and self.config.ocr_backend == "shortcut":
                    ocr_text = self.ocr_via_shortcut(abs_path)
                    ocr_status = "ok" if ocr_text else "failed"

                if is_text:
                    lang = LANG_MAP.get(abs_path.suffix.lower().lstrip("."), "")
                    self._write_content(out, abs_path, lang, size)
                else:
                    out.write(f"> Binary/Media file. Not included as text.\n\n")
                    if abs_path.suffix.lower() in MEDIA_IMAGE_EXTS:
                        out.write(f"![{rel_path}]({rel_path})\n\n")

                    if ocr_text:
                        out.write("#### 🖹 OCR Extracted Text\n\n")
                        out.write("```text\n")
                        out.write(ocr_text)
                        out.write("\n```\n\n")

                manifest_files.append({
                    "path": str(rel_path),
                    "size": size,
                    "md5": md5,
                    "category": cat,
                    "ocr": ocr_status
                })

        # Write Manifest
        manifest = {
            "tool": "all-ein-wandler",
            "version": 2,
            "source": str(source),
            "created": datetime.now().isoformat(),
            "stats": stats,
            "files": manifest_files
        }
        json_path.write_text(json.dumps(manifest, indent=2), encoding=ENCODING)

        if delete_source and source != dest_dir:
            try:
                shutil.rmtree(source)
                print(f"🗑️ Deleted source: {source}")
            except Exception as e:
                print(f"⚠️ Could not delete source: {e}")

        return md_path, json_path

    def _categorize(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext in MEDIA_IMAGE_EXTS or ext == ".pdf": return "media"
        if ext in {".md", ".txt", ".rst"}: return "doc"
        if ext in {".json", ".yaml", ".yml", ".toml"}: return "config"
        return "other"

    def _write_content(self, out: io.TextIOBase, path: Path, lang: str, size: int):
        if self.config.max_file_bytes > 0 and size > self.config.max_file_bytes:
            out.write(f"> File too large ({human_size(size)}). Truncated.\n\n")
            return

        try:
            text = path.read_text(encoding=ENCODING, errors="replace")
            out.write(f"```{lang}\n{text}\n```\n\n")
        except Exception as e:
            out.write(f"> Error reading file: {e}\n\n")

    def enforce_retention(self, dest_dir: Path, keep: int = 5):
        try:
            files = list(dest_dir.glob("*_all-ein_*.md"))
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for f in files[keep:]:
                f.unlink(missing_ok=True)
                f.with_suffix(".manifest.json").unlink(missing_ok=True)
        except Exception:
            pass

# --- UI Class ---

class WandlerUI:
    def __init__(self, core: WandlerCore, hub_dir: Path):
        self.core = core
        self.hub_dir = hub_dir
        self.files = self._scan_hub()
        self.view = self._build_view()

    def _scan_hub(self) -> List[Path]:
        if not self.hub_dir.exists():
            self.hub_dir.mkdir(parents=True, exist_ok=True)

        cands = []
        for p in self.hub_dir.iterdir():
            if p.is_dir() and p.name != "wandlungen" and not p.name.startswith("."):
                cands.append(p)
        # Sort new to old
        cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return cands

    def _build_view(self) -> ui.View:
        v = ui.View()
        v.name = "All-Ein-Wandler"
        v.background_color = "#111111"
        v.flex = "WH"

        # List
        tv = ui.TableView()
        tv.frame = (0, 0, v.width, v.height - 120)
        tv.flex = "WH"
        tv.background_color = "#111111"
        tv.separator_color = "#333333"

        ds = ui.ListDataSource([p.name for p in self.files])
        ds.text_color = "white"
        ds.highlight_color = "#0050ff"
        ds.action = self._on_select

        tv.data_source = ds
        tv.delegate = ds
        v.add_subview(tv)
        self.tv = tv

        # Bottom Bar
        bb = ui.View()
        bb.frame = (0, v.height - 120, v.width, 120)
        bb.flex = "WT"
        bb.background_color = "#222222"
        v.add_subview(bb)

        # Labels
        lbl = ui.Label(frame=(10, 10, v.width-20, 20))
        lbl.text = "Tap a folder to convert."
        lbl.text_color = "#aaaaaa"
        lbl.flex = "W"
        bb.add_subview(lbl)
        self.status_lbl = lbl

        # Delete switch
        sw = ui.Switch()
        sw.frame = (10, 40, 50, 32)
        sw.value = True
        bb.add_subview(sw)
        self.del_switch = sw

        sw_lbl = ui.Label(frame=(70, 40, 200, 32))
        sw_lbl.text = "Delete source after success"
        sw_lbl.text_color = "white"
        bb.add_subview(sw_lbl)

        # Refresh Button
        btn = ui.Button(frame=(v.width - 100, 40, 90, 32))
        btn.title = "Refresh"
        btn.background_color = "#444444"
        btn.tint_color = "white"
        btn.corner_radius = 6
        btn.action = self._refresh
        btn.flex = "L"
        bb.add_subview(btn)

        return v

    def _refresh(self, sender):
        self.files = self._scan_hub()
        self.tv.data_source.items = [p.name for p in self.files]
        self.tv.reload_data()

    def _on_select(self, sender):
        idx = self.tv.selected_row
        if idx < 0 or idx >= len(self.files): return

        src = self.files[idx]
        self.status_lbl.text = f"Processing {src.name}..."

        # Async run to not block UI completely (though in Pythonista main thread is shared)
        def worker():
            try:
                dest = self.hub_dir / "wandlungen"
                dest.mkdir(exist_ok=True)
                should_del = self.del_switch.value

                md, _ = self.core.run(src, dest, delete_source=should_del)
                self.core.enforce_retention(dest)

                if console:
                    console.hud_alert("Success!", "success", 1.0)

                self._refresh(None)
                self.status_lbl.text = f"Done: {md.name}"
            except Exception as e:
                if console:
                    console.alert("Error", str(e))
                self.status_lbl.text = "Error occurred."

        ui.delay(worker, 0.1)

    def present(self):
        self.view.present("fullscreen", hide_title_bar=True)


# --- Main ---

def main():
    config = WandlerConfig()
    core = WandlerCore(config)

    # Args
    source_arg = None
    if len(sys.argv) > 1:
        source_arg = sys.argv[1]

    # Env var
    if not source_arg:
        source_arg = os.environ.get("AEW_SOURCE")

    # Mode selection
    if source_arg:
        # CLI / Explicit Mode
        src = Path(source_arg).resolve()
        if not src.exists():
            print(f"Error: Source {src} not found.")
            sys.exit(1)

        print(f"Running in Explicit Mode for {src}")
        md, _ = core.run(src, src.parent, delete_source=False)
        print(f"Done: {md}")

    else:
        # Hub Mode
        hub_dir = Path.home() / "Documents" / "wandler-hub"

        # Fix for crash: Auto-create if missing
        if not hub_dir.exists():
            try:
                hub_dir.mkdir(parents=True, exist_ok=True)
                (hub_dir / "wandlungen").mkdir(exist_ok=True)
            except Exception as e:
                print(f"Error creating hub: {e}")
                sys.exit(1)

        # Check for UI availability
        if ui:
            app = WandlerUI(core, hub_dir)
            app.present()
        else:
            # Fallback for headless hub mode
            print("Running Headless Hub Mode...")
            cands = []
            for p in hub_dir.iterdir():
                if p.is_dir() and p.name != "wandlungen" and not p.name.startswith("."):
                    cands.append(p)

            if not cands:
                print("No folders found in wandler-hub.")
                return

            # Pick newest
            src = max(cands, key=lambda p: p.stat().st_mtime)
            print(f"Processing newest: {src.name}")

            dest = hub_dir / "wandlungen"
            dest.mkdir(exist_ok=True)

            core.run(src, dest, delete_source=True)
            core.enforce_retention(dest)

if __name__ == "__main__":
    main()
