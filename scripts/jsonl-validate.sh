#!/usr/bin/env bash
set -euo pipefail
usage() {
 cat <<USAGE
jsonl-validate.sh

Validates every non-empty line as standalone JSON object against a JSON Schema (draft 2020-12).
Requires: node + npm
USAGE
}
[[ $# -ge 2 ]] || { usage >&2; exit 2; }
PATTERN="$1"; SCHEMA="$2"; shift 2 || true
STRICT=false; FORMATS=true
while [[ $# -gt 0 ]]; do
 case "$1" in
 --strict) STRICT=true ;;
 --no-formats) FORMATS=false ;;
 -h|--help) usage; exit 0 ;;
 *) echo "Unknown flag: $1" >&2; usage >&2; exit 2 ;;
 esac
 shift
done

command -v node >/dev/null || { echo "node required" >&2; exit 127; }
command -v npm >/dev/null || { echo "npm required" >&2; exit 127; }

shopt -s nullglob
mapfile -t FILES < <(compgen -G "$PATTERN" || true)
(( ${#FILES[@]} )) || { echo "no files match: $PATTERN" >&2; exit 1; }

# Setup temporary environment for validation script
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

# Copy schema to work dir to avoid path issues
cp "$SCHEMA" "$WORK_DIR/schema.json"
SCHEMA_PATH="$WORK_DIR/schema.json"

# Create the JS validator script
cat <<'JS' > "$WORK_DIR/validate.js"
const fs = require('fs');
const Ajv2020 = require('ajv/dist/2020');
const addFormats = require('ajv-formats');

const schemaPath = process.argv[2];
const strictMode = process.argv[3] === 'true';
const validateFormats = process.argv[4] === 'true';
const files = process.argv.slice(5);

try {
    const schemaContent = fs.readFileSync(schemaPath, 'utf8');
    const schema = JSON.parse(schemaContent);

    const ajv = new Ajv2020({ allErrors: true, strict: strictMode });
    if (validateFormats) {
        addFormats(ajv);
    }
    const validate = ajv.compile(schema);

    let fails = 0;

    files.forEach(file => {
        console.log("==> " + file);
        try {
            const content = fs.readFileSync(file, 'utf8');
            const lines = content.split('\n');
            lines.forEach((line, index) => {
                if (!line.trim()) return;
                try {
                    const data = JSON.parse(line);
                    const valid = validate(data);
                    if (!valid) {
                        console.error(`::error file=${file},line=${index + 1}::validation failed`);
                        validate.errors.forEach(err => {
                             console.error(`  ${err.instancePath} ${err.message}`);
                        });
                        fails = 1;
                    }
                } catch (e) {
                    console.error(`::error file=${file},line=${index + 1}::invalid json: ${e.message}`);
                    fails = 1;
                }
            });
        } catch (e) {
             console.error(`::error file=${file}::could not read file: ${e.message}`);
             fails = 1;
        }
    });

    process.exit(fails);
} catch (e) {
    console.error("Fatal error:", e);
    process.exit(1);
}
JS

# Install dependencies quietly
pushd "$WORK_DIR" >/dev/null
# Initialize package.json to avoid warnings
echo '{}' > package.json
# Install ajv and ajv-formats
npm install --silent --no-audit --no-fund ajv ajv-formats >/dev/null 2>&1
popd >/dev/null

# Run the validation
NODE_PATH="$WORK_DIR/node_modules" node "$WORK_DIR/validate.js" "$SCHEMA_PATH" "$STRICT" "$FORMATS" "${FILES[@]}"
