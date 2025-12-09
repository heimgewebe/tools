# Tools – Index

Kurzüberblick über Ordner:
- `scripts/` – wiederverwendbare Helfer
- `merger/` – Merge- und Extraktions-Tools
  - `repo-merger/` – Text-basierter Repository/Code-Merger
  - `folder-extractor/` – Universeller Ordner-zu-Text-Konverter
  - `wc-merger/` – Working-Copy Merger (Heimgewebe)
  - `repomerger/` – Repo-Zusammenführungen (legacy)
  - `ordnermerger/` – Ordner-Zusammenführungen (legacy)

## Nutzung (Beispiele)

Minimale Befehle, um die verfügbaren Werkzeuge aufzurufen:

```bash
bash scripts/jsonl-validate.sh --help
bash scripts/jsonl-tail.sh --help

# Merger Tools
python3 merger/repo-merger/repo_merger.py --help
python3 merger/folder-extractor/folder_extractor.py --help
```

Weitere Details zu den einzelnen Werkzeugen findest du in den jeweiligen README-Dateien oder mittels der `--help`-Optionen.

## Merger Tools

### repo-merger
Text-basierter Repository/Code-Merger für KI-Kontext. Fokus auf Code, Dokumentation und Konfigurationsdateien.

```bash
# Repository zusammenführen
python3 merger/repo-merger/repo_merger.py --root . --level max --out merged_repo.md

# Verschiedene Levels: overview, summary, dev, max
python3 merger/repo-merger/repo_merger.py --level dev
```

📖 Siehe [merger/repo-merger/README.md](merger/repo-merger/README.md) für Details.

### folder-extractor
Universeller Ordner-zu-Text-Konverter. Extrahiert Text aus PDFs, Bildern, Office-Dokumenten und mehr.

```bash
# Ordner extrahieren
python3 merger/folder-extractor/folder_extractor.py --root /path/to/folder --out dump.md

# Mit PDF/OCR-Support (benötigt zusätzliche Pakete)
pip install PyPDF2 pdfplumber pytesseract python-docx python-pptx openpyxl
```

📖 Siehe [merger/folder-extractor/README.md](merger/folder-extractor/README.md) für Details.

**Unterschied:**
- `repo-merger`: Für Code-Repositories (nur Text)
- `folder-extractor`: Für beliebige Ordner (PDFs, Bilder, Office)

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
