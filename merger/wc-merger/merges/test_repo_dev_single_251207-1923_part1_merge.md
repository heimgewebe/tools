# WC-Merge Report (Part 1/1)

## Source & Profile
- **Source:** test_repo
- **Profile:** `dev`
- **Generated At:** 2025-12-07 19:23:07 (UTC)
- **Max File Bytes:** unlimited
- **Spec-Version:** 2.3
- **Contract:** wc-merge-report
- **Contract-Version:** 2.3
- **Profile Use-Case:** Tools – Code/Review Snapshot
- **Declared Purpose:** Repo Title
- **Scope:** single repo `test_repo`
- **Path Filter:** `none (full tree)`
- **Extension Filter:** `none (all text types)`

## Profile Description
`dev`
- Code, Tests, Config, CI, Contracts, ai-context, wgx-profile → voll
- Doku nur für Prioritätsdateien voll (README, Runbooks, ai-context), sonst Manifest
- Lockfiles / Artefakte: ab bestimmter Größe meta-only

## Reading Plan
1. Lies zuerst: `README.md`, `docs/runbook*.md`, `*.ai-context.yml`
2. Danach: `Structure` -> `Manifest` -> `Content`
3. Hinweis: „Multi-Repo-Merges: jeder Repo hat eigenen Block 📦“

## Plan

- **Total Files:** 3 (Text: 3)
- **Total Size:** 45.00 B
- **Included Content:** 3 files (full)
- **Coverage:** 3/3 Textdateien mit Inhalt (`full`/`truncated`)

### Repo Snapshots

- `test_repo` → 3 files (3 relevant text, 45.00 B, 3 with content)

**Folder Highlights:**
- Code: `src`
- Infra: `.wgx`

### Organism Overview

- AI-Kontext-Organe: 1 Datei(en) (`ai-context`)
- Contracts: 0 Datei(en) (category = `contract`)
- Pipelines (CI/CD): 0 Datei(en) (Tag `ci`)
- Fleet-/WGX-Profile: 1 Datei(en) (Tag `wgx-profile`)

<!-- @health:start -->
## 🩺 Repo Health

### ⚠️ `test_repo` – WARN

- **Total Files:** 3
- **Categories:** config=1, doc=1, source=1
- **Indicators:** README: yes, WGX Profile: yes, CI: no, Contracts: no, AI Context: yes
- **Warnings:**
  - No CI workflows found
  - No contracts found
- **Recommendations:**
  - Add .github/workflows for CI/CD
  - Consider adding contract schemas

<!-- @health:end -->
