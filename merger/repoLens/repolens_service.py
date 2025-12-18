import sys
import webbrowser
import os
from pathlib import Path

# When running from repolens.py, the merger/repoLens dir is in sys.path.
# 'service' is a subdirectory there.
try:
    from service.app import app, init_service
except ImportError:
    # Fallback if running as a package
    from .service.app import app, init_service

def run_server(hub_path: Path, host: str, port: int, open_browser: bool = False, token: str = None):
    """
    Entry point to run the FastAPI service.
    """
    try:
        import uvicorn
    except ImportError:
        print("Error: 'uvicorn' is required to run the server.")
        print("Please install it: pip install uvicorn fastapi pydantic")
        sys.exit(1)

    # Check env for token if not passed
    if not token:
        token = os.environ.get("REPOLENS_TOKEN")

    print(f"Starting repoLens Service on http://{host}:{port}")
    print(f"Hub: {hub_path}")
    if token:
        print("🔒 Security: Token Authentication Enabled")
    else:
        print("⚠️ Security: No Token configured (open access)")

    # Initialize global state
    init_service(hub_path, token=token)

    if open_browser:
        webbrowser.open(f"http://{host}:{port}")

    # Run uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")
