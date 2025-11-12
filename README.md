# Tools – Index

Kurzüberblick über Ordner:
- `scripts/` – wiederverwendbare Helfer
- `repomergers/` – Repo-Zusammenführungen
- `ordnermergers/` – Ordner-Zusammenführungen

## Nutzung (Beispiele)

Minimale Befehle, um die verfügbaren Werkzeuge aufzurufen:

```bash
bash scripts/jsonl-validate.sh --help
bash scripts/jsonl-tail.sh --help
```

Weitere Details zu den einzelnen Werkzeugen findest du in den jeweiligen README-Dateien oder mittels der `--help`-Optionen.

## JSONL Tools
- `scripts/jsonl-validate.sh` – prüft NDJSON (eine JSON-Entität pro Zeile) gegen ein JSON-Schema (AJV v5).
- `scripts/jsonl-tail.sh`
- `scripts/jsonl-compact.sh`
