#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  cat <<USAGE >&2
Usage: $(basename "$0") <schema.json> <data.jsonl>

Validate a JSON Lines file against a JSON Schema using ajv-cli.
USAGE
  exit 1
fi

schema=$1
data_file=$2

if [[ ! -f "$schema" ]]; then
  echo "Schema file not found: $schema" >&2
  exit 1
fi

if [[ ! -f "$data_file" ]]; then
  echo "Data file not found: $data_file" >&2
  exit 1
fi

npx ajv-cli@5 validate -s "$schema" -d "$data_file"
