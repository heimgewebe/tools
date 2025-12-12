# repoLens

Der `repoLens` erzeugt aus lokalen Repository-Checkouts strukturierte „Merge-Berichte“ im Markdown-Format.

Hauptziel: **KIs einen möglichst vollständigen Blick auf ein oder mehrere Repositories geben**, damit sie

- Code verstehen,
- Reviews erstellen,
- Refactorings vorschlagen,
- Dokumentation prüfen,
- CI- und Contract-Setups analysieren können.

**⚠️ WICHTIG: Verbindliche Spezifikation**

Ab Version 2.1 folgt dieses Tool einer strikten, unverhandelbaren Spezifikation.
Jede Änderung am Code muss diese Regeln einhalten.

👉 [**repoLens-spec.md**](./repoLens-spec.md) (Die Single Source of Truth)

---

## 🏗️ Jules Guidelines (Strict Mode)

Für die Weiterentwicklung (und speziell für Agenten wie Jules) gelten folgende **Meta-Regeln**:

1.  **Strict Compliance Check:**
    *   Verstößt der Patch gegen die festgelegte Abschnittsreihenfolge?
    *   Werden neue Kategorien/Tags eingeführt? → **VERBOTEN**
    *   Werden bestehende Tags verändert? → **VERBOTEN**
    *   Wird irgendwo neue Logik eingeführt, die „intelligent“ ist? → **VERBOTEN**
    *   Verändert der Patch einen optionalen Abschnitt so, dass er verpflichtend wird? → **VERBOTEN**
    *   Entsteht eine neue potenzielle Halluzinationsquelle? → **SOFORT ABBRECHEN**

2.  **Explicit Non-Interpretation:**
    *   `if some_field_unsure: do NOT fill it, NOT invent fallback, leave as (none)`
    *   Keine „kleinen automatischen Schlauheiten“.

3.  **Strict Sorting:**
    *   Multi-Repo-Merges müssen der in der Spec definierten Reihenfolge folgen (`metarepo` -> `wgx` -> `hausKI` ...).
    *   Dateien alphabetisch nach Pfad.

4.  **KI-Safety:**
    *   Timestamps immer in UTC (`YYYY-MM-DD HH:MM:SS (UTC)`).
    *   `Spec-Version: 2.4` Header immer setzen.

---

## Zielbild

Ein idealer repoLens-merge erfüllt:

- bildet **den gesamten relevanten Textinhalt** eines Repos ab (Code, Skripte, Configs, Tests, Docs),
- macht die **Struktur** des Repos sichtbar,
- zeigt **Zusammenhänge** (Workflows, Contracts, Tools, Tests),
- ermöglicht KIs, auf Basis des Merges so zu arbeiten, als hätten sie das Repo lokal ausgecheckt – nur ohne Binärmüll und ohne sensible Daten.
- hält strikt die in `repoLens-spec.md` definierte Struktur ein,
- deklariert seine `Spec-Version` und den verwendeten Merge-Contract,
- gibt KIs eine klare Aussage über Profil/Use-Case (Index, Doku, Dev, Vollsnapshot),
- und ist maschinenlesbar validierbar.

---

## Manifest und Roles

Das Manifest listet alle Dateien des Merges mit ihren Metadaten auf. Neben Kategorie und Tags gibt es eine **Roles**-Spalte.

### Was sind „Roles"?

**Roles** sind semantische Kurzlabels, die automatisch aus Kategorie, Tags und Pfad abgeleitet werden. Sie helfen KIs und Menschen, die Funktion einer Datei auf einen Blick zu erkennen.

**Wofür sind sie gedacht?**
- Schnelle Filterung: „Zeige mir alle Contracts", „Wo sind die CI-Pipelines?"  
- Semantische Navigation: Roles ergänzen die technische Kategorie um den Anwendungskontext.

**Wie entstehen sie?**
- **Doc-Essentials:** README-Dokumente werden als `doc-essential` markiert.
- **Config:** Pfade mit `config` oder die Endungen `.yml`, `.yaml`, `.toml` → Role `config`.
- **Entrypoint:** Dateien, die mit `run_`, `main`, `index` beginnen → Role `entrypoint`.
- **AI-Context:** Pfade/Tags mit `ai` oder `context` → Role `ai-context`.
- **Trivialfälle:** Plain Source-Dateien ohne besondere Signale → **keine Rolle** (Redundanz vermeiden)

**Beispiele:**
- `README.md` + Tag `ai-context` → Role `ai-context`
- `.github/workflows/ci.yml` → Roles `ci`
- `src/main.rs` ohne Tags → **keine Rolle** (Category `source` reicht)
- `pyproject.toml` → Roles `config`

---

## Meta-Contract & Schema (`repoLens-report`)

Ab Spec-Version `2.4` existiert ein formaler Merge-Contract:

- **Contract-Name:** `repoLens-report`
- **Contract-Version:** `2.4`

Jeder Report muss:

1. Im Header (Block „Source & Profile“) diese Felder tragen:

   ```markdown
   - **Spec-Version:** 2.4
   - **Contract:** repoLens-report
   - **Contract-Version:** 2.4
   ```

2. Im `@meta`-Block die Contract-Information maschinenlesbar haben:
   (Der Block ist in HTML-Kommentare eingebettet, um das Rendering nicht zu stören.)

   ```html
   <!-- @meta:start -->
   ```yaml
   merge:
     spec_version: "2.4"
     profile: "max"
     contract: "repoLens-report"
     contract_version: "2.4"
     plan_only: false
     max_file_bytes: 0
     scope: "single repo `tools`"
     source_repos:
       - tools
     path_filter: null
     ext_filter: null
     generated_at: "2025-12-11T05:55:00Z"
     total_files: 42
     total_size_bytes: 1234567
   ```
   <!-- @meta:end -->
   ```

Das JSON Schema für diesen Block liegt hier:

- `merger/repoLens/repoLens-report.schema.json`

---

## Lokale Validierung (`validate_merge_meta.py`)

Optionales Helfer-Script, um den `@meta`-Block gegen das Schema zu prüfen:

```bash
cd merger/repoLens
python validate_merge_meta.py ../../merges/tools_max_part1.md
```

- Exit-Code `0` → Meta-Block ist gültig.
- Exit-Code `1` → Schema-Verletzung (Details auf STDERR).
- Exit-Code `2` → technischer Fehler (z. B. `jsonschema`/`pyyaml` fehlt).

### Abhängigkeiten

- Python 3.x
- [`PyYAML`](https://pyyaml.org/) (`pip install pyyaml`)
- [`jsonschema`](https://github.com/python-jsonschema/jsonschema) (`pip install jsonschema`)

Auf iPad/Pythonista können diese Pakete ebenfalls installiert werden (z. B. per `pip` in der integrierten Konsole).

---

## Detailgrade (Profile)

Der repoLens v2 kennt vier optimierte Profile:

### 1. Overview (`overview`)
- Kopf, Plan, Strukturbaum, Manifest.
- **Inhalte nur für Prioritätsdateien:** `README.*`, `docs/runbook.*`, `.ai-context.yml`
- Alle anderen Dateien nur als Metadaten im Manifest (`meta-only`).

### 2. Summary (`summary`)
- Fokus auf Dokumentation und Kontext.
- **Vollständig:** `README`, Runbooks, `.ai-context`, `docs/`, `.wgx/`, `.github/workflows/`, zentrale Configs, Contracts.
- **Meta-Only:** Der eigentliche Source-Code und Tests erscheinen nur im Manifest (außer sie sind Priority-Files).

### 3. Dev (`dev`)
- **Vollständig:** Source-Code, Tests, zentrale Configs, CI/CD, Contracts, ai-context, `.wgx/profile`.
- **Vollständig bei Doku:** nur README, Runbooks und `.ai-context`-Dateien.
- **Zusammengefasst:** große Lockfiles (nur Manifest).

### 4. Max (`max`)
- Inhalte **aller Textdateien** (bis zum Limit).
- Maximale Tiefe.
- Keine Kürzung auf Merge-Ebene, nur optionaler Split in mehrere Dateien.

---

## Nutzung

### CLI-Nutzung:

```bash
# Overview-Profil (Scannt aktuelles Verzeichnis oder nutzt --hub)
python3 repoLens.py repo1 repo2 --level overview

# Dev-Profil, einzelner Merge pro Repo
python3 repoLens.py myrepo --level dev --mode pro-repo

# Max-Profil mit Split (z. B. 20MB)
python3 repoLens.py myrepo --level max --split-size 20MB
```

Hinweis: `--split-size` **und** `--max-bytes` akzeptieren menschenlesbare Werte
wie `5MB`, `500K` oder `1GB`. `0` bedeutet „kein Limit pro Datei“.

### Nutzung in iOS Shortcuts (Headless)

Shortcuts startet Pythonista oft als **App-Extension** mit stark eingeschränkten Rechten.
In dieser Umgebung sind die Pythonista-Module `editor`, `ui`, `console` u. a. nicht verfügbar.

Der repoLens unterstützt deshalb einen **Headless-Modus**:

```bash
# Variante 1: per Flag
python3 repoLens.py --headless --level dev --mode gesamt

# Variante 2: per Umgebungsvariable
REPOLENS_HEADLESS=1 python3 repoLens.py --level dev --mode gesamt
```

**Tipp:** Soll ein Shortcut Pythonista *voll* starten (mit UI/editor),
nutze das URL-Scheme:

```
pythonista3://merger/repoLens/repoLens.py?action=run
```

### Power-User (Variante B: URL-Scheme mit Parametern)

Das URL-Scheme ist die empfohlene Variante, um die Einschränkungen von App-Extensions zu umgehen.
Es unterstützt nun auch Parameter, um die UI vorzubelegen oder Modi direkt zu wählen:

**Beispiel: Max-Profil, Gesamt-Merge**

```
pythonista3://repoLens/repoLens.py?action=run&root=icloud&argv=--level&argv=max&argv=--mode&argv=gesamt
```

**Beispiel: Extractor (ZIPs entpacken)**

```
pythonista3://repoLens/repoLens-extractor.py?action=run&root=icloud
```

Diese Methode garantiert vollen Zugriff auf UI, Alerts und das Dateisystem.

Weitere Details siehe [repoLens-spec.md](./repoLens-spec.md).

### KI-Lesepfad (kurz)

Dieser Abschnitt richtet sich an KIs und beschreibt **nur**, wie die
fertige Merge-Datei zu lesen ist – unabhängig davon, welches Profil
(`overview`, `summary`, `dev`, `max`) den Merge erzeugt hat.

1. **Meta-Block zuerst**
   - Suche im Kopf des Dokuments nach dem `@meta`-Block (YAML).
   - Dort stehen: Profil, Scope (welche Repos), Grenzen (`max_file_bytes`),
     und Zeitstempel (`generated_at`).
   - Nutze diese Infos, um deine eigene Antwort zu kalibrieren
     (z. B. ob der Merge eher Überblick oder Vollabdeckung liefert).

2. **Manifest als Index**
   - Das Manifest listet alle Dateien mit Pfad, Größe und Rolle.
   - Behandle das Manifest wie ein Inhaltsverzeichnis:
     - Wähle zuerst Dateien mit hoher Relevanz für deine Aufgabe
       (Readmes, `.ai-context`, Runbooks, CI/Contracts etc.).

3. **Datei-Abschnitte lesen**
   - Jede Datei mit Inhalt hat einen eigenen Abschnitt mit Überschrift
     (typisch: `### <pfad/der/datei>`).
   - Verwende die Rücksprung-Links wie `[↑ Zurück zum Manifest]`, um
     zwischen Manifest und Datei-Blöcken zu navigieren.

4. **Mehrere Repos**
   - Wenn mehrere Repos in einem Merge stecken, sind sie in der Struktur
     und im Manifest entsprechend gruppiert. Lies ggf. Repo-für-Repo.
