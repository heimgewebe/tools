#!/usr/bin/env bash
set -euo pipefail
usage() {
 cat <<USAGE
jsonl-validate.sh

Validates every non-empty line as standalone JSON object against a JSON Schema (draft 2020-12).
Requires: node + npx (ajv-cli@5)
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
CMD="npx --yes ajv-cli@5 validate --spec=draft2020 --all-errors"
[[ "$STRICT" == "true" ]] && CMD="$CMD --strict=true" || CMD="$CMD --strict=false"
[[ "$FORMATS" == "true" ]] && CMD="$CMD --validate-formats=true" || CMD="$CMD --validate-formats=false"
shopt -s nullglob
mapfile -t FILES < <(compgen -G "$PATTERN" || true)
(( ${#FILES[@]} )) || { echo "no files match: $PATTERN" >&2; exit 1; }
fails=0
for f in "${FILES[@]}"; do
 echo "==> $f"
 line=0
 while IFS= read -r ln || [[ -n "$ln" ]]; do
 line=$((line+1))
 [[ -n "${ln//[[:space:]]/}" ]] || continue
 tmp="$(mktemp -t ajv-XXXX.json)"; printf '%s\n' "$ln" >"$tmp"
 if ! bash -c "$CMD -s \"$SCHEMA\" -d \"$tmp\" >/dev/null"; then
 echo "::error file=$f,line=$line::validation failed"
 fails=1
 fi
 rm -f "$tmp"
 done < "$f"
done
exit $fails
