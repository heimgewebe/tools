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

## `parse_icf_who.py`

Backfill WHO ICF descriptions from a plain-text source (`data/ifc-who.txt`) into the JSON databases `data/icf-complete-full.json` and `data/icf_codes_complete.json`.

```bash
python scripts/parse_icf_who.py \
  --who-file data/ifc-who.txt \
  --full-json data/icf-complete-full.json \
  --codes-json data/icf_codes_complete.json
```

Use `--overwrite` to replace existing `who_description` fields; by default only missing descriptions are filled. The script is tolerant to either dict- or list-based JSON layouts and writes the updated datasets back to disk.
