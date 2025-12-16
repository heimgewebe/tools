#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import os

try:
    import console  # type: ignore
except Exception:
    console = None  # type: ignore

try:
    import dialogs  # type: ignore
except Exception:
    dialogs = None  # type: ignore

def safe_script_path() -> Path:
    try:
        return Path(__file__).resolve()
    except Exception:
        # letzte Rettung
        return Path.cwd().resolve() / "repolens-hub-pathfinder.py"

def main() -> int:
    # Default fallback: CWD
    hub_dir = Path.cwd().resolve()

    # Try to be smart if CWD seems to be the tool dir itself (e.g. merger/repoLens)
    # If we are in 'merger/repoLens', the hub is likely two levels up.
    if hub_dir.name == "repoLens" and hub_dir.parent.name == "merger":
        # Propose grandparent as default if we are deep in the structure
        hub_dir = hub_dir.parent.parent

    # If UI is available, let the user pick explicitly
    if dialogs:
        if console:
            try:
                console.hud_alert("Select Hub Folder...", "system", 1.0)
            except Exception:
                pass

        # Use pick_document with folder type for stability in Pythonista
        selected = dialogs.pick_document(types=['public.folder'])
        if selected:
            hub_dir = Path(selected).resolve()
        else:
            # User cancelled, inform them
            msg = "Selection cancelled. Using detected path."
            print(msg)

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
        msg = f"Saved hub path:\n{hub_dir}\n\n→ {out_file.name}"
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
