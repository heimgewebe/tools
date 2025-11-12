#!/usr/bin/env bash
set -euo pipefail
in="${1:-}"; out="${2:-/dev/stdout}"
[[ -n "$in" && -f "$in" ]] || { echo "usage: jsonl-compact.sh <input-file> [output-file]" >&2; exit 2; }
while IFS= read -r ln || [[ -n "$ln" ]]; do
 [[ -n "${ln//[[:space:]]/}" ]] || continue
 printf '%s\n' "$ln" | tr -d '\r' | jq -c . || { echo "bad json line" >&2; exit 1; }
done < "$in" > "$out"
