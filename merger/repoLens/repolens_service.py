#!/usr/bin/env python3
"""
RepoLens Service Entry Point

Usage (preferred):
  export REPOLENS_TOKEN=heimgewebe-local
  python3 repolens_service.py --hub /home/alex/repos --host 127.0.0.1 --port 8787 --open

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

# Robust import for service.app
try:
    from service.app import app, init_service
except ImportError:
    # Fallback if running as a package or different context
    from .service.app import app, init_service


def _is_loopback_host(host: str) -> bool:
    h = (host or "").strip().lower()
    return h in ("127.0.0.1", "localhost", "::1")


def run(host: str, port: int, hub: str | None, token: str | None, open_browser: bool = False) -> None:
    hub_path = None
    if hub:
        hub_path = Path(hub).expanduser().resolve()
        if not hub_path.exists():
            raise SystemExit(f"[repolens] hub path does not exist: {hub_path}")
        if not hub_path.is_dir():
            raise SystemExit(f"[repolens] hub path is not a directory: {hub_path}")

    # Safety: Enforce token for non-loopback hosts
    if not _is_loopback_host(host) and not token:
        raise SystemExit("[repolens] refusing to bind non-loopback host without token. Set --token or REPOLENS_TOKEN.")

    init_service(hub_path=hub_path, token=token)

    url = f"http://{host}:{port}"
    if open_browser:
        try:
            webbrowser.open(url, new=2)
        except Exception:
            # non-fatal
            pass

    print(f"[repolens] serving on {url}")
    if hub_path:
        print(f"[repolens] hub: {hub_path}")
        # Diagnostic: Check for git repos to detect "wrong folder" issues early
        try:
            repos = [p for p in hub_path.iterdir() if p.is_dir() and (p / ".git").exists()]
            print(f"[repolens] hub repos (git): {len(repos)}")
        except Exception as e:
            print(f"[repolens] hub scan warning: {e}")
    else:
        print("[repolens] hub: (not set)  -> set --hub or REPOLENS_HUB")

    if token:
        print("[repolens] token: (set)")
    else:
        print("[repolens] token: (not set) -> set REPOLENS_TOKEN")

    uvicorn.run(app, host=host, port=port, log_level="info")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="repolens_service.py")
    p.add_argument("--host", default=os.environ.get("REPOLENS_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.environ.get("REPOLENS_PORT", "8787")))
    p.add_argument("--hub", default=os.environ.get("REPOLENS_HUB"))
    p.add_argument("--token", default=os.environ.get("REPOLENS_TOKEN"))
    p.add_argument("--open", action="store_true", help="open browser after start")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(sys.argv[1:] if argv is None else argv)
    run(host=ns.host, port=ns.port, hub=ns.hub, token=ns.token, open_browser=ns.open)
    return 0


# Adapter for repolens.py compatibility
def run_server(hub_path: Path, host: str, port: int, open_browser: bool = False, token: str = None):
    run(host=host, port=port, hub=str(hub_path) if hub_path else None, token=token, open_browser=open_browser)


if __name__ == "__main__":
    raise SystemExit(main())
