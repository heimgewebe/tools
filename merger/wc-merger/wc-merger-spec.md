# WC-MERGER SPEC v2.3

(Normative Spezifikation)

## 1. Zweck

Der wc-merger erzeugt aus Working-Copy-Repositories KI-optimierte, strukturierte Hyper-Merges.
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

- Spec-Version: 2.3

Optional:

- Spec-Checksum: <sha256>

---

## 4. Kategorien

Erlaubte Werte:
- source
- doc
- config
- test
- contract
- ci
- other

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
- [CI](#cat-ci)
- [WGX Profiles](#tag-wgx-profile)
```

Für jede Kategorie:

```markdown
## Category: source {#cat-source}
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

Jede Ausgabe wird geprüft:
- Abschnittsreihenfolge
- vollständige Manifest-Anker
- vollständige Content-Anker
- nur erlaubte Kategorien
- nur erlaubte Tags
- Spec-Version vorhanden
- keine verbotenen Schlüsselwörter oder Strukturen

Fehler → kein Merge wird geschrieben.
