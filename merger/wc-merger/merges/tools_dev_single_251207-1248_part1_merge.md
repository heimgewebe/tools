# WC-Merge Report (Part 1/1)

## Source & Profile
- **Source:** tools
- **Profile:** `dev`
- **Generated At:** 2025-12-07 12:48:23 (UTC)
- **Max File Bytes:** unlimited
- **Spec-Version:** 2.3
- **Contract:** wc-merge-report
- **Contract-Version:** 2.3
- **Profile Use-Case:** Tools – Code/Review Snapshot
- **Declared Purpose:** Tools – Index
- **Scope:** single repo `tools`
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
  scope: "single repo `tools`"
  source_repos: ['tools']
  path_filter: null
  ext_filter: null
  extras:
    health: true
    organism_index: true
    fleet_panorama: false
    augment_sidecar: true
    delta_reports: false
  health:
    status: "ok"
    missing: ['contracts']
  augment:
    sidecar: "tools_augment.yml"
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

- **Total Files:** 43 (Text: 43)
- **Total Size:** 475.12 KB
- **Included Content:** 36 files (full)
- **Coverage:** 36/43 Textdateien mit Inhalt (`full`/`truncated`)

### Repo Snapshots

- `tools` → 43 files (43 relevant text, 475.12 KB, 36 with content)

**Folder Highlights:**
- Code: `scripts`
- Infra: `.github, .wgx`

### Organism Overview

- AI-Kontext-Organe: 5 Datei(en) (`ai-context`)
- Contracts: 0 Datei(en) (category = `contract`)
- Pipelines (CI/CD): 6 Datei(en) (Tag `ci`)
- Fleet-/WGX-Profile: 2 Datei(en) (Tag `wgx-profile`)

<!-- @health:start -->
## 🩺 Repo Health

### ✅ `tools` – OK

- **Total Files:** 43
- **Categories:** config=14, doc=11, source=18
- **Indicators:** README: yes, WGX Profile: yes, CI: yes, Contracts: no, AI Context: yes
- **Warnings:**
  - No contracts found
- **Recommendations:**
  - Consider adding contract schemas

<!-- @health:end -->
<!-- @organism-index:start -->
## 🧬 Organism Index

**AI-Context:**
- `.ai-context.yml`
- `merger/repomerger/heimgewebe-merge/README.md`
- `merger/wc-merger/README.md`
- `README.md`
- `scripts/README.md`

**CI & Pipelines:**
- `.github/workflows/ai-context-guard.yml`
- `.github/workflows/contracts-validate.yml`
- `.github/workflows/metrics.yml`
- `.github/workflows/pr-heimgewebe-commands.yml`
- `.github/workflows/validate-merges.yml`
- `.github/workflows/wgx-guard.yml`

**WGX-Profile:**
- `.wgx/profile.example.yml`
- `.wgx/profile.yml`

<!-- @organism-index:end -->
