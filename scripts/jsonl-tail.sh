#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
jsonl-tail.sh [-n <lines>] <file>

Pretty-print the last entries of a JSON Lines file.

Options:
  -n, --lines <lines>  Number of lines to display (default: 10)
  -h, --help           Show this help message
USAGE
}

lines=10
file=""

while (($#)); do
  case "$1" in
    -n|--lines)
      shift
      [[ $# -gt 0 ]] || { echo "Missing value for $1" >&2; usage >&2; exit 2; }
      lines="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      if [[ -z "$file" ]]; then
        file="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
  shift || true
done

[[ -n "$file" ]] || { echo "Missing JSONL file path" >&2; usage >&2; exit 2; }
[[ -f "$file" ]] || { echo "File not found: $file" >&2; exit 2; }
command -v jq >/dev/null || { echo "jq required" >&2; exit 127; }

awk 'NF' "$file" | tail -n "$lines" | while IFS= read -r ln; do
  printf '%s\n' "$ln" | jq .
done
