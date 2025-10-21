# Heimgewebe-Merger (Org-Überblick mit Crosslinks)

Mergt **alle öffentlichen Repos** der Orga `heimgewebe` in **gesplittete Markdown-Dossiers**,
mit zusätzlichem **Index** und **Cross-Repo-Analyse**.

## Scope
- **Ausgeschlossen**: `vault-gewebe`, `vault-privat`, `weltgewebe` (anpassbar via `EXCLUDES_CSV`).
- Typische Code-/Doku-Dateien werden inkludiert; große/binäre Artefakte werden übersprungen.
- Splits bei Erreichen eines konfigurierbaren Byte-Limits.

## Output
- `dossier-part-XXXX.md` – Gesamtsicht in Häppchen (GPT-Upload-freundlich)
- `index.md` – Kennzahlen pro Repo (Dateien, MB, grobe Sprachverteilung per Dateiendung)
- `crosslinks.md` – Textuelle Bezüge zwischen Repos (Fundstellen/Counts)
- `crosslinks.mmd` – Mermaid Graph (kann in Markdown-Viewer gerendert werden)

## Voraussetzungen
- `bash`, `python3`, `git`, `gh` (GitHub CLI, eingeloggt; read-only reicht)

## Quickstart
```bash
bash repomergers/heimgewebe-merge/run.sh out/heimgewebe-dossier
```

## Nützliche ENV-Schalter
```bash
# Nur bestimmte Repos (Komma-Liste)
ONLY="hausKI,leitstand" bash repomergers/heimgewebe-merge/run.sh out/hgw

# Byte-Limit je Part (Default 5 MiB)
MAX_BYTES=$((8*1024*1024)) bash repomergers/heimgewebe-merge/run.sh out/hgw

# Exclude-Liste ergänzen/ändern
EXCLUDES_CSV="vault-gewebe,vault-privat,weltgewebe,foo" bash repomergers/heimgewebe-merge/run.sh out/hgw

# Muster für Inklusion (Komma-Liste, Glob)
GLOBS="README.md,docs/**,**/*.md,**/*.rs,**/*.py,**/*.ts,**/*.svelte,**/*.sh" \
  bash repomergers/heimgewebe-merge/run.sh out/hgw
```

## Hinweise
- Reihenfolge ist kuratiert: Kern-Repos zuerst, Rest alphabetisch.
- Crosslinks basieren auf Repo-Namens-Erwähnungen im Text (heuristisch, schnell und offline).
