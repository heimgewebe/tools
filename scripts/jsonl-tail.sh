#!/usr/bin/env bash
set -euo pipefail
file="${1:-}"
limit="${2:-50}"
[[ -n "$file" && -f "$file" ]] || { echo "usage: jsonl-tail.sh <file> [limit]" >&2; exit 2; }
awk 'NF' "$file" | tail -n "$limit"
