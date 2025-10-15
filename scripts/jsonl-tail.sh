#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE >&2
Usage: $(basename "$0") [-n <lines>] <file.jsonl>

Pretty-print the last N entries of a JSON Lines file using jq.
USAGE
  exit 1
}

lines=10

while getopts ":n:h" opt; do
  case "$opt" in
    n)
      if [[ -z "$OPTARG" || ! "$OPTARG" =~ ^[0-9]+$ ]]; then
        echo "-n requires a positive integer" >&2
        usage
      fi
      lines=$OPTARG
      ;;
    h)
      usage
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      usage
      ;;
    \?)
      echo "Unknown option: -$OPTARG" >&2
      usage
      ;;
  esac
done

shift $((OPTIND - 1))

if [[ $# -ne 1 ]]; then
  usage
fi

file=$1

if [[ ! -f "$file" ]]; then
  echo "File not found: $file" >&2
  exit 1
fi

tail -n "$lines" "$file" | jq -R 'select(length > 0) | fromjson'
