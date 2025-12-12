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
