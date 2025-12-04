# wc-merger (Working Copy Merger)

Der `wc-merger` erzeugt aus lokalen Working-Copy-Checkouts strukturierte „Merge-Berichte“ im Markdown-Format.

Hauptziel: **KIs einen möglichst vollständigen Blick auf ein oder mehrere Repositories geben**, damit sie

- Code verstehen,
- Reviews erstellen,
- Refactorings vorschlagen,
- Dokumentation prüfen,
- CI- und Contract-Setups analysieren können.

Der Merge soll also nicht nur Überblick, sondern einen **arbeitsfähigen Gesamtblick** liefern – mit Schwerpunkt auf **Quelltext und relevanten Textartefakten**. Binärdateien werden nur über Metadaten erfasst; Textdateien bilden den Kern.

---

## Zielbild

Ein idealer wc-merge erfüllt:

- bildet **den gesamten relevanten Textinhalt** eines Repos ab (Code, Skripte, Configs, Tests, Docs),
- macht die **Struktur** des Repos sichtbar,
- zeigt **Zusammenhänge** (Workflows, Contracts, Tools, Tests),
- ermöglicht KIs, auf Basis des Merges so zu arbeiten, als hätten sie das Repo lokal ausgecheckt – nur ohne Binärmüll und ohne sensible Daten.

Zusätzlich soll es möglich sein, einen **vollumfänglichen, maximal detaillierten Snapshot** zu erzeugen:
- alle Textdateien eingebettet (bis zu einer konfigurierbaren Größenobergrenze),
- alle Dateien (inkl. Binärdateien) zumindest im Manifest erfasst,
- klar markiert, wo Inhalte gekürzt wurden.

---

## Funktionsweise (Überblick)

1. **Quellenauswahl**
   - Der Merger arbeitet auf einem konfigurierten `wc-hub` mit Working-Copy-Checkouts.
   - Über eine Pythonista-UI lassen sich:
     - ein oder mehrere Repos,
     - optional Unterordner,
     - Detailgrad und Merge-Art auswählen.

2. **Dateiscan**
   - Rekursives Durchlaufen der gewählten Verzeichnisse.
   - Erkennung von Text- vs. Binärdateien (heuristisch).
   - Filterung sensibler Dateien (z. B. `.env`, Schlüssel, Tokens, Cache-/Build-Ordner).

3. **Klassifikation**
   - Zuordnung zu Kategorien:
     - `config` (z. B. `.yml`, `.yaml`, `.toml`, `.json`),
     - `doc` (z. B. `.md`, `.adoc`),
     - `source` (z. B. `.rs`, `.py`, `.ts`, `.sh`),
     - `test` (z. B. `tests/**`, `*_test.*`, `.bats`),
     - `ci` (z. B. `.github/workflows/**`),
     - `contract` (z. B. `contracts/**`, `json/**`, `proto/**`),
     - `other` (alles übrige).

4. **Merge-Erzeugung**
   - Erstellung eines Markdown-Dokuments mit:
     1. Kopf (Metadaten),
     2. Plan (Statistiken),
     3. Strukturbaum,
     4. Manifest,
     5. eingebetteten Dateiinhalten.

---

## Detailgrade (Profile)

Der wc-merger v2 kennt drei optimierte Profile:

### 1. Overview (`overview`)

- Kopf, Plan, Strukturbaum, Manifest.
- **Inhalte nur für Prioritätsdateien:**
  - `README.*`, `docs/runbook.*`, `.ai-context.yml`
- Alle anderen Dateien nur als Metadaten im Manifest.

Einsatz:
- schneller Überblick mit Fokus auf Dokumentation,
- Vorprüfung (z. B. welche Dateien es gibt, wie groß das Repo ist),
- Orientierung für KIs ohne vollen Code-Download.

### 2. Dev (`dev`)

- Kopf, Plan, Struktur, Manifest,
- **Vollständige Inhalte für:**
  - Source-Code (`.py`, `.rs`, `.ts`, `.js`, `.sh`, etc.),
  - Dokumentation (`.md`, `.adoc`, `.txt`),
  - CI/CD-Workflows (`.github/workflows/**`),
  - Contracts/Schemas (`contracts/**`, `json/**`, `proto/**`),
  - Konfigurationsdateien (`.yml`, `.toml`, `.json`).
- **Zusammengefasste Inhalte für:**
  - Große Lockfiles (`package-lock.json`, `Cargo.lock`, `poetry.lock`).

Einsatz:
- gute Balance zwischen Vollständigkeit und Dateigröße,
- ideal für KI-Entwicklungsaufgaben (Code-Review, Refactoring, Architekturüberblick),
- reduziert Rauschen durch Summarisierung großer Artifacts.

### 3. Max (`max`)

- Kopf, Plan, Struktur, Manifest,
- Inhalte **aller Textdateien** (bis zu einer konfigurierbaren Byte-Grenze pro Datei),
- Binärdateien werden **nicht als Inhalt**, sondern über das Manifest und optional kurze Hinweise erfasst.

Einsatz:
- maximal detaillierter Schnappschuss für Deep-Dives,
- Grundlage für semantische Indizes,
- komplexe Codearbeiten und Reviews, die das ganze Repo betreffen.

---

## Ordnertypen

Der Merger kann auf unterschiedliche Bereiche angewendet werden:

- **Repo-Wurzel**
  Merge über das gesamte Repository.

- **Teilbäume**
  Merge nur für einen Ausschnitt, z. B.:
  - `apps/web/`,
  - `tools/`,
  - `infra/compose/`,
  - `docs/`.

- **Freie Pfadwahl**
  beliebige Unterpfade, die im Hub vorhanden sind.

Das erlaubt es, große Monorepos gezielt in handliche Segmente zu schneiden.

---

## Merge-Arten

### Single-Repo-Merge

- Ein Merge-Dokument pro Repository.
- Klarer Fokus, gut für verständliche KI-Sessions.

### Multi-Repo-Merge (in einer Datei)

- Mehrere Repos in einem Markdown-Dokument.
- Pro Repo eigener Abschnitt mit:
  - Kopf,
  - Plan,
  - Struktur,
  - Manifest,
  - Inhalten.

Gut geeignet, um ein „Subsystem“ (z. B. mehrere Dienste) gemeinsam zu betrachten.

### Batch-Merge

- UI erzeugt pro ausgewähltem Repo eine eigene Merge-Datei.
- Sinnvoll für Fleet-Scans oder regelmäßige Snapshots.

---

## Umgang mit Dateien

### Textdateien

- werden nach Möglichkeit **vollständig eingebettet** (abhängig vom Detailgrad),
- bei sehr großen Textdateien wird nach einem Limit abgeschnitten,
- im Kopf der Datei wird vermerkt, wenn Inhalte gekürzt wurden.

### Binärdateien

- keine Inhaltseinbettung (kein Hexdump),
- im Manifest mit Pfad, Größe und Hash aufgeführt,
- optional kurze Hinweise, falls der Dateityp besondere Bedeutung hat (z. B. Migrationen, Datenbankdateien, Assets).

### Sensible Dateien

- bestimmte Muster werden generell nicht eingebettet (z. B. `.env`, Schlüssel, Token-Dateien),
- sie können im Manifest auftauchen, werden aber als „sensitiv“ markiert oder ganz ausgelassen,
- Ziel: der Merge ist als privates Arbeitsartefakt gedacht, **nicht** als öffentlicher Dump.

---

## Ausgabeformat (Layout) – Strenge Pflichtenheft-Struktur

Die v2-Implementierung folgt einer strikten, AI-optimierten Dokumentstruktur gemäß „Pflichtenheft":

1. **📋 Header** (Metadaten)
   - Zeitpunkt der Erstellung,
   - Hub-Pfad und betrachtete Repos,
   - Gewähltes Profil (`overview`, `dev`, `max`),
   - Max-Bytes pro Datei,
   - Aktive Filter (Extensions, Path-Contains).

2. **🧮 Plan** (Statistiken)
   - Anzahl Dateien insgesamt,
   - Aufschlüsselung nach Kategorien (config, doc, source, test, ci, contract, other),
   - Anzahl eingebetteter Dateien (full/truncated),
   - Statistik nach Endungen.

3. **📁 Structure** (Verzeichnisbaum)
   - Hierarchische Darstellung der Repository-Struktur,
   - Gruppiert nach Root-Verzeichnis (bei Multi-Repo-Merges),
   - Einrückung pro Ebene für klare Übersicht.

4. **🧾 Manifest** (Datei-Inventar)
   - Tabelle mit:
     - **Root** (Repository-Name),
     - **Path** (relativer Pfad),
     - **Category** (config, doc, source, test, ci, contract, other),
     - **Tags** (z. B. `runbook`, `feed`, `ai-context`, `lockfile`, `ci`, `wgx-profile`),
     - **Size** (lesbar formatiert),
     - **Included** (full, truncated, meta-only, skipped),
     - **MD5** (für Versionskontrolle).

5. **📄 Content** (Dateiinhalte)
   - Pro Textdatei ein Abschnitt mit:
     - **Überschrift:** Pfad + Kategorie,
     - **Metadaten-Block:**
       - Root, Category, Tags, Size, Included-Status,
     - **Codeblock:** Syntax-Highlighted Content,
     - **Hinweise:** Bei Kürzung, Summarisierung oder besonderer Rolle.
   - **Gruppierung:** Content-Blöcke sind nach Root-Verzeichnis gruppiert für bessere Übersicht.

### Neue Features in v2:

- **Semantic Tags:** Dateien werden mit semantischen Tags versehen:
  - `runbook`: Runbook-Dokumentation,
  - `feed`: Feed-Files (.ai-context.yml, data feeds),
  - `lockfile`: Dependency-Lockfiles,
  - `ci`: CI/CD-Workflows,
  - `wgx-profile`: WGX-Profile,
  - `adr`: Architecture Decision Records,
  - `script`: Ausführbare Skripte.

- **Included-Column:** Das Manifest zeigt explizit, ob eine Datei vollständig (`full`), gekürzt (`truncated`), nur als Metadaten (`meta-only`) oder übersprungen (`skipped`) eingebunden ist.

- **Intelligente Summarisierung:** Im `dev`-Profil werden große Lockfiles automatisch zusammengefasst, statt vollständig eingebettet.

- **Split-Size-Option:** Große Merges können automatisch in mehrere Dateien gesplittet werden (z. B. alle 10 MB), um KI-Token-Limits zu respektieren.

---

## Einsatzszenarien

Typische Nutzung:

- **Code-Review durch KI**:
  Merge eines Repos im Detailgrad „kompakt“ oder „max“ erzeugen und an eine KI übergeben, um:
  - kritische Stellen zu finden,
  - Refactoring-Vorschläge zu erhalten,
  - Tests und CI-Setup zu bewerten.

- **Architektur- und CI-Analyse**:
  - Fokus auf `.github/workflows/**`, `contracts/**`, `docs/**`,
  - mit Plan/Manifest schnell erkennen, wie ein Repo in ein größeres System eingebettet ist.

- **Fleet-Überblick**:
  - mehrere Repos in einem Multi-Repo-Merge zusammenfassen,
  - KIs können daraus eine „Landkarte“ der Komponenten ableiten.

---

## Designprinzipien

- **Arbeitsfähigkeit**
  Merges sollen KIs in die Lage versetzen, direkt mit dem Code zu arbeiten, nicht nur oberflächlich zu kommentieren.

- **Vollständigkeit für Textartefakte**
  Alle relevanten Textdateien sind erfasst und – je nach Detailgrad – eingebettet.

- **Struktur vor Rauschen**
  Auch in maximalen Merges bleibt die Struktur erkennbar; große Textblöcke sind in sinnvolle Abschnitte gegliedert.

- **Determinismus**
  Gleiches Repo + gleiche Optionen → reproduzierbarer Merge.

- **Sicherheit**
  Kein bewusster Export von Geheimnissen oder privaten Daten.

---

## v2-Dateien und Nutzung

Die aktuelle v2-Implementation besteht aus:

- **`merge_core_v2.py`**: Kern-Logik für Scanning, Kategorisierung, Tagging und Report-Generierung
- **`wc-merger-v2.py`**: Pythonista-UI und CLI-Interface für v2
- **`wc-extractor-v2.py`**: Extraktion einzelner Dateien aus Merges (v2-kompatibel)

### CLI-Nutzung:

```bash
# Overview-Profil (nur Prioritätsdateien)
python3 wc-merger-v2.py --cli --repos repo1,repo2 --detail overview

# Dev-Profil (Code + Docs, summarisierte Lockfiles)
python3 wc-merger-v2.py --cli --repos myrepo --detail dev --mode batch

# Max-Profil mit Split (alle 20 MB)
python3 wc-merger-v2.py --cli --repos myrepo --detail max --split-size 20

# Plan-Only (keine Inhalte, nur Metadaten)
python3 wc-merger-v2.py --cli --repos myrepo --plan-only
```

### Pythonista-UI:

Die UI bietet Felder für:
- Repo-Auswahl (Mehrfachauswahl)
- Pfad-Filter (optional)
- Extension-Filter (optional)
- Profil-Auswahl (overview, dev, max)
- Mode (single, multi, batch)
- Max-Bytes pro Datei
- Split-Size (in MB, 0 = kein Split)
- Plan-Only-Checkbox

## Roadmap / Ideen

Mögliche zukünftige Erweiterungen:

- automatische Kurz-Zusammenfassungen aus README / Runbook / ADRs,
- Erkennung und Markierung von Rollen (`service`, `cli`, `library`, `infra`),
- CI- und Contract-Matrix (welche Workflows nutzen welche zentralen Contracts),
- optionaler Diff-Modus zwischen zwei Merges,
- Ausgabe des Manifests zusätzlich als JSON/YAML zur Weiterverarbeitung,
- Integration mit Vector-Datenbanken für semantische Suche.

---

## Kurzfassung

Der `wc-merger` erzeugt **KI-taugliche Schnappschüsse von Repositories**:

- vollständige Sicht auf **Code und relevante Textartefakte**,
- sinnvolle Strukturierung,
- verschiedene Detailgrade,
- Unterstützung von Single-Repo-, Multi-Repo- und Batch-Merges.

Binärdateien werden nicht ausgeschüttet, sondern nur sauber erfasst – damit die KI das sieht, was sie zum Arbeiten braucht.
