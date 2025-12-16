# OmniWandler

**Der "Alles-in-einen-Topf" Wandler für generische Ordner.**

## 🎯 Zweck

Der **OmniWandler** (ehemals all-ein-wandler) ist das Gegenstück zum `repoLens`. Während `repoLens` für Code-Repositories optimiert ist, kümmert sich der `OmniWandler` um **Inhalts-Ordner**:

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
- **Smarte Pfad-Erkennung:** Findet den `wandler-hub` auch wenn das Skript verschoben wurde.

## 🚀 Nutzung

### 1. Pythonista (iPad) - Hub Modus (Empfohlen)

1.  Erstelle (oder lass erstellen) den Ordner `wandler-hub` in deinen Pythonista-Dokumenten (oder nutze die UI, um ihn auszuwählen).
2.  Lege einen Ordner, den du konvertieren willst, dort hinein.
3.  Starte `omniwandler.py`.
4.  Wähle den Ordner in der Liste aus.
5.  Ergebnis landet in `wandler-hub/wandlungen`.

### 2. CLI / Desktop

```bash
# Einen spezifischen Ordner wandeln (Ausgabe im Elternverzeichnis)
python3 merger/omniwandler/omniwandler.py /Pfad/zum/Ordner

# Via Environment Variable
export OMNIWANDLER_SOURCE="/Pfad/zum/Ordner"
python3 merger/omniwandler/omniwandler.py
```

## ⚙️ Konfiguration

Erstelle `~/.config/omniwandler/config.toml` (optional):

```toml
[general]
max_file_bytes = 10485760   # 10 MB Limit für Textdateien

[ocr]
backend = "shortcut"        # "none" oder "shortcut"
shortcut_name = "OmniWandler OCR" # Name des iOS Shortcuts
```

## 🤖 Unterschied zu `repoLens`

| Feature | `OmniWandler` | `repoLens` |
| :--- | :--- | :--- |
| **Ziel** | Dokumente, PDFs, Bilder, Notizen | Code-Repositories, Software-Projekte |
| **Output** | Fokus auf Lesbarkeit & Content | Fokus auf Struktur, Diff & Code-Kontext |
| **OCR** | Ja (via Shortcuts) | Nein (nur Text) |
| **Filter** | Ignoriert Code-Noise (node_modules) | Strikte `.gitignore` & Profil-Logik |
| **Modus** | Hub-Verarbeitung (Löschen nach Erfolg) | Non-destructive (Liest nur) |
