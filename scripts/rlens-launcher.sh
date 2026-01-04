#!/bin/bash
set -euo pipefail

# Canonical rLens Launcher (Systemd Wrapper)
# Wraps systemctl with robust health checks.
# Intended to be installed as ~/.local/bin/rlens.

HOST=${RLENS_HOST:-127.0.0.1}
PORT=${RLENS_PORT:-8787}
URL="http://${HOST}:${PORT}"

# 1. Start Service
echo "[rlens] Starting service via systemd..."
systemctl --user start rlens

# Check if unit is actually active (fast fail)
if ! systemctl --user is-active --quiet rlens; then
    echo "[rlens] Warning: Service unit is not active immediately after start." >&2
fi

# 2. Wait for Health (Retry Loop)
# 30 retries * 0.5s = ~15s timeout (generous for python imports on slow machines)
echo "[rlens] Waiting for health check at ${URL}/health ..."
MAX_RETRIES=30
for ((i=1; i<=MAX_RETRIES; i++)); do
    if curl -sf "${URL}/health" >/dev/null; then
        echo "[rlens] Service is HEALTHY."
        echo "[rlens] URL: ${URL}"

        # Optional: Open Browser
        if command -v xdg-open >/dev/null; then
            echo "[rlens] Opening browser..."
            xdg-open "${URL}" || true
        fi

        exit 0
    fi
    sleep 0.5
done

# 3. Failure Handler
echo "[rlens] ERROR: Health check failed after startup (${MAX_RETRIES} attempts)." >&2
echo "[rlens] Dumping diagnostic info:" >&2

echo "--- Unit Status ---" >&2
systemctl --user status rlens --no-pager >&2 || true

echo "--- Unit Definition ---" >&2
systemctl --user cat rlens >&2 || true

echo "--- Recent Logs ---" >&2
journalctl --user -u rlens -n 50 --no-pager >&2 || true

exit 1
