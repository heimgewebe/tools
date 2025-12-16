#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys

# Visual cue for user to verify they are running the fixed version
print("repoLens Pathfinder (Fixed Version)")

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
    # Default fallback: CWD (Place-and-run workflow)
    hub_dir = Path.cwd().resolve()

    # Heuristic: If we are in 'merger/repoLens', the hub is likely two levels up.
    if hub_dir.name == "repoLens" and hub_dir.parent.name == "merger":
        hub_dir = hub_dir.parent.parent

    # If UI is available, ask the user what to do
    if dialogs and console:
        try:
            # Ask user: Use detected path (CWD) or pick manually?
            choice = console.alert(
                "repoLens Setup",
                f"Current Directory:\n{hub_dir.name}\n\nUse this as Hub?",
                "Use Current",
                "Pick Folder...",
                hide_cancel_button=True
            )

            if choice == 2:  # "Pick Folder..."
                # Use pick_document with file_mode=False for folder picking
                # Wrapped in try/except because some Pythonista versions/contexts are picky
                try:
                    selected = dialogs.pick_document(file_mode=False)
                    if selected:
                        hub_dir = Path(selected).resolve()
                    else:
                        print("Selection cancelled. Keeping detected path.")
                except Exception as e:
                    console.alert("Picker Error", f"{e}", "OK", hide_cancel_button=True)
                    print(f"Picker Error: {e}")
        except Exception:
            # Fallback if alert fails (e.g. background run)
            pass

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
