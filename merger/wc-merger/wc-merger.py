#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc-merger – Working-Copy Merger.
Enhanced AI-optimized reports with strict Pflichtenheft structure.

Entry point dispatcher.
"""

import sys
import os
from pathlib import Path

try:
    import appex
except Exception:
    appex = None

try:
    import ui
except Exception:
    ui = None

try:
    import console
except Exception:
    console = None

# Helper to determine headless mode (also used in cli.py but we need it here for dispatch)
def _is_headless_requested() -> bool:
    return ("--headless" in sys.argv) or (os.environ.get("WC_HEADLESS") == "1")

# Helper for script path
def safe_script_path() -> Path:
    try:
        return Path(__file__).resolve()
    except NameError:
        argv0 = None
        try:
            if getattr(sys, "argv", None):
                argv0 = sys.argv[0] or None
        except Exception:
            argv0 = None

        if argv0:
            try:
                return Path(argv0).resolve()
            except Exception:
                pass
        return Path.cwd().resolve()

SCRIPT_PATH = safe_script_path()
SCRIPT_DIR = SCRIPT_PATH.parent

# Ensure script dir is in path to find siblings
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

try:
    from core import detect_hub_dir
except ImportError:
    # Fallback if core is not yet importable directly (should not happen with sys.path append)
    from .core import detect_hub_dir

def main():
    # Dispatch logic:
    # 1. If running as App Extension (Share Sheet) -> CLI mode usually, or specialized UI.
    #    (wc-merger is often used as a tool inside Pythonista app, not as a share extension)
    # 2. If --headless or WC_HEADLESS=1 -> CLI mode.
    # 3. If ui module is missing -> CLI mode.
    # 4. Otherwise -> UI mode.

    use_ui = (
        ui is not None
        and not _is_headless_requested()
        and (appex is None or not appex.is_running_extension())
    )

    if use_ui:
        try:
            # Import UI module only if needed
            import ui_ios
            hub = detect_hub_dir(SCRIPT_PATH)
            return ui_ios.run_ui(hub)
        except Exception as e:
            # Fallback to CLI if UI launch fails
            if console:
                try:
                    console.alert(
                        "wc-merger",
                        f"UI not available, falling back to CLI. ({e})",
                        "OK",
                        hide_cancel_button=True,
                    )
                except Exception:
                    pass
            else:
                print(
                    f"wc-merger: UI not available, falling back to CLI. ({e})",
                    file=sys.stderr,
                )

            import cli
            cli.main_cli()
    else:
        import cli
        cli.main_cli()

if __name__ == "__main__":
    main()
