#!/bin/bash
set -euo pipefail

# Canonical rLens Launcher (Systemd Wrapper)
# Wraps systemctl with health checks to prevent "silent failure" false positives.
# This script is intended to be installed as ~/.local/bin/rlens.

HOST=${RLENS_HOST:-127.0.0.1}
PORT=${RLENS_PORT:-8787}

# 1. Start Service
echo "[rlens] Starting service via systemd..."
systemctl --user start rlens

# 2. Wait for Health (Retry Loop)
echo "[rlens] Waiting for health check at http://${HOST}:${PORT}/health ..."
MAX_RETRIES=10
for ((i=1; i<=MAX_RETRIES; i++)); do
    # Try connecting. -s=silent, -f=fail on error (4xx/5xx)
    if curl -sf "http://${HOST}:${PORT}/health" >/dev/null; then
        echo "[rlens] Service is HEALTHY."
        echo "[rlens] URL: http://${HOST}:${PORT}"
        exit 0
    fi
    sleep 0.5
done

# 3. Failure Handler
echo "[rlens] ERROR: Health check failed after startup." >&2
echo "[rlens] Dumping status and recent logs:" >&2
systemctl --user status rlens --no-pager >&2 || true
journalctl --user -u rlens -n 50 --no-pager >&2 || true
exit 1
