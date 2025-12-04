# wc-merger v2.1 – SPEC

**Version:** 2.1
**Status:** Active / Mandatory
**Date:** 2024-05-23

Zweck:
Dieses Dokument definiert verbindlich Struktur, Semantik und Verhalten des wc-merger.
wc-merger erzeugt deterministische, KI-freundliche Text-Merges aus einem oder mehreren Repositories, ohne jemals Bedeutungen zu erfinden.

---

## 1. Grundprinzipien

1.  **Null-Halluzinationsprinzip**
    wc-merger interpretiert nie, sondern extrahiert nur.
2.  **Determinismus**
    Gleicher Input → gleicher Output (abgesehen von Zeitstempel).
3.  **Strikte Struktur**
    Die Reihenfolge aller Abschnitte ist fest und unverhandelbar.
4.  **KI-Optimierung**
    Ziel: KIs sollen einen maximal vollständigen, maschinenlesbaren Überblick erhalten, ohne nach-trägliche Interpretation.
5.  **Profiles**
    Alle Merges basieren auf einem der Profile:
    *   `overview`
    *   `dev`
    *   `max`
6.  **Multi-Repo-Unterstützung**
    Jeder Merge kann mehrere Repositories enthalten.
    Ordnung und Sortierung sind definiert.

---

## 2. Output-Struktur (unverhandelbar)

Jeder Merge hat exakt die folgende Struktur:

1.  `# WC-Merger Report (v2.x)`
2.  `## Source & Profile`
3.  `## Profile Description`
4.  `## Reading Plan`
5.  `## Plan`
6.  `## 📁 Structure`
7.  `## 🧾 Manifest`
8.  `## 📦 <repo-1>`
    *   `### ...`
    *   `<content>`
9.  `## 📦 <repo-2>` ...

Die Reihenfolge ist fest. Fehlt ein Abschnitt → der Merge gilt als ungültig.

---

## 3. Abschnittsdefinitionen

### 3.1 Source & Profile

Muss enthalten:
*   **Source:** Liste aller Repos (alphabetisch sortiert oder deklarierte Reihenfolge).
*   **Profile:** `overview` • `dev` • `max`
*   **Generated At:** ISO-Zeitstempel (UTC)
*   **Max File Bytes:** Limit für Truncation
*   **Spec-Version:** `2.1`

Optional (aber empfohlen):
*   **Declared Purpose:**
    Wird nur übernommen aus:
    1.  `.ai-context.yml` -> `project.description`, oder
    2.  oberste Überschrift + erster Absatz aus `README.md`
    → niemals raten
    → wenn nichts da: `(none)`

### 3.2 Profile Description

Muss exakt beschreiben, was das Profil bedeutet.

*   **overview**
    *   Nur: `README` (voll), `Runbook` (voll), `ai-context` (voll)
    *   Andere Dateien: Included = `meta-only`
*   **dev**
    *   Alles relevante (Code, Tests, CI, Contracts, ai-context, wgx-profile) → voll
    *   Lockfiles / Artefakte: truncated oder meta-only
*   **max**
    *   alle Textdateien → voll
    *   nur > Max Bytes → BIT-ECHT truncated

### 3.3 Reading Plan

Muss enthalten:
1.  „Lies zuerst“: `README.md`, `docs/runbook*.md`, `*.ai-context.yml`
2.  Danach: `Structure` -> `Manifest` -> `Content`
3.  Hinweis: „Multi-Repo-Merges: jeder Repo hat eigenen Block 📦“

### 3.4 Plan

Muss enthalten:
*   **Total Files**
*   **Total Size**
*   **Included Content:** (Anzahl full/truncated/meta-only)
*   **Folder Highlights:** Code, Docs, Infra

### 3.5 📁 Structure

Eine Baumansicht aller Repos.
*   max. 5 Ebenen tief
*   einheitliche Einrückung
*   Ellipsen (…) erlaubt

### 3.6 🧾 Manifest

Tabellenformat ist verbindlich:

`| Root | Path | Category | Tags | Size | Included | MD5 |`

Regeln:
*   **Root:** Repo-Name
*   **Path:** relativ zum Repo-Root
*   **Category** ∈ `{source, test, doc, config, contract, other}`
*   **Tags:** siehe Abschnitt 4. Tag-System
*   **Included** ∈ `{full, truncated, meta-only, omitted}`
*   **MD5:** Hash des Originalinhalts
*   **Sortierung:** alphabetisch nach Path

### 3.7 Per-Repo-Blöcke 📦 <repo>

Jedes Repo bekommt eigenen Block.

**Reihenfolge der Repos (Multi-Repo-Merge):**
1.  metarepo
2.  wgx
3.  hausKI
4.  hausKI-audio
5.  heimgeist
6.  chronik
7.  aussensensor
8.  semantAH
9.  leitstand
10. heimlern
11. tools
12. weltgewebe
13. vault-gewebe
14. rest (alphabetisch)

**Pro Datei:**

```markdown
### `pfad/datei`

- Category: ...
- Tags: ...
- Size: X KB
- Included: full|truncated|meta-only|omitted
- MD5: abc123...

<code-fence>
...
```

Keine Datei ohne diese Metadaten.
Keine Metadaten ohne Datei.

---

## 4. Tag-System (deterministisch)

**Regeln:**
*   Tags basieren **ausschließlich auf Pfadmustern**.
*   Keine Interpretation, kein Raten.

**Tag-Liste:**

| Pattern | Tag |
|---|---|
| `*.ai-context.yml` | `ai-context` |
| `.github/workflows/*.yml` | `ci` |
| `contracts/*.json` | `contract` |
| `docs/adr/*.md` | `adr` |
| `docs/runbook*.md` | `runbook` |
| `scripts/*.sh` | `script` |
| `export/*.jsonl` | `feed` |
| `*lock*` | `lockfile` |
| `tools/*/src/*` | `cli` |
| `README.md` | `readme` |

Tags werden **kommagetrennt** ausgegeben.

---

## 5. Truncation

Eine Datei wird gekürzt wenn:
`Size > Max File Bytes`

**Schema:**
`[TRUNCATED] Original size: X MB. Included: first 128 KB + last 8 KB.`

**Metadaten:**
`Included: truncated`

---

## 6. Konsistenzprüfung („Fleet Consistency“)

Optionaler, aber empfohlener Abschnitt:

**Fleet Consistency**
*   chronik: present in system-overview, commented out in repos.yml
*   hausKI-audio: inconsistent casing
*   <repo>: missing .wgx/profile.yml
*   <repo>: adr folder present but empty

Regeln:
*   Nur **objektive** Diskrepanzen melden
*   Nie interpretieren

---

## 7. Verbotene Features

wc-merger darf **niemals**:
*   Zweck von Repos erraten
*   Inhalte zusammenfassen
*   Prioritäten zuweisen
*   Beziehungen interpretieren
*   Repos umsortieren außerhalb der definierten Reihenfolge
*   „intelligente“ Patterns anwenden

wc-merger ist **dumm aber strukturell brillant**.

---

## 8. Testing & Determinismus

### Golden-Files (empfohlen)
Für ausgewählte Repos (z. B. metarepo, hausKI, aussensensor):
*   vorhandene Merges als Golden Files
*   Vergleiche: Header, Strukturabschnitte, Manifest, Reihenfolge.

### Validator
Ein optionales Tool `wc-merger validate <file>` prüft:
*   Abschnittsstruktur stimmt
*   Manifest vollständig
*   Tags gültig
*   Kategorien gültig
*   Content-Blöcke vollständig
*   Keine ratenen Inhalte

---

## 10. Schlussformel

Dies ist die **verbindliche Spezifikation** für wc-merger ab Version 2.1+.
Jede Implementierung muss diese Struktur **zu 100 %** einhalten.

> **wc-merger ist nicht klug. wc-merger ist zuverlässig. Und Zuverlässigkeit ist klüger als Intelligenz.**
