### 📄 scripts/README.md

**Größe:** 705 B | **md5:** `8b5fd3bbea862544e86d1553b30fec6d`

```markdown
# JSONL helper scripts

## `jsonl-validate.sh`

Validate a JSON Lines file against a JSON Schema using [`ajv-cli`](https://github.com/ajv-validator/ajv-cli).

```bash
scripts/jsonl-validate.sh schema.json data.jsonl
```

This command will run `npx ajv-cli@5 validate -s schema.json -d data.jsonl` under the hood. Ensure `npx` is available (provided by Node.js) so that the Ajv CLI can be downloaded on demand.

## `jsonl-tail.sh`

Pretty-print the last entries of a JSON Lines file.

```bash
scripts/jsonl-tail.sh [-n <lines>] data.jsonl
```

The default is to display the last 10 entries. Increase or decrease the number of lines with `-n`. Each line is parsed and rendered through `jq` for readability.
```

### 📄 scripts/jsonl-tail.sh

**Größe:** 829 B | **md5:** `a4c79865b028b60ef8e6d5b7228725fb`

```bash
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
```

### 📄 scripts/jsonl-validate.sh

**Größe:** 913 B | **md5:** `c6119566db93c5306705a21dcab7b09d`

```bash
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
```

