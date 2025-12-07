# WC-Merge Report (Part 1/1)

## Source & Profile
- **Source:** repo1, repo2
- **Profile:** `dev`
- **Generated At:** 2025-12-07 12:36:10 (UTC)
- **Max File Bytes:** unlimited
- **Spec-Version:** 2.3
- **Contract:** wc-merge-report
- **Contract-Version:** 2.3
- **Profile Use-Case:** Tools – Code/Review Snapshot
- **Declared Purpose:** Repo1
- **Scope:** 2 repos: `repo1`, `repo2`
- **Path Filter:** `none (full tree)`
- **Extension Filter:** `none (all text types)`

<!-- @meta:start -->
```yaml
merge:
  spec_version: "2.3"
  profile: "dev"
  contract: "wc-merge-report"
  contract_version: "2.3"
  plan_only: true
  max_file_bytes: 0
  scope: "2 repos: `repo1`, `repo2`"
  source_repos: ['repo1', 'repo2']
  path_filter: null
  ext_filter: null
  extras:
    health: false
    organism_index: false
    fleet_panorama: true
    augment_sidecar: false
    delta_reports: false
```
<!-- @meta:end -->

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

- **Total Files:** 4 (Text: 4)
- **Total Size:** 42.00 B
- **Included Content:** 4 files (full)
- **Coverage:** 4/4 Textdateien mit Inhalt (`full`/`truncated`)

### Repo Snapshots

- `repo1` → 2 files (2 relevant text, 21.00 B, 2 with content)
- `repo2` → 2 files (2 relevant text, 21.00 B, 2 with content)

**Folder Highlights:**

### Organism Overview

- AI-Kontext-Organe: 2 Datei(en) (`ai-context`)
- Contracts: 0 Datei(en) (category = `contract`)
- Pipelines (CI/CD): 0 Datei(en) (Tag `ci`)
- Fleet-/WGX-Profile: 0 Datei(en) (Tag `wgx-profile`)

<!-- @fleet-panorama:start -->
## 🛰 Fleet Panorama

**Summary:** 2 repos, 42.00 B, 4 files

**`repo1`:**
- Files: 2
- Size: 21.00 B
- Categories: doc=1, source=1
- Role: utility

**`repo2`:**
- Files: 2
- Size: 21.00 B
- Categories: doc=1, source=1
- Role: utility

<!-- @fleet-panorama:end -->
