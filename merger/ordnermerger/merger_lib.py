#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merger_lib — Shared utility functions for merger scripts.

This module provides common functions used across different merger tools:
- human(): Format file sizes in human-readable format
- is_text(): Detect if a file is text or binary
- md5(): Compute MD5 checksums
- lang(): Get language identifier for markdown code blocks
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

# Erweiterungen, die sehr wahrscheinlich Text sind
TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".rs",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".jsonl",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".dockerfile",
    "dockerfile",  # Files named "Dockerfile" without extension
    ".svelte",
    ".css",
    ".scss",
    ".html",
    ".htm",
    ".xml",
    ".csv",
    ".log",
    ".lock",   # z.B. Cargo.lock, pnpm-lock.yaml
}

LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "html": "html", "css": "css",
    "scss": "scss", "sass": "sass", "json": "json", "xml": "xml", "yaml": "yaml", "yml": "yaml",
    "md": "markdown", "sh": "bash", "bat": "batch", "sql": "sql", "php": "php", "cpp": "cpp",
    "c": "c", "java": "java", "cs": "csharp", "go": "go", "rs": "rust", "rb": "ruby",
    "swift": "swift", "kt": "kotlin", "svelte": "svelte",
}


def human(n: int) -> str:
    """
    Konvertiert Bytes in ein menschenlesbares Format (KB, MB, ...).
    
    Args:
        n: Anzahl Bytes
        
    Returns:
        Formatierte Größe, z.B. "1.23 MB"
    """
    u = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(u) - 1:
        f /= 1024
        i += 1
    return f"{f:.2f} {u[i]}"


def is_text(path: Path) -> bool:
    """
    Heuristik: Ist dies eher eine Textdatei?
    
    - bekannte Text-Endungen -> True
    - große unbekannte Dateien -> eher False
    - ansonsten: 4 KiB lesen, auf NUL-Bytes prüfen
    
    Args:
        path: Pfad zur Datei
        
    Returns:
        True wenn wahrscheinlich Textdatei, sonst False
    """
    try:
        size = path.stat().st_size
    except OSError:
        return False
        
    name = path.name.lower()
    base, ext = os.path.splitext(name)
    if ext in TEXT_EXTENSIONS or name in TEXT_EXTENSIONS:
        return True
    
    # Sehr große unbekannte Dateien eher als binär behandeln
    if size > 20 * 1024 * 1024:  # 20 MiB
        return False
    
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
    except OSError:
        return False
    
    if not chunk:
        return True
    if b"\x00" in chunk:
        return False
    
    return True


def md5(path: Path, limit_bytes: Optional[int] = None) -> str:
    """
    Berechnet MD5-Hash einer Datei.
    
    Args:
        path: Pfad zur Datei
        limit_bytes: Optional, maximale Anzahl Bytes zu lesen
        
    Returns:
        MD5-Hash als Hexstring, oder "ERROR" bei Fehlern
    """
    # Note: MD5 is used here for file integrity checking, not security.
    # Python 3.9+ requires usedforsecurity parameter.
    try:
        h = hashlib.md5(usedforsecurity=False)
    except TypeError:
        # Fallback for Python < 3.9
        h = hashlib.md5()  # nosec B303
    
    try:
        with path.open("rb") as f:
            remaining = limit_bytes
            while True:
                if remaining is None:
                    chunk = f.read(65536)
                else:
                    chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                h.update(chunk)
                if remaining is not None:
                    remaining -= len(chunk)
                    if remaining <= 0:
                        break
        return h.hexdigest()
    except OSError:
        return "ERROR"


def lang(path: Path) -> str:
    """
    Ermittelt die Sprache für Markdown-Blöcke anhand der Dateiendung.
    
    Args:
        path: Pfad zur Datei
        
    Returns:
        Sprachbezeichner für Code-Block (z.B. "python", "javascript")
    """
    ext = path.suffix.lower().lstrip(".")
    return LANG_MAP.get(ext, "")
