# all-ein-wandler – Zweck & Funktion

## Zweck

Der all-ein-wandler dient als universelles Werkzeug, um Ordner mit beliebigen Dateien (Text, PDFs, Bilder, Office-Dateien usw.) in eine einheitliche, KI-freundliche Textform zu überführen.
Der Fokus: schnelle, kompakte, maschinenlesbare Zusammenfassungen, die auf iPad und Pythonista problemlos funktionieren.

Das Tool ist speziell darauf ausgelegt, Inhalte aus Unterricht, Projekten, Recherche oder Dokumenten aller Art so aufzubereiten, dass sie unmittelbar von KI-Systemen verarbeitet, durchsucht oder analysiert werden können.

## Funktion

### 1. Wandler-Hub Workflow (Standardmodus auf iPad)

Der all-ein-wandler arbeitet im Standardfall vollautomatisch im Verzeichnis:

Auf meinem iPad / Pythonista 3 / `wandler-hub`

Ablauf:
1.  Im Ordner `wandler-hub` liegt genau ein Ordner, der gewandelt werden soll
    (z. B. ein exportierter Schulordner, Unterlagen, Dokumente, Fotos usw.).
2.  Das Script erkennt automatisch den zuletzt geänderten Unterordner (außer `wandlungen`).
3.  Der Inhalt dieses Ordners wird vollständig zu einer
    Markdown-Datei + JSON-Manifest verarbeitet.
4.  Das Ergebnis landet im Zielordner:

    `wandler-hub/wandlungen`

5.  Nach erfolgreicher Wandlung:
    - Der gewandelte Quellordner wird automatisch gelöscht.
    - Im Ordner `wandlungen` bleiben stets nur die letzten 5 Wandlungen bestehen
      (ältere Versionen werden automatisch entfernt).

Damit eignet sich der Workflow ideal für iPad-Shortcuts („Ordner auswählen → wandeln → löschen → fertig“).

### 2. Direkter Aufruf mit Pfad (CLI/AEW_SOURCE)

Wenn du das Tool manuell oder mit einer expliziten Quelle startest – z. B. durch:

```bash
python3 all_ein_wandler.py --source-dir /Pfad/zum/Ordner
export AEW_SOURCE=/Pfad
```

…dann gilt:
- Kein Auto-Löschen
- Kein „nur letzte 5 behalten“
- Zielordner = Elternordner der Quelle
- Verhalten entspricht der klassischen, sicheren Nutzung

Damit ist der all-ein-wandler sowohl ein One-Tap iPad Tool
als auch ein Präzisionswerkzeug für Desktop-Workflows.

### 3. Ausgabeformat

Der Wandler erzeugt zwei Dateien:
1.  `<name>_all-ein_<timestamp>.md`
    – enthält die gesamte lesbare Information
    – inkl. Ordnerstruktur, Kategorien, Inhalte, OCR-Texte (falls konfiguriert)
2.  `<name>_all-ein_<timestamp>.manifest.json`
    – maschinenlesbare Metadaten
    – Dateiliste, Kategorien, Checksummen, OCR-Status, Chunk-Informationen

Beides ist optimal auf KI-Systeme abgestimmt.

### 4. OCR-Integration

OCR ist optional und kann genutzt werden über:
- iOS Shortcuts
- Tesseract (falls installiert)

Konfiguration:

`~/.config/all-ein-wandler/config.toml`

## Kurzfassung
- Ordner rein → ein vollständiger, KI-geeigneter Textdump raus
- Automatischer Hub-Modus auf iPad (Quellordner löschen, nur letzte 5 behalten)
- Manuelle Nutzung optional ohne Auto-Löschen
- PDFs, Bilder, Office-Dateien → werden bestmöglich extrahiert
- Markdown + JSON → optimale Weitergabe an KI-Systeme
