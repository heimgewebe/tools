#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc-merger – Entry point.
Detects environment (CLI vs iOS/Pythonista) and delegates to appropriate implementation.
"""

import sys
import os
from pathlib import Path

# Detect headless request
def _is_headless_requested() -> bool:
    return ("--headless" in sys.argv) or (os.environ.get("WC_HEADLESS") == "1")

# Check for Pythonista environment
try:
    import ui
    import appex
    HAS_UI = True
except ImportError:
    HAS_UI = False
    ui = None
    appex = None
except Exception:
    # Some environments might raise other exceptions on import
    HAS_UI = False
    ui = None
    appex = None

def main():
    # Helper to resolve imports if running from symlink or weird context
    script_dir = str(Path(__file__).resolve().parent)
    if script_dir not in sys.path:
        sys.path.append(script_dir)

    use_ui = (
        HAS_UI
        and not _is_headless_requested()
        and (appex is None or not appex.is_running_extension())
    )

    if use_ui:
        try:
            from ui_ios import run_ui
            from core import detect_hub_dir
            hub = detect_hub_dir(Path(__file__).resolve())
            return run_ui(hub)
        except Exception as e:
            # Fallback to CLI if UI fails to load/run
            try:
                import console
                console.alert("wc-merger", f"UI unavailable: {e}", "OK", hide_cancel_button=True)
            except Exception:
                print(f"wc-merger: UI unavailable ({e}), falling back to CLI.", file=sys.stderr)

            from cli import main_cli
            main_cli()
    else:
        from cli import main_cli
        main_cli()

if __name__ == "__main__":
    main()
