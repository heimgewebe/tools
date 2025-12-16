#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys

try:
    import console  # type: ignore
except Exception:
    console = None  # type: ignore

def safe_script_path() -> Path:
    try:
        return Path(__file__).resolve()
    except Exception:
        # letzte Rettung
        return Path.cwd().resolve() / "repolens-hub-pathfinder.py"

def main() -> int:
    hub_dir = Path.cwd().resolve()
    script_path = safe_script_path()
    script_dir = script_path.parent

    out_file = script_dir / ".repolens-hub-path.txt"

    if not hub_dir.is_dir():
        msg = f"Not a directory: {hub_dir}"
        print(msg)
        if console:
            console.alert("repoLens hub pathfinder", msg, "OK", hide_cancel_button=True)
        return 2

    try:
        out_file.write_text(str(hub_dir), encoding="utf-8")
        msg = f"Saved hub path:\n{hub_dir}\n\n→ {out_file}"
        print(msg)
        if console:
            console.alert("repoLens hub pathfinder", msg, "OK", hide_cancel_button=True)
        return 0
    except Exception as e:
        msg = f"Failed to write {out_file}:\n{e}"
        print(msg)
        if console:
            console.alert("repoLens hub pathfinder", msg, "OK", hide_cancel_button=True)
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
