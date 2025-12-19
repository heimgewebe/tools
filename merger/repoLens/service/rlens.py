#!/usr/bin/env python3
"""
rLens Service Entry Point (Canonical)
"""
import os
import sys
import argparse
from pathlib import Path
import uvicorn

# Ensure correct path for imports if run as script
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from service.app import app, init_service

def main():
    parser = argparse.ArgumentParser(prog="rlens")
    parser.add_argument("--host", default=os.environ.get("RLENS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("RLENS_PORT", "8787")))
    parser.add_argument("--hub", default=os.environ.get("RLENS_HUB"))
    parser.add_argument("--merges", default=os.environ.get("RLENS_MERGES"))
    parser.add_argument("--token", default=os.environ.get("RLENS_TOKEN"))
    parser.add_argument("--open", action="store_true", help="open browser after start (legacy flag, ignored)")

    args = parser.parse_args()

    hub_path = Path(args.hub or os.environ.get("RLENS_HUB", "/home/alex/repos"))
    token = args.token or os.environ.get("RLENS_TOKEN", "heimgewebe-local")
    merges_path = Path(args.merges) if args.merges else None

    # Initialize the ONE app instance
    init_service(
        hub_path=hub_path,
        token=token,
        host=args.host,
        merges_dir=merges_path
    )

    print(f"[rlens] serving on http://{args.host}:{args.port}", flush=True)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )

if __name__ == "__main__":
    main()
