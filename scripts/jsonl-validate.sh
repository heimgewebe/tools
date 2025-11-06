#!/usr/bin/env bash
set -euo pipefail

# Ensure non-interactive npx in CI and headless shells (npm>=7) and
# provide compatibility for older npm versions via the env var.
export npm_config_yes=${npm_config_yes:-true}

if [[ $# -lt 2 ]]; then
	cat <<USAGE >&2
Usage: $(basename "$0") <schema.json> <data.jsonl> [ajv options...]

Validate a JSON Lines file against a JSON Schema using ajv-cli.
USAGE
	exit 1
fi

schema=$1
shift
data_file=$1
shift

if [[ ! -f "$schema" ]]; then
	echo "Schema file not found: $schema" >&2
	exit 1
fi

if [[ ! -f "$data_file" ]]; then
	echo "Data file not found: $data_file" >&2
	exit 1
fi

if command -v ajv >/dev/null 2>&1; then
	ajv validate -s "$schema" -d "$data_file" "$@"
else
	# Non-interactive install/run. --yes avoids the "Need to install ..." prompt.
	# Pin ajv-cli major version for stability.
	npx --yes ajv-cli@5 validate -s "$schema" -d "$data_file" "$@"
fi
