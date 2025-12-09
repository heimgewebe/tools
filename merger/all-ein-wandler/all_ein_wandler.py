#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
all-ein-wandler – Ordner → eine Markdown-Datei + JSON-Manifest

Primär für iPad/Pythonista, aber auch auf Linux/macOS nutzbar.

Funktion:
- Nimmt einen Quellordner (rekursiv)
- Erzeugt:
  1) <basisname>_all-ein_YYYYMMDD-HHMM.md
  2) <basisname>_all-ein_YYYYMMDD-HHMM.manifest.json
- Alles Textartige wird vollständig eingebettet (bis max_file_bytes, Standard 10 MB pro Datei, bei Bedarf chunking)
- Binäre Dateien (Bilder, Audio, PDFs etc.) werden als Medien erfasst, nicht gelesen
- Optional: OCR via iOS Shortcut-Backend (für Bilder), per Config aktivierbar

Konfiguration (optional, TOML):
  ~/.config/all-ein-wandler/config.toml

Beispiel:

  [general]
  max_file_bytes = 10485760   # 10 MB

  [ocr]
  backend = "none"            # oder "shortcut"
  shortcut_name = "AllEin OCR"  # Name deines Shortcuts

OCR-Backend "shortcut":
- Erwartet ein iOS Shortcut mit dem Namen aus `shortcut_name`
- Der Shortcut bekommt als Input den Bildpfad (String)
- Der Shortcut gibt erkannten Text als String zurück
"""

from __future__ import annotations

import sys
import os
import io
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# --- Versuche tomllib / tomli für Config ---
try:
    import tomllib  # Python 3.11+
except Exception:  # Pythonista 3.10 etc.
    tomllib = None  # type: ignore


# ========= Defaults & Konstanten =========

ENCODING = "utf-8"
DEFAULT_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

# Typische "Cache-/Build-Ordner", die wir ignorieren
IGNORE_DIR_NAMES = {
    ".git", ".hg", ".svn",
    "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", "dist", "build", ".next",
    ".venv", "venv",
    ".idea", ".vscode", ".DS_Store",
    ".cargo", ".gradle", ".ruff_cache", ".cache"
}

# Dateien, die wir eher ignorieren würden (hier nur sehr konservativ)
IGNORE_FILE_SUFFIXES = {
    ".lock", ".log"
}

# Endungen, die wir als klar binär betrachten
BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".ico",
    ".tif", ".tiff",
    ".pdf",
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
    ".mp4", ".mkv", ".mov", ".avi", ".webm",
    ".zip", ".gz", ".bz2", ".xz", ".7z", ".rar", ".zst",
    ".ttf", ".otf", ".woff", ".woff2",
    ".so", ".dylib", ".dll", ".exe",
    ".db", ".sqlite", ".sqlite3", ".realm", ".mdb", ".pack", ".idx",
    ".psd", ".ai", ".sketch", ".fig",
}

# Endungen, die wir als "Media/Scan" zählen (OCR-relevant)
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


# ========= Utils =========

def human_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024
        i += 1
    return f"{f:.1f} {units[i]}"


def deurl_path(s: str) -> str:
    """Handle file:// URLs, ansonsten String durchreichen."""
    if not s:
        return ""
    s = s.strip()
    if s.lower().startswith("file://"):
        from urllib.parse import unquote
        return unquote(s[7:])
    return s


def is_probably_text(path: Path, sniff_bytes: int = 4096) -> bool:
    """Heuristik: Ist das eine Textdatei? (ohne harte Garantie)"""
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
        # Versuche UTF-8
        try:
            chunk.decode(ENCODING)
            return True
        except UnicodeDecodeError:
            # fallback latin-1 → wenn das auch kracht, dann eher binär
            try:
                chunk.decode("latin-1")
                return True
            except Exception:
                return False
    except Exception:
        return False


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def language_for(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return LANG_MAP.get(ext, "")


def categorize_file(path: Path) -> str:
    """
    Grobe Kategorien:
    - doc: Dokumentationstexte
    - config: Konfiguration
    - source: Quellcode
    - media: Bilder/Scans etc.
    - other: alles andere
    """
    ext = path.suffix.lower()
    name = path.name.lower()

    if ext in MEDIA_IMAGE_EXTS:
        return "media"
    if ext == ".pdf":
        return "media"

    # doc
    if ext in {".md", ".rst", ".txt"}:
        return "doc"

    # config
    if ext in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}:
        return "config"
    if name in {"pyproject.toml", "package.json", "cargo.toml", "poetry.lock"}:
        return "config"

    # source
    if ext in {
        ".py", ".js", ".ts", ".rs", ".go",
        ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
        ".java", ".kt", ".swift", ".cs",
        ".rb", ".php", ".svelte", ".vue"
    }:
        return "source"

    # fallback
    return "other"


def write_tree(out: io.TextIOBase, root: Path) -> None:
    """Einfache Tree-Ansicht des Ordners."""
    def rec(cur: Path, depth: int) -> None:
        try:
            entries = sorted(cur.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception:
            return
        for e in entries:
            if e.is_dir() and e.name in IGNORE_DIR_NAMES:
                continue
            rel = e.relative_to(root)
            indent = "  " * depth
            if e.is_dir():
                out.write(f"{indent}- 📁 {rel}\n")
                rec(e, depth + 1)
            else:
                out.write(f"{indent}- 📄 {rel}\n")

    out.write("```tree\n")
    out.write(str(root) + "\n")
    rec(root, 0)
    out.write("```\n")


# ========= Config & OCR =========

def load_config() -> Dict[str, Any]:
    """
    Versucht ~/.config/all-ein-wandler/config.toml zu lesen.
    Gibt dict mit 'general' und 'ocr' zurück, falls vorhanden.
    """
    cfg: Dict[str, Any] = {
        "general": {},
        "ocr": {}
    }
    cfg_path = Path.home() / ".config" / "all-ein-wandler" / "config.toml"
    if not cfg_path.exists():
        return cfg
    text = ""
    try:
        text = cfg_path.read_text(encoding=ENCODING)
    except Exception:
        return cfg
    if not tomllib:
        return cfg
    try:
        data = tomllib.loads(text)
        if isinstance(data, dict):
            if "general" in data and isinstance(data["general"], dict):
                cfg["general"] = data["general"]
            if "ocr" in data and isinstance(data["ocr"], dict):
                cfg["ocr"] = data["ocr"]
    except Exception:
        pass
    return cfg


def get_ocr_backend(cfg: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    ocr_cfg = cfg.get("ocr") or {}
    backend = str(ocr_cfg.get("backend", "none")).strip().lower()
    return backend, ocr_cfg


def ocr_via_shortcut(image_path: Path, shortcut_name: str) -> Optional[str]:
    """
    Ruft einen iOS Shortcut auf (nur Pythonista).
    Der Shortcut soll den Bildpfad als Input bekommen und Text zurückliefern.
    """
    try:
        import shortcuts  # type: ignore
    except Exception:
        return None
    try:
        result = shortcuts.run(shortcut_name, input=str(image_path))
        if isinstance(result, str) and result.strip():
            return result
        return None
    except Exception:
        return None


def run_ocr_if_enabled(
    backend: str,
    ocr_cfg: Dict[str, Any],
    path: Path,
) -> Tuple[Optional[str], str]:
    """
    Versucht ggf. OCR auszuführen.
    Rückgabe: (ocr_text, ocr_status)
    ocr_status z. B. "none", "shortcut-ok", "shortcut-error"
    """
    if backend == "none":
        return None, "none"

    ext = path.suffix.lower()
    if ext not in MEDIA_IMAGE_EXTS:
        return None, "not-media"

    if backend == "shortcut":
        shortcut_name = str(ocr_cfg.get("shortcut_name", "AllEin OCR"))
        txt = ocr_via_shortcut(path, shortcut_name=shortcut_name)
        if txt is None:
            return None, "shortcut-error"
        return txt, "shortcut-ok"

    # andere Backends könnten später kommen (http etc.)
    return None, "unsupported-backend"


# ========= Hauptlogik: Sammeln & Schreiben =========

def gather_files(source: Path) -> List[Tuple[Path, Path]]:
    """Gibt Liste von (abs_path, rel_path) zurück."""
    files: List[Tuple[Path, Path]] = []
    for dirpath, dirnames, filenames in os.walk(source):
        d = Path(dirpath)
        # Ordner filtern
        # .github erlauben, andere hidden ordner ausschließen
        dirnames[:] = [
            dn for dn in dirnames
            if dn not in IGNORE_DIR_NAMES and (not dn.startswith(".") or dn == ".github")
        ]
        for fn in filenames:
            p = d / fn
            if not p.is_file():
                continue
            if any(p.name.endswith(suf) for suf in IGNORE_FILE_SUFFIXES):
                continue
            rel = p.relative_to(source)
            files.append((p, rel))
    files.sort(key=lambda t: str(t[1]).lower())
    return files


def write_text_file_content(
    out: io.TextIOBase,
    abs_path: Path,
    rel_path: Path,
    lang: str,
    size: int,
    max_bytes: int
) -> int:
    """
    Schreibt Inhalt einer Textdatei, chunked bei Bedarf.
    Gibt Anzahl der erzeugten Chunks zurück.
    """
    # max_bytes <= 0 → kein Limit, alles in einem Block
    if max_bytes <= 0 or size <= max_bytes:
        # Einfacher Fall: alles auf einmal
        try:
            text = abs_path.read_text(encoding=ENCODING, errors="replace")
        except Exception as e:
            out.write(f"```{lang}\n<<Lesefehler: {e}>>\n```\n\n")
            return 1
        out.write(f"```{lang}\n")
        out.write(text)
        if not text.endswith("\n"):
            out.write("\n")
        out.write("```\n\n")
        return 1

    # Großer Fall: chunkweise (nach Bytes)
    chunk_index = 0
    try:
        with abs_path.open("rb") as f:
            while True:
                raw = f.read(max_bytes)
                if not raw:
                    break
                chunk_index += 1
                text = raw.decode(ENCODING, errors="replace")
                # suffix nicht verwendet
                out.write(f"```{lang}\n")
                out.write(text)
                if not text.endswith("\n"):
                    out.write("\n")
                out.write("```\n\n")
    except Exception as e:
        out.write(f"```{lang}\n<<Lesefehler: {e}>>\n```\n\n")
        if chunk_index == 0:
            chunk_index = 1
    if chunk_index == 0:
        chunk_index = 1
    return chunk_index


def build_output_paths(source: Path, dest_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Erzeugt Pfade für:
      - Markdown
      - JSON-Manifest
    im Zielordner (dest_dir) oder, falls nicht gesetzt, im Elternordner der Quelle.
    """
    base_dir = dest_dir or source.parent
    base_name = source.name
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    stem = f"{base_name}_all-ein_{ts}"
    md_path = base_dir / f"{stem}.md"
    json_path = base_dir / f"{stem}.manifest.json"
    return md_path, json_path


def run_all_ein_wandler(source: Path, max_file_bytes: int, dest_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    cfg = load_config()
    ocr_backend, ocr_cfg = get_ocr_backend(cfg)

    files = gather_files(source)

    # Zielordner bestimmen (explizit oder Standard = Elternordner der Quelle)
    md_path, json_path = build_output_paths(source, dest_dir=dest_dir)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    stats_total_bytes = 0
    category_counts = {
        "doc": 0,
        "config": 0,
        "source": 0,
        "media": 0,
        "other": 0
    }

    manifest_files: List[Dict[str, Any]] = []

    # --- Markdown schreiben ---
    with md_path.open("w", encoding=ENCODING, errors="replace") as out:
        # Header
        out.write(f"# all-ein-wandler Export: {source.name}\n\n")
        out.write("## 🧭 Meta\n\n")
        out.write(f"- Quelle: `{source}`\n")
        out.write(f"- Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        out.write(f"- Dateien: {len(files)}\n\n")

        # Struktur
        out.write("## 📁 Struktur\n\n")
        write_tree(out, source)
        out.write("\n")

        # Dateien einzeln
        out.write("## 📦 Dateien\n\n")

        for abs_path, rel_path in files:
            try:
                st = abs_path.stat()
                size = int(st.st_size)
            except Exception:
                size = 0

            stats_total_bytes += size

            cat = categorize_file(abs_path)
            category_counts[cat] = category_counts.get(cat, 0) + 1

            is_text = cat != "media" and is_probably_text(abs_path)
            md5 = ""
            try:
                md5 = file_md5(abs_path)
            except Exception:
                md5 = ""

            lang = language_for(abs_path) if is_text else ""

            # OCR (nur für Bilder, nur wenn konfiguriert)
            ocr_text: Optional[str] = None
            ocr_status = "none"
            if cat == "media" and ocr_backend != "none":
                ocr_text, ocr_status = run_ocr_if_enabled(
                    backend=ocr_backend,
                    ocr_cfg=ocr_cfg,
                    path=abs_path,
                )

            # Abschnitt im Markdown
            out.write(f"### 📄 {rel_path}\n\n")
            out.write(f"- Kategorie: `{cat}`\n")
            out.write(f"- Größe: {human_size(size)}\n")
            if md5:
                out.write(f"- md5: `{md5}`\n")
            if ocr_status != "none":
                out.write(f"- OCR-Status: `{ocr_status}`\n")
            out.write("\n")

            chunk_count = 0

            if is_text:
                chunk_count = write_text_file_content(
                    out=out,
                    abs_path=abs_path,
                    rel_path=rel_path,
                    lang=lang,
                    size=size,
                    max_bytes=max_file_bytes,
                )
            else:
                # Binär/Medien: wir betten kein Roh-Binary ein
                # Optional: Markdown-Image-Referenz für Bilder
                if abs_path.suffix.lower() in MEDIA_IMAGE_EXTS:
                    # relative Pfade für mögliche Anzeige in Obsidian, GitHub etc.
                    out.write(f"![{rel_path}]({rel_path})\n\n")
                else:
                    out.write("> (Binär-/Mediendatei, kein Text eingebettet)\n\n")

                # Wenn OCR-Text vorhanden, als Textblock einfügen
                if ocr_text:
                    out.write("#### 🖹 OCR-Text\n\n")
                    out.write("```text\n")
                    out.write(ocr_text)
                    if not ocr_text.endswith("\n"):
                        out.write("\n")
                    out.write("```\n\n")

                chunk_count = 0

            manifest_files.append({
                "path": str(rel_path).replace(os.sep, "/"),
                "size": size,
                "md5": md5 or None,
                "category": cat,
                "language": lang or None,
                "is_text": bool(is_text),
                "is_binary": not is_text,
                "chunk_count": chunk_count,
                "ocr": {
                    "backend": ocr_backend,
                    "status": ocr_status,
                    "has_text": bool(ocr_text),
                },
            })

        # Zusammenfassung am Ende
        out.write("## 🧾 Zusammenfassung\n\n")
        out.write(f"- Gesamtgröße (alle Dateien): **{human_size(stats_total_bytes)}**\n")
        out.write(f"- Dateien gesamt: **{len(files)}**\n")
        out.write("- Kategorien:\n")
        for k in ["doc", "config", "source", "media", "other"]:
            out.write(f"  - {k}: {category_counts.get(k, 0)}\n")
        out.write("\n")

    # --- JSON-Manifest schreiben ---
    manifest = {
        "tool": "all-ein-wandler",
        "version": 1,
        "source_dir": str(source),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "stats": {
            "file_count": len(files),
            "total_bytes": stats_total_bytes,
            "categories": category_counts,
        },
        "general": {
            "max_file_bytes": max_file_bytes,
            "encoding": ENCODING,
        },
        "files": manifest_files,
    }

    try:
        json_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding=ENCODING
        )
    except Exception as e:
        print(f"⚠️ Konnte Manifest nicht schreiben: {e}", file=sys.stderr)

    print(f"✅ all-ein-wandler fertig.")
    print(f"   Markdown : {md_path}")
    print(f"   Manifest : {json_path}")

    return md_path, json_path


# ========= CLI / Source-Ermittlung =========

def parse_args(argv: List[str]) -> Tuple[Optional[str], int]:
    """
    Sehr schlanke Arg-Parse, damit es auf Pythonista nicht nervt.
    Unterstützt:
      --source-dir <pfad|file://url>
      --max-file-bytes <zahl>
      [positional] <pfad>
    """
    src: Optional[str] = None
    max_bytes = DEFAULT_MAX_FILE_BYTES

    it = iter(enumerate(argv))
    for i, token in it:
        if token in ("--source-dir", "--source", "-s"):
            try:
                _, val = next(it)
                src = val
            except StopIteration:
                pass
        elif token == "--max-file-bytes":
            try:
                _, val = next(it)
                try:
                    max_bytes = int(val)
                except Exception:
                    pass
            except StopIteration:
                pass
        elif token.startswith("-"):
            # andere Flags ignorieren wir vorerst
            continue
        else:
            # erstes nicht-Flag → Pfad
            if src is None:
                src = token

    return src, max_bytes


def _resolve_paths(argv: List[str]) -> Tuple[Path, Path, int, bool]:
    """
    Ermittelt Quelle, Ziel, max_file_bytes und ob wir im wandler-hub-Modus laufen.

    - Wenn AEW_SOURCE oder CLI-Args gesetzt sind:
      → Quelle wie bisher, Ziel = source.parent, kein Auto-Löschen.
    - Wenn nichts gesetzt:
      → wandler-hub-Modus:
         Quelle = zuletzt geänderter Unterordner von ~/Documents/wandler-hub
                   (ohne 'wandlungen' und ohne versteckte Ordner)
         Ziel   = ~/Documents/wandler-hub/wandlungen
    """
    # 1) Env/CLI prüfen
    env_src = os.environ.get("AEW_SOURCE", "").strip()
    cli_src, cli_max_bytes = parse_args(argv)

    has_explicit_source = bool(env_src or cli_src)
    max_bytes = cli_max_bytes

    if has_explicit_source:
        cand = env_src or cli_src or ""
        cand = deurl_path(cand) if cand else ""
        if not cand:
            source = Path.cwd()
        else:
            p = Path(cand).expanduser()
            if p.is_file():
                source = p.parent
            else:
                source = p

        if not source.is_dir():
            raise SystemExit(f"❌ Quelle ist kein Ordner: {source}")

        # Config kann max_file_bytes noch überschreiben (wenn CLI nichts gesetzt hat)
        cfg = load_config()
        gen_cfg = cfg.get("general") or {}
        if cli_max_bytes == DEFAULT_MAX_FILE_BYTES:
            try:
                cfg_val = int(gen_cfg.get("max_file_bytes", DEFAULT_MAX_FILE_BYTES))
                max_bytes = cfg_val
            except Exception:
                max_bytes = DEFAULT_MAX_FILE_BYTES

        dest_dir = source.parent
        return source, dest_dir, max_bytes, False  # Kein Hub-Modus

    # 2) wandler-hub-Modus (Standard auf iPad ohne Args)
    docs_root = Path.home() / "Documents"
    hub_dir = docs_root / "wandler-hub"
    if not hub_dir.is_dir():
        raise SystemExit(f"❌ wandler-hub nicht gefunden: {hub_dir}")

    dest_dir = hub_dir / "wandlungen"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Alle Kandidatenordner (Unterordner außer 'wandlungen' und versteckte)
    candidates: List[Path] = []
    for entry in hub_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name == "wandlungen":
            continue
        if entry.name.startswith("."):
            continue
        candidates.append(entry)

    if not candidates:
        raise SystemExit("❌ Kein Quellordner in wandler-hub gefunden (außer 'wandlungen').")

    # Zuletzt geänderten Ordner nehmen (vermutlich der gerade abgelegte)
    try:
        source = max(candidates, key=lambda p: p.stat().st_mtime)
    except Exception:
        source = candidates[0]

    # max_file_bytes ggf. aus Config holen
    cfg = load_config()
    gen_cfg = cfg.get("general") or {}
    try:
        cfg_val = int(gen_cfg.get("max_file_bytes", DEFAULT_MAX_FILE_BYTES))
        max_bytes = cfg_val
    except Exception:
        max_bytes = DEFAULT_MAX_FILE_BYTES

    return source, dest_dir, max_bytes, True  # Hub-Modus aktiv


def _cleanup_source_dir(source: Path, dest_dir: Path) -> None:
    """
    Löscht den Quellordner nach erfolgreicher Wandlung.
    Sicherheitsleine: löscht niemals den Zielordner selbst.
    """
    try:
        if source.resolve() == dest_dir.resolve():
            print("⚠️ Quelle und Ziel sind identisch – nichts gelöscht.", file=sys.stderr)
            return
        shutil.rmtree(source)
        print(f"🗑️ Quellordner gelöscht: {source}")
    except Exception as e:
        print(f"⚠️ Konnte Quellordner nicht löschen: {e}", file=sys.stderr)


def _enforce_retention(dest_dir: Path, keep: int = 5) -> None:
    """
    Hält nur die letzten `keep` Wandlungen im Zielordner.
    Ältere Paare (<stem>.md + <stem>.manifest.json) werden entfernt.
    """
    try:
        runs: List[Tuple[str, float]] = []
        for md_file in dest_dir.glob("*_all-ein_*.md"):
            stem = md_file.stem
            try:
                mtime = md_file.stat().st_mtime
            except Exception:
                mtime = 0.0
            runs.append((stem, mtime))

        if len(runs) <= keep:
            return

        runs.sort(key=lambda x: x[1], reverse=True)  # Neueste zuerst
        to_delete = [stem for stem, _ in runs[keep:]]

        for stem in to_delete:
            for suffix in (".md", ".manifest.json"):
                path = dest_dir / f"{stem}{suffix}"
                if path.exists():
                    try:
                        path.unlink()
                    except Exception as e:
                        print(f"⚠️ Konnte alte Wandlung nicht löschen: {path} ({e})", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Fehler bei Aufräumlogik im Zielordner: {e}", file=sys.stderr)


def main() -> None:
    source, dest_dir, max_bytes, is_hub_mode = _resolve_paths(sys.argv[1:])
    md_path, json_path = run_all_ein_wandler(source, max_file_bytes=max_bytes, dest_dir=dest_dir)

    # Nur im wandler-hub-Modus aggressiv aufräumen
    if is_hub_mode:
        _cleanup_source_dir(source, dest_dir)
        _enforce_retention(dest_dir, keep=5)


if __name__ == "__main__":
    main()
