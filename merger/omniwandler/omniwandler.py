#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
omniwandler – Ordner → eine Markdown-Datei + JSON-Manifest

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

try:
    import dialogs
except ImportError:
    dialogs = None

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

PDF_EXTS = {".pdf"}

# Ort für den Hub-Override (wird von der "Pfadfinderin" geschrieben)
HUB_CONFIG_DIR = Path.home() / ".config" / "omniwandler"
HUB_CONFIG_PATH = HUB_CONFIG_DIR / "hub-path.txt"

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

class OmniWandlerConfig:
    def __init__(self):
        self.max_file_bytes = DEFAULT_MAX_FILE_BYTES
        self.ocr_backend = "none"
        self.ocr_shortcut = "OmniWandler OCR"
        self.keep_last_n = 5
        self.auto_delete_source = True # Im Hub-Modus Standard

        self.load()

    def load(self):
        # 1. ~/.config
        cfg_path = Path.home() / ".config" / "omniwandler" / "config.toml"
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

class OmniWandlerCore:
    def __init__(self, config: OmniWandlerConfig):
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
        stem = f"{source.name}_omniwandler_{ts}"
        md_path = dest_dir / f"{stem}.md"
        json_path = dest_dir / f"{stem}.manifest.json"

        stats = {"total_bytes": 0, "categories": {}}
        manifest_files = []

        with md_path.open("w", encoding=ENCODING, errors="replace") as out:
            # Header matching wc-merger style roughly
            out.write(f"# OmniWandler Report: {source.name}\n\n")
            out.write(f"<!-- @meta:start -->\n")
            out.write(f"tool: omniwandler\n")
            out.write(f"version: 2.2\n")
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
                ext = abs_path.suffix.lower()
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
                if cat == "pdf":
                    is_text = False
                ocr_text = None
                ocr_status = "none"

                if (
                    self.config.ocr_backend == "shortcut"
                    and ext in MEDIA_IMAGE_EXTS.union(PDF_EXTS)
                ):
                    ocr_text = self.ocr_via_shortcut(abs_path)
                    ocr_status = "ok" if ocr_text else "failed"

                if is_text:
                    lang = LANG_MAP.get(abs_path.suffix.lower().lstrip("."), "")
                    self._write_content(out, abs_path, lang, size)
                else:
                    if cat == "pdf":
                        out.write(
                            "> PDF-Datei. Originalinhalt nicht inline, Text ggf. über OCR.\n\n"
                        )
                    else:
                        out.write(f"> Binary/Media file. Not included as text.\n\n")
                    if ext in MEDIA_IMAGE_EXTS:
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
            "tool": "omniwandler",
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
        if ext in MEDIA_IMAGE_EXTS:
            return "media"
        if ext in PDF_EXTS:
            return "pdf"
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

    def enforce_retention(self, dest_dir: Path, keep: Optional[int] = None):
        """Löscht alte OmniWandler-Outputs gemäß Config.keep_last_n."""
        try:
            if keep is None:
                keep = int(getattr(self.config, "keep_last_n", 5))

            files = list(dest_dir.glob("*_omniwandler_*.md"))
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for f in files[keep:]:
                f.unlink(missing_ok=True)
                f.with_suffix(".manifest.json").unlink(missing_ok=True)
        except Exception:
            pass

# --- UI Class ---

class OmniWandlerUI:
    def __init__(self, core: OmniWandlerCore, hub_dir: Path):
        self.core = core
        # Normalize the hub path to avoid surprises with relative or
        # tilde-based inputs that may come from environment variables.
        self.hub_dir = hub_dir.expanduser()
        self.files = self._scan_hub()
        self.ds = None  # ListDataSource für die Tabelle
        # Eigene Mehrfachauswahl (Index in self.files)
        self.marked_rows: Set[int] = set()

        self.view = self._build_view()

    def _scan_hub(self) -> List[Path]:
        if not self.hub_dir.exists():
            try:
                self.hub_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                # Silently ignore creation errors if hub detection is fuzzy
                pass

        if not self.hub_dir.exists():
            print(f"Hub not found at: {self.hub_dir}")
            return []

        print(f"Scanning Hub: {self.hub_dir}")

        # Debug log every entry to diagnose candidate detection issues
        try:
            for p in self.hub_dir.iterdir():
                print(f"[OmniWandler] Hub entry: {p}  is_dir={p.is_dir()}  name={p.name}")
        except Exception as e:
            print(f"[OmniWandler] Error iterating hub_dir: {e}")

        cands = []
        try:
            for p in self.hub_dir.iterdir():
                if p.name == "wandlungen" or p.name.startswith("."):
                    continue
                if p.is_dir():
                    cands.append(p)
        except Exception as e:
            print(f"Error scanning hub: {e}")
            return []

        # Sort new to old
        cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        print(f"Found {len(cands)} candidates.")
        return cands

    def _build_view(self) -> ui.View:
        v = ui.View()
        v.name = "OmniWandler"
        v.background_color = "#111111"
        v.flex = "WH"

        # Header Area
        hdr_h = 60
        hdr = ui.View(frame=(0, 0, v.width, hdr_h))
        hdr.flex = "W"
        hdr.background_color = "#222222"
        v.add_subview(hdr)

        title = ui.Label(frame=(10, 5, v.width - 60, 24))
        title.text = "OmniWandler"
        title.font = ("<system-bold>", 18)
        title.text_color = "white"
        title.flex = "W"
        hdr.add_subview(title)

        # Show path for debug/confirmation + Select Action
        path_str = str(self.hub_dir)
        home = str(Path.home())
        if path_str.startswith(home):
            path_str = "~" + path_str[len(home):]

        path_lbl = ui.Button(frame=(10, 30, v.width - 60, 20))
        path_lbl.title = f"Hub: {path_str}"
        path_lbl.font = ("<system>", 12)
        path_lbl.tint_color = "#888888"
        path_lbl.alignment = ui.ALIGN_LEFT
        path_lbl.flex = "W"
        path_lbl.action = self._pick_hub_location
        hdr.add_subview(path_lbl)
        self.path_lbl = path_lbl

        # Close Button (oben rechts)
        close_btn = ui.Button(frame=(v.width - 60, 10, 50, 40))
        close_btn.title = "Close"
        close_btn.font = ("<system>", 14)
        close_btn.background_color = "#444444"
        close_btn.tint_color = "white"
        close_btn.corner_radius = 6
        close_btn.flex = "L"
        close_btn.action = self._close
        hdr.add_subview(close_btn)

        # Add Source Button (manuelle Ordnerwahl) – links neben Close
        add_btn = ui.Button(frame=(v.width - 120, 10, 50, 40))
        add_btn.title = "Add"
        add_btn.font = ("<system>", 14)
        add_btn.background_color = "#444444"
        add_btn.tint_color = "white"
        add_btn.corner_radius = 6
        add_btn.action = self._pick_folder
        add_btn.flex = "L"
        hdr.add_subview(add_btn)

        # List
        tv = ui.TableView()
        # etwas Abstand nach unten vom Header
        tv.frame = (0, hdr_h + 10, v.width, v.height - (hdr_h + 130))
        tv.flex = "WH"
        tv.background_color = "#111111"
        tv.separator_color = "#333333"

        # ListDataSource liefert die Daten
        ds = ui.ListDataSource([p.name for p in self.files])
        # Basisfarben (werden in der Cell-Factory überschrieben)
        ds.text_color = "white"
        ds.background_color = "#111111"
        ds.highlight_color = "#0050ff"
        # Swipe-Delete & Move deaktivieren, damit nicht „nur aus der Liste“ gelöscht wird
        ds.delete_enabled = False
        ds.move_enabled = False

        # Eigene Cell-Factory: dunkler Hintergrund, weiße Schrift, Checkmark bei Markierung
        def make_cell(tableview, section, row, ds=ds, outer=self):
            cell = ui.TableViewCell()

            # Basisname aus der DataSource
            if 0 <= row < len(ds.items):
                base_name = ds.items[row]
            else:
                base_name = "?"

            # Sichtbare Markierung im Text
            if row in outer.marked_rows:
                cell.text_label.text = f"✓ {base_name}"
            else:
                cell.text_label.text = base_name

            cell.text_label.text_color = "white"
            cell.background_color = "#111111"

            # Optional weiterhin Accessory-Checkmark setzen (falls Pythonista es anzeigt)
            try:
                if row in outer.marked_rows:
                    cell.accessory_type = ui.ACCESSORY_CHECKMARK
                else:
                    cell.accessory_type = ui.ACCESSORY_NONE
            except Exception:
                pass

            return cell

        ds.tableview_cell_for_row = make_cell

        # Action: Row-Tap → Markierung toggeln + Status updaten
        def on_row_tapped(sender):
            sel = sender.selected_row  # (section, row) oder int
            if sel is None:
                return
            if isinstance(sel, tuple):
                _, row = sel
            else:
                row = sel
            if row is None or row < 0 or row >= len(self.files):
                return

            # Markierung toggeln
            if row in self.marked_rows:
                self.marked_rows.remove(row)
            else:
                self.marked_rows.add(row)

            if self.marked_rows:
                names = [self.files[r].name for r in sorted(self.marked_rows)]
                if len(names) == 1:
                    self.status_lbl.text = f"Ausgewählt: {names[0]}"
                else:
                    self.status_lbl.text = f"{len(names)} Ordner ausgewählt"
            else:
                # Keine Markierung → Hinweis
                if self.files:
                    self.status_lbl.text = f"{len(self.files)} folders found. Tap to select, then press Wandeln."
                else:
                    self.status_lbl.text = "Tap to select folders, then press Wandeln."

            # Checkmarks neu zeichnen
            self.tv.reload_data()

        ds.action = on_row_tapped

        tv.data_source = ds
        tv.delegate = ds

        v.add_subview(tv)
        self.tv = tv
        self.ds = ds

        # Bottom Bar
        bb = ui.View()
        bb.frame = (0, v.height - 120, v.width, 120)
        bb.flex = "WT"
        bb.background_color = "#222222"
        v.add_subview(bb)

        # Labels
        lbl = ui.Label(frame=(10, 10, v.width-20, 20))
        if self.files:
            lbl.text = f"{len(self.files)} folders found. Tap to select, then press Wandeln."
        else:
            lbl.text = "Tap to select folders, then press Wandeln."
        lbl.text_color = "#aaaaaa"
        lbl.flex = "W"
        bb.add_subview(lbl)
        self.status_lbl = lbl

        # Delete switch
        sw = ui.Switch()
        sw.frame = (10, 40, 50, 32)
        # Voreinstellung aus der Config übernehmen
        sw.value = bool(getattr(self.core.config, "auto_delete_source", True))
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

        # Wandeln Button (convert selection)
        convert_btn = ui.Button(frame=(v.width - 200, 40, 90, 32))
        convert_btn.title = "Wandeln"
        convert_btn.background_color = "#555555"
        convert_btn.tint_color = "white"
        convert_btn.corner_radius = 6
        convert_btn.action = self._convert_selected
        convert_btn.flex = "L"
        bb.add_subview(convert_btn)

        return v

    def _close(self, sender):
        """Schließt die OmniWandler-UI."""
        try:
            self.view.close()
        except Exception:
            pass

    def _refresh(self, sender):
        self.files = self._scan_hub()
        # Markierte Zeilen zurücksetzen (Hub kann sich verändert haben)
        self.marked_rows.clear()
        if self.ds is not None:
            self.ds.items = [p.name for p in self.files]
        # TableView komplett neu zeichnen
        self.tv.reload_data()
        if self.files:
            self.status_lbl.text = f"{len(self.files)} folders found. Tap to select, then press Wandeln."
        else:
            self.status_lbl.text = "Tap to select folders, then press Wandeln."

        # Update Hub Label text in case it changed
        path_str = str(self.hub_dir)
        home = str(Path.home())
        if path_str.startswith(home):
            path_str = "~" + path_str[len(home):]
        self.path_lbl.title = f"Hub: {path_str}"

    def _pick_hub_location(self, sender):
        """Allows re-selecting the Hub directory if detection failed."""
        if not dialogs: return

        # We need a folder picker for the Hub root. Explicitly enable
        # folder-picking mode because the default file picker on iOS
        # ignores folders even when a folder UTI is provided.
        folder = dialogs.pick_document(file_mode=False)
        if folder:
            self.hub_dir = Path(folder)
            self._refresh(None)
            if console:
                console.hud_alert("Hub updated")

    def _pick_folder(self, sender):
        if not dialogs:
            if console: console.alert("Dialogs module not available.")
            return

        # Pick a folder manually (explicitly enable folder mode)
        folder = dialogs.pick_document(file_mode=False)
        if folder:
            src = Path(folder)
            self.status_lbl.text = f"Manual pick: {src.name}"
            # Direct processing without blocking console.alert
            # to avoid UI thread issues
            self._run_conversion(src, manual_mode=True)

    def _convert_selected(self, sender):
        """
        Wandelt:
        - alle markierten Ordner gemeinsam (Combined-File), falls vorhanden
        - sonst den aktuell selektierten Ordner (Single-Run).
        """
        # 1) Falls markierte Ordner existieren → Combined
        if self.marked_rows:
            rows = sorted(r for r in self.marked_rows if 0 <= r < len(self.files))
            if not rows:
                if console:
                    console.hud_alert("Auswahl ungültig", "error", 1.0)
                return

            selected_paths = [self.files[r] for r in rows]
            dest = self.hub_dir / "wandlungen"
            dest.mkdir(exist_ok=True)

            self.status_lbl.text = f"Merging {len(selected_paths)} folders…"

            def worker():
                try:
                    ts = datetime.now().strftime("%Y%m%d-%H%M")
                    stem = f"combined_{len(selected_paths)}_folders_{ts}"
                    md_path = dest / f"{stem}.md"

                    with md_path.open("w", encoding=ENCODING, errors="replace") as out:
                        out.write("# OmniWandler Combined Report\n\n")
                        out.write("## Ordner\n\n")
                        for p in selected_paths:
                            out.write(f"- {p}\n")
                        out.write("\n## Inhalte\n\n")

                        for p in selected_paths:
                            partial_md, _ = self.core.run(
                                p,
                                dest,
                                delete_source=self.del_switch.value,
                            )

                            out.write(f"\n\n# --- {p.name} ---\n\n")
                            try:
                                with partial_md.open("r", encoding=ENCODING) as f:
                                    out.write(f.read())
                            except Exception as e:
                                out.write(f"> Error reading partial result for {p.name}: {e}\n\n")

                            # Einzel-Outputs wieder entfernen
                            try:
                                partial_md.unlink()
                                partial_md.with_suffix(".manifest.json").unlink()
                            except Exception:
                                pass

                    # Retention wie üblich
                    self.core.enforce_retention(dest)

                    if console:
                        console.hud_alert("Combined Success!", "success", 1.0)

                    # Auswahl leeren + UI refresh
                    self.marked_rows.clear()
                    self._refresh(None)
                    self.status_lbl.text = f"Done: {md_path.name}"
                except Exception as e:
                    traceback.print_exc()
                    if console:
                        console.hud_alert(f"Error: {e}", "error", 2.0)
                    self.status_lbl.text = "Error occurred."

            ui.delay(worker, 0.1)
            return

        # 2) Kein markierter Ordner → Single-Run via selected_row
        sel = self.tv.selected_row
        if sel is None:
            if console:
                console.hud_alert("Kein Ordner ausgewählt", "error", 1.0)
            return

        if isinstance(sel, tuple):
            _, row = sel
        else:
            row = sel

        if row is None or row < 0 or row >= len(self.files):
            if console:
                console.hud_alert("Auswahl ungültig", "error", 1.0)
            return

        src = self.files[row]
        self._run_conversion(src)

    def _run_conversion(self, src: Path, manual_mode: bool = False):
        self.status_lbl.text = f"Processing {src.name}..."

        def worker():
            try:
                # Output dir: wandlungen subdir in Hub
                # If hub_dir is not writable/valid, maybe use src parent?
                # But let's try Hub first.
                dest = self.hub_dir / "wandlungen"
                if not dest.exists():
                    try:
                        dest.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        # Fallback to source parent if hub is readonly/invalid
                        dest = src.parent

                should_del = self.del_switch.value

                md, _ = self.core.run(src, dest, delete_source=should_del)
                self.core.enforce_retention(dest)

                if console:
                    console.hud_alert("Success!", "success", 1.0)

                self._refresh(None)
                self.status_lbl.text = f"Done: {md.name}"
            except Exception as e:
                traceback.print_exc()
                if console:
                    # Non-blocking error if possible, or just log
                    console.hud_alert(f"Error: {e}", "error", 2.0)
                self.status_lbl.text = "Error occurred."

        ui.delay(worker, 0.1)

    def present(self):
        self.view.present("fullscreen", hide_title_bar=True)


# --- Hub Detection ---

def detect_wandler_hub(script_path: Path) -> Path:
    """
    Versucht den wandler-hub möglichst robust zu finden.

    Reihenfolge:
    1. OMNIWANDLER_HUB (falls gesetzt und existiert)
    2. Override-Datei (~/.config/omniwandler/hub-path.txt)
    3. Falls das Skript selbst in einem „wandler-hub“-Ordner liegt → genau dieser
    4. Bekannte Standardpfade (iOS/Desktop)
    5. Relativ zum Script (für „alles liegt in einem Ordner“-Setup)
    6. Fallback: bevorzugt ~/wandler-hub
    """
    print(f"[OmniWandler] script_path={script_path}")
    home = Path.home()
    print(f"[OmniWandler] Path.home()={home}")

    # 1) Explizite Vorgabe schlägt alles
    env = os.environ.get("OMNIWANDLER_HUB", "").strip()
    if env:
        p = Path(env).expanduser()
        print(f"[OmniWandler] OMNIWANDLER_HUB set to {p}")
        if p.is_dir():
            print("[OmniWandler] Using env hub dir")
            return p

    # 2) Override-Datei (wenn vorhanden und gültig)
    try:
        if HUB_CONFIG_PATH.exists():
            raw = HUB_CONFIG_PATH.read_text(encoding="utf-8").strip()
            if raw:
                p = Path(raw).expanduser()
                print(f"[OmniWandler] hub override file → {p}")
                if p.is_dir():
                    print("[OmniWandler] Using hub dir from override file")
                    return p
                else:
                    print("[OmniWandler] Override path does not exist, ignoring.")
    except Exception as e:
        print(f"[OmniWandler] Error reading hub override file: {e}")

    candidates: list[Path] = []

    # 3) Spezialfall iPad: Script liegt direkt im wandler-hub,
    # z. B. „Auf meinem iPad › Pythonista 3 › wandler-hub › omniwandler.py“
    script_dir = script_path.parent
    print(f"[OmniWandler] script_dir={script_dir}")
    if script_dir.name == "wandler-hub" and script_dir.is_dir():
        print("[OmniWandler] Adding script_dir as preferred hub candidate")
        candidates.append(script_dir)

    # 4) Standardpfade anhand von Path.home()

    # Pythonista-Shared-Container: home zeigt auf …/Pythonista3
    # → offizieller wandler-hub typischerweise unter ~/Documents/wandler-hub
    if home.name.lower() == "documents":
        candidates.append(home / "wandler-hub")
    else:
        candidates.append(home / "Documents" / "wandler-hub")
        candidates.append(home / "wandler-hub")

    # 5) Noch ein paar Varianten relativ zum Skript
    for up in range(4):
        base = script_path
        for _ in range(up):
            base = base.parent
        candidates.append(base / "wandler-hub")

    def has_content(path: Path) -> bool:
        try:
            for child in path.iterdir():
                if child.is_dir() and child.name != "wandlungen" and not child.name.startswith("."):
                    return True
        except Exception as e:
            print(f"[OmniWandler] Error checking {path} for content: {e}")
        return False

    # 6) Deduplizieren und ersten existierenden Kandidaten nehmen
    seen: set[Path] = set()
    unique: list[Path] = []
    for c in candidates:
        c = c.expanduser()
        if c in seen:
            continue
        seen.add(c)
        unique.append(c)

    print("[OmniWandler] Hub candidates:")
    for c in unique:
        print(f"  {c}  exists={c.is_dir()}  has_content={has_content(c) if c.is_dir() else False}")

    # Priorisiere Hubs, die tatsächlich Unterordner (Kandidaten) enthalten.
    for c in unique:
        if c.is_dir() and has_content(c):
            print(f"[OmniWandler] Using hub candidate with content: {c}")
            return c

    # Danach erster existierender Kandidat
    for c in unique:
        if c.is_dir():
            print(f"[OmniWandler] Using hub candidate: {c}")
            return c

    # Fallback: wenn wirklich gar nichts existiert
    fallback = unique[0] if unique else (home / "wandler-hub")
    print(f"[OmniWandler] Fallback hub: {fallback}")
    return fallback


# --- Main ---

def main():
    config = OmniWandlerConfig()
    core = OmniWandlerCore(config)

    # Args
    source_arg = None
    if len(sys.argv) > 1:
        source_arg = sys.argv[1]

    # Env var
    if not source_arg:
        source_arg = os.environ.get("OMNIWANDLER_SOURCE") or os.environ.get("AEW_SOURCE")

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
        script_path = safe_script_path()
        hub_dir = detect_wandler_hub(script_path)

        print(f"[OmniWandler] Using hub directory: {hub_dir}")

        # Fix for crash: Auto-create if missing
        if not hub_dir.exists():
            try:
                hub_dir.mkdir(parents=True, exist_ok=True)
                (hub_dir / "wandlungen").mkdir(exist_ok=True)
            except Exception as e:
                print(f"Error creating hub: {e}")
                # Don't exit, just continue, maybe permissions denied but UI might work with manual pick

        # Check for UI availability
        if ui:
            app = OmniWandlerUI(core, hub_dir)
            app.present()
        else:
            # Fallback for headless hub mode
            print("Running Headless Hub Mode...")
            cands = []
            if hub_dir.exists():
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
