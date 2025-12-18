#!/usr/bin/env python3
"""
rLens Service Entry Point (formerly repolensd)

Usage:
  export RLENS_TOKEN=heimgewebe-local
  python3 service/rlens.py --hub /home/alex/repos --host 127.0.0.1 --port 8787 --open

This script exists to:
- Provide a stable CLI to start the web UI.
- Bind hub path + auth token into the service state at startup.
"""

from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from pathlib import Path

import uvicorn

# Ensure we can import 'service' package
# Since this script is in service/rlens.py, we need parent dir in sys.path
# to allow 'from service.app import ...' and internal service imports to work.
SCRIPT_DIR = Path(__file__).resolve().parent
PARENT_DIR = SCRIPT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

try:
    from service.app import app, init_service
except ImportError:
    # Fallback/Safety
    sys.path.append(str(PARENT_DIR))
    from service.app import app, init_service


def _is_loopback_host(host: str) -> bool:
    h = (host or "").strip().lower()
    return h in ("127.0.0.1", "localhost", "::1")


def run(host: str, port: int, hub: str | None, token: str | None, open_browser: bool = False, merges: str | None = None) -> None:
    hub_path = None
    if hub:
        hub_path = Path(hub).expanduser().resolve()
        if not hub_path.exists():
            raise SystemExit(f"[rlens] hub path does not exist: {hub_path}")
        if not hub_path.is_dir():
            raise SystemExit(f"[rlens] hub path is not a directory: {hub_path}")

    merges_path = None
    if merges:
        merges_path = Path(merges).expanduser().resolve()
        if not merges_path.exists():
            try:
                merges_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise SystemExit(f"[rlens] output/merges path could not be created: {merges_path} ({e})")

    # Safety: Enforce token for non-loopback hosts
    if not _is_loopback_host(host) and not token:
        raise SystemExit("[rlens] refusing to bind non-loopback host without token. Set --token or RLENS_TOKEN.")

    init_service(hub_path=hub_path, token=token, merges_dir=merges_path)

    url = f"http://{host}:{port}"
    if open_browser:
        try:
            webbrowser.open(url, new=2)
        except Exception:
            # non-fatal
            pass

    print(f"[rlens] serving on {url}", flush=True)
    print(f"[rlens] hub: {hub_path if hub_path else '(not set)'}", flush=True)
    print(f"[rlens] output: {merges_path if merges_path else '(default: hub/merges)'}", flush=True)
    print(f"[rlens] token: {'(set)' if token else '(not set)'}", flush=True)

    if hub_path:
        # Diagnostic: Check for git repos to detect "wrong folder" issues early
        try:
            repos = [p for p in hub_path.iterdir() if p.is_dir() and (p / ".git").exists()]
            print(f"[rlens] hub repos (git): {len(repos)}", flush=True)
        except Exception as e:
            print(f"[rlens] hub scan warning: {e}", flush=True)

    uvicorn.run(app, host=host, port=port, log_level="info")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="rlens.py")
    p.add_argument("--host", default=os.environ.get("RLENS_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.environ.get("RLENS_PORT", "8787")))
    p.add_argument("--hub", "--input", dest="hub", default=os.environ.get("RLENS_HUB"), help="Input Hub Directory")
    p.add_argument("--merges", "--output", dest="merges", default=os.environ.get("RLENS_MERGES"), help="Output Directory for Reports")
    p.add_argument("--token", default=os.environ.get("RLENS_TOKEN"))
    p.add_argument("--open", action="store_true", help="open browser after start")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(sys.argv[1:] if argv is None else argv)
    run(host=ns.host, port=ns.port, hub=ns.hub, token=ns.token, open_browser=ns.open, merges=ns.merges)
    return 0


# Adapter for repolens.py compatibility (if needed, but imports need update)
def run_server(hub_path: Path, host: str, port: int, open_browser: bool = False, token: str = None):
    run(host=host, port=port, hub=str(hub_path) if hub_path else None, token=token, open_browser=open_browser)


if __name__ == "__main__":
    raise SystemExit(main())
