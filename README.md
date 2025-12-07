# Tools – Index

Kurzüberblick über Ordner:
- `scripts/` – wiederverwendbare Helfer
- `repomerger/` – Repo-Zusammenführungen
- `ordnermerger/` – Ordner-Zusammenführungen

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

## Organismus-Kontext

Dieses Repository ist Teil des **Heimgewebe-Organismus**.

Die übergeordnete Architektur, Achsen, Rollen und Contracts sind zentral beschrieben im  
👉 [`metarepo/docs/heimgewebe-organismus.md`](https://github.com/heimgewebe/metarepo/blob/main/docs/heimgewebe-organismus.md)  
👉 [`metarepo/docs/heimgewebe-zielbild.md`](https://github.com/heimgewebe/metarepo/blob/main/docs/heimgewebe-zielbild.md).

Alle Rollen-Definitionen, Datenflüsse und Contract-Zuordnungen dieses Repos
sind dort verankert.
