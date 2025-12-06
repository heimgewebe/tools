# wc-merger (Working Copy Merger)

Der `wc-merger` erzeugt aus lokalen Working-Copy-Checkouts strukturierte „Merge-Berichte“ im Markdown-Format.

Hauptziel: **KIs einen möglichst vollständigen Blick auf ein oder mehrere Repositories geben**, damit sie

- Code verstehen,
- Reviews erstellen,
- Refactorings vorschlagen,
- Dokumentation prüfen,
- CI- und Contract-Setups analysieren können.

**⚠️ WICHTIG: Verbindliche Spezifikation**

Ab Version 2.1 folgt dieses Tool einer strikten, unverhandelbaren Spezifikation.
Jede Änderung am Code muss diese Regeln einhalten.

👉 [**wc-merger-spec.md**](./wc-merger-spec.md) (Die Single Source of Truth)

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
    *   `Spec-Version: 2.1` Header immer setzen.

---

## Zielbild

Ein idealer wc-merge erfüllt:

- bildet **den gesamten relevanten Textinhalt** eines Repos ab (Code, Skripte, Configs, Tests, Docs),
- macht die **Struktur** des Repos sichtbar,
- zeigt **Zusammenhänge** (Workflows, Contracts, Tools, Tests),
- ermöglicht KIs, auf Basis des Merges so zu arbeiten, als hätten sie das Repo lokal ausgecheckt – nur ohne Binärmüll und ohne sensible Daten.
- hält strikt die in `wc-merger-spec.md` definierte Struktur ein,
- deklariert seine `Spec-Version` und den verwendeten Merge-Contract,
- gibt KIs eine klare Aussage über Profil/Use-Case (Index, Doku, Dev, Vollsnapshot),
- und ist maschinenlesbar validierbar.

---

## Meta-Contract & Schema (`wc-merge-report`)

Ab Spec-Version `2.3` existiert ein formaler Merge-Contract:

- **Contract-Name:** `wc-merge-report`
- **Contract-Version:** `2.3`

Jeder Report muss:

1. Im Header (Block „Source & Profile“) diese Felder tragen:

   ```markdown
   - **Spec-Version:** 2.3
   - **Contract:** wc-merge-report
   - **Contract-Version:** 2.3
   ```

2. Im `@meta`-Block die Contract-Information maschinenlesbar haben:
   (Der Block ist in HTML-Kommentare eingebettet, um das Rendering nicht zu stören.)

   ```html
   <!-- @meta:start -->
   ```yaml
   merge:
     spec_version: "2.3"
     profile: "max"
     contract: "wc-merge-report"
     contract_version: "2.3"
     plan_only: false
     max_file_bytes: 0
     scope: "single repo: `tools`"
     source_repos:
       - tools
     path_filter: null
     ext_filter: null
   ```
   <!-- @meta:end -->
   ```

Das JSON Schema für diesen Block liegt hier:

- `merger/wc-merger/wc-merge-report.schema.json`

---

## Lokale Validierung (`validate_merge_meta.py`)

Optionales Helfer-Script, um den `@meta`-Block gegen das Schema zu prüfen:

```bash
cd merger/wc-merger
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

Der wc-merger v2 kennt vier optimierte Profile:

### 1. Overview (`overview`)
- Kopf, Plan, Strukturbaum, Manifest.
- **Inhalte nur für Prioritätsdateien:** `README.*`, `docs/runbook.*`, `.ai-context.yml`
- Alle anderen Dateien nur als Metadaten im Manifest (`meta-only`).

### 2. Summary (`summary`)
- Fokus auf Dokumentation und Kontext.
- **Vollständig:** `README`, Runbooks, `.ai-context`, `docs/`, `.wgx/`, `.github/workflows/`, zentrale Configs, Contracts.
- **Meta-Only:** Der eigentliche Source-Code und Tests erscheinen nur im Manifest (außer sie sind Priority-Files).

### 3. Dev (`dev`)
- **Vollständig:** Source-Code, Docs, CI/CD, Contracts, Configs.
- **Zusammengefasst:** Große Lockfiles.

### 4. Max (`max`)
- Inhalte **aller Textdateien** (bis zum Limit).
- Maximale Tiefe.

---

## Nutzung

### CLI-Nutzung:

```bash
# Overview-Profil (Scannt aktuelles Verzeichnis oder nutzt --hub)
python3 wc-merger.py repo1 repo2 --level overview

# Dev-Profil, einzelner Merge pro Repo
python3 wc-merger.py myrepo --level dev --mode pro-repo

# Max-Profil mit Split (z. B. 20MB)
python3 wc-merger.py myrepo --level max --split-size 20MB
```

### Nutzung in iOS Shortcuts (Headless)

Shortcuts startet Pythonista oft als **App-Extension** mit stark eingeschränkten Rechten.
In dieser Umgebung sind die Pythonista-Module `editor`, `ui`, `console` u. a. nicht verfügbar.

Der wc-merger unterstützt deshalb einen **Headless-Modus**:

```bash
# Variante 1: per Flag
python3 wc-merger.py --headless --level dev --mode gesamt

# Variante 2: per Umgebungsvariable
WC_HEADLESS=1 python3 wc-merger.py --level dev --mode gesamt
```

**Tipp:** Soll ein Shortcut Pythonista *voll* starten (mit UI/editor),
nutze das URL-Scheme:

```
pythonista3://merger/wc-merger/wc-merger.py?action=run
```

### Power-User (Variante B: URL-Scheme mit Parametern)

Das URL-Scheme ist die empfohlene Variante, um die Einschränkungen von App-Extensions zu umgehen.
Es unterstützt nun auch Parameter, um die UI vorzubelegen oder Modi direkt zu wählen:

**Beispiel: Max-Profil, Gesamt-Merge**

```
pythonista3://wc-merger/wc-merger.py?action=run&root=icloud&argv=--level&argv=max&argv=--mode&argv=gesamt
```

**Beispiel: Extractor (ZIPs entpacken)**

```
pythonista3://wc-merger/wc-extractor.py?action=run&root=icloud
```

Diese Methode garantiert vollen Zugriff auf UI, Alerts und das Dateisystem.

Weitere Details siehe [wc-merger-spec.md](./wc-merger-spec.md).
