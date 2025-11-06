#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-out/heimgewebe-dossier}"
ORG="heimgewebe"
# Vaults + Weltgewebe pauschal raus:
EXCLUDES_CSV="${EXCLUDES_CSV:-vault-gewebe,vault-privat,weltgewebe}"
ONLY="${ONLY:-}"                               # optional: "repo1,repo2"
MAX_BYTES="${MAX_BYTES:-$((5 * 1024 * 1024))}" # 5 MiB Default
GLOBS="${GLOBS:-README.md,docs/**,**/*.md,**/*.rs,**/*.py,**/*.ts,**/*.tsx,**/*.js,**/*.svelte,**/*.sh,**/*.bash,**/*.fish,**/*.zsh,**/*.sql,**/*.yml,**/*.yaml,**/*.toml}"
BINARY_CUTOFF="${BINARY_CUTOFF:-262144}" # 256 KiB
WORK="${WORK:-.git/tmp/heimgewebe-merge}"

need() { command -v "$1" >/dev/null 2>&1 || {
	echo "Fehlt: $1" >&2
	exit 127
}; }
need git
need gh
need python3

mkdir -p "$OUT_DIR" "$WORK"

echo "• Liste Repos aus ORG '$ORG'…"
mapfile -t ALL < <(gh repo list "$ORG" --limit 200 --json name,isPrivate --jq '.[] | select(.isPrivate|not) .name')

IFS=',' read -r -a EX_ARR <<<"$EXCLUDES_CSV"
declare -A EX_SET
for e in "${EX_ARR[@]}"; do EX_SET["$e"]=1; done

# Kuratierte Reihenfolge zuerst
preferred=(metarepo wgx hausKI semantAH leitstand aussensensor heimlern)
declare -A PSET
for p in "${preferred[@]}"; do PSET["$p"]=1; done

# Filtern
sel=()
for r in "${ALL[@]}"; do
	[[ -n "${EX_SET[$r]:-}" ]] && continue
	sel+=("$r")
done

# ONLY anwenden (falls gesetzt)
if [[ -n "$ONLY" ]]; then
	IFS=',' read -r -a only_arr <<<"$ONLY"
	tmp=()
	for o in "${only_arr[@]}"; do
		for r in "${sel[@]}"; do
			[[ "$r" == "$o" ]] && tmp+=("$r")
		done
	done
	sel=("${tmp[@]}")
fi

# sortiere: preferred in angegebener Reihenfolge, Rest alphabetisch dahinter
ordered=()
for p in "${preferred[@]}"; do
	for r in "${sel[@]}"; do [[ "$r" == "$p" ]] && ordered+=("$r"); done
done
rest=()
for r in "${sel[@]}"; do [[ -z "${PSET[$r]:-}" ]] && rest+=("$r"); done
IFS=$'\n' rest_sorted=($(printf "%s\n" "${rest[@]}" | sort))
ordered+=("${rest_sorted[@]}")

echo "• Ausgewählt: ${#ordered[@]} Repos"
echo "• Excludes: ${EXCLUDES_CSV}"
python3 "$(dirname "$0")/merge.py" \
	--org "$ORG" \
	--repos "${ordered[@]}" \
	--out "$OUT_DIR" \
	--max-bytes "$MAX_BYTES" \
	--globs "$GLOBS" \
	--binary-cutoff "$BINARY_CUTOFF" \
	--work "$WORK"

echo "✓ Fertig. Outputs in: $OUT_DIR"
