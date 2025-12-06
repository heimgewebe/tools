#!/usr/bin/env python3
"""
validate_merge_meta.py

Ein kleines Hilfs-Script, um den @meta-Block eines wc-merger-Reports
gegen das JSON Schema `wc-merge-report.schema.json` zu validieren.

Nutzung:

    cd merger/wc-merger
    python validate_merge_meta.py ../../merges/tools_max_part1.md

Exit-Codes:
    0 = alle Dateien gültig
    1 = mindestens eine Datei verletzt das Schema
    2 = technischer Fehler (z. B. Abhängigkeiten fehlen)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

try:
    from jsonschema import validate, ValidationError  # type: ignore
except ImportError:
    validate = None  # type: ignore
    ValidationError = Exception  # Fallback-Typ


HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "wc-merge-report.schema.json"


def load_schema() -> Dict[str, Any]:
    if not SCHEMA_PATH.is_file():
        raise RuntimeError(f"Schema-Datei nicht gefunden: {SCHEMA_PATH}")
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_meta(path: Path) -> Dict[str, Any]:
    """
    Extrahiert den YAML-Block.
    Priorität 1: HTML-Kommentar-Block (<!-- @meta:start --> ... <!-- @meta:end -->)
    Priorität 2: Legacy Frontmatter-Block (@meta ... ---)
    """
    if yaml is None:
        raise RuntimeError("PyYAML ist nicht installiert (pip install pyyaml).")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Strategy 1: Look for HTML block
    meta_lines: List[str] = []
    in_html_block = False
    found_html = False

    for line in lines:
        stripped = line.strip()
        if stripped == "<!-- @meta:start -->":
            in_html_block = True
            found_html = True
            continue
        if stripped == "<!-- @meta:end -->":
            break

        if in_html_block:
            # Code fences in the HTML block should be ignored
            if stripped.startswith("```"):
                continue
            meta_lines.append(line)

    if found_html:
        return yaml.safe_load("\n".join(meta_lines)) or {}

    # Strategy 2: Look for Legacy block
    meta_lines = []
    in_legacy_block = False
    found_legacy = False

    for line in lines:
        stripped = line.strip()
        if stripped == "@meta":
            in_legacy_block = True
            found_legacy = True
            continue

        if in_legacy_block:
            if stripped.startswith("---"):
                break
            meta_lines.append(line)

    if found_legacy:
        return yaml.safe_load("\n".join(meta_lines)) or {}

    raise RuntimeError(f"Kein @meta-Block in Datei gefunden: {path}")


def validate_file(schema: Dict[str, Any], path: Path) -> List[str]:
    """
    Validiert eine einzelne Merge-Datei.
    Gibt eine Liste von Fehlermeldungen zurück (leer = alles ok).
    """
    if validate is None:
        raise RuntimeError(
            "jsonschema ist nicht installiert (pip install jsonschema)."
        )

    meta = extract_meta(path)
    errors: List[str] = []
    try:
        validate(instance=meta, schema=schema)
    except ValidationError as e:  # type: ignore[assignment]
        msg = f"{path}: {e.message}"
        if e.path:
            msg += f" (Pfad: {'/'.join(str(p) for p in e.path)})"
        errors.append(msg)
    return errors


def main(argv: List[str]) -> int:
    if len(argv) < 1:
        print("Usage: python validate_merge_meta.py <merge-file> [...]", file=sys.stderr)
        return 2

    try:
        schema = load_schema()
    except Exception as exc:
        print(f"[ERROR] Schema konnte nicht geladen werden: {exc}", file=sys.stderr)
        return 2

    had_errors = False
    for name in argv:
        path = Path(name)
        if not path.exists():
             print(f"[ERROR] Datei nicht gefunden: {path}", file=sys.stderr)
             had_errors = True
             continue

        try:
            errs = validate_file(schema, path)
        except Exception as exc:
            print(f"[ERROR] {path}: {exc}", file=sys.stderr)
            had_errors = True
            continue

        for msg in errs:
            print(f"[SCHEMA] {msg}", file=sys.stderr)
        if errs:
            had_errors = True

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
