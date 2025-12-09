# all-ein-wandler

**Der "Alles-in-einen-Topf" Wandler für generische Ordner.**

## 🎯 Zweck

Der **all-ein-wandler** ist das Gegenstück zum `wc-merger`. Während `wc-merger` für Code-Repositories optimiert ist, kümmert sich der `all-ein-wandler` um **Inhalts-Ordner**:

- Schulunterlagen / Studienmaterial
- Projektdokumente (PDFs, Word, Bilder)
- Rechnungssammlungen
- Gemischte Daten

Er konvertiert einen Ordner rekursiv in eine **einzelne Markdown-Datei** (+ JSON-Manifest), die perfekt für KI-Kontext-Fenster (ChatGPT, Claude, etc.) geeignet ist.

## ✨ Features

- **iOS First:** Optimierte UI für Pythonista auf dem iPad.
- **Hub-Workflow:** Wirf Ordner in `~/Documents/wandler-hub`, und das Tool verarbeitet sie automatisch.
- **OCR-Integration:** Nutzt iOS Shortcuts, um Text aus Bildern und (in Zukunft) PDFs zu extrahieren.
- **Binär-Handling:** Bilder und Medien werden erkannt und im Markdown referenziert (nicht als Buchstabensalat ausgegeben).
- **Auto-Cleanup:** Im Hub-Modus wird der Quellordner nach Erfolg gelöscht, um Speicherplatz zu sparen.

## 🚀 Nutzung

### 1. Pythonista (iPad) - Hub Modus (Empfohlen)

1.  Erstelle (oder lass erstellen) den Ordner `wandler-hub` in deinen Pythonista-Dokumenten.
2.  Lege einen Ordner, den du konvertieren willst, dort hinein.
3.  Starte `all_ein_wandler.py`.
4.  Wähle den Ordner in der Liste aus.
5.  Ergebnis landet in `wandler-hub/wandlungen`.

### 2. CLI / Desktop

```bash
# Einen spezifischen Ordner wandeln (Ausgabe im Elternverzeichnis)
python3 merger/all-ein-wandler/all_ein_wandler.py /Pfad/zum/Ordner

# Via Environment Variable
export AEW_SOURCE="/Pfad/zum/Ordner"
python3 merger/all-ein-wandler/all_ein_wandler.py
```

## ⚙️ Konfiguration

Erstelle `~/.config/all-ein-wandler/config.toml` (optional):

```toml
[general]
max_file_bytes = 10485760   # 10 MB Limit für Textdateien

[ocr]
backend = "shortcut"        # "none" oder "shortcut"
shortcut_name = "AllEin OCR" # Name des iOS Shortcuts
```

## 🤖 Unterschied zu `wc-merger`

| Feature | `all-ein-wandler` | `wc-merger` |
| :--- | :--- | :--- |
| **Ziel** | Dokumente, PDFs, Bilder, Notizen | Code-Repositories, Software-Projekte |
| **Output** | Fokus auf Lesbarkeit & Content | Fokus auf Struktur, Diff & Code-Kontext |
| **OCR** | Ja (via Shortcuts) | Nein (nur Text) |
| **Filter** | Ignoriert Code-Noise (node_modules) | Strikte `.gitignore` & Profil-Logik |
| **Modus** | Hub-Verarbeitung (Löschen nach Erfolg) | Non-destructive (Liest nur) |
