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
    Extrahiert den YAML-Block zwischen '@meta' und der nächsten '---'-Zeile.
    Erwartet ein Format wie:

        @meta
        merge:
          spec_version: "2.3"
          ...
        ---
    """
    if yaml is None:
        raise RuntimeError("PyYAML ist nicht installiert (pip install pyyaml).")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    meta_lines: List[str] = []
    in_meta = False

    for line in lines:
        if line.strip() == "@meta":
            in_meta = True
            continue
        if in_meta and line.strip().startswith("---"):
            break
        if in_meta:
            meta_lines.append(line)

    if not meta_lines:
        raise RuntimeError(f"Kein @meta-Block in Datei gefunden: {path}")

    return yaml.safe_load("\n".join(meta_lines)) or {}


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
        try:
            errs = validate_file(schema, path)
        except Exception as exc:
            print(f"[ERROR] {path}: {exc}", file=sys.stderr)
            return 2
        for msg in errs:
            print(f"[SCHEMA] {msg}", file=sys.stderr)
        if errs:
            had_errors = True

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
