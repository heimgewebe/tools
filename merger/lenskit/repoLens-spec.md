# REPOLENS SPEC v2.4

(Normative Spezifikation)

## Navigation & Anchors (Renderer Robustness)

Viele iOS/Preview-Renderer erzeugen keine stabilen Heading-IDs und/oder strippen HTML.
Der Report emittiert daher **mehrschichtige Navigation**:

- sichtbare Suchmarker: `§§ <token>` (immer auffindbar, auch wenn Links tot sind)
- HTML Anchor: `<a id="<token>"></a>` (wenn HTML zugelassen ist)
- tokenisierte Headings: `## <token>` (wenn Heading-IDs erzeugt werden)

Alle internen Links verwenden nur Tokens (`#manifest`, `#index`, `#file-...`).

## Render Mode

Der Report weist den Modus explizit aus:
`Render Mode: full | code-only | plan-only`

## 1. Zweck

Der repoLens erzeugt aus Working-Copy-Repositories KI-optimierte, strukturierte Hyper-Merges.
Diese dienen KIs als Navigations- und Arbeitsfläche, ähnlich einer Mini-IDE.

---

## 2. Invariante Struktur des Merges (strict ordering)

Jeder Merge folgt exakt dieser Reihenfolge:
1.  Source & Profile
2.  Profile Description
3.  Reading Plan
4.  Plan
5.  📁 Structure
6.  🧾 Manifest
7.  📄 Content

Fehlt ein Abschnitt → Fehler.

Reihenfolge falsch → Fehler.

---

## 3. Spec-Version-Pinning

Header muss enthalten:

- Spec-Version: 2.4

---

### TODO: Super-Merger / Extras (für google-labs-jules[bot])

Die folgenden Punkte sind für die Super-Merger-Ausbaustufe umzusetzen.

1. **Extras-Schalter in der UI implementieren**
   - Flags in `MergerUI`:
     - Repo Health Checks
     - Organism Index
     - Fleet Panorama (Multi-Repo)
     - Delta Reports (wenn Diff vorhanden)
     - Augment Sidecar (Playground-Block)
     - JSON Sidecar (maschinenlesbarer Zwilling)
     - Heatmap (Alias im CLI akzeptiert: `ai_heatmap` → `heatmap`)
   - Alle Extras müssen rein additive Textblöcke sein.
     Nichts an der Kernstruktur (Source & Profile → … → Content) entfernen oder umsortieren.

   ```python
   @dataclass
   class ExtrasConfig:
       health: bool = False
       organism_index: bool = False
       fleet_panorama: bool = False  # Nur für Multi-Repo-Merges
       augment_sidecar: bool = False
       delta_reports: bool = False
       json_sidecar: bool = False
       heatmap: bool = False  # CLI alias: ai_heatmap
   ```

2. **Header / Meta konsistent machen**
   - `Declared Purpose` je Profil korrekt setzen:
     - overview → `Tools – Index`
     - summary → `Tools – Doku/Kontext`
     - dev → `Tools – Code/Review Snapshot`
      - machine-lean → `Tools – Machine-Lean`
      - max → `Tools – Vollsnapshot`
   - Coverage-Zeile ergänzen, z. B.:
     - `Coverage: 17/35 Dateien mit vollem Inhalt`
   - Im `@meta`-Block:
     - `merge.extras.*`-Flags für alle aktivierten Extras ergänzen.
     - Schema `repolens-report.schema.json` entsprechend erweitern.
     - Beispiel:

       ```yaml
       merge:
         extras:
           health: true
           organism_index: true
           fleet_panorama: true
           augment_sidecar: true
           delta_reports: true
           json_sidecar: true
           heatmap: true
       ```

3. **Multi-Part-Merges klar kennzeichnen**
   - Dateinamen bleiben im bisherigen Schema (`…_part1_merge.md`, `…_part2_merge.md`, …).
   - Im Header jeder Datei:
     - `# WC-Merge Report (Part N/M)` setzen (bei Single-Part-Merges `1/1`).

4. **Validierung**
   - Alle Änderungen strikt gegen `repolens-report.schema.json` und die oben definierte Abschnittsreihenfolge prüfen.
   - Keine neuen Kategorien/Tags einführen, solange die Spec nicht explizit erweitert wird.

---

## 3a. Größenlimits (Size Behaviour)

- Es gibt **kein hartes globales Merge-Size-Limit**.
- `max_file_bytes` begrenzt ausschließlich die **einzelne Datei**
  (Trunkierung bzw. optionales Splitting auf Dateiebene).
- `split_size` steuert optional die **Aufteilung des Merges in mehrere Dateien**:
  - `split_size <= 0` → kein Split (ein einziger Merge).
  - `split_size > 0` → Multi-File-Merge, Inhalt wird nur über mehrere Dateien verteilt,
    aber nicht zusätzlich gekürzt.

Konsequenz:

> „Wenn Inhalt fehlt, liegt das an Profil-/Dateifiltern oder `max_file_bytes`, **nicht** an einem globalen Hard-Limit.“

KIs dürfen davon ausgehen, dass es auf Merge-Ebene keine „unsichtbare Schere“ gibt,
sondern nur explizit deklarierte Filter und Limits.

Optional:

- Spec-Checksum: <sha256>

---

## 3b. Merge-Contract

Jeder repoLens-Report implementiert einen formalen „Merge-Contract“.
Ziel:

- eindeutige Identifikation des Formats,
- maschinenlesbare Versionierung,
- Basis für externe Validatoren und CI-Checks.

Pflichtfelder:

Im Abschnitt **Source & Profile**:

- `Contract: repolens-report`
- `Contract-Version: 2.4`

Im `@meta`-Block (eingebettet in HTML-Kommentare `<!-- @meta:start -->` ... `<!-- @meta:end -->`):

```yaml
merge:
  contract: "repolens-report"
  contract_version: "2.4"
```

- Es gibt **kein hartes globales Merge-Size-Limit**.
- `max_file_bytes` begrenzt ausschließlich die **einzelne Datei**
  (Trunkierung bzw. optionales Splitting auf Dateiebene).
- `split_size` steuert optional die **Aufteilung des Merges in mehrere Dateien**:
  - `split_size <= 0` → kein Split (ein einziger Merge).
  - `split_size > 0` → Multi-File-Merge, Inhalt wird nur über mehrere Dateien verteilt,
    aber nicht zusätzlich gekürzt.

Konsequenz:

> „Wenn Inhalt fehlt, liegt das an Profil-/Dateifiltern oder `max_file_bytes`, **nicht** an einem globalen Hard-Limit.“

KIs dürfen davon ausgehen, dass es auf Merge-Ebene keine „unsichtbare Schere“ gibt,
sondern nur explizit deklarierte Filter und Limits.

Optional:

- Spec-Checksum: <sha256>

## 3c. Hub Path (Configuration)

repoLens speichert den Hub-Pfad in `.repolens-hub-path.txt` im Skript-Verzeichnis, um Umbenennungen (z. B. `wc-hub` -> `repolens-hub`) robust zu überstehen.

**Hub setzen:**
1. Öffne den gewünschten Hub-Ordner (z. B. `wc-hub`) in Pythonista als Working Directory.
2. Führe `repolens-hub-pathfinder.py` aus.
3. Starte `repolens.py` neu.

## 3d. Profil- und Modus-Flags

- `level` (string)
  - `overview`, `summary`, `dev`, `max`
  - steuert Umfang und Detailgrad des Inhalts

- `plan_only` (bool)
  - `false` (Default): Voll-Merge entsprechend Profil (inkl. Structure / Manifest / Content)
  - `true`: PLAN-ONLY-Modus
    - Ausgabe enthält:
      - Header („Source & Profile“)
      - Profilbeschreibung
      - **Reading Plan** (mit explizitem Hinweis auf Plan-Only)
      - `@meta`-Block
    - keine `Structure`-, `Manifest`- oder `Content`-Sektionen

### KI-Lesepfad-Minimum (nur Output, keine Configs)

Dieser Abschnitt definiert den minimalen Lesepfad für KIs, die
nur die Merge-Datei sehen – nicht den ausführenden Code und
nicht die Profile/Configs.

- Schritt 1 – @meta lesen:
  - KIs sollen zuerst den merge-Block lesen (Profil, Scope, Limits,
    `generated_at`). Der Block beschreibt, wie der Merge erzeugt wurde,
    ohne dass die KI Zugriff auf die ausführende Umgebung braucht.

- Schritt 2 – Manifest nutzen:
  - Das Manifest ist der zentrale Index über alle Dateien. KIs sollen es
    nutzen, um relevante Dateien zu identifizieren und zielgerichtet in
    die entsprechenden Abschnitte zu springen.

- Schritt 3 – Datei-Blöcke:
  - Jeder Datei-Block ist in Markdown sauber abgegrenzt, inkl. Rücksprung-
    Links zum Manifest. Es gibt keine versteckten Bedeutungen; KIs sollen
    die Inhalte so lesen, wie sie sind – ohne eigene Struktur in den Merge
    „hineinzuphantasieren“.

---

## 4. Kategorien

Erlaubte Werte:
- source
- doc
- config
- test
- contract
- other

(Hinweis: `ci` ist als Tag implementiert, nicht als eigene Kategorie.)

Neue Kategorien dürfen nicht entstehen.

---

## 5. Tags

Erlaubte Tags:
- ai-context
- runbook
- lockfile
- script
- ci
- adr
- feed
- wgx-profile

Jede Datei darf 0–n Tags haben.
Neue Tags sind verboten, außer Spec wird geändert.

---

## 6. Hyperlink-Schema (Pflicht)

### 6.1 Datei-Anchor (Pflicht)

Jede Datei im Content-Bereich erhält einen Anchor:

`<a id="file-<root>-<path-without-slashes>"></a>`

Regeln:
- `/` → `-`
- `.` → `-`

Beispiel:

`tools/merger/merge_core.py`
→ `file-tools-merger-merge_core-py`

---

### 6.2 Manifest-Link (Pflicht)

Pfadspalte:

[`<path>`](#file-<root>-<path>)

---

### 6.3 Strukturbaum-Link (optional)

📄 [filename](#file-…)

---

### 6.4 Repo-Anchor (Pflicht bei Multi-Repo)

`## 📦 tools {#repo-tools}`

---

### 6.5 Backlink (Pflicht)

Jeder Datei-Contentblock endet mit:

`[↑ Zurück zum Manifest](#manifest)`

---

## 7. Manifest-Anker

Oberhalb Manifest:

`## 🧾 Manifest {#manifest}`

---

## 8. Navigation-Indexe

Vor dem Manifest:

```markdown
## Index
- [Source Files](#cat-source)
- [Docs](#cat-doc)
- [Config](#cat-config)
- [Contracts](#cat-contract)
- [Tests](#cat-test)
- [CI Pipelines](#tag-ci)
- [WGX Profiles](#tag-wgx-profile)
```

Für jede Kategorie:

```markdown
## Category: source {#cat-source}
- [file](#file-...)
```

Für Tags (z. B. CI):

```markdown
## Tag: ci {#tag-ci}
- [file](#file-...)
```

---

## 9. Non-Interpretation Guard

Regeln:
- Keine Rateversuche.
- Unklare Klassifikation → other.
- Unklare Tags → keine Tags.
- Unklare Repo-Beschreibung → leer.

---

## 10. Repo-Zweck-Auslesung (safe)

Der Merger liest nur:
1.  README.md (erster Absatz)
2.  docs/intro.md (erster Absatz)

Keine weiteren Quellen. Keine Interpretation.

Output:

`- Declared Purpose: <ausgelesener Absatz>`

---

## 11. Debug Mode

CLI: `--debug`

Mindestinformationen:
- unbekannte Kategorien
- unbekannte Tags
- Dateien ohne Anchor
- Dateien ohne Manifest-Eintrag
- Dateien ohne Tags
- kollidierende Anchors
- Section-Ordering-Check-Report

---

## 12. Strict Validator

Jede Ausgabe wird auf folgende strukturelle Integrität geprüft:
- Abschnittsreihenfolge
- Spec-Version & Contract-Header vorhanden
- Manifest-Anker vorhanden

Erweiterte Prüfungen (z.B. unbekannte Tags/Kategorien, fehlende Anker) erfolgen im **Debug-Modus** oder als Warnungen und verhindern im Standardbetrieb nicht zwingend die Ausgabe, sollten aber behoben werden.

Fehler in der Grundstruktur → kein Merge wird geschrieben.

---

## 13. Agent Contract (JSON Sidecar)

Falls ein JSON Sidecar generiert wird (`artifacts.index_json`), gelten folgende Feld-Definitionen für die stabile Navigation:

### 13.1 Content References

`files[].content_ref`:
- `marker` (string): Exakter Substring, der im Markdown vorkommt. Muss zwingend Anführungszeichen enthalten (z. B. `file:id="FILE:..."`).
- `selector` (object, optional): Strukturierter Parser-Pfad.
  - `kind`: `html_comment_attr`
  - `tag`: `file`
  - `attr`: `id`
  - `value`: Die ID (z. B. `FILE:f_...`)

### 13.2 Markdown References

`files[].md_ref`:
- `anchor` (string): Der HTML-ID-String ohne `#` (für `<a id="...">`).
- `fragment` (string): Der vollständige Link-Fragment-Identifier inkl. `#` (für URL-Navigation).
