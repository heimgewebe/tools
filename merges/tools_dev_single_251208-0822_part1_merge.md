# WC-Merge Report (Part 1/1)

## Source & Profile
- **Source:** tools
- **Profile:** `dev`
- **Generated At:** 2025-12-08 08:22:47 (UTC)
- **Max File Bytes:** unlimited
- **Spec-Version:** 2.3
- **Contract:** wc-merge-report
- **Contract-Version:** 2.3
- **Profile Use-Case:** Tools – Code/Review Snapshot
- **Declared Purpose:** Tools – Index
- **Scope:** single repo `tools`
- **Path Filter:** `none (full tree)`
- **Extension Filter:** `none (all text types)`
- **Coverage:** 80% (37/46 text files with content)

<!-- @meta:start -->
```yaml
merge:
  augment:
    sidecar: tools_augment.yml
  contract: wc-merge-report
  contract_version: '2.3'
  delta:
    enabled: true
  ext_filter: none (all text types)
  extras:
    augment_sidecar: true
    delta_reports: true
    health: true
    organism_index: true
  health:
    missing:
    - contracts
    status: ok
  max_file_bytes: 0
  path_filter: none (full tree)
  plan_only: false
  profile: dev
  scope: single repo `tools`
  source_repos:
  - tools
  spec_version: '2.3'
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

- **Total Files:** 46 (Text: 46)
- **Total Size:** 817.56 KB
- **Included Content:** 37 files (full)
- **Coverage:** 37/46 Textdateien mit Inhalt (`full`/`truncated`)

### Repo Snapshots

- `tools` → 46 files (46 relevant text, 817.56 KB, 37 with content)

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

- **Total Files:** 46
- **Categories:** config=15, doc=13, source=18
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
<!-- @augment:start -->
## 🧩 Augment Intelligence

**Sidecar:** `tools_augment.yml`

### Hotspots
- `merger/wc-merger/merge_core.py` – Complex branching logic with multiple profile modes (Severity: medium; Lines: [1000, 1100])
- `merger/wc-merger/wc-merger.py` – UI state management and Pythonista-specific code (Severity: low; Lines: [200, 400])

### Suggestions
- Consider extracting profile logic into strategy pattern classes
- Add comprehensive unit tests for health and organism layers
- Document the relationship between merge_core and wc-extractor
- Consider splitting merge_core.py into smaller modules

### Risks
- Large merges may exhaust Pythonista memory on iOS
- Multi-part merges need proper header normalization
- Delta reports depend on wc-extractor being available

### Dependencies
- Pythonista (optional) – iOS UI support
- wc-extractor (optional) – ZIP import and delta generation

### Priorities
- P1: Complete all 5 stages of super-merger roadmap (in-progress)
- P2: Add contract validation for all extras (pending)
- P3: Improve test coverage (pending)

### Context
- **coding_style:** Python 3.7+, type hints, dataclasses
- **architecture:** Generator-based report building for memory efficiency
- **testing:** Manual testing via Pythonista and CLI
- **deployment:** Runs on iOS (Pythonista) and Linux/macOS (CLI)

<!-- @augment:end -->
## 📁 Structure

```
📁 tools/
    📁 .github/
        📁 workflows/
            📄 ai-context-guard.yml
            📄 contracts-validate.yml
            📄 metrics.yml
            📄 pr-heimgewebe-commands.yml
            📄 validate-merges.yml
            📄 wgx-guard.yml
    📁 .wgx/
        📄 profile.example.yml
        📄 profile.yml
    📁 merger/
        📁 ordnermerger/
            📄 __init__.py
            📄 merger_lib.py
            📄 ordnermerger.py
            📄 repomerger_lib.py
        📁 repomerger/
            📁 heimgewebe-merge/
                📄 .gitignore
                📄 README.md
                📄 merge.py
                📄 run.sh
            📄 hauski-merger.py
            📄 repomerger.py
            📄 weltgewebe-merger.py
            📄 wgx-merger.py
        📁 wc-merger/
            📁 merges/
                📄 test_repo_dev_single_251207-1923_part1_merge.md
            📄 README.md
            📄 SUPER_MERGER_IMPLEMENTATION.md
            📄 merge_core.py
            📄 tools_augment.yml
            📄 validate_merge_meta.py
            📄 wc-extractor.py
            📄 wc-merge-delta.schema.json
            📄 wc-merge-report.schema.json
            📄 wc-merger-spec.md
            📄 wc-merger.py
    📁 merges/
        📄 tools_dev_single_251208-0816_part1_merge.md
    📁 scripts/
        📄 README.md
        📄 jsonl-compact.sh
        📄 jsonl-tail.sh
        📄 jsonl-validate.sh
        📄 wgx-metrics-snapshot.sh
    📁 test_out/
        📄 test-repo_dev_repo_251207-1017_part1_merge.md
        📄 test-repo_dev_repo_251207-1017_part2_merge.md
        📄 test-repo_dev_repo_251207-1017_part3_merge.md
    📄 .ai-context.yml
    📄 .gitignore
    📄 FIXES_APPLIED.md
    📄 INCONSISTENCIES.md
    📄 README.md
    📄 tools_augment.yml
```

## Index
- [Source](#cat-source)
- [Doc](#cat-doc)
- [Config](#cat-config)
- [Contract](#cat-contract)
- [Test](#cat-test)
- [CI Pipelines](#tag-ci)
- [WGX Profiles](#tag-wgx-profile)

## Category: source {#cat-source}
- [`merger/ordnermerger/__init__.py`](#file-tools-merger-ordnermerger-__init__-py)
- [`merger/ordnermerger/merger_lib.py`](#file-tools-merger-ordnermerger-merger_lib-py)
- [`merger/ordnermerger/ordnermerger.py`](#file-tools-merger-ordnermerger-ordnermerger-py)
- [`merger/ordnermerger/repomerger_lib.py`](#file-tools-merger-ordnermerger-repomerger_lib-py)
- [`merger/repomerger/hauski-merger.py`](#file-tools-merger-repomerger-hauski-merger-py)
- [`merger/repomerger/heimgewebe-merge/merge.py`](#file-tools-merger-repomerger-heimgewebe-merge-merge-py)
- [`merger/repomerger/heimgewebe-merge/run.sh`](#file-tools-merger-repomerger-heimgewebe-merge-run-sh)
- [`merger/repomerger/repomerger.py`](#file-tools-merger-repomerger-repomerger-py)
- [`merger/repomerger/weltgewebe-merger.py`](#file-tools-merger-repomerger-weltgewebe-merger-py)
- [`merger/repomerger/wgx-merger.py`](#file-tools-merger-repomerger-wgx-merger-py)
- [`merger/wc-merger/merge_core.py`](#file-tools-merger-wc-merger-merge_core-py)
- [`merger/wc-merger/validate_merge_meta.py`](#file-tools-merger-wc-merger-validate_merge_meta-py)
- [`merger/wc-merger/wc-extractor.py`](#file-tools-merger-wc-merger-wc-extractor-py)
- [`merger/wc-merger/wc-merger.py`](#file-tools-merger-wc-merger-wc-merger-py)
- [`scripts/jsonl-compact.sh`](#file-tools-scripts-jsonl-compact-sh)
- [`scripts/jsonl-tail.sh`](#file-tools-scripts-jsonl-tail-sh)
- [`scripts/jsonl-validate.sh`](#file-tools-scripts-jsonl-validate-sh)
- [`scripts/wgx-metrics-snapshot.sh`](#file-tools-scripts-wgx-metrics-snapshot-sh)

## Category: doc {#cat-doc}
- [`FIXES_APPLIED.md`](#file-tools-FIXES_APPLIED-md)
- [`INCONSISTENCIES.md`](#file-tools-INCONSISTENCIES-md)
- [`merger/repomerger/heimgewebe-merge/README.md`](#file-tools-merger-repomerger-heimgewebe-merge-README-md)
- [`merger/wc-merger/merges/test_repo_dev_single_251207-1923_part1_merge.md`](#file-tools-merger-wc-merger-merges-test_repo_dev_single_251207-1923_part1_merge-md)
- [`merger/wc-merger/README.md`](#file-tools-merger-wc-merger-README-md)
- [`merger/wc-merger/SUPER_MERGER_IMPLEMENTATION.md`](#file-tools-merger-wc-merger-SUPER_MERGER_IMPLEMENTATION-md)
- [`merger/wc-merger/wc-merger-spec.md`](#file-tools-merger-wc-merger-wc-merger-spec-md)
- [`merges/tools_dev_single_251208-0816_part1_merge.md`](#file-tools-merges-tools_dev_single_251208-0816_part1_merge-md)
- [`README.md`](#file-tools-README-md)
- [`scripts/README.md`](#file-tools-scripts-README-md)
- [`test_out/test-repo_dev_repo_251207-1017_part1_merge.md`](#file-tools-test_out-test-repo_dev_repo_251207-1017_part1_merge-md)
- [`test_out/test-repo_dev_repo_251207-1017_part2_merge.md`](#file-tools-test_out-test-repo_dev_repo_251207-1017_part2_merge-md)
- [`test_out/test-repo_dev_repo_251207-1017_part3_merge.md`](#file-tools-test_out-test-repo_dev_repo_251207-1017_part3_merge-md)

## Category: config {#cat-config}
- [`.ai-context.yml`](#file-tools--ai-context-yml)
- [`.github/workflows/ai-context-guard.yml`](#file-tools--github-workflows-ai-context-guard-yml)
- [`.github/workflows/contracts-validate.yml`](#file-tools--github-workflows-contracts-validate-yml)
- [`.github/workflows/metrics.yml`](#file-tools--github-workflows-metrics-yml)
- [`.github/workflows/pr-heimgewebe-commands.yml`](#file-tools--github-workflows-pr-heimgewebe-commands-yml)
- [`.github/workflows/validate-merges.yml`](#file-tools--github-workflows-validate-merges-yml)
- [`.github/workflows/wgx-guard.yml`](#file-tools--github-workflows-wgx-guard-yml)
- [`.gitignore`](#file-tools--gitignore)
- [`.wgx/profile.example.yml`](#file-tools--wgx-profile-example-yml)
- [`.wgx/profile.yml`](#file-tools--wgx-profile-yml)
- [`merger/repomerger/heimgewebe-merge/.gitignore`](#file-tools-merger-repomerger-heimgewebe-merge--gitignore)
- [`merger/wc-merger/tools_augment.yml`](#file-tools-merger-wc-merger-tools_augment-yml)
- [`merger/wc-merger/wc-merge-delta.schema.json`](#file-tools-merger-wc-merger-wc-merge-delta-schema-json)
- [`merger/wc-merger/wc-merge-report.schema.json`](#file-tools-merger-wc-merger-wc-merge-report-schema-json)
- [`tools_augment.yml`](#file-tools-tools_augment-yml)

## Tag: ci {#tag-ci}
- [`.github/workflows/ai-context-guard.yml`](#file-tools--github-workflows-ai-context-guard-yml)
- [`.github/workflows/contracts-validate.yml`](#file-tools--github-workflows-contracts-validate-yml)
- [`.github/workflows/metrics.yml`](#file-tools--github-workflows-metrics-yml)
- [`.github/workflows/pr-heimgewebe-commands.yml`](#file-tools--github-workflows-pr-heimgewebe-commands-yml)
- [`.github/workflows/validate-merges.yml`](#file-tools--github-workflows-validate-merges-yml)
- [`.github/workflows/wgx-guard.yml`](#file-tools--github-workflows-wgx-guard-yml)

## Tag: wgx-profile {#tag-wgx-profile}
- [`.wgx/profile.example.yml`](#file-tools--wgx-profile-example-yml)
- [`.wgx/profile.yml`](#file-tools--wgx-profile-yml)

## 🧾 Manifest {#manifest}

| Root | Path | Category | Tags | Roles | Size | Included | MD5 |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| `tools` | [`.ai-context.yml`](#file-tools--ai-context-yml) | `config` | ai-context | ai-context | 809.00 B | `full` | `6f3438f39a6010a649a2abf1446dbb8d` |
| `tools` | [`.github/workflows/ai-context-guard.yml`](#file-tools--github-workflows-ai-context-guard-yml) | `config` | ci | ci, ai-context | 595.00 B | `full` | `7feeb042ecb013c1b3dbee5f8161f2e0` |
| `tools` | [`.github/workflows/contracts-validate.yml`](#file-tools--github-workflows-contracts-validate-yml) | `config` | ci | ci | 6.29 KB | `full` | `db43d69008c794c800b239dd92e598ce` |
| `tools` | [`.github/workflows/metrics.yml`](#file-tools--github-workflows-metrics-yml) | `config` | ci | ci | 1.55 KB | `full` | `3f9b352b8cb75eefc909f779afc5f13f` |
| `tools` | [`.github/workflows/pr-heimgewebe-commands.yml`](#file-tools--github-workflows-pr-heimgewebe-commands-yml) | `config` | ci | ci | 519.00 B | `full` | `c31bc0dfcb4728f961aa3d6c91aabfca` |
| `tools` | [`.github/workflows/validate-merges.yml`](#file-tools--github-workflows-validate-merges-yml) | `config` | ci | ci | 1.09 KB | `full` | `566b7738acad3e29534a413a51457b30` |
| `tools` | [`.github/workflows/wgx-guard.yml`](#file-tools--github-workflows-wgx-guard-yml) | `config` | ci | ci | 615.00 B | `full` | `e4d38b4afe1b53a20a2360e2ee9cd42f` |
| `tools` | [`.gitignore`](#file-tools--gitignore) | `config` | - | - | 173.00 B | `full` | `b0a081de474818b55a394e69935a127e` |
| `tools` | [`.wgx/profile.example.yml`](#file-tools--wgx-profile-example-yml) | `config` | wgx-profile | wgx-profile | 710.00 B | `full` | `38054d37bbea96723c93319717551341` |
| `tools` | [`.wgx/profile.yml`](#file-tools--wgx-profile-yml) | `config` | wgx-profile | wgx-profile | 1.87 KB | `full` | `a6bf0ed2cb8a24efdd9b49b8ef12ead1` |
| `tools` | [`FIXES_APPLIED.md`](#file-tools-FIXES_APPLIED-md) | `doc` | - | doc | 5.99 KB | `meta-only` | `fe13f8e13d8e893130698f2a76538ae8` |
| `tools` | [`INCONSISTENCIES.md`](#file-tools-INCONSISTENCIES-md) | `doc` | - | doc | 6.83 KB | `meta-only` | `37c811234d279e9257792f84b8032120` |
| `tools` | [`merger/ordnermerger/__init__.py`](#file-tools-merger-ordnermerger-__init__-py) | `source` | - | - | 100.00 B | `full` | `2e057065676352f58610f0542fdefcc8` |
| `tools` | [`merger/ordnermerger/merger_lib.py`](#file-tools-merger-ordnermerger-merger_lib-py) | `source` | - | - | 7.75 KB | `full` | `b57133b9e962d8655fa5680672fdfbbd` |
| `tools` | [`merger/ordnermerger/ordnermerger.py`](#file-tools-merger-ordnermerger-ordnermerger-py) | `source` | - | - | 8.81 KB | `full` | `492f2bab547923962cafe6c2ed168deb` |
| `tools` | [`merger/ordnermerger/repomerger_lib.py`](#file-tools-merger-ordnermerger-repomerger_lib-py) | `source` | - | - | 11.54 KB | `full` | `8c5a002d6b4a2dd7f0fa54b0226925c9` |
| `tools` | [`merger/repomerger/hauski-merger.py`](#file-tools-merger-repomerger-hauski-merger-py) | `source` | - | - | 22.96 KB | `full` | `56ae7f2907db9a2abbc69b6edeb45bd4` |
| `tools` | [`merger/repomerger/heimgewebe-merge/.gitignore`](#file-tools-merger-repomerger-heimgewebe-merge--gitignore) | `config` | - | - | 19.00 B | `full` | `aff18e7ddf2da8c1bebfb400cf4cbb17` |
| `tools` | [`merger/repomerger/heimgewebe-merge/merge.py`](#file-tools-merger-repomerger-heimgewebe-merge-merge-py) | `source` | - | - | 7.76 KB | `full` | `f290edc575f3ca5c0a20c55eddf8a65a` |
| `tools` | [`merger/repomerger/heimgewebe-merge/README.md`](#file-tools-merger-repomerger-heimgewebe-merge-README-md) | `doc` | ai-context | ai-context, doc | 1.70 KB | `full` | `a62845cc3c979895f57c6f93a6f9470d` |
| `tools` | [`merger/repomerger/heimgewebe-merge/run.sh`](#file-tools-merger-repomerger-heimgewebe-merge-run-sh) | `source` | - | - | 2.16 KB | `full` | `30e0c3b4f3f7a8cb125626cd74cb6ff4` |
| `tools` | [`merger/repomerger/repomerger.py`](#file-tools-merger-repomerger-repomerger-py) | `source` | - | - | 23.08 KB | `full` | `2d5415f3ac85f934e1f7e74b3c28ae6c` |
| `tools` | [`merger/repomerger/weltgewebe-merger.py`](#file-tools-merger-repomerger-weltgewebe-merger-py) | `source` | - | - | 22.82 KB | `full` | `e4397357d4bca19cbf68ca562626b5d4` |
| `tools` | [`merger/repomerger/wgx-merger.py`](#file-tools-merger-repomerger-wgx-merger-py) | `source` | - | - | 23.00 KB | `full` | `3bacf2a09ed28e057069e6c57adfc372` |
| `tools` | [`merger/wc-merger/merge_core.py`](#file-tools-merger-wc-merger-merge_core-py) | `source` | - | - | 75.18 KB | `full` | `b45490c25ee18e61edcfe6ae40ff9ea5` |
| `tools` | [`merger/wc-merger/merges/test_repo_dev_single_251207-1923_part1_merge.md`](#file-tools-merger-wc-merger-merges-test_repo_dev_single_251207-1923_part1_merge-md) | `doc` | - | doc | 1.82 KB | `meta-only` | `af435c16c9cd760fc0447f9207b23230` |
| `tools` | [`merger/wc-merger/README.md`](#file-tools-merger-wc-merger-README-md) | `doc` | ai-context | ai-context, doc | 6.72 KB | `full` | `63c94fde1efcff1050e511a744f9e742` |
| `tools` | [`merger/wc-merger/SUPER_MERGER_IMPLEMENTATION.md`](#file-tools-merger-wc-merger-SUPER_MERGER_IMPLEMENTATION-md) | `doc` | - | doc | 3.82 KB | `meta-only` | `58d5941cf0bfe2cca897aac676bf1c62` |
| `tools` | [`merger/wc-merger/tools_augment.yml`](#file-tools-merger-wc-merger-tools_augment-yml) | `config` | - | - | 400.00 B | `full` | `68576b277d2584c7c5a6196a9324a4ea` |
| `tools` | [`merger/wc-merger/validate_merge_meta.py`](#file-tools-merger-wc-merger-validate_merge_meta-py) | `source` | - | - | 3.24 KB | `full` | `7627015fff49c8e17a82febe8f4b4cb8` |
| `tools` | [`merger/wc-merger/wc-extractor.py`](#file-tools-merger-wc-merger-wc-extractor-py) | `source` | - | - | 19.71 KB | `full` | `e4c6e2660f5280b4f2ea6afd0d2a683b` |
| `tools` | [`merger/wc-merger/wc-merge-delta.schema.json`](#file-tools-merger-wc-merger-wc-merge-delta-schema-json) | `config` | - | - | 1.22 KB | `full` | `155b7dbfd8cf6185fa8472ee279c7ebf` |
| `tools` | [`merger/wc-merger/wc-merge-report.schema.json`](#file-tools-merger-wc-merger-wc-merge-report-schema-json) | `config` | - | - | 4.02 KB | `full` | `fd7fd4981baccb5dd65057c18eb749c8` |
| `tools` | [`merger/wc-merger/wc-merger-spec.md`](#file-tools-merger-wc-merger-wc-merger-spec-md) | `doc` | - | doc | 6.72 KB | `meta-only` | `666606393d813fad98907e90b35a1fde` |
| `tools` | [`merger/wc-merger/wc-merger.py`](#file-tools-merger-wc-merger-wc-merger-py) | `source` | - | - | 43.55 KB | `full` | `33fb8321cd2a8b3883fc5e816b541bd2` |
| `tools` | [`merges/tools_dev_single_251208-0816_part1_merge.md`](#file-tools-merges-tools_dev_single_251208-0816_part1_merge-md) | `doc` | - | doc | 334.51 KB | `meta-only` | `e82a335c0b22a0e1fdac7519bede89bc` |
| `tools` | [`README.md`](#file-tools-README-md) | `doc` | ai-context | ai-context, doc | 1.16 KB | `full` | `95c1304a1cf70a8aa6305bd21bc6a96e` |
| `tools` | [`scripts/jsonl-compact.sh`](#file-tools-scripts-jsonl-compact-sh) | `source` | script | tool | 375.00 B | `full` | `282492c366277ca1a983eac375b7e22a` |
| `tools` | [`scripts/jsonl-tail.sh`](#file-tools-scripts-jsonl-tail-sh) | `source` | script | tool | 199.00 B | `full` | `2c26222e41af7e908c1f7a837e5953ba` |
| `tools` | [`scripts/jsonl-validate.sh`](#file-tools-scripts-jsonl-validate-sh) | `source` | script | tool | 3.20 KB | `full` | `adf4b1b63385ab361e3684c270948d2e` |
| `tools` | [`scripts/README.md`](#file-tools-scripts-README-md) | `doc` | ai-context | ai-context, doc | 705.00 B | `full` | `8b5fd3bbea862544e86d1553b30fec6d` |
| `tools` | [`scripts/wgx-metrics-snapshot.sh`](#file-tools-scripts-wgx-metrics-snapshot-sh) | `source` | script | tool | 1.74 KB | `full` | `31a8b111ad533c6d71f66e3b2f564c4b` |
| `tools` | [`test_out/test-repo_dev_repo_251207-1017_part1_merge.md`](#file-tools-test_out-test-repo_dev_repo_251207-1017_part1_merge-md) | `doc` | - | doc | 51.19 KB | `meta-only` | `cee9d8f10f9fc9fb0d679a2675ee9bd4` |
| `tools` | [`test_out/test-repo_dev_repo_251207-1017_part2_merge.md`](#file-tools-test_out-test-repo_dev_repo_251207-1017_part2_merge-md) | `doc` | - | doc | 48.75 KB | `meta-only` | `96458be1e867e0eddb1b77d39aa4c1f7` |
| `tools` | [`test_out/test-repo_dev_repo_251207-1017_part3_merge.md`](#file-tools-test_out-test-repo_dev_repo_251207-1017_part3_merge-md) | `doc` | - | doc | 48.75 KB | `meta-only` | `c818ddae575d72d6d55538dd44650ca9` |
| `tools` | [`tools_augment.yml`](#file-tools-tools_augment-yml) | `config` | - | - | 1.96 KB | `full` | `1d91951e03ce43db6407bb43a757719a` |

## 📄 Content

## 📦 tools {#repo-tools}

<a id="file-tools--ai-context-yml"></a>
### `.ai-context.yml`
- Category: config
- Tags: ai-context
- Size: 809.00 B
- Included: full
- MD5: 6f3438f39a6010a649a2abf1446dbb8d

```yaml
ai_context_version: 1.0

project:
  name: tools
  summary: Pinned tool installers & shared scripts (e.g., yq/just pin).
  role: shared_dev_tooling
  primary_language: bash
  visibility: internal

dependencies:
  internal: []
  external:
    - name: curl
    - name: bash
      version: ">=4"

architecture:
  entrypoints:
    - scripts/tools/*-pin.sh
  key_paths:
    - path: scripts/tools/yq-pin.sh
      purpose: Install/pin yq v4
  data_flow:
    input: CI & local setup
    processing: download/pin utilities
    output: tools/bin/*

conventions:
  branching: "main, feature/*"
  commit_prefix: "tools"
  ci_platform: github_actions

documentation:
  runbook: docs/runbook.md

ai_guidance:
  do:
    - fail fast on missing commands; provide actionable hints
  dont:
    - silently skip version mismatches

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools--github-workflows-ai-context-guard-yml"></a>
### `.github/workflows/ai-context-guard.yml`
- Category: config
- Tags: ci
- Size: 595.00 B
- Included: full
- MD5: 7feeb042ecb013c1b3dbee5f8161f2e0

```yaml
name: ai-context-guard
permissions:
  contents: read
on:
  pull_request:
    paths:
      - ".ai-context.yml"
      - ".github/workflows/ai-context-guard.yml"
  push:
    branches: [ main ]
    paths:
      - ".ai-context.yml"
      - ".github/workflows/ai-context-guard.yml"
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Ensure AI context exists and is non-empty
        run: |
          if [ ! -s .ai-context.yml ]; then
            echo "::error file=.ai-context.yml::.ai-context.yml is missing or empty"
            exit 1
          fi

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools--github-workflows-contracts-validate-yml"></a>
### `.github/workflows/contracts-validate.yml`
- Category: config
- Tags: ci
- Size: 6.29 KB
- Included: full
- MD5: db43d69008c794c800b239dd92e598ce

```yaml
name: "contracts-validate"

permissions:
  contents: read

concurrency:
  # Keep PR-specific groups to prevent cross-branch cancellations.
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

on:
  workflow_dispatch: {}
  push:
    paths:
      - "json/**"
      - "proto/**"
      - "fixtures/**"
      - ".github/workflows/**"   # ensure pin guard runs when ANY workflow changes
  pull_request:
    paths:
      - "json/**"
      - "proto/**"
      - "fixtures/**"
      - ".github/workflows/**"   # ensure pin guard runs when ANY workflow changes

defaults:
  run:
    shell: bash --noprofile --norc -euo pipefail {0}

env:
  FAIL_ON_NO_BASE: "1"
  ALLOW_REMOVALS: "0"

jobs:
  version-sync-check:
    name: "Security: enforce static pin for contracts reusable workflow"
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 1
          persist-credentials: false

      - name: Verify 'uses:' pins for heimgewebe/contracts
        env:
          REQUIRED_REPO: "heimgewebe/contracts/.github/workflows/contracts-ajv-reusable.yml"
          REQUIRED_REF: "contracts-v1"
        run: |
          set -euo pipefail
          shopt -s extglob

          files=()
          while IFS= read -r -d '' f; do files+=("$f"); done < \
            <(git ls-files -z -- '.github/workflows/*.yml' '.github/workflows/*.yaml' || true)

          [[ ${#files[@]} -gt 0 ]] || { echo "::notice::No workflow files"; exit 0; }

          extract_pair() {
            local line="$1"
            line="${line%%#*}"
            line="${line##+([[:space:]])}"
            line="${line%%+([[:space:]])}"
            if [[ "$line" =~ ^(-[[:space:]]*)?uses:[[:space:]]*'([^']+)' ]]; then
              echo "${BASHREMATCH[2]}"; return 0
            fi
            if [[ "$line" =~ ^(-[[:space:]]*)?uses:[[:space:]]*\"([^\"]+)\" ]]; then
              echo "${BASHREMATCH[2]}"; return 0
            fi
            if [[ "$line" =~ ^(-[[:space:]]*)?uses:[[:space:]]*([^[:space:]#]+) ]]; then
              echo "${BASHREMATCH[2]}"; return 0
            fi
            return 1
          }

          check_pair() {
            local wf="$1" repo="$2" ref="$3"
            [[ "$repo" == "$REQUIRED_REPO" ]] || return 0
            if [[ "$ref" =~ (\$\{|\$\(|\$[A-Za-z_]) ]]; then
              echo "::error file=$wf::Dynamic ref not allowed: $ref"; return 1
            fi
            if [[ "$ref" != "$REQUIRED_REF" ]]; then
              echo "::error file=$wf::Pin mismatch: expected '$REQUIRED_REF', got '$ref'"; return 1
            fi
            return 0
          }

          mismatches=0
          for wf in "${files[@]}"; do
            while IFS= read -r line || [[ -n "$line" ]]; do
              if pair="$(extract_pair "$line")"; then
                [[ "$pair" == *"@"* ]] || continue
                repo="${pair%@*}"; ref="${pair#*@}"
                if ! check_pair "$wf" "$repo" "$ref"; then mismatches=1; fi
              fi
            done < "$wf"
          done

          [[ $mismatches -eq 0 ]] || exit 1
          echo "::notice::✅ All version pins validated"

  guard:
    name: "Security: guard deletion policy (json/proto)"
    runs-on: ubuntu-latest
    timeout-minutes: 8
    env:
      GH_DEFAULT_BRANCH: ${{ github.event.repository.default_branch || 'main' }}
      GH_PR_BASE_SHA: ${{ github.event.pull_request.base.sha }}
      GH_PUSH_BEFORE: ${{ github.event.before }}
      PROTECTED_REGEX: '^(json|proto)/'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

      - name: Enforce guard policy
        run: |
          set -euo pipefail
          is_truthy() { case "${1:-0}" in 1|true|yes|on) return 0 ;; esac; return 1; }

          if is_truthy "${ALLOW_REMOVALS:-0}"; then
            echo "::notice::ALLOW_REMOVALS=1 → skipping guard"
            exit 0
          fi

          base=""
          base_src=""

          if [[ -n "${GH_PR_BASE_SHA:-}" ]] && git rev-parse --verify "${GH_PR_BASE_SHA}^{commit}" &>/dev/null; then
            if mb="$(git merge-base "$GH_PR_BASE_SHA" HEAD 2>/dev/null)"; then
              base="$mb"; base_src="merge-base(pr_base,HEAD)"
            fi
          fi

          if [[ -z "$base" && -n "${GH_PUSH_BEFORE:-}" && ! "${GH_PUSH_BEFORE}" =~ ^0{40}$ ]] \
             && git rev-parse --verify "${GH_PUSH_BEFORE}^{commit}" &>/dev/null; then
            base="$GH_PUSH_BEFORE"; base_src="push_before"
          fi

          if [[ -z "$base" ]]; then
            git fetch -q origin "${GH_DEFAULT_BRANCH}" || true
            if git rev-parse "origin/${GH_DEFAULT_BRANCH}^{commit}" &>/dev/null; then
              if mb="$(git merge-base "origin/${GH_DEFAULT_BRANCH}" HEAD 2>/dev/null)"; then
                base="$mb"; base_src="merge-base(origin/${GH_DEFAULT_BRANCH},HEAD)"
              fi
            fi
          fi

          if [[ -z "$base" ]]; then
            if is_truthy "${FAIL_ON_NO_BASE:-1}"; then
              echo "::error::Cannot determine merge-base"; exit 1
            else
              echo "::notice::No merge-base found - skipping guard"; exit 0
            fi
          fi

          echo "::notice::Checking diff from ${base:0:8}...HEAD (source=$base_src)"

          blocked=()
          while IFS=$'\t' read -r -a fields; do
            status="${fields[0]}"
            p1="${fields[1]}"
            p2="${fields[2]:-}"
            [[ "$p1" =~ ${PROTECTED_REGEX} ]] || continue
            case "$status" in
              D)  blocked+=("DELETE: $p1") ;;
              R*) blocked+=("RENAME: $p1 → ${p2:-(unknown destination)}") ;;
            esac
          done < <(git diff --name-status --diff-filter=DR "${base}...HEAD")

          if (( ${#blocked[@]} )); then
            echo "::group::❌ Protected file deletions blocked"
            printf '  • %s\n' "${blocked[@]}" | sort -u
            echo "::endgroup::"
            echo "::error::Guard violation"
            exit 1
          fi

          echo "::notice::✅ Guard passed"

  validate:
    name: "Validate fixtures via reusable workflow"
    needs: [version-sync-check, guard]
    uses: heimgewebe/contracts/.github/workflows/contracts-ajv-reusable.yml@contracts-v1
    secrets: inherit
    with:
      fixtures_glob: ${{ vars.FIXTURES_GLOB || 'fixtures/**/*.jsonl' }}

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools--github-workflows-metrics-yml"></a>
### `.github/workflows/metrics.yml`
- Category: config
- Tags: ci
- Size: 1.55 KB
- Included: full
- MD5: 3f9b352b8cb75eefc909f779afc5f13f

```yaml
name: "📊 Metrics Snapshot & Validation"
permissions:
  contents: read          # Repo lesen, um Skripte auszuführen
  actions: write          # notwendig für upload-artifact
  checks: write
on:
  workflow_dispatch:
  schedule:
    - cron: "0 * * * *"

env:
  METRICS_SCHEMA_URL: https://raw.githubusercontent.com/heimgewebe/metarepo/contracts-v1/contracts/wgx/metrics.json
  HAUSKI_POST_URL: ${{ secrets.HAUSKI_METRICS_URL }}

jobs:
  snapshot:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Ensure Node for ajv-cli
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Snapshot metrics
        run: bash scripts/wgx-metrics-snapshot.sh --json
      - name: Fetch AJV schema (local file)
        run: |
          mkdir -p .ci
          curl -fsSL "$METRICS_SCHEMA_URL" -o .ci/metrics.schema.json

      - name: Validate metrics contract
        run: npx --yes ajv-cli@5 validate -s .ci/metrics.schema.json -d metrics.json

      - name: Optional POST to hausKI
        if: ${{ env.HAUSKI_POST_URL && env.HAUSKI_POST_URL != '' }}
        run: |
          curl --fail --silent --show-error --retry 3 --retry-delay 2 \
            -H 'Content-Type: application/json' \
            --data @metrics.json \
            "$HAUSKI_POST_URL"
        continue-on-error: true

      - name: Upload metrics.json artifact
        uses: actions/upload-artifact@v4
        with:
          name: metrics-snapshot
          path: metrics.json
          retention-days: 7

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools--github-workflows-pr-heimgewebe-commands-yml"></a>
### `.github/workflows/pr-heimgewebe-commands.yml`
- Category: config
- Tags: ci
- Size: 519.00 B
- Included: full
- MD5: c31bc0dfcb4728f961aa3d6c91aabfca

```yaml
---
name: PR Heimgewebe commands

"on":
  issue_comment:
    types: [created]

permissions:
  contents: read
  issues: write
  pull-requests: write

jobs:
  dispatch:
    if: github.event.issue.pull_request != null
    uses: heimgewebe/metarepo/.github/workflows/heimgewebe-command-dispatch.yml@main
    secrets:
      HEIMGEWEBE_APP_ID: ${{ secrets.HEIMGEWEBE_APP_ID }}
      HEIMGEWEBE_APP_PRIVATE_KEY: ${{ secrets.HEIMGEWEBE_APP_PRIVATE_KEY }}
      HEIMGEWEBE_AUTOBOT_TOKEN: ${{ secrets.HEIMGEWEBE_AUTOBOT_TOKEN }}

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools--github-workflows-validate-merges-yml"></a>
### `.github/workflows/validate-merges.yml`
- Category: config
- Tags: ci
- Size: 1.09 KB
- Included: full
- MD5: 566b7738acad3e29534a413a51457b30

```yaml
name: validate-merges

on:
  push:
    paths:
      - "merges/**.md"
      - "merger/wc-merger/**"
      - ".github/workflows/validate-merges.yml"
  workflow_dispatch: {}

permissions:
  contents: read

jobs:
  validate-merge-meta:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pyyaml jsonschema

      - name: Validate merge meta blocks
        working-directory: merger/wc-merger
        run: |
          set -e
          # Alle Merge-Dateien finden, z. B. tools_*_merge.md oder allgemein *.md
          files=$(ls ../../merges/*.md 2>/dev/null || true)

          if [ -z "$files" ]; then
            echo "Keine Merge-Dateien unter merges/ gefunden – nichts zu validieren."
            exit 0
          fi

          echo "Validiere folgende Merge-Dateien:"
          echo "$files"

          python validate_merge_meta.py $files

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools--github-workflows-wgx-guard-yml"></a>
### `.github/workflows/wgx-guard.yml`
- Category: config
- Tags: ci
- Size: 615.00 B
- Included: full
- MD5: e4d38b4afe1b53a20a2360e2ee9cd42f

```yaml
name: wgx-guard

permissions:
  contents: read

on:
  pull_request:
    paths:
      - ".wgx/**"
      - ".github/workflows/**"
      - "scripts/**"
  push:
    branches: [ main ]
    paths:
      - ".wgx/**"
      - ".github/workflows/**"
      - "scripts/**"
  workflow_dispatch:

jobs:
  guard:
    name: "WGX guard (central)"
    uses: heimgewebe/wgx/.github/workflows/wgx-guard.yml@main
    secrets: inherit

    # Hinweis:
    # - Die eigentliche Logik (Profilvalidierung, Task-Aufruf etc.) liegt im zentralen WGX-Repo.
    # - Dieses Repo stellt das Profil (.wgx/profile.yml) und die konkreten Tasks bereit.

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools--gitignore"></a>
### `.gitignore`
- Category: config
- Tags: -
- Size: 173.00 B
- Included: full
- MD5: b0a081de474818b55a394e69935a127e

```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/
.tox/
.eggs/
.mypy_cache/
.pytest_cache/
*.swp
*.swo
*.swn
.DS_Store
metrics.json

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools--wgx-profile-example-yml"></a>
### `.wgx/profile.example.yml`
- Category: config
- Tags: wgx-profile
- Size: 710.00 B
- Included: full
- MD5: 38054d37bbea96723c93319717551341

```yaml
---
# Beispiel-WGX-Profil für heimgewebe/tools (WGX v1-Stil)
profile: tools-example
description: "Beispielprofil für WGX v1 in heimgewebe/tools"

wgx-version: ">=1.0.0"

class: bash-tooling

wgx:
  apiVersion: v1

lang:
  - shell

meta:
  org: heimgewebe
  repo: heimgewebe/tools
  maintainer: alexdermohr@gmail.com
  tags:
    - tools
    - metrics
    - wgx
  ci: true

tasks:
  smoke: |
    echo "[wgx.smoke] tools-example – Profil geladen"
  guard: |
    echo "[wgx.guard] tools-example – keine echten Checks (nur Beispielprofil)"
  metrics: |
    echo "[wgx.metrics] tools-example – Beispiel, bitte im echten Profil anpassen"
  snapshot: |
    echo "[wgx.snapshot] tools-example – Beispieltask"

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools--wgx-profile-yml"></a>
### `.wgx/profile.yml`
- Category: config
- Tags: wgx-profile
- Size: 1.87 KB
- Included: full
- MD5: a6bf0ed2cb8a24efdd9b49b8ef12ead1

```yaml
---
# WGX Profil für heimgewebe/tools
profile: heimgewebe-tools
description: "Host- und CI-Hilfsskripte für Heimgewebe"

# Semantische Version des hauski-/WGX-Profils (nicht dasselbe wie wgx CLI-Version)
wgx-version: ">=1.0.0"

# Fleet-Klasse dieses Repos – dient als Oberflächen-Typ für Tools
class: bash-tooling

wgx:
  apiVersion: v1

lang:
  - shell

meta:
  org: heimgewebe
  repo: heimgewebe/tools
  maintainer: alexdermohr@gmail.com
  tags:
    - tools
    - metrics
    - host
    - wgx
  ci: true

env:
  WGX_METRICS_OUTPUT: "metrics.json"

tasks:
  smoke: |
    echo "[wgx.smoke] tools – schneller Grundcheck"
    if [ -f scripts/wgx-metrics-snapshot.sh ]; then
      bash scripts/wgx-metrics-snapshot.sh --json || echo "[wgx.smoke] metrics-snapshot optional fehlgeschlagen"
    else
      echo "[wgx.smoke] kein scripts/wgx-metrics-snapshot.sh gefunden – skip."
    fi

  guard: |
    set -euo pipefail
    echo "[wgx.guard] tools – Shell-Skripte prüfen…"
    if [ -f scripts/wgx-metrics-snapshot.sh ]; then
      bash -n scripts/wgx-metrics-snapshot.sh
      if command -v shellcheck >/dev/null 2>&1; then
        shellcheck scripts/wgx-metrics-snapshot.sh
      else
        echo "[wgx.guard] shellcheck nicht installiert – nur bash -n ausgeführt."
      fi
    else
      echo "[wgx.guard] scripts/wgx-metrics-snapshot.sh fehlt – nichts zu prüfen."
    fi

  metrics: |
    echo "[wgx.metrics] tools – metrics-Snapshot (best effort)…"
    if [ -f scripts/wgx-metrics-snapshot.sh ]; then
      bash scripts/wgx-metrics-snapshot.sh --json || echo "[wgx.metrics] metrics-snapshot fehlgeschlagen."
    else
      echo "[wgx.metrics] kein metrics-Skript vorhanden – skip."
    fi

  snapshot: |
    echo "[wgx.snapshot] tools – Snapshot (best effort)…"
    if [ -f scripts/wgx-metrics-snapshot.sh ]; then
      bash scripts/wgx-metrics-snapshot.sh --json || true
    fi

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-ordnermerger-__init__-py"></a>
### `merger/ordnermerger/__init__.py`
- Category: source
- Tags: -
- Size: 100.00 B
- Included: full
- MD5: 2e057065676352f58610f0542fdefcc8

```python
# -*- coding: utf-8 -*-
"""
ordnermerger - Package for folder and repository merging utilities.
"""

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-ordnermerger-merger_lib-py"></a>
### `merger/ordnermerger/merger_lib.py`
- Category: source
- Tags: -
- Size: 7.75 KB
- Included: full
- MD5: b57133b9e962d8655fa5680672fdfbbd

```python
# -*- coding: utf-8 -*-
"""
merger_lib — Gemeinsame Hilfsfunktionen für ordnermerger Skripte.
"""

from __future__ import annotations
import hashlib
from pathlib import Path
from typing import TextIO

ENC = "utf-8"

# Robuster Satz von binären Erweiterungen
BINARY_EXTS = {
    # Bilder
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".heic", ".heif", ".psd", ".ai",
    # Audio & Video
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm",
    # Archive
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz",
    # Schriften
    ".ttf", ".otf", ".woff", ".woff2",
    # Dokumente
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pages", ".numbers", ".key",
    # Kompilierte/Binärdateien
    ".exe", ".dll", ".so", ".dylib", ".bin", ".class", ".o", ".a",
    # Datenbanken
    ".db", ".sqlite", ".sqlite3", ".realm", ".mdb", ".pack", ".idx",
}

# Umfangreiche Sprachzuordnung
LANG_MAP = {
    'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'html': 'html', 'css': 'css', 'scss': 'scss', 'sass': 'sass',
    'json': 'json', 'xml': 'xml', 'yaml': 'yaml', 'yml': 'yaml', 'md': 'markdown', 'sh': 'bash', 'bat': 'batch',
    'sql': 'sql', 'php': 'php', 'cpp': 'cpp', 'c': 'c', 'java': 'java', 'cs': 'csharp', 'go': 'go', 'rs': 'rust',
    'rb': 'ruby', 'swift': 'swift', 'kt': 'kotlin', 'svelte': 'svelte', 'txt': ''
}


def human(n: int) -> str:
    """Konvertiert Bytes in ein menschenlesbares Format (KB, MB, ...)."""
    u = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(u) - 1:
        f /= 1024
        i += 1
    return f"{f:.2f} {u[i]}"


def is_text(p: Path, sniff_bytes=4096) -> bool:
    """
    Prüft, ob eine Datei wahrscheinlich Text ist.
    Kombiniert eine Prüfung der Dateiendung mit einer Inhaltsanalyse (Sniffing).
    """
    if p.suffix.lower() in BINARY_EXTS:
        return False
    try:
        with p.open("rb") as f:
            chunk = f.read(sniff_bytes)
            if not chunk:
                return True  # Leere Datei ist Text
            if b"\x00" in chunk:
                return False  # Null-Bytes sind ein starkes Indiz für Binärdaten
            # Versuche, als UTF-8 zu dekodieren, wenn das fehlschlägt, ist es wahrscheinlich kein Text.
            chunk.decode("utf-8")
            return True
    except UnicodeDecodeError:
        return False  # Konnte nicht als UTF-8 dekodiert werden
    except Exception:
        return False  # Andere Fehler (z.B. Lesefehler)


def md5(p: Path, block_size=65536) -> str:
    """Berechnet den MD5-Hash einer Datei."""
    h = hashlib.md5()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()


def lang(p: Path) -> str:
    """Gibt die Markdown-Sprachkennung für eine Datei zurück."""
    return LANG_MAP.get(p.suffix.lstrip(".").lower(), "")


def write_tree(out: TextIO, root: Path, max_depth: int | None = None):
    """Schreibt eine Baumdarstellung des Ordners `root` in den Stream `out`."""
    def lines(d: Path, lvl=0):
        if max_depth is not None and lvl >= max_depth:
            return []
        res = []
        try:
            items = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            dirs = [i for i in items if i.is_dir()]
            files = [i for i in items if i.is_file()]
            for i, sub in enumerate(dirs):
                pref = "└── " if (i == len(dirs) - 1 and not files) else "├── "
                res.append("    " * lvl + f"{pref}📁 {sub.name}/")
                res += lines(sub, lvl + 1)
            for i, f in enumerate(files):
                pref = "└── " if i == len(files) - 1 else "├── "
                try:
                    icon = "📄" if is_text(f) else "🔒"
                    res.append("    " * lvl + f"{pref}{icon} {f.name} ({human(f.stat().st_size)})")
                except Exception:
                    res.append("    " * lvl + f"{pref}📄 {f.name}")
        except PermissionError:
            res.append("    " * lvl + "❌ Zugriff verweigert")
        return res

    out.write("```\n")
    out.write(f"📁 {root.name}/\n")
    for ln in lines(root):
        out.write(ln + "\n")
    out.write("```\n\n")


def parse_manifest(md: Path) -> dict[str, tuple[str, int]]:
    """Liest ein Manifest aus einer früheren Merge-Datei."""
    m: dict[str, tuple[str, int]] = {}
    if not md or not md.exists():
        return m
    try:
        inside = False
        with md.open("r", encoding=ENC, errors="ignore") as f:
            for line in f:
                s = line.strip()
                if s.startswith("## 🧾 Manifest"):
                    inside = True
                    continue
                if inside:
                    if not s.startswith("- "):
                        if s.startswith("## "):
                            break
                        continue
                    row = s[2:]
                    parts = row.split("|")
                    rel, md5_val, size_val = "", "", 0

                    if len(parts) >= 3:
                        # Parse from right to left to be robust against '|' in filename
                        size_part = parts[-1].strip()
                        md5_part = parts[-2].strip()

                        has_size = size_part.startswith("size=")
                        has_md5 = md5_part.startswith("md5=")

                        if has_size:
                            try:
                                size_val = int(size_part[5:].strip())
                            except ValueError:
                                size_val = 0

                        if has_md5:
                            md5_val = md5_part[4:].strip()

                        if has_size or has_md5:
                            rel = "|".join(parts[:-2]).strip()
                    elif len(parts) == 2:
                        # Handle case where only one of md5 or size is present
                        p1 = parts[0].strip()
                        p2 = parts[1].strip()
                        if p2.startswith("md5="):
                            md5_val = p2[4:].strip()
                            rel = p1
                        elif p2.startswith("size="):
                            try:
                                size_val = int(p2[5:].strip())
                            except ValueError:
                                size_val = 0
                            rel = p1

                    elif len(parts) == 1:
                        rel = parts[0].strip()

                    if rel:
                        m[rel] = (md5_val, size_val)
    except Exception as e:
        import sys
        print(f"Warning: Failed to parse manifest from {md}: {e}", file=sys.stderr)
    return m


def build_diff(current: list[tuple[Path, Path, int, str]], merge_dir: Path, merge_prefix: str) -> tuple[list[tuple[str, str]], int, int, int]:
    """Vergleicht den aktuellen Zustand mit dem letzten Merge und erstellt einen Diff."""
    try:
        merges = sorted(merge_dir.glob(f"{merge_prefix}*.md"))
        if not merges:
            return [], 0, 0, 0
    except Exception:
        return [], 0, 0, 0

    last = merges[-1]
    old = parse_manifest(last)

    cur_paths = {str(rel) for _, rel, _, _ in current}
    old_paths = set(old.keys())

    added = sorted(cur_paths - old_paths)
    removed = sorted(old_paths - cur_paths)
    changed = []
    for _, rel, _, h in current:
        r = str(rel)
        old_h, _ = old.get(r, ("", 0))
        if r in old_paths and old_h and h and old_h != h:
            changed.append(r)
    changed.sort()
    diffs = [("+", p) for p in added] + [("-", p) for p in removed] + [("~", p) for p in changed]
    return diffs, len(added), len(removed), len(changed)

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-ordnermerger-ordnermerger-py"></a>
### `merger/ordnermerger/ordnermerger.py`
- Category: source
- Tags: -
- Size: 8.81 KB
- Included: full
- MD5: 492f2bab547923962cafe6c2ed168deb

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ordnermerger — Ordner zu Markdown zusammenführen (non-destructive by default)

MODI:
--selected <PATH>: (Standard) Verarbeitet den/die angegebenen Ordner. Mehrfach nutzbar.
--here:            Verarbeitet den aktuellen Ordner (PWD).
--batch:           Verarbeitet alle Unterordner im Arbeitsverzeichnis (--workdir, default PWD).

OPTIONEN:
--delete:          Löscht Quellordner nach erfolgreichem Merge (destruktiv!).
--retain <N>:      Behält nur die N neuesten Merges im Zielordner.
--yes, -y:         Überspringt die Sicherheitsabfrage bei --delete.
--utc:             Verwendet UTC im Zeitstempel des Dateinamens.
--pattern <P>:     Format für den Dateinamen (default: "{name}_merge_%y%m%d%H%M").

ZIELORDNER:
Der Zielordner "merges" wird standardmäßig neben der Skriptdatei angelegt.
Dies kann via Environment-Variable ORDNERMERGER_HOME angepasst werden.
"""

from __future__ import annotations
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone
from merger_lib import human, is_text, md5, lang

ENC = "utf-8"
DEFAULT_NAME_PATTERN = "{name}_merge_%y%m%d%H%M"
FORBIDDEN_DIR_NAMES = {"merges", ".git", ".cache", ".venv", "__pycache__"}


def _script_home() -> Path:
    h = os.environ.get("ORDNERMERGER_HOME")
    if h:
        return Path(h).expanduser().resolve()
    return Path(__file__).resolve().parent


def _should_skip_dir(entry: Path, merge_dir: Path | None) -> bool:
    name = entry.name
    if name in FORBIDDEN_DIR_NAMES or name.startswith(".") or name.startswith("_"):
        return True
    if merge_dir is not None:
        try:
            if entry.resolve() == merge_dir.resolve():
                return True
        except Exception:
            return False
    return False


def _tree(out, root: Path, merge_dir: Path | None):
    def rec(cur: Path, depth: int):
        try:
            entries = sorted(cur.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except Exception:
            return
        for e in entries:
            if e.is_dir() and _should_skip_dir(e, merge_dir):
                continue
            rel = e.relative_to(root)
            mark = "📁" if e.is_dir() else "📄"
            out.write(f"{'  '*depth}- {mark} {rel}\n")
            if e.is_dir():
                rec(e, depth+1)
    out.write("```tree\n")
    out.write(f"{root}\n")
    rec(root, 0)
    out.write("```\n")


def _out_path(src: Path, merge_dir: Path, utc: bool, pattern: str) -> Path:
    now = datetime.now(timezone.utc if utc else None)
    stem = now.strftime(pattern.replace("{name}", src.name))
    return merge_dir / f"{stem}.md"


def merge_folder(src: Path, out_file: Path):
    included = []
    skipped = []
    total = 0
    merge_dir = out_file.parent.resolve()
    for dirpath, dirnames, files in os.walk(src):
        if dirnames:
            cur = Path(dirpath)
            dirnames[:] = [d for d in dirnames if not _should_skip_dir(cur / d, merge_dir)]
        for fn in files:
            p = Path(dirpath)/fn
            rel = p.relative_to(src)
            if not is_text(p):
                skipped.append(f"{rel} (binär)")
                continue
            try:
                sz = p.stat().st_size
                dig = md5(p)
            except Exception as e:
                skipped.append(f"{rel} (err {e})")
                continue
            included.append((p, rel, sz, dig))
            total += sz
    included.sort(key=lambda t: str(t[1]).lower())

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding=ENC) as out:
        out.write(f"# Ordner-Merge: {src.name}\n\n")
        out.write(f"**Zeitpunkt:** {datetime.now():%Y-%m-%d %H:%M}\n")
        out.write(f"**Quelle:** `{src}`\n")
        out.write(f"**Dateien:** {len(included)}\n")
        out.write(f"**Gesamtgröße:** {human(total)}\n\n")
        out.write("## 📁 Struktur\n\n")
        _tree(out, src, merge_dir)
        out.write("\n")
        out.write("## 📦 Dateien\n\n")
        for p, rel, sz, dig in included:
            out.write(f"### 📄 {rel}\n\n**Größe:** {human(sz)} | **md5:** `{dig}`\n\n```{lang(p)}\n")
            try:
                txt = p.read_text(encoding=ENC, errors="replace")
            except Exception as e:
                txt = f"<<Lesefehler: {e}>>"
            out.write(txt + ("\n" if not txt.endswith("\n") else ""))
            out.write("```\n\n")
        if skipped:
            out.write("## ⏭️ Übersprungen\n\n")
            for s in skipped:
                out.write(f"- {s}\n")


def retention_clean(merge_dir: Path, keep: int):
    """Behält nur die 'keep' neuesten Merges im Zielordner."""
    if keep < 0:
        keep = 0
    try:
        files = sorted(merge_dir.glob("*_merge_*.md"), key=lambda p: p.stat().st_mtime)
    except Exception as e:
        print(f"⚠️ Fehler beim Lesen des Merge-Verzeichnisses: {e}")
        return

    to_delete = files[:-keep] if keep > 0 and len(files) > keep else (files if keep == 0 else [])
    if not to_delete:
        print("ℹ️ Retention: Nichts zu löschen.")
        return

    print(f"🧹 Retention: Lösche {len(to_delete)} alte(n) Merge(s), behalte die neuesten {keep}.")
    for f in to_delete:
        try:
            f.unlink()
            print(f"  🗑️ Gelöscht: {f.name}")
        except Exception as e:
            print(f"  ⚠️ Fehler beim Löschen von {f.name}: {e}")


def parse_args(argv):
    import argparse
    ap = argparse.ArgumentParser(description="ordnermerger — Ordner zu Markdown zusammenführen")
    ap.add_argument("--selected", action="append", help="Einzelner Ordnerpfad; Option mehrfach nutzbar")
    ap.add_argument("--here", action="store_true", help="Aktuellen Ordner (PWD) als Quelle nehmen")
    ap.add_argument("--batch", action="store_true", help="Alle Unterordner im Arbeitsverzeichnis verarbeiten")
    ap.add_argument("--workdir", help="Arbeitsverzeichnis für --batch (Default: PWD)")
    ap.add_argument("--delete", action="store_true", help="Quellordner nach erfolgreichem Merge löschen")
    ap.add_argument("--retain", type=int, help="Nur die N neuesten Merges behalten, ältere löschen")
    ap.add_argument("-y", "--yes", action="store_true", help="Rückfragen überspringen (z.B. bei --delete)")
    ap.add_argument("--utc", action="store_true", help="UTC statt lokale Zeit im Dateinamen verwenden")
    ap.add_argument("--pattern", default=DEFAULT_NAME_PATTERN,
                    help=f"Namensmuster für Zieldatei (Default: {DEFAULT_NAME_PATTERN})")
    return ap.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    home = _script_home()
    merge_dir = home / "merges"
    merge_dir.mkdir(parents=True, exist_ok=True)

    sources: list[Path] = []
    if args.batch:
        workdir = Path(args.workdir).expanduser() if args.workdir else Path.cwd()
        print(f"BATCH-Modus im Verzeichnis: {workdir}")
        for c in sorted(workdir.iterdir()):
            if not c.is_dir():
                continue
            if _should_skip_dir(c, merge_dir):
                continue
            sources.append(c)
    elif args.selected:
        sources = [Path(s).expanduser() for s in args.selected]
    else:  # Default is --here
        sources = [Path.cwd()]

    if not sources:
        print("ℹ️ Keine passenden Quellordner gefunden.")
        return 0

    if args.delete and not args.yes:
        print("\nWARNUNG: Die Option --delete löscht die Quellordner nach dem Merge.")
        print(f"Betroffene Ordner: {', '.join(p.name for p in sources)}")
        ok = input("Möchten Sie fortfahren? [y/N] ").strip().lower()
        if ok not in ("y", "yes"):
            print("Abgebrochen.")
            return 1

    successful_merges: list[Path] = []
    for src in sources:
        src_res = src.resolve()
        if not src_res.is_dir():
            print(f"⚠️ Überspringe (kein Ordner): {src}")
            continue
        if src_res == home or src_res == merge_dir:
            print(f"⛔ Überspringe geschützte Quelle: {src} (App-Home oder Merge-Ziel)")
            continue

        try:
            out = _out_path(src, merge_dir, args.utc, args.pattern)
            merge_folder(src, out)
            print(f"✅ {src.name} → {out}")
            successful_merges.append(src)
        except Exception as e:
            print(f"❌ Fehler beim Mergen von {src.name}: {e}")

    if args.delete:
        for src in successful_merges:
            try:
                shutil.rmtree(src)
                print(f"🗑️ Quelle gelöscht: {src.name}")
            except Exception as e:
                print(f"⚠️ Quelle konnte nicht gelöscht werden ({src.name}): {e}")

    if args.retain is not None:
        retention_clean(merge_dir, args.retain)

    print(f"📂 Ziel: {merge_dir}")
    return 0 if successful_merges else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-ordnermerger-repomerger_lib-py"></a>
### `merger/ordnermerger/repomerger_lib.py`
- Category: source
- Tags: -
- Size: 11.54 KB
- Included: full
- MD5: 8c5a002d6b4a2dd7f0fa54b0226925c9

```python
# -*- coding: utf-8 -*-
"""
repomerger_lib — Hauptlogik für die repo-spezifischen Merger-Skripte.
"""

from __future__ import annotations
import os
import sys
import argparse
import configparser
import urllib.parse
from pathlib import Path
from datetime import datetime
from . import merger_lib as ml

# Gemeinsame Basispfade für die Suche
COMMON_BASES = [
    Path("/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents"),
    Path.home() / "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents",
    Path.home() / "Documents",
]


class RepoMerger:
    """
    Diese Klasse kapselt die Logik zum Mergen eines bestimmten Repo-Ordners.
    Sie wird von den Wrapper-Skripten (hauski-merger.py, etc.) instanziiert und ausgeführt.
    """

    def __init__(self, *, config_name: str, title: str, env_var: str, merge_prefix: str, def_basename: str):
        self.config_name = config_name
        self.title = title
        self.env_var = env_var
        self.merge_prefix = merge_prefix
        self.def_basename = def_basename
        self.DEF_KEEP = 2
        self.DEF_MERGE_DIRNAME = "merge"
        self.DEF_ENCODING = "utf-8"
        self.DEF_SRCH_DEPTH = 4

    def _deurl(self, s: str) -> str:
        if s and s.lower().startswith("file://"):
            return urllib.parse.unquote(s[7:])
        return s or ""

    def _safe_is_dir(self, p: Path) -> bool:
        try:
            return p.is_dir()
        except Exception:
            return False

    def _load_config(self) -> tuple[configparser.ConfigParser, Path]:
        cfg = configparser.ConfigParser()
        cfg_path = Path.home() / ".config" / self.config_name / "config.ini"
        try:
            if cfg_path.exists():
                cfg.read(cfg_path, encoding="utf-8")
        except Exception as e:
            import sys
            print(f"Warning: Failed to read config from {cfg_path}: {e}", file=sys.stderr)
        return cfg, cfg_path

    def _cfg_get_int(self, cfg, section, key, default):
        try:
            return cfg.getint(section, key, fallback=default)
        except Exception:
            return default

    def _cfg_get_str(self, cfg, section, key, default):
        try:
            return cfg.get(section, key, fallback=default)
        except Exception:
            return default

    def _find_dir_by_basename(self, basename: str, aliases: dict[str, str], search_depth: int) -> tuple[Path | None, list[Path]]:
        if basename in aliases:
            p = Path(self._deurl(aliases[basename]).strip('"'))
            if self._safe_is_dir(p):
                return p, []

        candidates = []
        for base in COMMON_BASES:
            if not base.exists():
                continue
            pref = [base / basename, base / "ordnermerger" / basename, base / "Obsidian" / basename]
            for c in pref:
                if self._safe_is_dir(c):
                    candidates.append(c)
            try:
                max_depth_abs = len(str(base).split(os.sep)) + max(1, int(search_depth))
                for p in base.rglob(basename):
                    if p.is_dir() and p.name == basename and len(str(p).split(os.sep)) <= max_depth_abs:
                        candidates.append(p)
            except (OSError, PermissionError) as e:
                # Ignore permission errors during recursive search
                pass
            except Exception as e:
                import sys
                print(f"Warning: Error during directory search in {base}: {e}", file=sys.stderr)

        uniq = sorted(list(set(candidates)), key=lambda p: (len(str(p)), str(p)))
        if not uniq:
            return None, []

        best = uniq[0]
        others = uniq[1:]
        return best, others

    def _extract_source_path(self, argv: list[str], *, aliases: dict[str, str], search_depth: int) -> tuple[Path | None, str | None]:
        env_src = os.environ.get(self.env_var, "").strip()
        if env_src:
            p = Path(self._deurl(env_src).strip('"'))
            if not self._safe_is_dir(p) and p.exists():
                p = p.parent
            if self._safe_is_dir(p):
                return p, f"{self.env_var} (ENV)"

        tokens = [t for t in argv if t and t != "--source-dir"]
        if "--source-dir" in argv:
            try:
                idx = argv.index("--source-dir")
                if idx + 1 < len(argv):
                    tokens.insert(0, argv[idx+1])
            except ValueError:
                pass

        for tok in tokens:
            cand = self._deurl((tok or "").strip('"'))
            if not cand:
                continue
            if os.sep in cand or cand.lower().startswith("file://"):
                p = Path(cand)
                if p.exists():
                    if p.is_file():
                        p = p.parent
                    if self._safe_is_dir(p):
                        return p, "direktes Argument"

        for tok in tokens:
            cand = self._deurl((tok or "").strip('"'))
            if not cand or os.sep in cand or cand.lower().startswith("file://"):
                continue

            hit, others = self._find_dir_by_basename(cand, aliases, search_depth=search_depth)
            if hit:
                info = f"Basename-Fallback ('{cand}')"
                if others:
                    others_s = " | ".join(str(p) for p in others[:3])
                    print(f"__{self.config_name.upper()}_INFO__: Mehrere Kandidaten, nehme kürzesten: {hit} | weitere: {others_s}")
                return hit, info

        return None, None

    def _keep_last_n(self, merge_dir: Path, keep: int, keep_new: Path | None = None, *, merge_prefix: str | None = None):
        prefix = merge_prefix or self.merge_prefix
        merges = sorted(merge_dir.glob(f"{prefix}*.md"))
        if keep_new and keep_new not in merges:
            merges.append(keep_new)
            merges.sort(key=lambda p: p.stat().st_mtime)

        if keep > 0 and len(merges) > keep:
            for old in merges[:-keep]:
                try:
                    old.unlink()
                except Exception as e:
                    import sys
                    print(f"Warning: Failed to delete old merge file {old}: {e}", file=sys.stderr)

    def _do_merge(
        self,
        source: Path,
        out_file: Path,
        *,
        encoding: str,
        keep: int,
        merge_dir: Path,
        max_tree_depth: int | None,
        search_info: str | None,
        merge_prefix: str,
    ):
        included, skipped, total = [], [], 0
        for dirpath, _, files in os.walk(source):
            d = Path(dirpath)
            for fn in files:
                p = d / fn
                rel = p.relative_to(source)
                if not ml.is_text(p):
                    skipped.append(f"{rel} (binär)")
                    continue
                try:
                    sz = p.stat().st_size
                    h = ml.md5(p)
                    included.append((p, rel, sz, h))
                    total += sz
                except Exception as e:
                    skipped.append(f"{rel} (Fehler: {e})")

        included.sort(key=lambda t: str(t[1]).lower())
        out_file.parent.mkdir(parents=True, exist_ok=True)

        diffs, add_c, del_c, chg_c = ml.build_diff(included, merge_dir, merge_prefix)

        with out_file.open("w", encoding=encoding) as out:
            out.write(f"# {self.title}\n\n")
            out.write(f"**Zeitpunkt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            out.write(f"**Quelle:** `{source}`\n")
            if search_info:
                out.write(f"**Quelle ermittelt:** {search_info}\n")
            out.write(f"**Dateien (inkludiert):** {len(included)}\n")
            out.write(f"**Gesamtgröße:** {ml.human(total)}\n")
            if diffs:
                out.write(f"**Änderungen:** +{add_c} / -{del_c} / ~{chg_c}\n")
            out.write("\n## 📁 Struktur\n\n")
            ml.write_tree(out, source, max_tree_depth)
            if diffs:
                out.write("## 📊 Änderungen\n\n")
                for sym, pth in diffs:
                    out.write(f"{sym} {pth}\n")
                out.write("\n")
            if skipped:
                out.write("## ⏭️ Übersprungen\n\n")
                for s in skipped:
                    out.write(f"- {s}\n")
                out.write("\n")
            out.write("## 🧾 Manifest\n\n")
            for _, rel, sz, h in included:
                out.write(f"- {rel} | md5={h} | size={sz}\n")
            out.write("\n## 📄 Dateiinhalte\n\n")
            for p, rel, sz, _ in included:
                out.write(f"### 📄 {rel}\n\n**Größe:** {ml.human(sz)}\n\n```{ml.lang(p)}\n")
                try:
                    txt = p.read_text(encoding=encoding, errors="replace")
                    out.write(txt + ("" if txt.endswith("\n") else "\n"))
                except Exception as e:
                    out.write(f"<<Lesefehler: {e}>>\n")
                out.write("```\n\n")

        self._keep_last_n(merge_dir, keep, out_file, merge_prefix=merge_prefix)
        print(f"✅ Merge geschrieben: {out_file} ({ml.human(out_file.stat().st_size)})")

    def run(self, argv: list[str]):
        parser = argparse.ArgumentParser(description=self.title, add_help=False)
        parser.add_argument("--source-dir", dest="src_flag")
        parser.add_argument("--keep", type=int)
        parser.add_argument("--encoding")
        parser.add_argument("--max-depth", type=int, dest="max_tree_depth")
        parser.add_argument("--search-depth", type=int, dest="search_depth")
        parser.add_argument("--merge-dirname")
        parser.add_argument("--merge-prefix")
        parser.add_argument("-h", "--help", action="store_true")
        parser.add_argument("rest", nargs="*")

        args = parser.parse_args(argv)

        if args.help:
            print(f"Hilfe für {self.config_name}: Startskript zeigt Details.")
            return 0

        cfg, _ = self._load_config()

        keep = args.keep if args.keep is not None else self._cfg_get_int(cfg, "general", "keep", self.DEF_KEEP)
        merge_dirname = args.merge_dirname or self._cfg_get_str(cfg, "general", "merge_dirname", self.DEF_MERGE_DIRNAME)
        merge_prefix_final = args.merge_prefix or self._cfg_get_str(cfg, "general", "merge_prefix", self.merge_prefix)
        encoding = args.encoding or self._cfg_get_str(cfg, "general", "encoding", self.DEF_ENCODING)
        search_depth = args.search_depth if args.search_depth is not None else self._cfg_get_int(
            cfg, "general", "max_search_depth", self.DEF_SRCH_DEPTH)

        aliases = {k: v for k, v in cfg.items("aliases")} if cfg.has_section("aliases") else {}

        src_argv = ([args.src_flag] + args.rest) if args.src_flag else args.rest
        src, src_info = self._extract_source_path(src_argv, aliases=aliases, search_depth=search_depth)

        if not src:
            print(f"❌ Quelle nicht gefunden. Setze {self.env_var} oder gib einen Pfad an.")
            return 2
        if not self._safe_is_dir(src):
            print(f"❌ Quelle ist kein Ordner: {src}")
            return 1

        script_root = Path(sys.argv[0]).resolve().parent
        merge_dir = script_root / merge_dirname
        merge_dir.mkdir(parents=True, exist_ok=True)

        out_file = merge_dir / f"{merge_prefix_final}{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        self._do_merge(
            src,
            out_file,
            encoding=encoding,
            keep=keep,
            merge_dir=merge_dir,
            max_tree_depth=args.max_tree_depth,
            search_info=src_info,
            merge_prefix=merge_prefix_final,
        )
        return 0

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-repomerger-hauski-merger-py"></a>
### `merger/repomerger/hauski-merger.py`
- Category: source
- Tags: -
- Size: 22.96 KB
- Included: full
- MD5: 56ae7f2907db9a2abbc69b6edeb45bd4

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
hauski-merger – Shortcuts-freundlich, Dotfiles inklusive, Basename/Env/Config-Fallbacks, keep last N merges

Nutzung auf iOS (Shortcuts → "Run Pythonista Script" → Arguments):
    – GIB GENAU EINE DER VARIANTEN, KEINE UMBRÜCHE:
      1) --source-dir "/private/var/.../hauski"
      2) "/private/var/.../hauski"
      3) file:///private/var/.../hauski"
      4) hauski   (nur Basename; Fallback-Suche aktiv)
    – Alternativ Env: HAUSKI_SOURCE="/private/var/.../hauski"

Ausgabe:
    ./merge/hauski_DDMM.md
    (bei Mehrfach-Merges am selben Tag: hauski_DDMM_2.md, hauski_DDMM_3.md, ...)
    – Standard: nur die letzten 2 Merges bleiben (per Config / CLI änderbar)

Konfig (optional):
    ~/.config/hauski-merger/config.ini

    [general]
    keep = 2
    merge_dirname = merge
    merge_prefix  = hauski
    max_search_depth = 4
    encoding = utf-8

    [aliases]
    hauski = /private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/hauski
"""

import sys
import os
import argparse
import hashlib
import urllib.parse
import configparser
from pathlib import Path
from datetime import datetime

# ===== Defaults =====
DEF_KEEP          = 2
DEF_MERGE_DIRNAME = "merge"
# Basisname im Dateinamen, z. B. "hauski" -> hauski_DDMM.md
DEF_MERGE_PREFIX  = "hauski"
DEF_ENCODING      = "utf-8"
DEF_SRCH_DEPTH    = 4

# nur wirklich binäre Endungen (Dotfiles & .svg bleiben erhalten)
BINARY_EXT = {
    ".png",".jpg",".jpeg",".gif",".bmp",".ico",".webp",".heic",".heif",".psd",".ai",
    ".mp3",".wav",".flac",".ogg",".m4a",".aac",".mp4",".mkv",".mov",".avi",".wmv",".flv",".webm",
    ".zip",".rar",".7z",".tar",".gz",".bz2",".xz",".tgz",
    ".ttf",".otf",".woff",".woff2",
    ".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".pages",".numbers",".key",
    ".exe",".dll",".so",".dylib",".bin",".class",".o",".a",
    ".db",".sqlite",".sqlite3",".realm",".mdb",".pack",".idx",
}

LANG_MAP = {
    "py": "python","js": "javascript","ts": "typescript","html": "html","css": "css",
    "scss": "scss","sass": "sass","json": "json","xml": "xml","yaml": "yaml","yml": "yaml",
    "md": "markdown","sh": "bash","bat": "batch","sql": "sql","php": "php","cpp": "cpp",
    "c": "c","java": "java","cs": "csharp","go": "go","rs": "rust","rb": "ruby",
    "swift": "swift","kt": "kotlin","svelte": "svelte",
}

COMMON_BASES = [
    Path("/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents"),
    Path.home() / "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents",
    Path.home() / "Documents",
]

# --- Klassifikations-Hilfen --------------------------------------------------

DOC_EXTENSIONS = {".md", ".rst", ".txt"}

SOURCE_EXTENSIONS = {
    ".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".svelte",
    ".c", ".cpp", ".h", ".hpp", ".go", ".java", ".cs",
}

CONFIG_FILENAMES = {
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "Cargo.toml",
    "Cargo.lock",
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Justfile",
    "Makefile",
    "toolchain.versions.yml",
    ".editorconfig",
    ".markdownlint.jsonc",
    ".markdownlint.yaml",
    ".yamllint",
    ".yamllint.yml",
    ".lychee.toml",
    ".vale.ini",
}

# ===== Utilities ============================================================

def human(n: int) -> str:
    u = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(u) - 1:
        f /= 1024
        i += 1
    return f"{f:.2f} {u[i]}"


def is_text_file(p: Path, sniff: int = 4096) -> bool:
    # harte Binär-Endungen
    if p.suffix.lower() in BINARY_EXT:
        return False
    # .env / .env.* aus Sicherheitsgründen ignorieren, außer Vorlagen
    name = p.name
    if name.startswith(".env") and name not in (".env.example", ".env.template", ".env.sample"):
        return False
    try:
        with p.open("rb") as f:
            chunk = f.read(sniff)
        if not chunk:
            return True
        if b"\x00" in chunk:
            return False
        try:
            chunk.decode("utf-8")
            return True
        except UnicodeDecodeError:
            chunk.decode("latin-1", errors="ignore")
            return True
    except Exception:
        return False


def lang_for(p: Path) -> str:
    return LANG_MAP.get(p.suffix.lower().lstrip("."), "")


def file_md5(p: Path, block: int = 65536) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_is_dir(p: Path) -> bool:
    try:
        return p.is_dir()
    except Exception:
        return False


def _deurl(s: str) -> str:
    if s and s.lower().startswith("file://"):
        return urllib.parse.unquote(s[7:])
    return s or ""


def load_config() -> tuple[configparser.ConfigParser, Path]:
    cfg = configparser.ConfigParser()
    cfg_path = Path.home() / ".config" / "hauski-merger" / "config.ini"
    try:
        if cfg_path.exists():
            cfg.read(cfg_path, encoding="utf-8")
    except Exception:
        pass
    return cfg, cfg_path


def cfg_get_int(cfg, section, key, default):
    try:
        return cfg.getint(section, key, fallback=default)
    except Exception:
        return default


def cfg_get_str(cfg, section, key, default):
    try:
        return cfg.get(section, key, fallback=default)
    except Exception:
        return default

# ===== Klassifikation & Statistik ===========================================

def classify_category(rel: Path, ext: str) -> str:
    """Grobe Heuristik: doc / config / source / other."""
    name = rel.name
    if name in CONFIG_FILENAMES:
        return "config"
    if ext in DOC_EXTENSIONS:
        return "doc"
    if ext in SOURCE_EXTENSIONS:
        return "source"
    parts = [p.lower() for p in rel.parts]
    if any(p in ("config", "configs", "settings", "etc", ".github") for p in parts):
        return "config"
    if "docs" in parts or "doc" in parts:
        return "doc"
    return "other"


def summarize_ext(manifest_rows):
    """
    manifest_rows: Liste von (rel:Path, size:int, md5:str, cat:str, ext:str)
    -> (ext_counts, ext_sizes)
    """
    counts: dict[str, int] = {}
    sizes: dict[str, int] = {}
    for rel, sz, md5, cat, ext in manifest_rows:
        key = ext or "<none>"
        counts[key] = counts.get(key, 0) + 1
        sizes[key] = sizes.get(key, 0) + sz
    return counts, sizes


def summarize_cat(manifest_rows):
    """
    Kleine Übersicht nach Kategorien.
    -> dict cat -> (count, size)
    """
    result: dict[str, list[int]] = {}
    for rel, sz, md5, cat, ext in manifest_rows:
        if cat not in result:
            result[cat] = [0, 0]
        result[cat][0] += 1
        result[cat][1] += sz
    return result

# ===== Basename-Fallback ====================================================

def find_dir_by_basename(basename: str, aliases: dict[str, str], search_depth: int = DEF_SRCH_DEPTH) -> tuple[Path | None, list[Path]]:
    # 0) Aliases
    if basename in aliases:
        p = Path(_deurl(aliases[basename]).strip('"'))
        if safe_is_dir(p):
            return p, []

    candidates: list[Path] = []
    for base in COMMON_BASES:
        if not base.exists():
            continue

        # schnelle Treffer
        pref = [
            base / basename,
            base / "ordnermerger" / basename,
            base / "Obsidian" / basename,
        ]
        for c in pref:
            if safe_is_dir(c):
                candidates.append(c)

        # vorsichtige Suche
        try:
            max_depth_abs = len(str(base).split(os.sep)) + max(1, int(search_depth))
            for p in base.rglob(basename):
                if p.is_dir() and p.name == basename and len(str(p).split(os.sep)) <= max_depth_abs:
                    candidates.append(p)
        except Exception:
            pass

    uniq: list[Path] = []
    seen: set[str] = set()
    for c in candidates:
        s = str(c)
        if s not in seen:
            uniq.append(c)
            seen.add(s)

    if not uniq:
        return None, []
    best = sorted(uniq, key=lambda p: (len(str(p)), str(p)))[0]
    others = [p for p in uniq if p != best]
    return best, others

# ===== Dateinamen-Logik =====================================================

def make_output_filename(merge_dir: Path, base_name: str) -> Path:
    """
    Erzeugt einen Dateinamen nach Schema:
        <base_name>_DDMM.md
    und hängt bei Kollisionen _2, _3, ... an.
    """
    now = datetime.now()
    ddmm = now.strftime("%d%m")
    base = f"{base_name}_{ddmm}"
    candidate = merge_dir / f"{base}.md"
    idx = 2
    while candidate.exists():
        candidate = merge_dir / f"{base}_{idx}.md"
        idx += 1
    return candidate

# ===== Manifest/Diff/Tree ===================================================

def write_tree(out, root: Path, max_depth: int | None = None):
    def lines(d: Path, lvl: int = 0):
        if max_depth is not None and lvl >= max_depth:
            return []
        res: list[str] = []
        try:
            items = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            dirs = [i for i in items if i.is_dir()]
            files = [i for i in items if i.is_file()]
            for i, sub in enumerate(dirs):
                pref = "└── " if (i == len(dirs) - 1 and not files) else "├── "
                res.append("    " * lvl + f"{pref}📁 {sub.name}/")
                res += lines(sub, lvl + 1)
            for i, f in enumerate(files):
                pref = "└── " if i == len(files) - 1 else "├── "
                try:
                    icon = "📄" if is_text_file(f) else "🔒"
                    res.append("    " * lvl + f"{pref}{icon} {f.name} ({human(f.stat().st_size)})")
                except Exception:
                    res.append("    " * lvl + f"{pref}📄 {f.name}")
        except PermissionError:
            res.append("    " * lvl + "❌ Zugriff verweigert")
        return res

    out.write("```\n")
    out.write(f"📁 {root.name}/\n")
    for ln in lines(root):
        out.write(ln + "\n")
    out.write("```\n\n")


def parse_manifest(md: Path) -> dict[str, tuple[str, int]]:
    m: dict[str, tuple[str, int]] = {}
    if not md or not md.exists():
        return m
    try:
        inside = False
        with md.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if s.startswith("## 🧾 Manifest"):
                    inside = True
                    continue
                if inside:
                    if not s.startswith("- "):
                        if s.startswith("## "):
                            break
                        continue
                    row = s[2:]
                    parts = [p.strip() for p in row.split("|")]
                    rel = parts[0] if parts else ""
                    md5 = ""
                    size = 0
                    for p in parts[1:]:
                        if p.startswith("md5="):
                            md5 = p[4:].strip()
                        elif p.startswith("size="):
                            try:
                                size = int(p[5:].strip())
                            except Exception:
                                size = 0
                    if rel:
                        m[rel] = (md5, size)
    except Exception:
        pass
    return m


def build_diff(current: list[tuple[Path, Path, int, str]], merge_dir: Path, merge_prefix: str):
    # merge_prefix als Basisname: <prefix>_DDMM*.md
    merges = sorted(merge_dir.glob(f"{merge_prefix}_*.md"))
    if not merges:
        return [], 0, 0, 0
    last = merges[-1]
    old = parse_manifest(last)

    cur_paths = {str(rel) for _, rel, _, _ in current}
    old_paths = set(old.keys())

    added = sorted(cur_paths - old_paths)
    removed = sorted(old_paths - cur_paths)
    changed: list[str] = []
    for _, rel, _, h in current:
        r = str(rel)
        old_h = old.get(r, ("", 0))[0]
        if r in old_paths and old_h and h and old_h != h:
            changed.append(r)
    changed.sort()
    diffs = [("+", p) for p in added] + [("-", p) for p in removed] + [("~", p) for p in changed]
    return diffs, len(added), len(removed), len(changed)


def keep_last_n(merge_dir: Path, keep: int, keep_new: Path | None = None, merge_prefix: str = DEF_MERGE_PREFIX):
    merges = sorted(merge_dir.glob(f"{merge_prefix}_*.md"))
    if keep_new and keep_new not in merges:
        merges.append(keep_new)
        merges.sort()
    if keep <= 0 or len(merges) <= keep:
        return
    for old in merges[:-keep]:
        try:
            old.unlink()
        except Exception:
            pass

# ===== Merge ================================================================

def do_merge(
    source: Path,
    out_file: Path,
    *,
    encoding: str,
    keep: int,
    merge_dir: Path,
    merge_prefix: str,
    max_tree_depth: int | None,
    search_info: str | None,
):
    included: list[tuple[Path, Path, int, str]] = []
    manifest_rows: list[tuple[Path, int, str, str, str]] = []
    skipped: list[str] = []
    total = 0

    for dirpath, _, files in os.walk(source):
        d = Path(dirpath)
        for fn in files:
            p = d / fn
            rel = p.relative_to(source)

            if not is_text_file(p):
                skipped.append(f"{rel} (binär/ignoriert)")
                continue

            try:
                sz = p.stat().st_size
            except Exception as e:
                skipped.append(f"{rel} (stat error: {e})")
                continue
            try:
                h = file_md5(p)
            except Exception:
                h = ""

            total += sz
            included.append((p, rel, sz, h))

            ext = p.suffix.lower()
            cat = classify_category(rel, ext)
            manifest_rows.append((rel, sz, h, cat, ext))

    included.sort(key=lambda t: str(t[1]).lower())
    manifest_rows.sort(key=lambda t: str(t[0]).lower())

    out_file.parent.mkdir(parents=True, exist_ok=True)

    base_prefix = merge_prefix.rstrip("_")

    diffs, add_c, del_c, chg_c = build_diff(included, out_file.parent, base_prefix)
    ext_counts, ext_sizes = summarize_ext(manifest_rows)
    cat_stats = summarize_cat(manifest_rows)

    with out_file.open("w", encoding=encoding) as out:
        out.write("# HausKI-Merge\n\n")
        out.write(f"**Zeitpunkt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"**Quelle:** `{source}`\n")
        if search_info:
            out.write(f"**Quelle ermittelt:** {search_info}\n")
        out.write(f"**Dateien (inkludiert):** {len(included)}\n")
        out.write(f"**Gesamtgröße:** {human(total)}\n")
        if diffs:
            out.write(f"**Änderungen seit letztem Merge:** +{add_c} / -{del_c} / ~{chg_c}\n")
        out.write("\n")

        # KI-Hinweisblock
        out.write("> Hinweis für KIs:\n")
        out.write("> - Dies ist ein Schnappschuss des Dateisystems, keine vollständige Git-Historie.\n")
        out.write("> - Die Baumstruktur findest du unter `## 📁 Struktur`.\n")
        out.write("> - Alle aufgenommenen Dateien stehen im `## 🧾 Manifest`.\n")
        out.write("> - Dateiinhalte stehen unter `## 📄 Dateiinhalte`.\n")
        out.write("> - `.env` und ähnliche Dateien können bewusst fehlen (Sicherheitsfilter).\n\n")

        # Plan / Übersicht
        out.write("## 🧮 Plan\n\n")
        out.write(f"- Textdateien im Merge: **{len(included)}**\n")
        out.write(f"- Gesamtgröße der Quellen: **{human(total)}**\n")

        if cat_stats:
            out.write("\n**Dateien nach Kategorien:**\n\n")
            out.write("| Kategorie | Dateien | Gesamtgröße |\n")
            out.write("| --- | ---: | ---: |\n")
            for cat in sorted(cat_stats.keys()):
                cnt, sz = cat_stats[cat]
                out.write(f"| `{cat}` | {cnt} | {human(sz)} |\n")
            out.write("\n")

        if ext_counts:
            out.write("**Statistik nach Dateiendungen:**\n\n")
            out.write("| Ext | Dateien | Gesamtgröße |\n")
            out.write("| --- | ---: | ---: |\n")
            for ext in sorted(ext_counts.keys()):
                out.write(f"| `{ext}` | {ext_counts[ext]} | {human(ext_sizes[ext])} |\n")
            out.write("\n")

        out.write("Hinweis: Obwohl `.env`-ähnliche Dateien gefiltert werden, können sensible Daten ")
        out.write("in anderen Dateien (z. B. JSON/YAML) vorkommen. Nutze den Merge nicht als public Dump.\n\n")

        out.write("## 📁 Struktur\n\n")
        write_tree(out, source, max_tree_depth)

        if diffs:
            out.write("## 📊 Änderungen seit letztem Merge\n\n")
            for sym, pth in diffs:
                out.write(f"{sym} {pth}\n")
            out.write("\n")

        if skipped:
            out.write("## ⏭️ Übersprungen\n\n")
            for s in skipped:
                out.write(f"- {s}\n")
            out.write("\n")

        out.write("## 🧾 Manifest\n\n")
        for rel, sz, h, cat, ext in manifest_rows:
            out.write(f"- {rel} | md5={h} | size={sz} | cat={cat}\n")
        out.write("\n")

        out.write("## 📄 Dateiinhalte\n\n")
        for p, rel, sz, h in included:
            out.write(f"### 📄 {rel}\n\n**Größe:** {human(sz)}\n\n```{lang_for(p)}\n")
            try:
                txt = p.read_text(encoding=encoding, errors="replace")
            except Exception as e:
                txt = f"<<Lesefehler: {e}>>"
            out.write(txt)
            if not txt.endswith("\n"):
                out.write("\n")
            out.write("```\n\n")

    keep_last_n(out_file.parent, keep=keep, keep_new=out_file, merge_prefix=base_prefix)
    print(f"✅ Merge geschrieben: {out_file} ({human(out_file.stat().st_size)})")

# ===== CLI ==================================================================

def build_parser():
    p = argparse.ArgumentParser(description="hauski-merger – genau ein Quellordner", add_help=False)
    p.add_argument("--source-dir", dest="src_flag")
    p.add_argument("--keep", type=int, dest="keep")
    p.add_argument("--encoding", dest="encoding")
    p.add_argument("--max-depth", type=int, dest="max_tree_depth")
    p.add_argument("--search-depth", type=int, dest="search_depth")
    p.add_argument("--merge-dirname", dest="merge_dirname")
    p.add_argument("--merge-prefix", dest="merge_prefix")  # Basisname für Dateinamen (Default: hauski)
    p.add_argument("-h", "--help", action="store_true", dest="help")
    p.add_argument("rest", nargs="*")
    return p


def print_help():
    print(__doc__.strip())


def extract_source_path(argv: list[str], *, aliases: dict[str, str], search_depth: int) -> tuple[Path | None, str | None]:
    """
    Akzeptiert:
      - --source-dir <PATH|BASENAME|file://>
      - <PATH|BASENAME|file://>
      - Datei → Elternordner
      - Env: HAUSKI_SOURCE
      - Fallback: Nur-Basename unter COMMON_BASES
    Rückgabe: (Pfad, InfoStringFürReport)
    """
    # Env
    env_src = os.environ.get("HAUSKI_SOURCE", "").strip()
    if env_src:
        p = Path(_deurl(env_src).strip('"'))
        if not safe_is_dir(p) and p.exists():
            p = p.parent
        if safe_is_dir(p):
            return p, "HAUSKI_SOURCE (ENV)"

    # Tokens
    tokens: list[str] = []
    if "--source-dir" in argv:
        idx = argv.index("--source-dir")
        if idx + 1 < len(argv):
            tokens.append(argv[idx + 1])
    tokens += [t for t in argv if t != "--source-dir"]

    # Direktpfad
    for tok in tokens:
        cand = _deurl((tok or "").strip('"'))
        if not cand:
            continue
        if os.sep not in cand and not cand.lower().startswith("file://"):
            continue
        p = Path(cand)
        if p.exists():
            if p.is_file():
                p = p.parent
            if safe_is_dir(p):
                return p, "direktes Argument"

    # Basename/Alias
    for tok in tokens:
        cand = _deurl((tok or "").strip('"'))
        if not cand:
            continue
        if os.sep in cand or cand.lower().startswith("file://"):
            continue
        base = cand
        hit, others = find_dir_by_basename(base, aliases, search_depth=search_depth)
        if hit:
            info = f"Basename-Fallback ('{base}')"
            if others:
                others_s = " | ".join(str(p) for p in others[:5])
                print(f"__HAUSKI_MERGER_INFO__: Mehrere Kandidaten gefunden, nehme kürzesten: {hit} | weitere: {others_s}")
            return hit, info
    return None, None


def _running_in_shortcuts() -> bool:
    return os.environ.get("HAUSKI_SHORTCUTS", "1") == "1"


def main(argv: list[str]) -> int:
    cfg, cfg_path = load_config()
    args = build_parser().parse_args(argv)
    if args.help:
        print_help()
        return 0

    keep = args.keep if args.keep is not None else cfg_get_int(cfg, "general", "keep", DEF_KEEP)
    merge_dirname = args.merge_dirname or cfg_get_str(cfg, "general", "merge_dirname", DEF_MERGE_DIRNAME)
    merge_prefix = args.merge_prefix or cfg_get_str(cfg, "general", "merge_prefix", DEF_MERGE_PREFIX)
    encoding = args.encoding or cfg_get_str(cfg, "general", "encoding", DEF_ENCODING)
    search_depth = args.search_depth if args.search_depth is not None else cfg_get_int(cfg, "general", "max_search_depth", DEF_SRCH_DEPTH)
    max_tree_depth = args.max_tree_depth if args.max_tree_depth is not None else None

    aliases: dict[str, str] = {}
    if cfg.has_section("aliases"):
        for k, v in cfg.items("aliases"):
            aliases[k] = v

    src, src_info = extract_source_path(
        [args.src_flag] + args.rest if args.src_flag else args.rest,
        aliases=aliases,
        search_depth=search_depth,
    )
    if not src:
        print("❌ Quelle fehlt/unerkannt. Übergib Pfad/URL/Basename oder setze HAUSKI_SOURCE. (-h für Hilfe)")
        return 2
    if not safe_is_dir(src):
        print(f"❌ Quelle nicht gefunden oder kein Ordner: {src}")
        return 1

    script_root = Path(__file__).resolve().parent
    merge_dir = ensure_dir(script_root / merge_dirname)

    # Dateiname: <merge_prefix>_DDMM(.md) + Kollision-Handling
    base_name = merge_prefix.rstrip("_")
    out_file = make_output_filename(merge_dir, base_name=base_name)

    do_merge(
        src,
        out_file,
        encoding=encoding,
        keep=keep,
        merge_dir=merge_dir,
        merge_prefix=merge_prefix,
        max_tree_depth=max_tree_depth,
        search_info=src_info,
    )
    return 0


def _safe_main():
    try:
        rc = main(sys.argv[1:])
    except SystemExit as e:
        rc = int(getattr(e, "code", 1) or 0)
    except Exception as e:
        print(f"__HAUSKI_MERGER_ERR__: {e}")
        rc = 1
    if _running_in_shortcuts():
        if rc != 0:
            print(f"__HAUSKI_MERGER_WARN__: Exit {rc}")
        print("__HAUSKI_MERGER_OK__")
    else:
        sys.exit(rc)


if __name__ == "__main__":
    _safe_main()

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-repomerger-heimgewebe-merge--gitignore"></a>
### `merger/repomerger/heimgewebe-merge/.gitignore`
- Category: config
- Tags: -
- Size: 19.00 B
- Included: full
- MD5: aff18e7ddf2da8c1bebfb400cf4cbb17

```
/.git/
/out/
/*.md

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-repomerger-heimgewebe-merge-merge-py"></a>
### `merger/repomerger/heimgewebe-merge/merge.py`
- Category: source
- Tags: -
- Size: 7.76 KB
- Included: full
- MD5: f290edc575f3ca5c0a20c55eddf8a65a

```python
#!/usr/bin/env python3
from __future__ import annotations
import argparse
import fnmatch
import re
import shutil
import subprocess
import sys
from pathlib import Path


# -------- utils --------
def sh(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd) if cwd else None, text=True).strip()


def want(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in patterns)


def looks_binary(p: Path, cutoff: int) -> bool:
    try:
        with p.open("rb") as f:
            chunk = f.read(min(cutoff, 8192))
        return b"\0" in chunk
    except Exception:
        return True


def human_bytes(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GiB"


def append_with_split(parts_dir: Path, parts: list[Path], cur_size: int, max_bytes: int, text: str):
    if not parts:
        parts.append(parts_dir / "dossier-part-0001.md")
        parts[-1].write_text("", encoding="utf-8")
        cur_size = 0
    data = text.encode("utf-8")
    if cur_size + len(data) > max_bytes:
        idx = len(parts) + 1
        parts.append(parts_dir / f"dossier-part-{idx:04d}.md")
        parts[-1].write_text("", encoding="utf-8")
        cur_size = 0
    with parts[-1].open("a", encoding="utf-8") as f:
        f.write(text)
    return parts, cur_size + len(data)


# -------- main --------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge heimgewebe org repos into split Markdown dossiers with crosslinks.")
    p.add_argument("--org", required=True)
    p.add_argument("--repos", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-bytes", type=int, default=5 * 1024 * 1024)
    p.add_argument("--globs", default="README.md,docs/**,**/*.md,**/*.rs,**/*.py,**/*.ts,**/*.tsx,**/*.js,**/*.svelte,**/*.sh,**/*.bash,**/*.fish,**/*.zsh,**/*.sql,**/*.yml,**/*.yaml,**/*.toml")
    p.add_argument("--binary-cutoff", type=int, default=256 * 1024)
    p.add_argument("--work", default=".git/tmp/heimgewebe-merge")
    return p.parse_args()


EXT_LANG = {
    ".rs": "Rust", ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript",
    ".svelte": "Svelte", ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".fish": "Shell",
    ".sql": "SQL", ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".md": "Markdown",
}

if __name__ == "__main__":
    a = parse_args()
    org = a.org
    repos = a.repos
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path(a.work)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    patterns = [p.strip() for p in a.globs.split(",") if p.strip()]

    # Parts
    parts: list[Path] = []
    cur_size = 0
    header = "# Heimgewebe – Gesamtüberblick (automatisch generiert)\n\n"
    parts, cur_size = append_with_split(out, parts, cur_size, a.max_bytes, header)

    # For index/crosslinks
    info_rows = []  # (repo, files, bytes, langs_dict)
    texts_by_repo: dict[str, list[tuple[str, str]]] = {}  # repo -> [(relpath, text), ...]

    # Helper: sichere Mermaid-IDs (alnum + _), Label separat
    def safe_id(name: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]", "_", name)

    for repo in repos:
        repo_url = f"https://github.com/{org}/{repo}.git"
        repo_dir = work / repo
        print(f"• Cloning {repo_url}", file=sys.stderr)
        sh(["git", "clone", "--depth=1", "--filter=blob:none", repo_url, str(repo_dir)])
        commit = sh(["git", "rev-parse", "HEAD"], cwd=repo_dir)
        files = sh(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo_dir).splitlines()
        keep = [f for f in files if want(f, patterns)]

        repo_title = f"\n\n## {repo}@{commit[:12]}\n\n"
        parts, cur_size = append_with_split(out, parts, cur_size, a.max_bytes, repo_title)

        total_bytes = 0
        langs: dict[str, int] = {}
        texts: list[tuple[str, str]] = []

        for rel in keep:
            p = repo_dir / rel
            if not p.exists():
                try:
                    sh(["git", "checkout", "--", rel], cwd=repo_dir)
                except subprocess.CalledProcessError:
                    continue
            if not p.exists() or p.is_dir():
                continue
            try:
                st = p.stat()
                total_bytes += st.st_size
                ext = p.suffix.lower()
                langs[EXT_LANG.get(ext, "Other")] = langs.get(EXT_LANG.get(ext, "Other"), 0) + 1
                if st.st_size > a.binary_cutoff or looks_binary(p, a.binary_cutoff):
                    banner = f"\n<!-- skipped binary or large file: {rel} ({st.st_size} bytes) -->\n"
                    parts, cur_size = append_with_split(out, parts, cur_size, a.max_bytes, banner)
                    continue
                code = p.read_text(encoding="utf-8", errors="replace")
                texts.append((rel, code))
            except Exception:
                continue

        # write files content after collection for deterministic order
        for rel, code in texts:
            fence = "```"
            banner = f"\n### {rel}\n\n{fence}\n{code}\n{fence}\n"
            parts, cur_size = append_with_split(out, parts, cur_size, a.max_bytes, banner)

        info_rows.append((repo, len(texts), total_bytes, langs))
        texts_by_repo[repo] = texts

    # Build index.md
    idx = out / "index.md"
    idx.write_text("## Index\n\n| Repo | Dateien | Größe | Sprachen (grobe Zählung) |\n|---|---:|---:|---|\n", encoding="utf-8")
    for (repo, cnt, b, langs) in info_rows:
        lang_str = ", ".join(f"{k}:{v}" for k, v in sorted(langs.items(), key=lambda x: (-x[1], x[0])) if v > 0)
        idx.write_text(idx.read_text(encoding="utf-8") + f"| {repo} | {cnt} | {human_bytes(b)} | {lang_str} |\n", encoding="utf-8")

    # Cross-repo mentions (heuristic: wortgrenzen-suche, case-insensitiv)
    edges: dict[tuple[str, str], int] = {}
    for src in repos:
        texts = texts_by_repo.get(src, [])
        blob = "\n".join(t for _, t in texts)
        for dst in repos:
            if src == dst:
                continue
            # \b<dst>\b mit Escape (Repo-Namen können Bindestriche enthalten)
            pat = re.compile(rf'(?<!\w){re.escape(dst)}(?!\w)', re.IGNORECASE)
            n = len(pat.findall(blob))
            if n > 0:
                edges[(src, dst)] = n

    # crosslinks.md
    cl = out / "crosslinks.md"
    cl.write_text("## Cross-Repo-Bezüge (Namens-Erwähnungen)\n\n", encoding="utf-8")
    if not edges:
        cl.write_text(cl.read_text(encoding="utf-8") + "*(keine Bezüge gefunden – Heuristik ist konservativ)*\n", encoding="utf-8")
    else:
        cl.write_text(cl.read_text(encoding="utf-8") + "Quelle: String-Suche nach Repo-Namen in Textdateien.\n\n", encoding="utf-8")
        cl.write_text(cl.read_text(encoding="utf-8") + "| Quelle → Ziel | Erwähnungen |\n|---|---:|\n", encoding="utf-8")
        for (s, d), n in sorted(edges.items(), key=lambda x: (x[0][0], x[0][1])):
            cl.write_text(cl.read_text(encoding="utf-8") + f"| {s} → {d} | {n} |\n", encoding="utf-8")

    # Mermaid
    mmd = out / "crosslinks.mmd"
    if not edges:
        mmd.write_text("graph LR\n  A[Keine Bezüge]--0-->B[—]\n", encoding="utf-8")
    else:
        lines = ["graph LR"]
        for (s, d), n in sorted(edges.items()):
            sid = safe_id(s)
            did = safe_id(d)
            # Node mit Label = Originalname
            lines.append(f'  {sid}["{s}"] -->|{n}| {did}["{d}"]')
        mmd.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("✓ merge completed", file=sys.stderr)

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-repomerger-heimgewebe-merge-README-md"></a>
### `merger/repomerger/heimgewebe-merge/README.md`
- Category: doc
- Tags: ai-context
- Size: 1.70 KB
- Included: full
- MD5: a62845cc3c979895f57c6f93a6f9470d

```markdown
# Heimgewebe-Merger (Org-Überblick mit Crosslinks)

Mergt **alle öffentlichen Repos** der Orga `heimgewebe` in **gesplittete Markdown-Dossiers**,
mit zusätzlichem **Index** und **Cross-Repo-Analyse**.

## Scope
- **Ausgeschlossen**: `vault-gewebe`, `vault-privat`, `weltgewebe` (anpassbar via `EXCLUDES_CSV`).
- Typische Code-/Doku-Dateien werden inkludiert; große/binäre Artefakte werden übersprungen.
- Splits bei Erreichen eines konfigurierbaren Byte-Limits.

## Output
- `dossier-part-XXXX.md` – Gesamtsicht in Häppchen (GPT-Upload-freundlich)
- `index.md` – Kennzahlen pro Repo (Dateien, MB, grobe Sprachverteilung per Dateiendung)
- `crosslinks.md` – Textuelle Bezüge zwischen Repos (Fundstellen/Counts)
- `crosslinks.mmd` – Mermaid Graph (kann in Markdown-Viewer gerendert werden)

## Voraussetzungen
- `bash`, `python3`, `git`, `gh` (GitHub CLI, eingeloggt; read-only reicht)

## Quickstart
```bash
bash repomerger/heimgewebe-merge/run.sh out/heimgewebe-dossier
```

## Nützliche ENV-Schalter
```bash
# Nur bestimmte Repos (Komma-Liste)
ONLY="hausKI,chronik" bash repomerger/heimgewebe-merge/run.sh out/hgw

# Byte-Limit je Part (Default 5 MiB)
MAX_BYTES=$((8*1024*1024)) bash repomerger/heimgewebe-merge/run.sh out/hgw

# Exclude-Liste ergänzen/ändern
EXCLUDES_CSV="vault-gewebe,vault-privat,weltgewebe,foo" bash repomerger/heimgewebe-merge/run.sh out/hgw

# Muster für Inklusion (Komma-Liste, Glob)
GLOBS="README.md,docs/**,**/*.md,**/*.rs,**/*.py,**/*.ts,**/*.svelte,**/*.sh" \
  bash repomerger/heimgewebe-merge/run.sh out/hgw
```

## Hinweise
- Reihenfolge ist kuratiert: Kern-Repos zuerst, Rest alphabetisch.
- Crosslinks basieren auf Repo-Namens-Erwähnungen im Text (heuristisch, schnell und offline).

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-repomerger-heimgewebe-merge-run-sh"></a>
### `merger/repomerger/heimgewebe-merge/run.sh`
- Category: source
- Tags: -
- Size: 2.16 KB
- Included: full
- MD5: 30e0c3b4f3f7a8cb125626cd74cb6ff4

```bash
#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-out/heimgewebe-dossier}"
ORG="heimgewebe"
# Vaults + Weltgewebe pauschal raus:
EXCLUDES_CSV="${EXCLUDES_CSV:-vault-gewebe,vault-privat,weltgewebe}"
ONLY="${ONLY:-}"                               # optional: "repo1,repo2"
MAX_BYTES="${MAX_BYTES:-$((5 * 1024 * 1024))}" # 5 MiB Default
GLOBS="${GLOBS:-README.md,docs/**,**/*.md,**/*.rs,**/*.py,**/*.ts,**/*.tsx,**/*.js,**/*.svelte,**/*.sh,**/*.bash,**/*.fish,**/*.zsh,**/*.sql,**/*.yml,**/*.yaml,**/*.toml}"
BINARY_CUTOFF="${BINARY_CUTOFF:-262144}" # 256 KiB
WORK="${WORK:-.git/tmp/heimgewebe-merge}"

need() { command -v "$1" >/dev/null 2>&1 || {
	echo "Fehlt: $1" >&2
	exit 127
}
}
need git
need gh
need python3

mkdir -p "$OUT_DIR" "$WORK"

echo "• Liste Repos aus ORG '$ORG'…"
mapfile -t ALL < <(gh repo list "$ORG" --limit 200 --json name,isPrivate --jq '.[] | select(.isPrivate|not) .name')

IFS=',' read -r -a EX_ARR <<<"$EXCLUDES_CSV"
declare -A EX_SET
for e in "${EX_ARR[@]}"; do EX_SET["$e"]=1; done

# Kuratierte Reihenfolge zuerst
preferred=(metarepo wgx hausKI semantAH chronik aussensensor heimlern)
declare -A PSET
for p in "${preferred[@]}"; do PSET["$p"]=1; done

# Filtern
sel=()
for r in "${ALL[@]}"; do
	[[ -n "${EX_SET[$r]:-}" ]] && continue
	sel+=("$r")
done

# ONLY anwenden (falls gesetzt)
if [[ -n "$ONLY" ]]; then
	IFS=',' read -r -a only_arr <<<"$ONLY"
	tmp=()
	for o in "${only_arr[@]}"; do
		for r in "${sel[@]}"; do
			[[ "$r" == "$o" ]] && tmp+=("$r")
		done
	done
	sel=("${tmp[@]}")
fi

# sortiere: preferred in angegebener Reihenfolge, Rest alphabetisch dahinter
ordered=()
for p in "${preferred[@]}"; do
	for r in "${sel[@]}"; do [[ "$r" == "$p" ]] && ordered+=("$r"); done
done
rest=()
for r in "${sel[@]}"; do [[ -z "${PSET[$r]:-}" ]] && rest+=("$r"); done
mapfile -t rest_sorted < <(printf "%s\n" "${rest[@]}" | sort)
ordered+=("${rest_sorted[@]}")

echo "• Ausgewählt: ${#ordered[@]} Repos"
echo "• Excludes: ${EXCLUDES_CSV}"
python3 "$(dirname "$0")/merge.py" \
	--org "$ORG" \
	--repos "${ordered[@]}" \
	--out "$OUT_DIR" \
	--max-bytes "$MAX_BYTES" \
	--globs "$GLOBS" \
	--binary-cutoff "$BINARY_CUTOFF" \
	--work "$WORK"

echo "✓ Fertig. Outputs in: $OUT_DIR"

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-repomerger-repomerger-py"></a>
### `merger/repomerger/repomerger.py`
- Category: source
- Tags: -
- Size: 23.08 KB
- Included: full
- MD5: 2d5415f3ac85f934e1f7e74b3c28ae6c

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
repomerger – Multi-Repo-Merge ohne Diff, mit Plan-Phase, Kategorien und 3 Detailstufen.

Funktionen:
- Erzeugt EIN Markdown-File mit Überblick über ein oder mehrere Repos.
- Inhalte:
  - Plan-Abschnitt (Metaüberblick mit Kategorien- und Endungsstatistik).
  - Baumstruktur über alle Quellen.
  - Manifest aller gefundenen Dateien.
  - Je nach Detailstufe: Inhalte von Textdateien (mit Größenlimit pro Datei).

Detailstufen:
- overview: Struktur + Manifest, keine Inhalte.
- summary:  Struktur + Manifest + Inhalte aller Textdateien <= max_file_bytes.
- full:     Struktur + Manifest + Inhalte aller Textdateien,
            größere Textdateien werden bis max_file_bytes gekürzt.

Besonderheiten:
- Keine Diffs zu früheren Läufen: jeder Merge ist ein eigenständiger Schnappschuss.
- Mehrere Repos pro Lauf möglich.
- .env / .env.* werden ignoriert, außer .env.example / .env.template / .env.sample.
- Merge-Dateien werden IMMER in den Ordner "merges" geschrieben (neben dem Script).
- Quellordner werden nach dem Merge gelöscht, WENN sie im gleichen Ordner wie das Script liegen
  (und nicht der merges-Ordner sind). Abschaltbar mit --no-delete.
"""

import argparse
import datetime
import hashlib
import os
import shutil
from pathlib import Path

# --- Konfiguration / Heuristiken --------------------------------------------

MERGES_DIR_NAME = "merges"

# Verzeichnisse, die standardmäßig ignoriert werden (rekursiv)
SKIP_DIRS = {
    ".git",
    ".idea",
    # bewusst NICHT: ".vscode" (tasks.json etc. sind interessant)
    "node_modules",
    ".svelte-kit",
    ".next",
    "dist",
    "build",
    "target",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}

# Top-Level-Verzeichnisse, die bei Auto-Discovery nicht als Repos genommen werden sollen
SKIP_ROOTS = {
    MERGES_DIR_NAME,
    "merge",
    "output",
    "out",
}

# Einzelne Dateien, die ignoriert werden
SKIP_FILES = {
    ".DS_Store",
}

# Erweiterungen, die sehr wahrscheinlich Text sind
TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".rs",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".jsonl",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".dockerfile",
    "dockerfile",
    ".svelte",
    ".css",
    ".scss",
    ".html",
    ".htm",
    ".xml",
    ".csv",
    ".log",
    ".lock",   # z.B. Cargo.lock, pnpm-lock.yaml
}

# Dateien, die typischerweise Konfiguration sind
CONFIG_FILENAMES = {
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "Cargo.toml",
    "Cargo.lock",
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Justfile",
    "Makefile",
    "toolchain.versions.yml",
    ".editorconfig",
    ".markdownlint.jsonc",
    ".markdownlint.yaml",
    ".yamllint",
    ".yamllint.yml",
    ".lychee.toml",
    ".vale.ini",
}

DOC_EXTENSIONS = {".md", ".rst", ".txt"}

LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "html": "html", "css": "css",
    "scss": "scss", "sass": "sass", "json": "json", "xml": "xml", "yaml": "yaml", "yml": "yaml",
    "md": "markdown", "sh": "bash", "bat": "batch", "sql": "sql", "php": "php", "cpp": "cpp",
    "c": "c", "java": "java", "cs": "csharp", "go": "go", "rs": "rust", "rb": "ruby",
    "swift": "swift", "kt": "kotlin", "svelte": "svelte",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".rs",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".svelte",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".go",
    ".java",
    ".cs",
}


class FileInfo(object):
    """Einfache Container-Klasse für Dateimetadaten."""

    def __init__(self, root_label, abs_path, rel_path, size, is_text, md5, category, ext):
        self.root_label = root_label
        self.abs_path = abs_path
        self.rel_path = rel_path
        self.size = size
        self.is_text = is_text
        self.md5 = md5
        self.category = category
        self.ext = ext


# --- Hilfsfunktionen ---------------------------------------------------------

def human_size(n):
    """Formatierte Dateigröße, z.B. '1.23 MB'."""
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0 or unit == "GB":
            return "{0:.2f} {1}".format(size, unit)
        size /= 1024.0
    return "{0:.2f} GB".format(size)


def is_probably_text(path, size):
    """
    Heuristik: Ist dies eher eine Textdatei?

    - bekannte Text-Endungen -> True
    - große unbekannte Dateien -> eher False
    - ansonsten: 4 KiB lesen, auf NUL-Bytes prüfen.
    """
    name = path.name.lower()
    base, ext = os.path.splitext(name)
    if ext in TEXT_EXTENSIONS or name in TEXT_EXTENSIONS:
        return True

    # Sehr große unbekannte Dateien eher als binär behandeln
    if size > 20 * 1024 * 1024:  # 20 MiB
        return False

    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
    except OSError:
        return False

    if not chunk:
        return True
    if b"\x00" in chunk:
        return False

    return True


def compute_md5(path, limit_bytes=None):
    """
    MD5-Hash einer Datei.

    - Wenn limit_bytes gesetzt ist, lesen wir höchstens so viele Bytes.
    - Bei Fehlern: 'ERROR'.
    """
    h = hashlib.md5()
    try:
        with path.open("rb") as f:
            remaining = limit_bytes
            while True:
                if remaining is None:
                    chunk = f.read(65536)
                else:
                    chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                h.update(chunk)
                if remaining is not None:
                    remaining -= len(chunk)
                    if remaining <= 0:
                        break
        return h.hexdigest()
    except OSError:
        return "ERROR"


def lang_for(ext):
    """Ermittelt die Sprache für Markdown-Blöcke anhand der Endung."""
    return LANG_MAP.get(ext.lower().lstrip("."), "")


def classify_category(rel_path, ext):
    """
    Grobe Einteilung in doc / config / source / other.
    """
    name = rel_path.name
    if name in CONFIG_FILENAMES:
        return "config"
    if ext in DOC_EXTENSIONS:
        return "doc"
    if ext in SOURCE_EXTENSIONS:
        return "source"
    parts = [p.lower() for p in rel_path.parts]
    for p in parts:
        if p in ("config", "configs", "settings", "etc", ".github"):
            return "config"
    if "docs" in parts or "doc" in parts:
        return "doc"
    return "other"


def summarize_extensions(file_infos):
    """Anzahl und Gesamtgröße pro Dateiendung."""
    counts = {}
    sizes = {}
    for fi in file_infos:
        ext = fi.ext or "<none>"
        counts[ext] = counts.get(ext, 0) + 1
        sizes[ext] = sizes.get(ext, 0) + fi.size
    return counts, sizes


def summarize_categories(file_infos):
    """Anzahl und Gesamtgröße pro Kategorie."""
    stats = {}
    for fi in file_infos:
        cat = fi.category or "other"
        if cat not in stats:
            stats[cat] = [0, 0]
        stats[cat][0] += 1
        stats[cat][1] += fi.size
    return stats


def scan_repo(repo, md5_limit_bytes):
    """
    Scannt ein einzelnes Repo und erzeugt FileInfo-Einträge.
    """
    repo = repo.resolve()
    root_label = repo.name
    files = []

    for dirpath, dirnames, filenames in os.walk(str(repo)):
        # Verzeichnisse filtern
        keep_dirs = []
        for d in dirnames:
            if d in SKIP_DIRS:
                continue
            keep_dirs.append(d)
        dirnames[:] = keep_dirs

        for fn in filenames:
            if fn in SKIP_FILES:
                continue

            # .env und .env.* ignorieren, außer expliziten Vorlagen
            if fn.startswith(".env") and fn not in (".env.example", ".env.template", ".env.sample"):
                continue

            abs_path = Path(dirpath) / fn
            try:
                st = abs_path.stat()
            except OSError:
                continue
            size = st.st_size

            rel = abs_path.relative_to(repo)
            ext = abs_path.suffix.lower()

            is_text = is_probably_text(abs_path, size)

            if is_text or size <= md5_limit_bytes:
                md5 = compute_md5(abs_path, md5_limit_bytes)
            else:
                md5 = ""

            category = classify_category(rel, ext)

            fi = FileInfo(
                root_label=root_label,
                abs_path=abs_path,
                rel_path=rel,
                size=size,
                is_text=is_text,
                md5=md5,
                category=category,
                ext=ext,
            )
            files.append(fi)

    files.sort(key=lambda fi: (fi.root_label.lower(), str(fi.rel_path).lower()))
    return files


def build_tree(file_infos):
    """
    Erzeugt eine einfache Baumdarstellung pro Root.
    """
    by_root = {}
    for fi in file_infos:
        by_root.setdefault(fi.root_label, []).append(fi.rel_path)

    lines = ["```"]
    for root in sorted(by_root.keys()):
        rels = by_root[root]
        lines.append(u"📁 {0}/".format(root))

        tree = {}
        for r in rels:
            parts = list(r.parts)
            node = tree
            for p in parts:
                if p not in node:
                    node[p] = {}
                node = node[p]

        def walk(node, indent):
            dirs = []
            files = []
            for k, v in node.items():
                if v:
                    dirs.append(k)
                else:
                    files.append(k)
            for d in sorted(dirs):
                lines.append(u"{0}📁 {1}/".format(indent, d))
                walk(node[d], indent + "    ")
            for f in sorted(files):
                lines.append(u"{0}📄 {1}".format(indent, f))

        walk(tree, "    ")

    lines.append("```")
    return "\n".join(lines)


def make_output_filename(sources, now):
    """
    Dateiname: <repo1>-<repo2>-..._<ddmm>.md
    """
    names = sorted(set([src.name for src in sources]))
    joined = "-".join(names)
    joined = joined.replace(" ", "-")
    if len(joined) > 60:
        joined = joined[:60]
    date_str = now.strftime("%d%m")
    return "{0}_{1}.md".format(joined, date_str)


# --- Report-Erzeugung --------------------------------------------------------

def write_report(files, level, max_file_bytes, output_path, sources,
                 encoding="utf-8", plan_only=False):
    """
    Schreibt den Merge-Report.
    """
    now = datetime.datetime.now()

    total_size = sum(fi.size for fi in files)
    text_files = [fi for fi in files if fi.is_text]
    binary_files = [fi for fi in files if not fi.is_text]

    if level == "overview":
        planned_with_content = 0
    elif level == "summary":
        planned_with_content = sum(1 for fi in text_files if fi.size <= max_file_bytes)
    else:  # full
        planned_with_content = len(text_files)

    ext_counts, ext_sizes = summarize_extensions(files)
    cat_stats = summarize_categories(files)

    lines = []

    # Header & Hinweise
    lines.append("# Gewebe-Merge")
    lines.append("")
    lines.append("**Zeitpunkt:** {0}".format(now.strftime("%Y-%m-%d %H:%M:%S")))
    if sources:
        lines.append("**Quellen:**")
        for src in sources:
            lines.append("- `{0}`".format(src))
    lines.append("**Detailstufe:** `{0}`".format(level))
    lines.append("**Maximale Inhaltsgröße pro Datei:** {0}".format(human_size(max_file_bytes)))
    lines.append("")
    lines.append("> Hinweis für KIs:")
    lines.append("> - Dies ist ein Schnappschuss des Dateisystems, keine vollständige Git-Historie.")
    lines.append("> - Baumansicht: `## 📁 Struktur`.")
    lines.append("> - Manifest: `## 🧾 Manifest`.")
    if level == "overview":
        lines.append("> - In dieser Detailstufe werden keine Dateiinhalte eingebettet.")
    elif level == "summary":
        lines.append("> - In dieser Detailstufe werden Inhalte kleiner Textdateien eingebettet;")
        lines.append(">   größere Textdateien erscheinen nur im Manifest.")
    else:
        lines.append("> - In dieser Detailstufe werden Inhalte aller Textdateien eingebettet;")
        lines.append(">   große Dateien werden nach einer einstellbaren Byte-Grenze gekürzt.")
    lines.append("> - `.env`-ähnliche Dateien werden gefiltert; sensible Daten können trotzdem in")
    lines.append(">   anderen Textdateien vorkommen. Nutze den Merge nicht als öffentlichen Dump.")
    lines.append("")

    # Plan
    lines.append("## 🧮 Plan")
    lines.append("")
    lines.append("- Gefundene Dateien gesamt: **{0}**".format(len(files)))
    lines.append("- Davon Textdateien: **{0}**".format(len(text_files)))
    lines.append("- Davon Binärdateien: **{0}**".format(len(binary_files)))
    lines.append("- Geplante Dateien mit Inhalteinbettung: **{0}**".format(planned_with_content))
    lines.append("- Gesamtgröße der Quellen: **{0}**".format(human_size(total_size)))
    if any(fi.size > max_file_bytes for fi in text_files):
        lines.append(
            "- Hinweis: Textdateien größer als {0} werden abhängig von der Detailstufe "
            "gekürzt oder nur im Manifest aufgeführt.".format(human_size(max_file_bytes))
        )
    lines.append("")

    if cat_stats:
        lines.append("**Dateien nach Kategorien:**")
        lines.append("")
        lines.append("| Kategorie | Dateien | Gesamtgröße |")
        lines.append("| --- | ---: | ---: |")
        for cat in sorted(cat_stats.keys()):
            cnt, sz = cat_stats[cat]
            lines.append("| `{0}` | {1} | {2} |".format(cat, cnt, human_size(sz)))
        lines.append("")

    if ext_counts:
        lines.append("**Grobe Statistik nach Dateiendungen:**")
        lines.append("")
        lines.append("| Ext | Dateien | Gesamtgröße |")
        lines.append("| --- | ---: | ---: |")
        for ext in sorted(ext_counts.keys()):
            lines.append("| `{0}` | {1} | {2} |".format(
                ext, ext_counts[ext], human_size(ext_sizes[ext])
            ))
        lines.append("")

    lines.append(
        "Da der repomerger häufig nacheinander unterschiedliche Repos verarbeitet, "
        "werden keine Diffs zu früheren Läufen berechnet. "
        "Jeder Merge ist ein eigenständiger Schnappschuss."
    )
    lines.append("")

    if plan_only:
        output_path.write_text("\n".join(lines), encoding=encoding)
        return

    # Struktur
    lines.append("## 📁 Struktur")
    lines.append("")
    lines.append(build_tree(files))
    lines.append("")

    # Manifest
    lines.append("## 🧾 Manifest")
    lines.append("")
    lines.append("| Root | Pfad | Kategorie | Text | Größe | MD5 |")
    lines.append("| --- | --- | --- | --- | ---: | --- |")
    for fi in files:
        lines.append(
            "| `{0}` | `{1}` | `{2}` | {3} | {4} | `{5}` |".format(
                fi.root_label,
                fi.rel_path,
                fi.category,
                "ja" if fi.is_text else "nein",
                human_size(fi.size),
                fi.md5,
            )
        )
    lines.append("")

    # Inhalte
    if level != "overview":
        lines.append("## 📄 Dateiinhalte")
        lines.append("")
        for fi in files:
            if not fi.is_text:
                continue

            if level == "summary" and fi.size > max_file_bytes:
                continue

            lines.append("### `{0}/{1}`".format(fi.root_label, fi.rel_path))
            lines.append("")
            if fi.size > max_file_bytes and level == "full":
                lines.append(
                    "**Hinweis:** Datei ist größer als {0} – es wird nur ein Ausschnitt "
                    "bis zu dieser Grenze gezeigt.".format(human_size(max_file_bytes))
                )
                lines.append("")

            try:
                with fi.abs_path.open("r", encoding=encoding, errors="replace") as f:
                    if fi.size > max_file_bytes and level == "full":
                        remaining = max_file_bytes
                        collected = []
                        for line in f:
                            encoded = line.encode(encoding, errors="replace")
                            if remaining <= 0:
                                break
                            if len(encoded) > remaining:
                                part = encoded[:remaining].decode(encoding, errors="replace")
                                collected.append(part + "\n[... gekürzt ...]\n")
                                remaining = 0
                                break
                            collected.append(line)
                            remaining -= len(encoded)
                        content = "".join(collected)
                    else:
                        content = f.read()
            except OSError as e:
                lines.append("_Fehler beim Lesen der Datei: {0}_".format(e))
                lines.append("")
                continue

            lines.append("```{0}".format(lang_for(fi.ext)))
            lines.append(content.rstrip("\n"))
            lines.append("```")
            lines.append("")

    output_path.write_text("\n".join(lines), encoding=encoding)


# --- CLI / Source-Erkennung / Delete-Logik ----------------------------------

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Erzeuge einen Gewebe-Merge-Bericht für ein oder mehrere Repos."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "Quellverzeichnisse (Repos). "
            "Wenn leer, werden alle Unterordner im Script-Ordner verwendet, "
            "die nicht mit '.' oder '_' beginnen."
        ),
    )
    parser.add_argument(
        "--level",
        choices=["overview", "summary", "full", "medium", "max"],
        help=(
            "Detailstufe: overview=Struktur+Manifest, summary=mit kleinen Inhalten, "
            "full=maximal. medium≈summary, max≈full."
        ),
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=10_000_000,
        help="Maximale Bytes pro Datei für Inhalteinbettung (Standard: 10 MiB).",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encoding für Textdateien (Standard: utf-8).",
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Nur den Plan-Teil des Berichts erzeugen (kein Manifest, keine Inhalte).",
    )
    parser.add_argument(
        "--no-delete",
        action="store_true",
        help="Quellordner nach dem Merge NICHT löschen.",
    )
    return parser.parse_args(argv)


def resolve_level(raw_level):
    """
    Übersetzt CLI/ENV-Level in eines der drei Kern-Level.
    Default = full.
    """
    if raw_level is None:
        return "full"
    raw = str(raw_level).lower()
    if raw == "overview":
        return "overview"
    if raw in ("summary", "medium"):
        return "summary"
    if raw in ("full", "max"):
        return "full"
    return "full"


def discover_sources(base_dir, paths):
    """
    Ermittelt die zu scannenden Repos.
    - Wenn paths angegeben: nutzt genau diese (falls Verzeichnisse).
    - Sonst: alle Unterordner im Script-Ordner, außer '.', '_', MERGES_DIR_NAME, SKIP_ROOTS.
    """
    if paths:
        sources = []
        for p in paths:
            path = Path(p).expanduser().resolve()
            if path.is_dir():
                sources.append(path)
            else:
                print("Warnung: Pfad ist kein Verzeichnis und wird ignoriert: {0}".format(p))
        return sources

    sources = []
    for child in sorted(base_dir.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name.startswith("_"):
            continue
        if child.name in SKIP_ROOTS:
            continue
        sources.append(child.resolve())
    return sources


def safe_delete_source(src, base_dir, merges_dir, no_delete):
    """
    Löscht eine Quelle nur, wenn:
    - sie im gleichen Ordner wie das Script liegt (parent == base_dir) UND
    - sie nicht der merges-Ordner ist.
    """
    if no_delete:
        print("Löschen deaktiviert (--no-delete): {0}".format(src))
        return

    try:
        src = src.resolve()
        base_dir = base_dir.resolve()
        merges_dir = merges_dir.resolve()
    except Exception as e:
        print("Warnung: Fehler beim Auflösen von Pfaden: {0}".format(e), file=sys.stderr)
        return

    parent = src.parent
    if parent != base_dir:
        print("Quelle wird nicht gelöscht (liegt nicht im Script-Ordner): {0}".format(src))
        return
    if src == merges_dir:
        print("Merges-Ordner wird nicht gelöscht: {0}".format(src))
        return

    try:
        shutil.rmtree(str(src))
        print("Quelle gelöscht: {0}".format(src))
    except Exception as e:
        print("Fehler beim Löschen von {0}: {1}".format(src, e))


def main(argv=None):
    import sys
    import traceback

    if argv is None:
        argv = sys.argv[1:]

    try:
        script_path = Path(__file__).resolve()
        base_dir = script_path.parent
        merges_dir = base_dir / MERGES_DIR_NAME
        merges_dir.mkdir(parents=True, exist_ok=True)

        args = parse_args(argv)

        sources = discover_sources(base_dir, args.paths)
        if not sources:
            print("Keine gültigen Quellverzeichnisse gefunden.", file=sys.stderr)
            return 1

        env_level = os.environ.get("REPOMERGER_LEVEL")
        raw_level = args.level or env_level
        level = resolve_level(raw_level)

        now = datetime.datetime.now()
        filename = make_output_filename(sources, now)
        output_path = merges_dir / filename

        md5_limit = args.max_file_bytes

        all_files = []
        for src in sources:
            print("Scanne Quelle: {0}".format(src))
            repo_files = scan_repo(src, md5_limit_bytes=md5_limit)
            print("  -> {0} Dateien gefunden.".format(len(repo_files)))
            all_files.extend(repo_files)

        if not all_files:
            print("Keine Dateien in den Quellen gefunden.", file=sys.stderr)
            return 1

        print("Erzeuge Merge-Bericht mit {0} Dateien: {1}".format(len(all_files), output_path))
        write_report(
            files=all_files,
            level=level,
            max_file_bytes=args.max_file_bytes,
            output_path=output_path,
            sources=sources,
            encoding=args.encoding,
            plan_only=args.plan_only,
        )
        print("Fertig.")

        # Quellordner löschen (falls im gleichen Ordner wie das Script)
        for src in sources:
            safe_delete_source(src, base_dir, merges_dir, args.no_delete)

        if args.plan_only:
            print("Hinweis: Es wurde nur der Plan-Teil erzeugt (--plan-only).")
        return 0

    except Exception as e:
        print("repomerger: Unbehandelter Fehler:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-repomerger-weltgewebe-merger-py"></a>
### `merger/repomerger/weltgewebe-merger.py`
- Category: source
- Tags: -
- Size: 22.82 KB
- Included: full
- MD5: e4397357d4bca19cbf68ca562626b5d4

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
repo-merger – Shortcuts-freundlich, Dotfiles inklusive, Basename/Env/Config-Fallbacks, keep last N merges

Nutzung auf iOS (Shortcuts → "Run Pythonista Script" → Arguments):
    – GIB GENAU EINE DER VARIANTEN, KEINE UMBRÜCHE:
      1) --source-dir "/private/var/.../weltgewebe"
      2) "/private/var/.../weltgewebe"
      3) file:///private/var/.../weltgewebe
      4) weltgewebe   (nur Basename; Fallback-Suche aktiv)
    – Alternativ Env: GEWEBE_SOURCE="/private/var/.../weltgewebe"

Ausgabe:
    ./merge/weltgewebe_DDMM.md (bei Mehrfach-Merges: weltgewebe_DDMM_2.md, ...)
    – Standard: nur die letzten 2 Merges bleiben (per Config / CLI änderbar)

Konfig (optional):
    ~/.config/repo-merger/config.ini

    [general]
    keep = 2
    merge_dirname = merge
    merge_prefix  = weltgewebe
    max_search_depth = 4
    encoding = utf-8

    [aliases]
    weltgewebe = /private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/weltgewebe

CLI (optional):
    --source-dir <PATH|BASENAME|file://URL>
    --keep <N>
    --encoding <ENC>
    --max-depth <N>        # Baumdarstellung im Report (None = alles)
    --search-depth <N>     # Fallback-Suche (tiefer = langsamer)
    --merge-dirname <NAME> # Ordner für Merges
    --merge-prefix <STR>   # Basisname für Merge-Dateien (Default: weltgewebe)
    -h / --help            # Minimalhelp (add_help=False, aber wir drucken selbst)
"""

import sys, os, argparse, hashlib, urllib.parse, configparser
from pathlib import Path
from datetime import datetime

# ===== Defaults (per Config/CLI überschreibbar) =====
DEF_KEEP          = 2
DEF_MERGE_DIRNAME = "merge"
# merge_prefix = Basisname im Dateinamen, z. B. "weltgewebe" -> weltgewebe_DDMM.md
DEF_MERGE_PREFIX  = "weltgewebe"
DEF_ENCODING      = "utf-8"
DEF_SRCH_DEPTH    = 4

# nur wirklich binäre Endungen (Dotfiles & .svg bleiben erhalten)
BINARY_EXT = {
    ".png",".jpg",".jpeg",".gif",".bmp",".ico",".webp",".heic",".heif",".psd",".ai",
    ".mp3",".wav",".flac",".ogg",".m4a",".aac",".mp4",".mkv",".mov",".avi",".wmv",".flv",".webm",
    ".zip",".rar",".7z",".tar",".gz",".bz2",".xz",".tgz",
    ".ttf",".otf",".woff",".woff2",
    ".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".pages",".numbers",".key",
    ".exe",".dll",".so",".dylib",".bin",".class",".o",".a",
    ".db",".sqlite",".sqlite3",".realm",".mdb",".pack",".idx",
}

LANG_MAP = {
    'py':'python','js':'javascript','ts':'typescript','html':'html','css':'css','scss':'scss','sass':'sass',
    'json':'json','xml':'xml','yaml':'yaml','yml':'yaml','md':'markdown','sh':'bash','bat':'batch',
    'sql':'sql','php':'php','cpp':'cpp','c':'c','java':'java','cs':'csharp','go':'go','rs':'rust',
    'rb':'ruby','swift':'swift','kt':'kotlin','svelte':'svelte'
}

COMMON_BASES = [
    Path("/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents"),
    Path.home() / "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents",  # iOS/macOS iCloud
    Path.home() / "Documents",
]

# --- Klassifikations-Hilfen --------------------------------------------------

DOC_EXTENSIONS = {".md", ".rst", ".txt"}

SOURCE_EXTENSIONS = {
    ".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".svelte",
    ".c", ".cpp", ".h", ".hpp", ".go", ".java", ".cs",
}

CONFIG_FILENAMES = {
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "Cargo.toml",
    "Cargo.lock",
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Justfile",
    "Makefile",
    "toolchain.versions.yml",
    ".editorconfig",
    ".markdownlint.jsonc",
    ".markdownlint.yaml",
    ".yamllint",
    ".yamllint.yml",
    ".lychee.toml",
    ".vale.ini",
}

# ===== Utilities ============================================================

def human(n: int) -> str:
    u=["B","KB","MB","GB","TB"]; f=float(n); i=0
    while f>=1024 and i<len(u)-1: f/=1024; i+=1
    return f"{f:.2f} {u[i]}"

def is_text_file(p: Path, sniff=4096) -> bool:
    # harte Binär-Endungen
    if p.suffix.lower() in BINARY_EXT:
        return False
    # .env / .env.* aus Sicherheitsgründen ignorieren, außer Vorlagen
    name = p.name
    if name.startswith(".env") and name not in (".env.example", ".env.template", ".env.sample"):
        return False
    try:
        with p.open("rb") as f:
            chunk = f.read(sniff)
        if not chunk: return True
        if b"\x00" in chunk: return False
        try:
            chunk.decode("utf-8"); return True
        except UnicodeDecodeError:
            chunk.decode("latin-1", errors="ignore"); return True
    except Exception:
        return False

def lang_for(p: Path) -> str:
    return LANG_MAP.get(p.suffix.lower().lstrip("."), "")

def file_md5(p: Path, block=65536) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True); return p

def safe_is_dir(p: Path) -> bool:
    try:
        return p.is_dir()
    except Exception:
        return False

def _deurl(s: str) -> str:
    if s and s.lower().startswith("file://"):
        return urllib.parse.unquote(s[7:])
    return s or ""

def load_config():
    cfg = configparser.ConfigParser()
    cfg_path = Path.home() / ".config" / "repo-merger" / "config.ini"
    try:
        if cfg_path.exists():
            cfg.read(cfg_path, encoding="utf-8")
    except Exception:
        pass
    return cfg, cfg_path

def cfg_get_int(cfg, section, key, default):
    try:
        return cfg.getint(section, key, fallback=default)
    except Exception:
        return default

def cfg_get_str(cfg, section, key, default):
    try:
        return cfg.get(section, key, fallback=default)
    except Exception:
        return default

# ===== Klassifikation & Statistik ===========================================

def classify_category(rel: Path, ext: str) -> str:
    """Grobe Heuristik: doc / config / source / other."""
    name = rel.name
    if name in CONFIG_FILENAMES:
        return "config"
    if ext in DOC_EXTENSIONS:
        return "doc"
    if ext in SOURCE_EXTENSIONS:
        return "source"
    parts = [p.lower() for p in rel.parts]
    if any(p in ("config", "configs", "settings", "etc", ".github") for p in parts):
        return "config"
    if "docs" in parts or "doc" in parts:
        return "doc"
    return "other"

def summarize_ext(manifest_rows):
    """
    manifest_rows: Liste von (rel:Path, size:int, md5:str, cat:str, ext:str)
    -> (ext_counts, ext_sizes)
    """
    counts = {}
    sizes = {}
    for rel, sz, md5, cat, ext in manifest_rows:
        key = ext or "<none>"
        counts[key] = counts.get(key, 0) + 1
        sizes[key] = sizes.get(key, 0) + sz
    return counts, sizes

def summarize_cat(manifest_rows):
    """
    Kleine Übersicht nach Kategorien.
    -> dict cat -> (count, size)
    """
    result = {}
    for rel, sz, md5, cat, ext in manifest_rows:
        if cat not in result:
            result[cat] = [0, 0]
        result[cat][0] += 1
        result[cat][1] += sz
    return result

# ===== Fallback-Suche nach Basename =========================================

def find_dir_by_basename(basename: str, aliases, search_depth: int = DEF_SRCH_DEPTH):
    # 0) Aliases
    if basename in aliases:
        p = Path(_deurl(aliases[basename]).strip('"'))
        if safe_is_dir(p):
            return p, []

    candidates = []
    for base in COMMON_BASES:
        if not base.exists(): continue

        # schnelle Treffer
        pref = [
            base / basename,
            base / "ordnermerger" / basename,
            base / "Obsidian" / basename,
            base / "weltgewebe-programmierung" / basename,
        ]
        for c in pref:
            if safe_is_dir(c): candidates.append(c)

        # vorsichtige Suche
        try:
            max_depth_abs = len(str(base).split(os.sep)) + max(1, int(search_depth))
            for p in base.rglob(basename):
                if p.is_dir() and p.name == basename:
                    if len(str(p).split(os.sep)) <= max_depth_abs:
                        candidates.append(p)
        except Exception:
            pass

    uniq = []
    seen = set()
    for c in candidates:
        s = str(c)
        if s not in seen:
            uniq.append(c); seen.add(s)

    if not uniq:
        return None, []
    best = sorted(uniq, key=lambda p: (len(str(p)), str(p)))[0]
    others = [p for p in uniq if p != best]
    return best, others

# ===== Manifest/Diff/Tree ===================================================

def write_tree(out, root: Path, max_depth=None):
    def lines(d: Path, lvl=0):
        if max_depth is not None and lvl >= max_depth:
            return []
        res=[]
        try:
            items = sorted(d.iterdir(), key=lambda x:(not x.is_dir(), x.name.lower()))
            dirs  = [i for i in items if i.is_dir()]
            files = [i for i in items if i.is_file()]
            for i, sub in enumerate(dirs):
                pref = "└── " if (i==len(dirs)-1 and not files) else "├── "
                res.append("    "*lvl + f"{pref}📁 {sub.name}/")
                res += lines(sub, lvl+1)
            for i, f in enumerate(files):
                pref = "└── " if i==len(files)-1 else "├── "
                try:
                    icon = "📄" if is_text_file(f) else "🔒"
                    res.append("    "*lvl + f"{pref}{icon} {f.name} ({human(f.stat().st_size)})")
                except Exception:
                    res.append("    "*lvl + f"{pref}📄 {f.name}")
        except PermissionError:
            res.append("    "*lvl + "❌ Zugriff verweigert")
        return res

    out.write("```\n"); out.write(f"📁 {root.name}/\n")
    for ln in lines(root): out.write(ln+"\n")
    out.write("```\n\n")

def parse_manifest(md: Path):
    m = {}
    if not md or not md.exists(): return m
    try:
        inside = False
        with md.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if s.startswith("## 🧾 Manifest"):
                    inside = True; continue
                if inside:
                    if not s.startswith("- "):
                        if s.startswith("## "): break
                        continue
                    row = s[2:]
                    parts = [p.strip() for p in row.split("|")]
                    rel = parts[0] if parts else ""
                    md5 = ""
                    size = 0
                    for p in parts[1:]:
                        if p.startswith("md5="): md5 = p[4:].strip()
                        elif p.startswith("size="):
                            try: size = int(p[5:].strip())
                            except Exception: size = 0
                    if rel: m[rel] = (md5, size)
    except Exception:
        pass
    return m

def build_diff(current, merge_dir: Path, merge_prefix: str):
    # merge_prefix als Basisname: <prefix>_DDMM*.md
    merges = sorted(merge_dir.glob(f"{merge_prefix}_*.md"))
    if not merges: return [], 0, 0, 0
    last = merges[-1]
    old = parse_manifest(last)

    cur_paths = {str(rel) for _, rel, _, _ in current}
    old_paths = set(old.keys())

    added   = sorted(cur_paths - old_paths)
    removed = sorted(old_paths - cur_paths)
    changed = []
    for _, rel, _, h in current:
        r = str(rel)
        old_h = old.get(r, ("", 0))[0]
        if r in old_paths and old_h and h and old_h != h:
            changed.append(r)
    changed.sort()
    diffs = [("+", p) for p in added] + [("-", p) for p in removed] + [("~", p) for p in changed]
    return diffs, len(added), len(removed), len(changed)

def keep_last_n(merge_dir: Path, keep: int, keep_new: Path = None, merge_prefix: str = DEF_MERGE_PREFIX):
    merges = sorted(merge_dir.glob(f"{merge_prefix}_*.md"))
    if keep_new and keep_new not in merges:
        merges.append(keep_new); merges.sort()
    if keep <= 0: return
    if len(merges) <= keep: return
    for old in merges[:-keep]:
        try: old.unlink()
        except Exception: pass

# ===== Dateinamen-Logik =====================================================

def make_output_filename(merge_dir: Path, base_name: str) -> Path:
    """
    Erzeugt einen Dateinamen nach Schema:
        <base_name>_DDMM.md
    und hängt bei Kollisionen _2, _3, ... an.
    """
    now = datetime.now()
    ddmm = now.strftime("%d%m")
    base = f"{base_name}_{ddmm}"
    candidate = merge_dir / f"{base}.md"
    idx = 2
    while candidate.exists():
        candidate = merge_dir / f"{base}_{idx}.md"
        idx += 1
    return candidate

# ===== Merge ================================================================

def do_merge(source: Path, out_file: Path, *,
             encoding: str, keep: int,
             merge_dir: Path, merge_prefix: str,
             max_tree_depth, search_info: str):

    included = []      # (p, rel, sz, h)
    manifest_rows = [] # (rel, sz, h, cat, ext)
    skipped = []
    total = 0

    for dirpath, _, files in os.walk(source):
        d = Path(dirpath)
        for fn in files:
            p = d / fn
            rel = p.relative_to(source)

            if not is_text_file(p):
                skipped.append(f"{rel} (binär/ignoriert)")
                continue

            try:
                sz = p.stat().st_size
            except Exception as e:
                skipped.append(f"{rel} (stat error: {e})")
                continue
            try:
                h = file_md5(p)
            except Exception:
                h = ""

            total += sz
            included.append((p, rel, sz, h))

            ext = p.suffix.lower()
            cat = classify_category(rel, ext)
            manifest_rows.append((rel, sz, h, cat, ext))

    included.sort(key=lambda t: str(t[1]).lower())
    manifest_rows.sort(key=lambda t: str(t[0]).lower())

    out_file.parent.mkdir(parents=True, exist_ok=True)

    diffs, add_c, del_c, chg_c = build_diff(included, out_file.parent, merge_prefix)
    ext_counts, ext_sizes = summarize_ext(manifest_rows)
    cat_stats = summarize_cat(manifest_rows)

    with out_file.open("w", encoding=encoding) as out:
        out.write("# Gewebe-Merge\n\n")
        out.write(f"**Zeitpunkt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"**Quelle:** `{source}`\n")
        if search_info:
            out.write(f"**Quelle ermittelt:** {search_info}\n")
        out.write(f"**Dateien (inkludiert):** {len(included)}\n")
        out.write(f"**Gesamtgröße:** {human(total)}\n")
        if diffs:
            out.write(f"**Änderungen seit letztem Merge:** +{add_c} / -{del_c} / ~{chg_c}\n")
        out.write("\n")

        # KI-Hinweisblock
        out.write("> Hinweis für KIs:\n")
        out.write("> - Dies ist ein Schnappschuss des Dateisystems, keine vollständige Git-Historie.\n")
        out.write("> - Die Baumstruktur findest du unter `## 📁 Struktur`.\n"
                  "> - Alle aufgenommenen Dateien stehen im `## 🧾 Manifest`.\n")
        out.write("> - Dateiinhalte stehen unter `## 📄 Dateiinhalte`.\n")
        out.write("> - `.env` und ähnliche Dateien können bewusst fehlen (Sicherheitsfilter).\n\n")

        # Plan / Übersicht
        out.write("## 🧮 Plan\n\n")
        out.write(f"- Textdateien im Merge: **{len(included)}**\n")
        out.write(f"- Gesamtgröße der Quellen: **{human(total)}**\n")

        if cat_stats:
            out.write("\n**Dateien nach Kategorien:**\n\n")
            out.write("| Kategorie | Dateien | Gesamtgröße |\n")
            out.write("| --- | ---: | ---: |\n")
            for cat in sorted(cat_stats.keys()):
                cnt, sz = cat_stats[cat]
                out.write(f"| `{cat}` | {cnt} | {human(sz)} |\n")
            out.write("\n")

        if ext_counts:
            out.write("**Statistik nach Dateiendungen:**\n\n")
            out.write("| Ext | Dateien | Gesamtgröße |\n")
            out.write("| --- | ---: | ---: |\n")
            for ext in sorted(ext_counts.keys()):
                out.write(f"| `{ext}` | {ext_counts[ext]} | {human(ext_sizes[ext])} |\n")
            out.write("\n")

        out.write("Hinweis: Obwohl `.env`-ähnliche Dateien gefiltert werden, können sensible Daten ")
        out.write("in anderen Dateien (z. B. JSON/YAML) vorkommen. Nutze den Merge nicht als public Dump.\n\n")

        out.write("## 📁 Struktur\n\n")
        write_tree(out, source, max_tree_depth)

        if diffs:
            out.write("## 📊 Änderungen seit letztem Merge\n\n")
            for sym, pth in diffs:
                out.write(f"{sym} {pth}\n")
            out.write("\n")

        if skipped:
            out.write("## ⏭️ Übersprungen\n\n")
            for s in skipped:
                out.write(f"- {s}\n")
            out.write("\n")

        out.write("## 🧾 Manifest\n\n")
        for rel, sz, h, cat, ext in manifest_rows:
            out.write(f"- {rel} | md5={h} | size={sz} | cat={cat}\n")
        out.write("\n")

        out.write("## 📄 Dateiinhalte\n\n")
        for p, rel, sz, h in included:
            out.write(f"### 📄 {rel}\n\n**Größe:** {human(sz)}\n\n```{lang_for(p)}\n")
            try:
                txt = p.read_text(encoding=encoding, errors="replace")
            except Exception as e:
                txt = f"<<Lesefehler: {e}>>"
            out.write(txt)
            if not txt.endswith("\n"): out.write("\n")
            out.write("```\n\n")

    keep_last_n(out_file.parent, keep=keep, keep_new=out_file, merge_prefix=merge_prefix)
    print(f"✅ Merge geschrieben: {out_file} ({human(out_file.stat().st_size)})")

# ===== CLI / ARG-PARSING ====================================================

def build_parser():
    p = argparse.ArgumentParser(description="repo-merger – genau ein Quellordner", add_help=False)
    p.add_argument("--source-dir", dest="src_flag")
    p.add_argument("--keep", type=int, dest="keep")
    p.add_argument("--encoding", dest="encoding")
    p.add_argument("--max-depth", type=int, dest="max_tree_depth")
    p.add_argument("--search-depth", type=int, dest="search_depth")
    p.add_argument("--merge-dirname", dest="merge_dirname")
    p.add_argument("--merge-prefix", dest="merge_prefix")  # Basisname für Dateinamen
    p.add_argument("-h","--help", action="store_true", dest="help")
    p.add_argument("rest", nargs="*")  # Shortcuts liefert gern extra Tokens
    return p

def print_help():
    print(__doc__.strip())

def extract_source_path(argv, *, aliases, search_depth: int):
    """
    Akzeptiert:
      - --source-dir <PATH|BASENAME|file://>
      - <PATH|BASENAME|file://>
      - Datei → Elternordner
      - Env: GEWEBE_SOURCE
      - Fallback: Nur-Basename unter COMMON_BASES
    Rückgabe: (Pfad, InfoStringFürReport)
    """
    # Env-Override
    env_src = os.environ.get("GEWEBE_SOURCE", "").strip()
    if env_src:
        p = Path(_deurl(env_src).strip('"'))
        if not safe_is_dir(p) and p.exists():
            p = p.parent
        if safe_is_dir(p):
            return p, "GEWEBE_SOURCE (ENV)"

    # Flags + restliche Tokens
    tokens = []
    if "--source-dir" in argv:
        idx = argv.index("--source-dir")
        if idx + 1 < len(argv):
            tokens.append(argv[idx+1])
    tokens += [t for t in argv if t != "--source-dir"]

    # Schritt 1: direkte Pfade/URLs
    for tok in tokens:
        cand = _deurl((tok or "").strip('"'))
        if not cand: continue
        # Nur-Basename?
        if os.sep not in cand and not cand.lower().startswith("file://"):
            continue
        p = Path(cand)
        if p.exists():
            if p.is_file(): p = p.parent
            if safe_is_dir(p):
                return p, "direktes Argument"

    # Schritt 2: Basename-Suche (inkl. Aliases)
    for tok in tokens:
        cand = _deurl((tok or "").strip('"'))
        if not cand: continue
        if os.sep in cand or cand.lower().startswith("file://"):
            continue
        base = cand
        hit, others = find_dir_by_basename(base, aliases, search_depth=search_depth)
        if hit:
            info = f"Basename-Fallback ('{base}')"
            if others:
                others_s = " | ".join(str(p) for p in others[:5])
                print(f"__REPO_MERGER_INFO__: Mehrere Kandidaten gefunden, nehme kürzesten: {hit} | weitere: {others_s}")
            return hit, info

    return None, None

def _running_in_shortcuts() -> bool:
    # Heuristik: Shortcuts defaultet auf 1, sonst env überschreiben (GEWEBE_SHORTCUTS=0)
    return os.environ.get("GEWEBE_SHORTCUTS", "1") == "1"

def main(argv):
    cfg, cfg_path = load_config()
    args = build_parser().parse_args(argv)
    if args.help:
        print_help()
        return 0

    # Konfig lesen
    keep          = args.keep if args.keep is not None else cfg_get_int(cfg, "general", "keep", DEF_KEEP)
    merge_dirname = args.merge_dirname or cfg_get_str(cfg, "general", "merge_dirname", DEF_MERGE_DIRNAME)
    merge_prefix  = args.merge_prefix  or cfg_get_str(cfg, "general", "merge_prefix",  DEF_MERGE_PREFIX)
    encoding      = args.encoding or cfg_get_str(cfg, "general", "encoding", DEF_ENCODING)
    search_depth  = args.search_depth if args.search_depth is not None else cfg_get_int(cfg, "general", "max_search_depth", DEF_SRCH_DEPTH)
    max_tree_depth= args.max_depth if hasattr(args, "max_depth") and args.max_depth is not None else None

    # Aliases sammeln
    aliases = {}
    if cfg.has_section("aliases"):
        for k,v in cfg.items("aliases"):
            aliases[k] = v

    # Pfad extrahieren
    src, src_info = extract_source_path(
        [args.src_flag] + args.rest if args.src_flag else args.rest,
        aliases=aliases, search_depth=search_depth
    )
    if not src:
        print("❌ Quelle fehlt/unerkannt. Übergib Pfad/URL/Basename oder setze GEWEBE_SOURCE. (-h für Hilfe)")
        return 2
    if not safe_is_dir(src):
        print(f"❌ Quelle nicht gefunden oder kein Ordner: {src}")
        return 1

    script_root = Path(__file__).resolve().parent
    merge_dir   = ensure_dir(script_root / merge_dirname)

    # Dateiname: <merge_prefix>_DDMM(.md) + Kollision-Handling
    base_name = merge_prefix.rstrip("_")
    out_file  = make_output_filename(merge_dir, base_name=base_name)

    # Merge
    do_merge(
        src, out_file,
        encoding=encoding,
        keep=keep,
        merge_dir=merge_dir,
        merge_prefix=base_name,
        max_tree_depth=max_tree_depth,
        search_info=src_info
    )
    return 0

def _safe_main():
    try:
        rc = main(sys.argv[1:])
    except SystemExit as e:
        rc = int(getattr(e, "code", 1) or 0)
    except Exception as e:
        print(f"__REPO_MERGER_ERR__: {e}")
        rc = 1

    if _running_in_shortcuts():
        if rc != 0:
            print(f"__REPO_MERGER_WARN__: Exit {rc}")
        print("__REPO_MERGER_OK__")
    else:
        sys.exit(rc)

if __name__ == "__main__":
    _safe_main()

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-repomerger-wgx-merger-py"></a>
### `merger/repomerger/wgx-merger.py`
- Category: source
- Tags: -
- Size: 23.00 KB
- Included: full
- MD5: 3bacf2a09ed28e057069e6c57adfc372

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wgx-merger – Shortcuts-freundlich, Dotfiles inklusive, Basename/Env/Config-Fallbacks, keep last N merges

Nutzung auf iOS (Shortcuts → "Run Pythonista Script" → Arguments):
    – GIB GENAU EINE DER VARIANTEN, KEINE UMBRÜCHE:
      1) --source-dir "/private/var/.../wgx"
      2) "/private/var/.../wgx"
      3) file:///private/var/.../wgx
      4) wgx   (nur Basename; Fallback-Suche aktiv)
    – Alternativ Env: WGX_SOURCE="/private/var/.../wgx"

Ausgabe:
    ./merge/wgx_DDMM.md
    (bei Mehrfach-Merges am selben Tag: wgx_DDMM_2.md, wgx_DDMM_3.md, ...)
    – Standard: nur die letzten 2 Merges bleiben (per Config / CLI änderbar)

Konfig (optional):
    ~/.config/wgx-merger/config.ini

    [general]
    keep = 2
    merge_dirname = merge
    merge_prefix  = wgx
    max_search_depth = 4
    encoding = utf-8

    [aliases]
    wgx = /private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/wgx
"""

import sys
import os
import argparse
import hashlib
import urllib.parse
import configparser
from pathlib import Path
from datetime import datetime

# ===== Defaults =====
DEF_KEEP          = 2
DEF_MERGE_DIRNAME = "merge"
# Basisname im Dateinamen, z. B. "wgx" -> wgx_DDMM.md
DEF_MERGE_PREFIX  = "wgx"
DEF_ENCODING      = "utf-8"
DEF_SRCH_DEPTH    = 4

# nur wirklich binäre Endungen (Dotfiles & .svg bleiben erhalten)
BINARY_EXT = {
    ".png",".jpg",".jpeg",".gif",".bmp",".ico",".webp",".heic",".heif",".psd",".ai",
    ".mp3",".wav",".flac",".ogg",".m4a",".aac",".mp4",".mkv",".mov",".avi",".wmv",".flv",".webm",
    ".zip",".rar",".7z",".tar",".gz",".bz2",".xz",".tgz",
    ".ttf",".otf",".woff",".woff2",
    ".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".pages",".numbers",".key",
    ".exe",".dll",".so",".dylib",".bin",".class",".o",".a",
    ".db",".sqlite",".sqlite3",".realm",".mdb",".pack",".idx",
}

LANG_MAP = {
    "py": "python","js": "javascript","ts": "typescript","html": "html","css": "css",
    "scss": "scss","sass": "sass","json": "json","xml": "xml","yaml": "yaml","yml": "yaml",
    "md": "markdown","sh": "bash","bat": "batch","sql": "sql","php": "php","cpp": "cpp",
    "c": "c","java": "java","cs": "csharp","go": "go","rs": "rust","rb": "ruby",
    "swift": "swift","kt": "kotlin","svelte": "svelte",
}

COMMON_BASES = [
    Path("/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents"),
    Path.home() / "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents",
    Path.home() / "Documents",
]

# --- Klassifikations-Hilfen --------------------------------------------------

DOC_EXTENSIONS = {".md", ".rst", ".txt"}

SOURCE_EXTENSIONS = {
    ".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".svelte",
    ".c", ".cpp", ".h", ".hpp", ".go", ".java", ".cs",
}

CONFIG_FILENAMES = {
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "Cargo.toml",
    "Cargo.lock",
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Justfile",
    "Makefile",
    "toolchain.versions.yml",
    ".editorconfig",
    ".markdownlint.jsonc",
    ".markdownlint.yaml",
    ".yamllint",
    ".yamllint.yml",
    ".lychee.toml",
    ".vale.ini",
}

# ===== Utilities ============================================================

def human(n: int) -> str:
    u = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(u) - 1:
        f /= 1024
        i += 1
    return f"{f:.2f} {u[i]}"


def is_text_file(p: Path, sniff: int = 4096) -> bool:
    # harte Binär-Endungen
    if p.suffix.lower() in BINARY_EXT:
        return False
    # .env / .env.* aus Sicherheitsgründen ignorieren, außer Vorlagen
    name = p.name
    if name.startswith(".env") and name not in (".env.example", ".env.template", ".env.sample"):
        return False
    try:
        with p.open("rb") as f:
            chunk = f.read(sniff)
        if not chunk:
            return True
        if b"\x00" in chunk:
            return False
        try:
            chunk.decode("utf-8")
            return True
        except UnicodeDecodeError:
            chunk.decode("latin-1", errors="ignore")
            return True
    except Exception:
        return False


def lang_for(p: Path) -> str:
    return LANG_MAP.get(p.suffix.lower().lstrip("."), "")


def file_md5(p: Path, block: int = 65536) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_is_dir(p: Path) -> bool:
    try:
        return p.is_dir()
    except Exception:
        return False


def _deurl(s: str) -> str:
    if s and s.lower().startswith("file://"):
        return urllib.parse.unquote(s[7:])
    return s or ""


def load_config() -> tuple[configparser.ConfigParser, Path]:
    cfg = configparser.ConfigParser()
    cfg_path = Path.home() / ".config" / "wgx-merger" / "config.ini"
    try:
        if cfg_path.exists():
            cfg.read(cfg_path, encoding="utf-8")
    except Exception:
        pass
    return cfg, cfg_path


def cfg_get_int(cfg, section, key, default):
    try:
        return cfg.getint(section, key, fallback=default)
    except Exception:
        return default


def cfg_get_str(cfg, section, key, default):
    try:
        return cfg.get(section, key, fallback=default)
    except Exception:
        return default

# ===== Klassifikation & Statistik ===========================================

def classify_category(rel: Path, ext: str) -> str:
    """Grobe Heuristik: doc / config / source / other."""
    name = rel.name
    if name in CONFIG_FILENAMES:
        return "config"
    if ext in DOC_EXTENSIONS:
        return "doc"
    if ext in SOURCE_EXTENSIONS:
        return "source"
    parts = [p.lower() for p in rel.parts]
    if any(p in ("config", "configs", "settings", "etc", ".github") for p in parts):
        return "config"
    if "docs" in parts or "doc" in parts:
        return "doc"
    return "other"


def summarize_ext(manifest_rows):
    """
    manifest_rows: Liste von (rel:Path, size:int, md5:str, cat:str, ext:str)
    -> (ext_counts, ext_sizes)
    """
    counts: dict[str, int] = {}
    sizes: dict[str, int] = {}
    for rel, sz, md5, cat, ext in manifest_rows:
        key = ext or "<none>"
        counts[key] = counts.get(key, 0) + 1
        sizes[key] = sizes.get(key, 0) + sz
    return counts, sizes


def summarize_cat(manifest_rows):
    """
    Kleine Übersicht nach Kategorien.
    -> dict cat -> (count, size)
    """
    result: dict[str, list[int]] = {}
    for rel, sz, md5, cat, ext in manifest_rows:
        if cat not in result:
            result[cat] = [0, 0]
        result[cat][0] += 1
        result[cat][1] += sz
    return result

# ===== Basename-Fallback ====================================================

def find_dir_by_basename(basename: str, aliases: dict[str, str], search_depth: int = DEF_SRCH_DEPTH) -> tuple[Path | None, list[Path]]:
    # 0) Aliases
    if basename in aliases:
        p = Path(_deurl(aliases[basename]).strip('"'))
        if safe_is_dir(p):
            return p, []

    candidates: list[Path] = []
    for base in COMMON_BASES:
        if not base.exists():
            continue

        # schnelle Treffer
        pref = [
            base / basename,
            base / "ordnermerger" / basename,
            base / "Obsidian" / basename,
        ]
        for c in pref:
            if safe_is_dir(c):
                candidates.append(c)

        # vorsichtige Suche
        try:
            max_depth_abs = len(str(base).split(os.sep)) + max(1, int(search_depth))
            for p in base.rglob(basename):
                if p.is_dir() and p.name == basename and len(str(p).split(os.sep)) <= max_depth_abs:
                    candidates.append(p)
        except Exception:
            pass

    uniq: list[Path] = []
    seen: set[str] = set()
    for c in candidates:
        s = str(c)
        if s not in seen:
            uniq.append(c)
            seen.add(s)

    if not uniq:
        return None, []
    best = sorted(uniq, key=lambda p: (len(str(p)), str(p)))[0]
    others = [p for p in uniq if p != best]
    return best, others

# ===== Dateinamen-Logik =====================================================

def make_output_filename(merge_dir: Path, base_name: str) -> Path:
    """
    Erzeugt einen Dateinamen nach Schema:
        <base_name>_DDMM.md
    und hängt bei Kollisionen _2, _3, ... an.
    """
    now = datetime.now()
    ddmm = now.strftime("%d%m")
    base = f"{base_name}_{ddmm}"
    candidate = merge_dir / f"{base}.md"
    idx = 2
    while candidate.exists():
        candidate = merge_dir / f"{base}_{idx}.md"
        idx += 1
    return candidate

# ===== Manifest/Diff/Tree ===================================================

def write_tree(out, root: Path, max_depth: int | None = None):
    def lines(d: Path, lvl: int = 0):
        if max_depth is not None and lvl >= max_depth:
            return []
        res: list[str] = []
        try:
            items = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            dirs = [i for i in items if i.is_dir()]
            files = [i for i in items if i.is_file()]
            for i, sub in enumerate(dirs):
                pref = "└── " if (i == len(dirs) - 1 and not files) else "├── "
                res.append("    " * lvl + f"{pref}📁 {sub.name}/")
                res += lines(sub, lvl + 1)
            for i, f in enumerate(files):
                pref = "└── " if i == len(files) - 1 else "├── "
                try:
                    icon = "📄" if is_text_file(f) else "🔒"
                    res.append("    " * lvl + f"{pref}{icon} {f.name} ({human(f.stat().st_size)})")
                except Exception:
                    res.append("    " * lvl + f"{pref}📄 {f.name}")
        except PermissionError:
            res.append("    " * lvl + "❌ Zugriff verweigert")
        return res

    out.write("```\n")
    out.write(f"📁 {root.name}/\n")
    for ln in lines(root):
        out.write(ln + "\n")
    out.write("```\n\n")


def parse_manifest(md: Path) -> dict[str, tuple[str, int]]:
    m: dict[str, tuple[str, int]] = {}
    if not md or not md.exists():
        return m
    try:
        inside = False
        with md.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if s.startswith("## 🧾 Manifest"):
                    inside = True
                    continue
                if inside:
                    if not s.startswith("- "):
                        if s.startswith("## "):
                            break
                        continue
                    row = s[2:]
                    parts = [p.strip() for p in row.split("|")]
                    rel = parts[0] if parts else ""
                    md5 = ""
                    size = 0
                    for p in parts[1:]:
                        if p.startswith("md5="):
                            md5 = p[4:].strip()
                        elif p.startswith("size="):
                            try:
                                size = int(p[5:].strip())
                            except Exception:
                                size = 0
                    if rel:
                        m[rel] = (md5, size)
    except Exception:
        pass
    return m


def build_diff(current: list[tuple[Path, Path, int, str]], merge_dir: Path, merge_prefix: str):
    # merge_prefix als Basisname: <prefix>_DDMM*.md
    merges = sorted(merge_dir.glob(f"{merge_prefix}_*.md"))
    if not merges:
        return [], 0, 0, 0
    last = merges[-1]
    old = parse_manifest(last)

    cur_paths = {str(rel) for _, rel, _, _ in current}
    old_paths = set(old.keys())

    added = sorted(cur_paths - old_paths)
    removed = sorted(old_paths - cur_paths)
    changed: list[str] = []
    for _, rel, _, h in current:
        r = str(rel)
        old_h = old.get(r, ("", 0))[0]
        if r in old_paths and old_h and h and old_h != h:
            changed.append(r)
    changed.sort()
    diffs = [("+", p) for p in added] + [("-", p) for p in removed] + [("~", p) for p in changed]
    return diffs, len(added), len(removed), len(changed)


def keep_last_n(merge_dir: Path, keep: int, keep_new: Path | None = None, merge_prefix: str = DEF_MERGE_PREFIX):
    merges = sorted(merge_dir.glob(f"{merge_prefix}_*.md"))
    if keep_new and keep_new not in merges:
        merges.append(keep_new)
        merges.sort()
    if keep <= 0 or len(merges) <= keep:
        return
    for old in merges[:-keep]:
        try:
            old.unlink()
        except Exception:
            pass

# ===== Merge ================================================================

def do_merge(
    source: Path,
    out_file: Path,
    *,
    encoding: str,
    keep: int,
    merge_dir: Path,
    merge_prefix: str,
    max_tree_depth: int | None,
    search_info: str | None,
):
    included: list[tuple[Path, Path, int, str]] = []
    manifest_rows: list[tuple[Path, int, str, str, str]] = []
    skipped: list[str] = []
    total = 0

    for dirpath, _, files in os.walk(source):
        d = Path(dirpath)
        for fn in files:
            p = d / fn
            rel = p.relative_to(source)

            if not is_text_file(p):
                skipped.append(f"{rel} (binär/ignoriert)")
                continue

            try:
                sz = p.stat().st_size
            except Exception as e:
                skipped.append(f"{rel} (stat error: {e})")
                continue
            try:
                h = file_md5(p)
            except Exception:
                h = ""

            total += sz
            included.append((p, rel, sz, h))

            ext = p.suffix.lower()
            cat = classify_category(rel, ext)
            manifest_rows.append((rel, sz, h, cat, ext))

    included.sort(key=lambda t: str(t[1]).lower())
    manifest_rows.sort(key=lambda t: str(t[0]).lower())

    out_file.parent.mkdir(parents=True, exist_ok=True)

    # base_name für Diff-Logik (ohne evtl. abschließenden Unterstrich)
    base_prefix = merge_prefix.rstrip("_")

    diffs, add_c, del_c, chg_c = build_diff(included, out_file.parent, base_prefix)
    ext_counts, ext_sizes = summarize_ext(manifest_rows)
    cat_stats = summarize_cat(manifest_rows)

    with out_file.open("w", encoding=encoding) as out:
        out.write("# WGX-Merge\n\n")
        out.write(f"**Zeitpunkt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"**Quelle:** `{source}`\n")
        if search_info:
            out.write(f"**Quelle ermittelt:** {search_info}\n")
        out.write(f"**Dateien (inkludiert):** {len(included)}\n")
        out.write(f"**Gesamtgröße:** {human(total)}\n")
        if diffs:
            out.write(f"**Änderungen seit letztem Merge:** +{add_c} / -{del_c} / ~{chg_c}\n")
        out.write("\n")

        # KI-Hinweisblock
        out.write("> Hinweis für KIs:\n")
        out.write("> - Dies ist ein Schnappschuss des Dateisystems, keine vollständige Git-Historie.\n")
        out.write("> - Die Baumstruktur findest du unter `## 📁 Struktur`.\n")
        out.write("> - Alle aufgenommenen Dateien stehen im `## 🧾 Manifest`.\n")
        out.write("> - Dateiinhalte stehen unter `## 📄 Dateiinhalte`.\n")
        out.write("> - `.env` und ähnliche Dateien können bewusst fehlen (Sicherheitsfilter).\n\n")

        # Plan / Übersicht
        out.write("## 🧮 Plan\n\n")
        out.write(f"- Textdateien im Merge: **{len(included)}**\n")
        out.write(f"- Gesamtgröße der Quellen: **{human(total)}**\n")

        if cat_stats:
            out.write("\n**Dateien nach Kategorien:**\n\n")
            out.write("| Kategorie | Dateien | Gesamtgröße |\n")
            out.write("| --- | ---: | ---: |\n")
            for cat in sorted(cat_stats.keys()):
                cnt, sz = cat_stats[cat]
                out.write(f"| `{cat}` | {cnt} | {human(sz)} |\n")
            out.write("\n")

        if ext_counts:
            out.write("**Statistik nach Dateiendungen:**\n\n")
            out.write("| Ext | Dateien | Gesamtgröße |\n")
            out.write("| --- | ---: | ---: |\n")
            for ext in sorted(ext_counts.keys()):
                out.write(f"| `{ext}` | {ext_counts[ext]} | {human(ext_sizes[ext])} |\n")
            out.write("\n")

        out.write("Hinweis: Obwohl `.env`-ähnliche Dateien gefiltert werden, können sensible Daten ")
        out.write("in anderen Dateien (z. B. JSON/YAML) vorkommen. Nutze den Merge nicht als public Dump.\n\n")

        out.write("## 📁 Struktur\n\n")
        write_tree(out, source, max_tree_depth)

        if diffs:
            out.write("## 📊 Änderungen seit letztem Merge\n\n")
            for sym, pth in diffs:
                out.write(f"{sym} {pth}\n")
            out.write("\n")

        if skipped:
            out.write("## ⏭️ Übersprungen\n\n")
            for s in skipped:
                out.write(f"- {s}\n")
            out.write("\n")

        out.write("## 🧾 Manifest\n\n")
        for rel, sz, h, cat, ext in manifest_rows:
            out.write(f"- {rel} | md5={h} | size={sz} | cat={cat}\n")
        out.write("\n")

        out.write("## 📄 Dateiinhalte\n\n")
        for p, rel, sz, h in included:
            out.write(f"### 📄 {rel}\n\n**Größe:** {human(sz)}\n\n```{lang_for(p)}\n")
            try:
                txt = p.read_text(encoding=encoding, errors="replace")
            except Exception as e:
                txt = f"<<Lesefehler: {e}>>"
            out.write(txt)
            if not txt.endswith("\n"):
                out.write("\n")
            out.write("```\n\n")

    # keep_last_n nutzt denselben Basis-Prefix (wgx)
    keep_last_n(out_file.parent, keep=keep, keep_new=out_file, merge_prefix=base_prefix)
    print(f"✅ Merge geschrieben: {out_file} ({human(out_file.stat().st_size)})")

# ===== CLI ==================================================================

def build_parser():
    p = argparse.ArgumentParser(description="wgx-merger – genau ein Quellordner", add_help=False)
    p.add_argument("--source-dir", dest="src_flag")
    p.add_argument("--keep", type=int, dest="keep")
    p.add_argument("--encoding", dest="encoding")
    p.add_argument("--max-depth", type=int, dest="max_tree_depth")
    p.add_argument("--search-depth", type=int, dest="search_depth")
    p.add_argument("--merge-dirname", dest="merge_dirname")
    p.add_argument("--merge-prefix", dest="merge_prefix")  # Basisname für Dateinamen (Default: wgx)
    p.add_argument("-h", "--help", action="store_true", dest="help")
    p.add_argument("rest", nargs="*")
    return p


def print_help():
    print(__doc__.strip())


def extract_source_path(argv: list[str], *, aliases: dict[str, str], search_depth: int) -> tuple[Path | None, str | None]:
    """
    Akzeptiert:
      - --source-dir <PATH|BASENAME|file://>
      - <PATH|BASENAME|file://>
      - Datei → Elternordner
      - Env: WGX_SOURCE
      - Fallback: Nur-Basename unter COMMON_BASES
    Rückgabe: (Pfad, InfoStringFürReport)
    """
    # Env
    env_src = os.environ.get("WGX_SOURCE", "").strip()
    if env_src:
        p = Path(_deurl(env_src).strip('"'))
        if not safe_is_dir(p) and p.exists():
            p = p.parent
        if safe_is_dir(p):
            return p, "WGX_SOURCE (ENV)"

    # Tokens
    tokens: list[str] = []
    if "--source-dir" in argv:
        idx = argv.index("--source-dir")
        if idx + 1 < len(argv):
            tokens.append(argv[idx + 1])
    tokens += [t for t in argv if t != "--source-dir"]

    # Direktpfad
    for tok in tokens:
        cand = _deurl((tok or "").strip('"'))
        if not cand:
            continue
        if os.sep not in cand and not cand.lower().startswith("file://"):
            continue
        p = Path(cand)
        if p.exists():
            if p.is_file():
                p = p.parent
            if safe_is_dir(p):
                return p, "direktes Argument"

    # Basename/Alias
    for tok in tokens:
        cand = _deurl((tok or "").strip('"'))
        if not cand:
            continue
        if os.sep in cand or cand.lower().startswith("file://"):
            continue
        base = cand
        hit, others = find_dir_by_basename(base, aliases, search_depth=search_depth)
        if hit:
            info = f"Basename-Fallback ('{base}')"
            if others:
                others_s = " | ".join(str(p) for p in others[:5])
                print(f"__WGX_MERGER_INFO__: Mehrere Kandidaten gefunden, nehme kürzesten: {hit} | weitere: {others_s}")
            return hit, info
    return None, None


def _running_in_shortcuts() -> bool:
    return os.environ.get("WGX_SHORTCUTS", "1") == "1"


def main(argv: list[str]) -> int:
    cfg, cfg_path = load_config()
    args = build_parser().parse_args(argv)
    if args.help:
        print_help()
        return 0

    keep = args.keep if args.keep is not None else cfg_get_int(cfg, "general", "keep", DEF_KEEP)
    merge_dirname = args.merge_dirname or cfg_get_str(cfg, "general", "merge_dirname", DEF_MERGE_DIRNAME)
    merge_prefix = args.merge_prefix or cfg_get_str(cfg, "general", "merge_prefix", DEF_MERGE_PREFIX)
    encoding = args.encoding or cfg_get_str(cfg, "general", "encoding", DEF_ENCODING)
    search_depth = args.search_depth if args.search_depth is not None else cfg_get_int(cfg, "general", "max_search_depth", DEF_SRCH_DEPTH)
    max_tree_depth = args.max_tree_depth if args.max_tree_depth is not None else None

    aliases: dict[str, str] = {}
    if cfg.has_section("aliases"):
        for k, v in cfg.items("aliases"):
            aliases[k] = v

    src, src_info = extract_source_path(
        [args.src_flag] + args.rest if args.src_flag else args.rest,
        aliases=aliases,
        search_depth=search_depth,
    )
    if not src:
        print("❌ Quelle fehlt/unerkannt. Übergib Pfad/URL/Basename oder setze WGX_SOURCE. (-h für Hilfe)")
        return 2
    if not safe_is_dir(src):
        print(f"❌ Quelle nicht gefunden oder kein Ordner: {src}")
        return 1

    script_root = Path(__file__).resolve().parent
    merge_dir = ensure_dir(script_root / merge_dirname)

    # Dateiname: <merge_prefix>_DDMM(.md) + Kollision-Handling
    base_name = merge_prefix.rstrip("_")
    out_file = make_output_filename(merge_dir, base_name=base_name)

    do_merge(
        src,
        out_file,
        encoding=encoding,
        keep=keep,
        merge_dir=merge_dir,
        merge_prefix=merge_prefix,
        max_tree_depth=max_tree_depth,
        search_info=src_info,
    )
    return 0


def _safe_main():
    try:
        rc = main(sys.argv[1:])
    except SystemExit as e:
        rc = int(getattr(e, "code", 1) or 0)
    except Exception as e:
        print(f"__WGX_MERGER_ERR__: {e}")
        rc = 1
    if _running_in_shortcuts():
        if rc != 0:
            print(f"__WGX_MERGER_WARN__: Exit {rc}")
        print("__WGX_MERGER_OK__")
    else:
        sys.exit(rc)


if __name__ == "__main__":
    _safe_main()

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-wc-merger-merge_core-py"></a>
### `merger/wc-merger/merge_core.py`
- Category: source
- Tags: -
- Size: 75.18 KB
- Included: full
- MD5: b45490c25ee18e61edcfe6ae40ff9ea5

```python
# -*- coding: utf-8 -*-

"""
merge_core – Core functions for wc-merger (v2.3 Standard).
Implements AI-friendly formatting, tagging, and strict Pflichtenheft structure.
"""

import os
import sys
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Iterator, NamedTuple
from dataclasses import dataclass, asdict

try:
    import yaml
except ImportError:
    pass

# --- Configuration & Heuristics ---

SPEC_VERSION = "2.3"
MERGES_DIR_NAME = "merges"

# Formale Contract-Deklaration für alle wc-merger-Reports.
# Name/Version können von nachgelagerten Tools verwendet werden,
# um das Format eindeutig zu erkennen.
MERGE_CONTRACT_NAME = "wc-merge-report"
MERGE_CONTRACT_VERSION = SPEC_VERSION

# Ab v2.3+: 0 = "kein Limit pro Datei".
# max_file_bytes wirkt nur noch als optionales Soft-Limit / Hint,
# nicht mehr als harte Abschneide-Grenze. Große Dateien werden
# vollständig gelesen und nur über die Split-Logik in Parts verteilt.
DEFAULT_MAX_BYTES = 0

# Debug-Config (kann später bei Bedarf erweitert werden)
ALLOWED_CATEGORIES = {"source", "test", "doc", "config", "contract", "other"}
ALLOWED_TAGS = {
    "ai-context",
    "runbook",
    "lockfile",
    "script",
    "ci",
    "adr",
    "feed",
    "wgx-profile",
}

# Delta Report configuration
MAX_DELTA_FILES = 10  # Maximum number of files to show in each delta section

# Directories to ignore
SKIP_DIRS = {
    ".git",
    ".idea",
    "node_modules",
    ".svelte-kit",
    ".next",
    "dist",
    "build",
    "target",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
    ".mypy_cache",
    "coverage",
}

# Top-level roots to skip in auto-discovery
SKIP_ROOTS = {
    MERGES_DIR_NAME,
    "merge",
    "output",
    "out",
}

# Individual files to ignore
SKIP_FILES = {
    ".DS_Store",
    "thumbs.db",
}

# Extensions considered text (broadened)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".rst", ".py", ".rs", ".ts", ".tsx", ".js", ".jsx",
    ".json", ".jsonl", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".sh", ".bash", ".zsh", ".fish", ".dockerfile", "dockerfile",
    ".svelte", ".css", ".scss", ".html", ".htm", ".xml", ".csv", ".log",
    ".lock", ".bats", ".properties", ".gradle", ".groovy", ".kt", ".kts",
    ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rb", ".php", ".pl",
    ".lua", ".sql", ".bat", ".cmd", ".ps1", ".make", "makefile", "justfile",
    ".tf", ".hcl", ".gitignore", ".gitattributes", ".editorconfig", ".cs",
    ".swift", ".adoc", ".ai-context"
}


# --- Debug-Kollektor -------------------------------------------------------

class DebugItem(NamedTuple):
    level: str   # "info", "warn", "error"
    code: str    # z. B. "tag-unknown"
    context: str # kurzer Pfad oder Repo-Name
    message: str # Menschentext


@dataclass
class ExtrasConfig:
    health: bool = False
    organism_index: bool = False
    fleet_panorama: bool = False
    augment_sidecar: bool = False
    delta_reports: bool = False

    @classmethod
    def none(cls):
        return cls()


class DebugCollector:
    """Sammelt Debug-Infos für optionale Report-Sektionen."""

    def __init__(self) -> None:
        self._items: List[DebugItem] = []

    @property
    def items(self) -> List[DebugItem]:
        return list(self._items)

    def info(self, code: str, context: str, msg: str) -> None:
        self._items.append(DebugItem("info", code, context, msg))

    def warn(self, code: str, context: str, msg: str) -> None:
        self._items.append(DebugItem("warn", code, context, msg))

    def error(self, code: str, context: str, msg: str) -> None:
        self._items.append(DebugItem("error", code, context, msg))

    def has_items(self) -> bool:
        return bool(self._items)

    def render_markdown(self) -> str:
        """Erzeugt eine optionale ## Debug-Sektion als Markdown-Tabelle."""
        if not self._items:
            return ""
        lines: List[str] = []
        lines.append("<!-- @debug:start -->")
        lines.append("## Debug")
        lines.append("")
        lines.append("| Level | Code | Kontext | Hinweis |")
        lines.append("|-------|------|---------|---------|")
        for it in self._items:
            lines.append(
                f"| {it.level} | `{it.code}` | `{it.context}` | {it.message} |"
            )
        lines.append("")
        lines.append("<!-- @debug:end -->")
        lines.append("")
        return "\n".join(lines)


@dataclass
class RepoHealth:
    """Health status for a single repository."""
    repo_name: str
    status: str  # "ok", "warn", "critical"
    total_files: int
    category_counts: Dict[str, int]
    has_readme: bool
    has_wgx_profile: bool
    has_ci_workflows: bool
    has_contracts: bool
    has_ai_context: bool
    unknown_categories: List[str]
    unknown_tags: List[str]
    warnings: List[str]
    recommendations: List[str]


class HealthCollector:
    """Collects health checks for repositories (Stage 1: Repo Doctor)."""

    def __init__(self) -> None:
        self._repo_health: Dict[str, RepoHealth] = {}

    def analyze_repo(self, root_label: str, files: List["FileInfo"]) -> RepoHealth:
        """Analyze health of a single repository."""
        # Count files per category
        category_counts: Dict[str, int] = {}
        for fi in files:
            cat = fi.category or "other"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Check for key files
        has_readme = any(f.rel_path.name.lower() == "readme.md" for f in files)
        has_wgx_profile = any(
            ".wgx" in f.rel_path.parts and str(f.rel_path).endswith("profile.yml")
            for f in files
        )
        has_ci_workflows = any("ci" in (f.tags or []) for f in files)
        has_contracts = any(f.category == "contract" for f in files)
        # Enhanced AI context detection: check tags and file paths (cached to avoid repeated conversions)
        has_ai_context = False
        for f in files:
            if "ai-context" in (f.tags or []):
                has_ai_context = True
                break
            path_lower = str(f.rel_path).lower()
            if "ai-context" in path_lower or path_lower.endswith(".ai-context.yml") or "ai-context" in f.rel_path.parts:
                has_ai_context = True
                break

        # Check for unknown categories/tags
        unknown_categories = []
        unknown_tags = []
        for fi in files:
            cat = fi.category or "other"
            if cat not in ALLOWED_CATEGORIES:
                if cat not in unknown_categories:
                    unknown_categories.append(cat)
            for tag in fi.tags or []:
                if tag not in ALLOWED_TAGS:
                    if tag not in unknown_tags:
                        unknown_tags.append(tag)

        # Generate warnings and recommendations
        warnings = []
        recommendations = []

        if not has_readme:
            warnings.append("No README.md found")
            recommendations.append("Add README.md for better AI/human navigation")

        if not has_wgx_profile:
            warnings.append("No .wgx/profile.yml found")
            recommendations.append("Create .wgx/profile.yml for Fleet conformance")

        if not has_ci_workflows:
            warnings.append("No CI workflows found")
            recommendations.append("Add .github/workflows for CI/CD")

        if not has_contracts:
            warnings.append("No contracts found")
            recommendations.append("Consider adding contract schemas")

        if not has_ai_context:
            warnings.append("No AI context files found")
            recommendations.append("Add .ai-context.yml files for better AI understanding")

        if unknown_categories:
            warnings.append(f"Unknown categories: {', '.join(unknown_categories)}")

        if unknown_tags:
            warnings.append(f"Unknown tags: {', '.join(unknown_tags)}")

        # Determine overall status
        if len(warnings) >= 4:
            status = "critical"
        elif len(warnings) >= 2:
            status = "warn"
        else:
            status = "ok"

        health = RepoHealth(
            repo_name=root_label,
            status=status,
            total_files=len(files),
            category_counts=category_counts,
            has_readme=has_readme,
            has_wgx_profile=has_wgx_profile,
            has_ci_workflows=has_ci_workflows,
            has_contracts=has_contracts,
            has_ai_context=has_ai_context,
            unknown_categories=unknown_categories,
            unknown_tags=unknown_tags,
            warnings=warnings,
            recommendations=recommendations,
        )

        self._repo_health[root_label] = health
        return health

    def get_all_health(self) -> List[RepoHealth]:
        """Get all repo health reports."""
        return list(self._repo_health.values())

    def render_markdown(self) -> str:
        """Render health report as markdown."""
        if not self._repo_health:
            return ""

        lines: List[str] = []
        lines.append("<!-- @health:start -->")
        lines.append("## 🩺 Repo Health")
        lines.append("")

        for health in sorted(self._repo_health.values(), key=lambda h: h.repo_name):
            # Status emoji
            status_emoji = {
                "ok": "✅",
                "warn": "⚠️",
                "critical": "🔴",
            }.get(health.status, "❓")

            lines.append(f"### {status_emoji} `{health.repo_name}` – {health.status.upper()}")
            lines.append("")
            lines.append(f"- **Total Files:** {health.total_files}")
            
            # Category breakdown
            if health.category_counts:
                cat_parts = [f"{cat}={count}" for cat, count in sorted(health.category_counts.items())]
                lines.append(f"- **Categories:** {', '.join(cat_parts)}")

            # Key indicators
            indicators = []
            indicators.append(f"README: {'yes' if health.has_readme else 'no'}")
            indicators.append(f"WGX Profile: {'yes' if health.has_wgx_profile else 'no'}")
            indicators.append(f"CI: {'yes' if health.has_ci_workflows else 'no'}")
            indicators.append(f"Contracts: {'yes' if health.has_contracts else 'no'}")
            indicators.append(f"AI Context: {'yes' if health.has_ai_context else 'no'}")
            lines.append(f"- **Indicators:** {', '.join(indicators)}")

            # Warnings
            if health.warnings:
                lines.append("- **Warnings:**")
                for warning in health.warnings:
                    lines.append(f"  - {warning}")

            # Recommendations
            if health.recommendations:
                lines.append("- **Recommendations:**")
                for rec in health.recommendations:
                    lines.append(f"  - {rec}")

            lines.append("")

        lines.append("<!-- @health:end -->")
        lines.append("")
        return "\n".join(lines)


def _build_extras_meta(extras: "ExtrasConfig", num_repos: int) -> Dict[str, bool]:
    """
    Hilfsfunktion: baut den extras-Block für den @meta-Contract.
    Nur aktivierte Flags werden gesetzt, damit das Schema schlank bleibt.
    
    Args:
        extras: ExtrasConfig mit den gewünschten Extras
        num_repos: Anzahl der Repos im Merge (für Fleet Panorama - muss explizit übergeben werden)
    """
    extras_meta: Dict[str, bool] = {}
    if extras.health:
        extras_meta["health"] = True
    if extras.organism_index:
        extras_meta["organism_index"] = True
    # Fleet Panorama nur bei Multi-Repo-Merges
    if extras.fleet_panorama and num_repos > 1:
        extras_meta["fleet_panorama"] = True
    if extras.augment_sidecar:
        extras_meta["augment_sidecar"] = True
    if extras.delta_reports:
        extras_meta["delta_reports"] = True
    return extras_meta


def _build_augment_meta(sources: List[Path]) -> Optional[Dict[str, Any]]:
    """
    Nutzt dieselbe Logik wie der Augment-Block, um das Sidecar im Meta zu verlinken.
    """
    sidecar = _find_augment_file_for_sources(sources)
    return {"sidecar": sidecar.name} if sidecar else None


def _find_augment_file_for_sources(sources: List[Path]) -> Optional[Path]:
    """
    Locate an augment sidecar YAML file for the given sources.
    Convention: {repo_name}_augment.yml either in the repo root or its parent.
    """
    for source in sources:
        try:
            # Try in the repo directory itself
            candidate = source / f"{source.name}_augment.yml"
            if candidate.exists():
                return candidate

            # Try in parent directory
            candidate_parent = source.parent / f"{source.name}_augment.yml"
            if candidate_parent.exists():
                return candidate_parent
        except (OSError, PermissionError):
            # If we cannot access this source, skip it
            continue
    return None


def _render_augment_block(sources: List[Path]) -> str:
    """
    Render the Augment Intelligence block based on an augment sidecar, if present.
    The expected structure matches tools_augment.yml (augment.hotspots, suggestions, risks, dependencies, priorities, context).
    """
    augment_path = _find_augment_file_for_sources(sources)
    if not augment_path:
        return ""

    # yaml is optional; if not available, render a basic block
    try:
        yaml  # type: ignore[name-defined]
    except NameError:
        lines = []
        lines.append("<!-- @augment:start -->")
        lines.append("## 🧩 Augment Intelligence")
        lines.append("")
        lines.append(f"**Sidecar:** `{augment_path.name}`")
        lines.append("")
        lines.append("_Hinweis: PyYAML nicht verfügbar – Details aus dem Sidecar können nicht automatisch geparst werden._")
        lines.append("")
        lines.append("<!-- @augment:end -->")
        lines.append("")
        return "\n".join(lines)

    try:
        raw = augment_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""

    try:
        data = yaml.safe_load(raw)  # type: ignore[name-defined]
    except Exception:
        # If the augment file is malformed, fail silently and do not break the merge
        return ""

    if not isinstance(data, dict):
        return ""

    augment = data.get("augment") or {}
    if not isinstance(augment, dict):
        return ""

    lines: List[str] = []
    lines.append("<!-- @augment:start -->")
    lines.append("## 🧩 Augment Intelligence")
    lines.append("")
    lines.append(f"**Sidecar:** `{augment_path.name}`")
    lines.append("")

    hotspots = augment.get("hotspots") or []
    if isinstance(hotspots, list) and hotspots:
        lines.append("### Hotspots")
        for hs in hotspots:
            if not isinstance(hs, dict):
                continue
            path = hs.get("path") or "?"
            reason = hs.get("reason") or ""
            severity = hs.get("severity") or ""
            line_range = hs.get("lines")
            details = []
            if severity:
                details.append(f"Severity: {severity}")
            if line_range:
                details.append(f"Lines: {line_range}")
            suffix = f" ({'; '.join(details)})" if details else ""
            if reason:
                lines.append(f"- `{path}` – {reason}{suffix}")
            else:
                lines.append(f"- `{path}`{suffix}")
        lines.append("")

    suggestions = augment.get("suggestions") or []
    if isinstance(suggestions, list) and suggestions:
        lines.append("### Suggestions")
        for s in suggestions:
            if isinstance(s, str):
                lines.append(f"- {s}")
        lines.append("")

    risks = augment.get("risks") or []
    if isinstance(risks, list) and risks:
        lines.append("### Risks")
        for r in risks:
            if isinstance(r, str):
                lines.append(f"- {r}")
        lines.append("")

    dependencies = augment.get("dependencies") or []
    if isinstance(dependencies, list) and dependencies:
        lines.append("### Dependencies")
        for dep in dependencies:
            if not isinstance(dep, dict):
                continue
            name = dep.get("name") or "unknown"
            required = dep.get("required")
            purpose = dep.get("purpose") or ""
            req_txt = ""
            if isinstance(required, bool):
                req_txt = "required" if required else "optional"
            parts = [name]
            if req_txt:
                parts.append(f"({req_txt})")
            if purpose:
                parts.append(f"– {purpose}")
            lines.append(f"- {' '.join(parts)}")
        lines.append("")

    priorities = augment.get("priorities") or []
    if isinstance(priorities, list) and priorities:
        lines.append("### Priorities")
        for pr in priorities:
            if not isinstance(pr, dict):
                continue
            prio = pr.get("priority")
            task = pr.get("task") or ""
            status = pr.get("status") or ""
            head = f"P{prio}: {task}" if prio is not None else task
            if status:
                lines.append(f"- {head} ({status})")
            else:
                lines.append(f"- {head}")
        lines.append("")

    context = augment.get("context") or {}
    if isinstance(context, dict) and context:
        lines.append("### Context")
        for key, value in context.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    lines.append("<!-- @augment:end -->")
    lines.append("")
    return "\n".join(lines)


def run_debug_checks(file_infos: List["FileInfo"], debug: DebugCollector) -> None:
    """
    Leichte, rein lesende Debug-Checks auf Basis der FileInfos.
    Verändert keine Merge-Logik, liefert nur Hinweise.
    """
    # 1. Unbekannte Kategorien / Tags
    for fi in file_infos:
        ctx = f"{fi.root_label}/{fi.rel_path.as_posix()}"
        cat = fi.category or "other"
        if cat not in ALLOWED_CATEGORIES:
            debug.warn(
                "category-unknown",
                ctx,
                f"Unbekannte Kategorie '{cat}' – erwartet sind {sorted(ALLOWED_CATEGORIES)}.",
            )
        for tag in getattr(fi, "tags", []) or []:
            if tag not in ALLOWED_TAGS:
                debug.warn(
                    "tag-unknown",
                    ctx,
                    f"Tag '{tag}' ist nicht im v2.3-Schema registriert.",
                )

    # 2. Fleet-/Heimgewebe-Checks pro Repo
    per_root: Dict[str, List["FileInfo"]] = {}
    for fi in file_infos:
        per_root.setdefault(fi.root_label, []).append(fi)

    for root, fis in per_root.items():
        # README-Check
        if not any(f.rel_path.name.lower() == "readme.md" for f in fis):
            debug.info(
                "repo-no-readme",
                root,
                "README.md fehlt – Repo ist für KIs schwerer einzuordnen.",
            )
        # WGX-Profil-Check
        if not any(
            ".wgx" in f.rel_path.parts and str(f.rel_path).endswith("profile.yml")
            for f in fis
        ):
            debug.info(
                "repo-no-wgx-profile",
                root,
                "`.wgx/profile.yml` nicht gefunden – Repo ist nicht vollständig Fleet-konform.",
            )


# Directories considered "noise" (build artifacts etc.)
NOISY_DIRECTORIES = ("node_modules/", "dist/", "build/", "target/")

# Standard lockfile names
LOCKFILE_NAMES = {
    "Cargo.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
}

# Files typically considered configuration
CONFIG_FILENAMES = {
    "pyproject.toml", "package.json", "package-lock.json", "pnpm-lock.yaml",
    "Cargo.toml", "Cargo.lock", "requirements.txt", "Pipfile", "Pipfile.lock",
    "poetry.lock", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "Justfile", "Makefile", "toolchain.versions.yml", ".editorconfig",
    ".markdownlint.jsonc", ".markdownlint.yaml", ".yamllint", ".yamllint.yml",
    ".lychee.toml", ".vale.ini", ".pre-commit-config.yaml", ".gitignore",
    ".gitmodules", "tsconfig.json", "babel.config.js", "webpack.config.js",
    "rollup.config.js", "vite.config.js", "vite.config.ts", ".ai-context.yml"
}

# Large generated files or lockfiles that should be summarized in 'dev' profile
SUMMARIZE_FILES = {
    "package-lock.json", "pnpm-lock.yaml", "Cargo.lock", "yarn.lock", "Pipfile.lock", "poetry.lock"
}

DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc"}
SOURCE_EXTENSIONS = {
    ".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".svelte", ".c", ".cpp",
    ".h", ".hpp", ".go", ".java", ".cs", ".rb", ".php", ".swift", ".kt",
    ".sh", ".bash", ".pl", ".lua"
}

LANG_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "html": "html", "css": "css",
    "scss": "scss", "sass": "sass", "json": "json", "xml": "xml", "yaml": "yaml", "yml": "yaml",
    "md": "markdown", "sh": "bash", "bat": "batch", "sql": "sql", "php": "php", "cpp": "cpp",
    "c": "c", "java": "java", "cs": "csharp", "go": "go", "rs": "rust", "rb": "ruby",
    "swift": "swift", "kt": "kotlin", "svelte": "svelte", "toml": "toml", "ini": "ini",
    "dockerfile": "dockerfile", "tf": "hcl", "hcl": "hcl", "bats": "bash", "pl": "perl", "lua": "lua",
    "ai-context": "yaml"
}

HARDCODED_HUB_PATH = (
    "/private/var/mobile/Containers/Data/Application/"
    "B60D0157-973D-489A-AA59-464C3BF6D240/Documents/wc-hub"
)

# Semantische Use-Case-Beschreibung pro Profil.
# Wichtig: das ersetzt NICHT den Repo-Zweck (Declared Purpose),
# sondern ergänzt ihn um die Rolle des aktuellen Merges.
PROFILE_USECASE = {
    "overview": "Tools – Index",
    "summary": "Tools – Doku/Kontext",
    "dev": "Tools – Code/Review Snapshot",
    "max": "Tools – Vollsnapshot",
}

# Mandatory Repository Order for Multi-Repo Merges (v2.1 Spec)
REPO_ORDER = [
    "metarepo",
    "wgx",
    "hausKI",
    "hausKI-audio",
    "heimgeist",
    "chronik",
    "aussensensor",
    "semantAH",
    "leitstand",
    "heimlern",
    "tools",
    "weltgewebe",
    "vault-gewebe",
]

class FileInfo(object):
    """Container for file metadata."""
    def __init__(self, root_label, abs_path, rel_path, size, is_text, md5, category, tags, ext, skipped=False, reason=None, content=None):
        self.root_label = root_label
        self.abs_path = abs_path
        self.rel_path = rel_path
        self.size = size
        self.is_text = is_text
        self.md5 = md5
        self.category = category
        self.tags = tags
        self.ext = ext
        self.skipped = skipped
        self.reason = reason
        self.content = content
        self.anchor = "" # Will be set during report generation
        self.roles = [] # Will be computed during report generation


# --- Utilities ---

def compute_file_roles(fi: "FileInfo") -> List[str]:
    """
    Compute semantic roles for a file based on category, tags, and path.
    Roles help AI agents understand the purpose/function of files.
    
    Possible roles: contract, ai-context, ci, wgx-profile, policy, tool, execution, governance, doc
    """
    roles = []
    
    # Role from category
    if fi.category == "contract":
        roles.append("contract")
    
    # Roles from tags
    if fi.tags:
        if "ai-context" in fi.tags:
            roles.append("ai-context")
        if "ci" in fi.tags:
            roles.append("ci")
        if "wgx-profile" in fi.tags:
            roles.append("wgx-profile")
        if "adr" in fi.tags:
            roles.append("policy")
        if "script" in fi.tags:
            roles.append("tool")
        if "runbook" in fi.tags:
            roles.append("execution")
    
    # Role from path patterns (cache normalized path)
    path_str = fi.rel_path.as_posix().lower()
    
    # Contracts directory
    if "contracts/" in path_str and fi.ext in {".json", ".yaml", ".yml"}:
        if "contract" not in roles:
            roles.append("contract")
    
    # CI/CD pipelines
    if ".github/workflows/" in path_str:
        if "ci" not in roles:
            roles.append("ci")
    
    # WGX profiles
    if ".wgx/" in path_str and "profile" in path_str:
        if "wgx-profile" not in roles:
            roles.append("wgx-profile")
    
    # AI context files
    if "ai-context" in path_str or path_str.endswith(".ai-context.yml"):
        if "ai-context" not in roles:
            roles.append("ai-context")
    
    # Governance files (metarepo, policies, ADRs) - check role first to avoid expensive pattern matching
    if "policy" not in roles:
        if any(p in path_str for p in ["adr/", "decision/", "policy/", "governance/"]):
            roles.append("policy")
    
    # Documentation role
    if fi.category == "doc" and "doc" not in roles:
        roles.append("doc")
    
    return roles

def is_noise_file(fi: "FileInfo") -> bool:
    """
    Heuristik für 'Noise'-Dateien:
    - offensichtliche Lockfiles / Paketmanager-Artefakte
    - typische Build-/Vendor-Verzeichnisse
    ohne das Manifest-Schema zu verändern – nur das Included-Label wird erweitert.
    """
    try:
        path_str = str(fi.rel_path).replace("\\", "/").lower()
        name = fi.rel_path.name.lower()
    except Exception:
        return False

    noisy_dirs = (
        "node_modules/",
        "dist/",
        "build/",
        "target/",
        "venv/",
        ".venv/",
        "__pycache__/",
    )
    if any(seg in path_str for seg in noisy_dirs):
        return True

    lock_names = {
        "cargo.lock",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "poetry.lock",
        "pipfile.lock",
        "composer.lock",
    }
    if name in lock_names or name.endswith(".lock"):
        return True

    tags_lower = {t.lower() for t in (fi.tags or [])}
    if "lockfile" in tags_lower or "deps" in tags_lower or "vendor" in tags_lower:
        return True

    return False

def detect_hub_dir(script_path: Path, arg_base_dir: Optional[str] = None) -> Path:
    env_base = os.environ.get("WC_MERGER_BASEDIR")
    if env_base:
        p = Path(env_base).expanduser()
        if p.is_dir(): return p

    p = Path(HARDCODED_HUB_PATH)
    try:
        if p.expanduser().is_dir(): return p
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to check hub dir {p}: {e}\n")

    if arg_base_dir:
        p = Path(arg_base_dir).expanduser()
        if p.is_dir(): return p

    return script_path.parent


def get_merges_dir(hub: Path) -> Path:
    merges = hub / MERGES_DIR_NAME
    merges.mkdir(parents=True, exist_ok=True)
    return merges


def human_size(n: float) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0 or unit == "GB":
            return "{0:.2f} {1}".format(size, unit)
        size /= 1024.0
    return "{0:.2f} GB".format(size)


def is_probably_text(path: Path, size: int) -> bool:
    name = path.name.lower()
    base, ext = os.path.splitext(name)
    if ext in TEXT_EXTENSIONS or name in TEXT_EXTENSIONS:
        return True
    if size > 20 * 1024 * 1024:  # 20 MiB
        return False
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
    except OSError:
        return False
    if not chunk:
        return True
    if b"\x00" in chunk:
        return False
    return True


def compute_md5(path: Path, limit_bytes: Optional[int] = None) -> str:
    h = hashlib.md5()
    try:
        with path.open("rb") as f:
            remaining = limit_bytes
            while True:
                if remaining is None:
                    chunk = f.read(65536)
                else:
                    chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                h.update(chunk)
                if remaining is not None:
                    remaining -= len(chunk)
                    if remaining <= 0:
                        break
        return h.hexdigest()
    except OSError:
        return "ERROR"


def lang_for(ext: str) -> str:
    return LANG_MAP.get(ext.lower().lstrip("."), "")


def get_repo_sort_index(repo_name: str) -> int:
    """Returns sort index for repo based on REPO_ORDER."""
    try:
        return REPO_ORDER.index(repo_name)
    except ValueError:
        return 999  # Put undefined repos at the end

def extract_purpose(repo_root: Path) -> str:
    """Safe purpose extraction from README or docs/intro.md. No guessing."""
    candidates = ["README.md", "README", "docs/intro.md"]
    for c in candidates:
        p = repo_root / c
        if p.exists():
            try:
                # Read text safely
                with p.open("r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read().strip()
                    # First paragraph is content until double newline
                    first = txt.split("\n\n")[0].strip()
                    # Markdown-Überschrift (#, ##, …) vorne abschneiden
                    first = first.lstrip("#").strip()
                    return first
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to extract purpose from {p}: {e}\n")
                return ""
    return ""

def get_declared_purpose(files: List[FileInfo]) -> str:
    # Deprecated in favor of extract_purpose for consistency with Spec v2.3 patch D logic
    # But kept as fallback or to support .ai-context which spec patch D didn't mention explicitly
    # but patch D implemented it as:
    # try: purpose = extract_purpose(sources[0]); ...
    return "(none)" # Handled in iter_report_blocks via extract_purpose


def classify_file_v2(rel_path: Path, ext: str) -> Tuple[str, List[str]]:
    """
    Returns (category, tags).
    Strict Pattern Matching based on v2.1 Spec.
    """
    parts = list(rel_path.parts)
    name = rel_path.name.lower()
    tags = []

    # Tag Patterns - Strict match
    # KI-Kontext-Dateien
    if name.endswith(".ai-context.yml"):
        tags.append("ai-context")

    # CI-Workflows
    if ".github" in parts and "workflows" in parts and ext in [".yml", ".yaml"]:
        tags.append("ci")

    # Contracts:
    # Nur als Kategorie, nicht mehr als Tag – Spec sieht kein 'contract'-Tag vor.
    # (Die Zuordnung passiert weiter unten über die Category-Logik.)

    if "docs" in parts and "adr" in parts and ext == ".md":
        tags.append("adr")
    if name.startswith("runbook") and ext == ".md":
        tags.append("runbook")

    # Skripte: Shell und Python unter scripts/ oder bin/ als 'script' markieren
    if (("scripts" in parts) or ("bin" in parts)) and ext in (".sh", ".py"):
        tags.append("script")

    if "export" in parts and ext == ".jsonl":
        tags.append("feed")

    # Lockfiles (package-lock, Cargo.lock, pnpm-lock, etc.)
    if "lock" in name:
        tags.append("lockfile")

    # README: Spec-konform als KI-Kontext markieren, kein eigener 'readme'-Tag
    if name == "readme.md":
        tags.append("ai-context")

    # WGX-Profile
    if ".wgx" in parts and name.startswith("profile"):
        tags.append("wgx-profile")


    # Determine Category - Strict Logic
    # Category ∈ {source, test, doc, config, contract, other}
    category = "other"

    # Order matters: check more specific first
    if name in CONFIG_FILENAMES or "config" in parts or ".github" in parts or ".wgx" in parts or ext in [".toml", ".yaml", ".yml", ".json", ".lock"]:
         # Note: .json could be contract or config, check contract path
         if "contracts" in parts:
             category = "contract"
         else:
             category = "config"
    elif ext in DOC_EXTENSIONS or "docs" in parts:
        category = "doc"
    elif "contracts" in parts: # Fallback if not caught above
        category = "contract"
    elif "tests" in parts or "test" in parts or name.endswith("_test.py") or name.startswith("test_"):
        category = "test"
    elif ext in SOURCE_EXTENSIONS or "src" in parts or "crates" in parts or "scripts" in parts:
        category = "source"

    return category, tags


def _normalize_ext_list(ext_text: str) -> List[str]:
    if not ext_text:
        return []
    parts = [p.strip() for p in ext_text.split(",")]
    cleaned: List[str] = []
    for p in parts:
        if not p:
            continue
        if not p.startswith("."):
            p = "." + p
        cleaned.append(p.lower())
    return cleaned


# --- Repo Scan Logic ---

def scan_repo(repo_root: Path, extensions: Optional[List[str]] = None, path_contains: Optional[str] = None, max_bytes: int = DEFAULT_MAX_BYTES) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    root_label = repo_root.name
    files = []

    ext_filter = set(e.lower() for e in extensions) if extensions else None
    path_filter = path_contains.strip() if path_contains else None

    total_files = 0
    total_bytes = 0
    ext_hist: Dict[str, int] = {}

    for dirpath, dirnames, filenames in os.walk(str(repo_root)):
        # Filter directories
        keep_dirs = []
        for d in dirnames:
            if d in SKIP_DIRS:
                continue
            keep_dirs.append(d)
        dirnames[:] = keep_dirs

        for fn in filenames:
            if fn in SKIP_FILES:
                continue
            if fn.startswith(".env") and fn not in (".env.example", ".env.template", ".env.sample"):
                continue

            abs_path = Path(dirpath) / fn
            try:
                rel_path = abs_path.relative_to(repo_root)
            except ValueError:
                continue

            rel_path_str = rel_path.as_posix()
            if path_filter and path_filter not in rel_path_str:
                continue

            ext = abs_path.suffix.lower()
            if ext_filter is not None and ext not in ext_filter:
                continue

            try:
                st = abs_path.stat()
            except OSError:
                continue

            size = st.st_size
            total_files += 1
            total_bytes += size
            ext_hist[ext] = ext_hist.get(ext, 0) + 1

            is_text = is_probably_text(abs_path, size)
            category, tags = classify_file_v2(rel_path, ext)

            # MD5 calculation:
            # - Textdateien: immer kompletter MD5
            # - Binärdateien: nur, falls ein positives Limit gesetzt ist
            #   und die Datei kleiner/gleich diesem Limit ist.
            md5 = ""
            # 0 oder <0 = "kein Limit" → komplette Textdateien hashen
            limit_bytes: Optional[int] = max_bytes if max_bytes and max_bytes > 0 else None
            if is_text:
                md5 = compute_md5(abs_path, limit_bytes)
            else:
                if limit_bytes is not None and size <= limit_bytes:
                    md5 = compute_md5(abs_path, limit_bytes)

            fi = FileInfo(
                root_label=root_label,
                abs_path=abs_path,
                rel_path=rel_path,
                size=size,
                is_text=is_text,
                md5=md5,
                category=category,
                tags=tags,
                ext=ext
            )
            files.append(fi)

    # Sort files: first by repo order (if multi-repo context handled outside,
    # but here root_label is constant per scan_repo call unless we merge lists later),
    # then by path.
    files.sort(key=lambda fi: str(fi.rel_path).lower())

    return {
        "root": repo_root,
        "name": root_label,
        "files": files,
        "total_files": total_files,
        "total_bytes": total_bytes,
        "ext_hist": ext_hist,
    }

def get_repo_snapshot(repo_root: Path) -> Dict[str, Tuple[int, str, str]]:
    """
    Liefert einen Snapshot des Repos für Diff-Zwecke.

    Rückgabe:
      Dict[rel_path] -> (size, md5, category)

    Wichtig:
      - nutzt scan_repo, d. h. dieselben Ignore-Regeln wie der Merger
      - Category stammt direkt aus classify_file_v2 und ist damit
        kompatibel zum Manifest (source/doc/config/test/contract/ci/other)
    """
    snapshot: Dict[str, Tuple[int, str, str]] = {}
    summary = scan_repo(
        repo_root, extensions=None, path_contains=None, max_bytes=100_000_000
    )  # großes Limit, damit wir verlässliche MD5s haben
    for fi in summary["files"]:
        snapshot[fi.rel_path.as_posix()] = (fi.size, fi.md5, fi.category or "other")
    return snapshot


# --- Reporting Logic V2 ---

def summarize_categories(file_infos: List[FileInfo]) -> Dict[str, List[int]]:
    stats: Dict[str, List[int]] = {}
    for fi in file_infos:
        cat = fi.category or "other"
        if cat not in stats:
            stats[cat] = [0, 0]
        stats[cat][0] += 1
        stats[cat][1] += fi.size
    return stats

def build_tree(file_infos: List[FileInfo]) -> str:
    by_root: Dict[str, List[Path]] = {}

    # Sort roots first
    sorted_files = sorted(file_infos, key=lambda fi: (get_repo_sort_index(fi.root_label), fi.root_label.lower()))

    for fi in sorted_files:
        by_root.setdefault(fi.root_label, []).append(fi.rel_path)

    lines = ["```"]
    # Keys are already sorted by insertion order in py3.7+, which matches our sorted_files loop,
    # but let's be safe and sort keys based on REPO_ORDER.
    sorted_roots = sorted(by_root.keys(), key=lambda r: (get_repo_sort_index(r), r.lower()))

    for root in sorted_roots:
        rels = by_root[root]
        lines.append(f"📁 {root}/")

        tree: Dict[str, Any] = {}
        for r in rels:
            parts = list(r.parts)
            node = tree
            for p in parts:
                if p not in node:
                    node[p] = {}
                node = node[p]

        def walk(node, indent, root_lbl):
            dirs = []
            files = []
            for k, v in node.items():
                if v:
                    dirs.append(k)
                else:
                    files.append(k)
            for d in sorted(dirs):
                lines.append(f"{indent}📁 {d}/")
                walk(node[d], indent + "    ", root_lbl)
            for f in sorted(files):
                # Optional: Hyperlinking in Tree
                # Needs rel path reconstruction which is tricky in this recursive walk without passing it down
                # For v2.3 Spec 6.3: 📄 [filename](#file-…)
                # We need to construct the full relative path to generate the anchor.
                # Since we don't pass the path down easily here, let's skip tree linking for this iteration
                # to keep it robust, or do a simple approximation if needed.
                # Actually, we can use a lookup if we want, but "optional" in spec allows skipping.
                # Let's stick to plain text for now to avoid complexity in build_tree.
                lines.append(f"{indent}📄 {f}")

        walk(tree, "    ", root)
    lines.append("```")
    return "\n".join(lines)

def make_output_filename(merges_dir: Path, repo_names: List[str], mode: str, detail: str, part: Optional[int] = None) -> Path:
    # Zeitstempel ohne Sekunden, damit die Namen ruhiger werden
    ts = datetime.datetime.now().strftime("%y%m%d-%H%M")
    base = "+".join(repo_names) if repo_names else "no-repos"
    if len(base) > 40:
        base = base[:37] + "..."
    base = base.replace(" ", "-").replace("/", "_")

    part_suffix = f"_part{part}" if part else ""
    # Neues Schema:
    #   <repos>_<detail>_<mode>_<YYMMDD-HHMM>[_partX]_merge.md
    # Beispiel:
    #   hausKI+wgx_dev_multi_251205-1457_merge.md
    return merges_dir / f"{base}_{detail}_{mode}_{ts}{part_suffix}_merge.md"

def read_smart_content(fi: FileInfo, max_bytes: int, encoding="utf-8") -> Tuple[str, bool, str]:
    """
    Reads content.
    Returns (content, truncated, truncation_msg).
    Truncation is disabled in v2.3+ per user request (files are split across parts if needed).
    max_bytes is ignored here, effectively reading the full file.
    """
    try:
        with fi.abs_path.open("r", encoding=encoding, errors="replace") as f:
            return f.read(), False, ""
    except OSError as e:
        return f"_Error reading file: {e}_", False, ""

def is_priority_file(fi: FileInfo) -> bool:
    if "ai-context" in fi.tags: return True
    if "runbook" in fi.tags: return True
    if fi.rel_path.name.lower() == "readme.md": return True
    return False

def _render_delta_block(delta_meta: Dict[str, Any]) -> str:
    """
    Render Delta Report block from delta metadata.
    Shows what changed between base and current import.
    
    Supports both formats:
    1. Schema-compliant (base_import, current_timestamp, summary.files_*)
    2. Detailed format (base_timestamp, files_added/removed/changed as arrays)
    """
    lines = []
    lines.append("<!-- @delta:start -->")
    lines.append("## ♻ Delta Report")
    lines.append("")
    
    # Extract timestamps - support both schema (base_import) and legacy (base_timestamp)
    base_ts = delta_meta.get("base_import") or delta_meta.get("base_timestamp", "unknown")
    current_ts = delta_meta.get("current_timestamp", "unknown")
    
    lines.append(f"- **Base Import:** {base_ts}")
    lines.append(f"- **Current:** {current_ts}")
    lines.append("")
    
    def _safe_list_len(val):
        """Helper: safely get length of value if it's a list, else 0."""
        return len(val) if isinstance(val, list) else 0
    
    # Check for schema-compliant summary object
    summary = delta_meta.get("summary", {})
    if summary and isinstance(summary, dict):
        # Schema-compliant format with counts
        added_count = summary.get("files_added", 0)
        removed_count = summary.get("files_removed", 0)
        changed_count = summary.get("files_changed", 0)
        
        lines.append("**Summary:**")
        lines.append(f"- Files added: {added_count}")
        lines.append(f"- Files removed: {removed_count}")
        lines.append(f"- Files changed: {changed_count}")
        lines.append("")
        
        # Check for detailed lists (optional extension to schema)
        added = delta_meta.get("files_added", [])
        removed = delta_meta.get("files_removed", [])
        changed = delta_meta.get("files_changed", [])
    else:
        # Legacy detailed format with arrays
        added = delta_meta.get("files_added", [])
        removed = delta_meta.get("files_removed", [])
        changed = delta_meta.get("files_changed", [])
        
        lines.append("**Summary:**")
        lines.append(f"- Files added: {_safe_list_len(added)}")
        lines.append(f"- Files removed: {_safe_list_len(removed)}")
        lines.append(f"- Files changed: {_safe_list_len(changed)}")
        lines.append("")
    
    # Detail sections (only if we have lists)
    if isinstance(added, list) and added:
        lines.append("### Added Files")
        for f in added[:MAX_DELTA_FILES]:
            lines.append(f"- `{f}`")
        if len(added) > MAX_DELTA_FILES:
            lines.append(f"- _(and {len(added) - MAX_DELTA_FILES} more)_")
        lines.append("")
    
    if isinstance(removed, list) and removed:
        lines.append("### Removed Files")
        for f in removed[:MAX_DELTA_FILES]:
            lines.append(f"- `{f}`")
        if len(removed) > MAX_DELTA_FILES:
            lines.append(f"- _(and {len(removed) - MAX_DELTA_FILES} more)_")
        lines.append("")
    
    if isinstance(changed, list) and changed:
        lines.append("### Changed Files")
        for f in changed[:MAX_DELTA_FILES]:
            if isinstance(f, dict):
                path = f.get("path", "unknown")
                size_delta = f.get("size_delta", 0)
                if size_delta > 0:
                    lines.append(f"- `{path}` (+{size_delta} bytes)")
                elif size_delta < 0:
                    lines.append(f"- `{path}` ({size_delta} bytes)")
                else:
                    lines.append(f"- `{path}`")
            else:
                lines.append(f"- `{f}`")
        if len(changed) > MAX_DELTA_FILES:
            lines.append(f"- _(and {len(changed) - MAX_DELTA_FILES} more)_")
        lines.append("")
    
    lines.append("<!-- @delta:end -->")
    lines.append("")
    return "\n".join(lines)

def check_fleet_consistency(files: List[FileInfo]) -> List[str]:
    """
    Checks for objective inconsistencies specified in the spec.
    """
    warnings = []

    # Check for hausKI casing
    roots = set(f.root_label for f in files)

    # Check for missing .wgx/profile.yml in repos
    for root in roots:
        has_profile = any(f.root_label == root and "wgx-profile" in f.tags for f in files)
        if not has_profile:
             if root in REPO_ORDER:
                 warnings.append(f"- {root}: missing .wgx/profile.yml")

    return warnings

def validate_report_structure(report: str):
    """Checks if report follows Spec v2.3 structure."""
    required = [
        "## Source & Profile",
        "## Profile Description",
        "## Reading Plan",
        "## Plan",
        "## 📁 Structure",
        "## 🧾 Manifest",
        "## 📄 Content",
    ]

    positions = []
    for sec in required:
        pos = report.find(sec)
        if pos == -1:
            raise ValueError(f"Missing section: {sec}")
        positions.append(pos)

    # enforce ordering
    if positions != sorted(positions):
        raise ValueError("Section ordering does not match Spec v2.3")

    # ensure Manifest has anchor
    if "{#manifest}" not in report:
        raise ValueError("Manifest missing required anchor {#manifest}")

def iter_report_blocks(
    files: List[FileInfo],
    level: str,
    max_file_bytes: int,
    sources: List[Path],
    plan_only: bool,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
    delta_meta: Optional[Dict[str, Any]] = None,
) -> Iterator[str]:
    if extras is None:
        extras = ExtrasConfig.none()

    # UTC Timestamp
    now = datetime.datetime.utcnow()

    # Sort files according to strict multi-repo order and then path
    files.sort(key=lambda fi: (get_repo_sort_index(fi.root_label), fi.root_label.lower(), str(fi.rel_path).lower()))

    # Pre-calculate status based on Profile Strict Logic
    processed_files = []

    unknown_categories = set()
    unknown_tags = set()
    files_missing_anchor = []

    for fi in files:
        # Generate deterministic anchor
        rel_id = fi.rel_path.as_posix().replace("/", "-").replace(".", "-")
        anchor = f"file-{fi.root_label}-{rel_id}"
        fi.anchor = anchor
        
        # Compute file roles
        fi.roles = compute_file_roles(fi)

        # Debug checks
        # Kategorien strikt gemäß Spec v2.3:
        # {source, doc, config, test, contract, other}
        if fi.category == "other" or fi.category not in ["source", "doc", "config", "test", "contract", "other"]:
            unknown_categories.add(fi.category)

        status = "omitted"
        if fi.is_text:
            if level == "overview":
                if is_priority_file(fi):
                    status = "full"
                else:
                    status = "meta-only"
            elif level == "summary":
                # Summary: Dokumentation und Konfiguration voll,
                # Code/Test eher manifest-orientiert – außer Prioritätsdateien.
                if fi.category in ["doc", "config", "contract", "ci"] or "ai-context" in fi.tags or "wgx-profile" in fi.tags:
                    status = "full"
                elif fi.category in ["source", "test"]:
                    if is_priority_file(fi):
                        status = "full"
                    else:
                        status = "meta-only"
                else:
                    # Fallback: wie overview – wichtiges voll, Rest meta-only
                    if is_priority_file(fi):
                        status = "full"
                    else:
                        status = "meta-only"
            elif level == "dev":
                # Dev-Profil: Fokus auf arbeitsrelevante Dateien.
                # - Source/Tests/Config/CI/Contracts → voll
                # - Lockfiles: ab bestimmter Größe nur Manifest
                # - Doku: nur Prioritätsdateien (README, Runbooks, ai-context) voll,
                #         Rest Manifest
                # - Sonstiges: Manifest
                if "lockfile" in fi.tags:
                    if fi.size > 20_000:
                        status = "meta-only"
                    else:
                        status = "full"
                elif fi.category in ["source", "test", "config", "ci", "contract"]:
                    status = "full"
                elif fi.category == "doc":
                    if is_priority_file(fi):
                        status = "full"
                    else:
                        status = "meta-only"
                else:
                    status = "meta-only"
            elif level == "max":
                status = "full"
            else:
                if fi.size <= max_file_bytes: status = "full"
                else: status = "omitted"

        # Explicitly removed: automatic downgrade from "full" to "truncated"
        # if status == "full" and fi.size > max_file_bytes:
        #    status = "truncated"

        processed_files.append((fi, status))

    if debug:
        print("DEBUG: total files:", len(files))
        print("DEBUG: unknown categories:", unknown_categories)
        # print("DEBUG: unknown tags:", unknown_tags) # Tags logic is simple, skipping for now
        print("DEBUG: files without anchors:", [fi.rel_path for fi in files if not hasattr(fi, "anchor")])

    total_size = sum(fi.size for fi in files)
    text_files = [fi for fi in files if fi.is_text]
    included_count = sum(1 for _, s in processed_files if s in ("full", "truncated"))

    cat_stats = summarize_categories(files)

    # pro-Repo-Statistik für "mit Inhalt" (full/truncated),
    # um später im Plan pro Repo eine Coverage-Zeile auszugeben
    included_by_root: Dict[str, int] = {}

    # Declared Purpose (Patch C)
    declared_purpose = ""
    try:
        if sources:
            declared_purpose = extract_purpose(sources[0])
    except Exception:
        pass

    if not declared_purpose:
        declared_purpose = "(none)"

    infra_folders = set()
    code_folders = set()
    doc_folders = set()

    # Organismus-Rollen (ohne neue Tags/Kategorien):
    organism_ai_ctx: List[FileInfo] = []
    organism_contracts: List[FileInfo] = []
    organism_pipelines: List[FileInfo] = []
    organism_wgx_profiles: List[FileInfo] = []

    for fi in files:
        parts = fi.rel_path.parts
        if ".github" in parts or ".wgx" in parts or "contracts" in parts:
            infra_folders.add(parts[0])
        if "src" in parts or "scripts" in parts:
            code_folders.add(parts[0])
        if "docs" in parts:
            doc_folders.add("docs")

        # Organismus-Rollen:
        if fi.category == "contract":
            organism_contracts.append(fi)
        if "ai-context" in (fi.tags or []):
            organism_ai_ctx.append(fi)
        if "ci" in (fi.tags or []):
            organism_pipelines.append(fi)
        if "wgx-profile" in (fi.tags or []):
            organism_wgx_profiles.append(fi)

    # Mini-Summary pro Repo – damit KIs schnell die Lastverteilung sehen
    # Re-calculate or re-use existing categorization?
    # We need files_by_root NOW for Health Check, before Header.
    # It was originally calculated later (at Plan block).
    # So we move the calculation here.
    files_by_root: Dict[str, List[FileInfo]] = {}
    for fi in files:
        files_by_root.setdefault(fi.root_label, []).append(fi)

    # jetzt, nachdem processed_files existiert, die Coverage pro Root berechnen
    for fi, status in processed_files:
        if status in ("full", "truncated"):
            included_by_root[fi.root_label] = included_by_root.get(fi.root_label, 0) + 1

    # Pre-Calculation for Health (needed for Meta Block)
    health_collector = None
    if extras.health:
        health_collector = HealthCollector()
        # Analyze each repo
        for root in sorted(files_by_root.keys()):
            root_files = files_by_root[root]
            health_collector.analyze_repo(root, root_files)

    # --- 1. Header ---
    header = []
    header.append(f"# WC-Merge Report (v{SPEC_VERSION.split('.')[0]}.x)")
    header.append("")

    # --- 2. Source & Profile ---
    header.append("## Source & Profile")
    source_names = sorted([s.name for s in sources])
    header.append(f"- **Source:** {', '.join(source_names)}")
    header.append(f"- **Profile:** `{level}`")
    header.append(f"- **Generated At:** {now.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
    if max_file_bytes and max_file_bytes > 0:
        header.append(f"- **Max File Bytes:** {human_size(max_file_bytes)}")
    else:
        # 0 / None = kein per-File-Limit – alles wird vollständig gelesen
        header.append("- **Max File Bytes:** unlimited")
    header.append(f"- **Spec-Version:** {SPEC_VERSION}")
    header.append(f"- **Contract:** {MERGE_CONTRACT_NAME}")
    header.append(f"- **Contract-Version:** {MERGE_CONTRACT_VERSION}")

    # Semantische Use-Case-Zeile pro Profil (ergänzend zum Repo-Zweck)
    profile_usecase = PROFILE_USECASE.get(level)
    if profile_usecase:
        header.append(f"- **Profile Use-Case:** {profile_usecase}")

    header.append(f"- **Declared Purpose:** {declared_purpose}")

    # Scope-Zeile: welche Roots/Repos sind beteiligt?
    roots = sorted({fi.root_label for fi in files})
    if not roots:
        scope_desc = "empty (no matching files)"
    elif len(roots) == 1:
        scope_desc = f"single repo `{roots[0]}`"
    else:
        preview = ", ".join(f"`{r}`" for r in roots[:5])
        if len(roots) > 5:
            preview += ", …"
        scope_desc = f"{len(roots)} repos: {preview}"
    header.append(f"- **Scope:** {scope_desc}")

    # Neue, explizite Filterangaben
    if path_filter:
        header.append(f"- **Path Filter:** `{path_filter}`")
    else:
        header.append("- **Path Filter:** `none (full tree)`")

    if ext_filter:
        header.append(
            "- **Extension Filter:** "
            + ", ".join(f"`{e}`" for e in sorted(ext_filter))
        )
    else:
        header.append("- **Extension Filter:** `none (all text types)`")
    
    # Coverage in header (for quick AI assessment)
    if text_files:
        coverage_pct = int((included_count / len(text_files)) * 100)
        header.append(f"- **Coverage:** {coverage_pct}% ({included_count}/{len(text_files)} text files with content)")
    
    header.append("")
    
    # Prepare filter descriptions for meta block
    path_filter_desc = path_filter if path_filter else "none (full tree)"
    ext_filter_desc = ", ".join(sorted(ext_filter)) if ext_filter else "none (all text types)"

    # --- 3. Machine-readable Meta Block (für KIs) ---
    # Wir bauen das Meta-Objekt sauber als Dict auf und dumpen es dann als YAML
    if not plan_only:
        meta_lines: List[str] = []
        meta_lines.append("<!-- @meta:start -->")
        meta_lines.append("```yaml")

        meta_dict: Dict[str, Any] = {
            "merge": {
                "spec_version": SPEC_VERSION,
                "profile": level,
                "contract": MERGE_CONTRACT_NAME,
                "contract_version": MERGE_CONTRACT_VERSION,
                "plan_only": plan_only,
                "max_file_bytes": max_file_bytes,
                "scope": scope_desc,
                "source_repos": sorted([s.name for s in sources]) if sources else [],
                "path_filter": path_filter_desc,
                "ext_filter": ext_filter_desc,
            }
        }

        # Extras-Flags
        if extras:
            extras_meta = _build_extras_meta(extras, len(roots))
            if extras_meta:
                meta_dict["merge"]["extras"] = extras_meta

        # Health-Status
        if extras and extras.health and health_collector:
            # Determine overall status from collector results
            all_health = health_collector.get_all_health()
            if any(h.status == "critical" for h in all_health):
                overall = "critical"
            elif any(h.status == "warn" for h in all_health):
                overall = "warning"
            else:
                overall = "ok"

            missing_set = set()
            for h in all_health:
                # Naive mapping logic for 'missing' based on recommendations/warnings
                if not h.has_contracts: missing_set.add("contracts")
                if not h.has_ci_workflows: missing_set.add("ci")
                if not h.has_wgx_profile: missing_set.add("wgx-profile")

            meta_dict["merge"]["health"] = {
                "status": overall,
                "missing": sorted(list(missing_set)),
            }

        # Delta-Metadaten
        if extras and extras.delta_reports:
            if delta_meta:
                meta_dict["merge"]["delta"] = delta_meta
            else:
                meta_dict["merge"]["delta"] = {"enabled": True}

        # Augment-Metadaten
        if extras and extras.augment_sidecar:
            augment_meta = _build_augment_meta(sources)
            if augment_meta:
                meta_dict["merge"]["augment"] = augment_meta

        # Dump to YAML (ohne sort_keys, damit auch ältere PyYAML-Versionen in Pythonista funktionieren)
        if "yaml" in globals():
            meta_yaml = yaml.safe_dump(meta_dict)
            for line in meta_yaml.rstrip("\n").splitlines():
                meta_lines.append(line)
        else:
             meta_lines.append("# YAML support missing")

        meta_lines.append("```")
        meta_lines.append("<!-- @meta:end -->")
        meta_lines.append("")
        header.extend(meta_lines)

    # --- 4. Profile Description ---
    header.append("## Profile Description")
    if level == "overview":
        header.append("`overview`")
        header.append("- Nur: README (voll), Runbook (voll), ai-context (voll)")
        header.append("- Andere Dateien: Included = meta-only")
    elif level == "summary":
        header.append("`summary`")
        header.append("- Voll: README, Runbooks, ai-context, docs/, .wgx/, .github/workflows/, zentrale Config, Contracts")
        header.append("- Code & Tests: Manifest + Struktur; nur Prioritätsdateien (README, Runbooks, ai-context) voll")
    elif level == "dev":
        header.append("`dev`")
        header.append("- Code, Tests, Config, CI, Contracts, ai-context, wgx-profile → voll")
        header.append("- Doku nur für Prioritätsdateien voll (README, Runbooks, ai-context), sonst Manifest")
        header.append("- Lockfiles / Artefakte: ab bestimmter Größe meta-only")
    elif level == "max":
        header.append("`max`")
        header.append("- alle Textdateien → voll")
        header.append("- keine Kürzung (Dateien werden ggf. gesplittet)")
    else:
        header.append(f"`{level}` (custom)")
    header.append("")

    # --- 4. Reading Plan ---
    header.append("## Reading Plan")
    header.append("1. Lies zuerst: `README.md`, `docs/runbook*.md`, `*.ai-context.yml`")
    header.append("2. Danach: `Structure` -> `Manifest` -> `Content`")
    header.append("3. Hinweis: „Multi-Repo-Merges: jeder Repo hat eigenen Block 📦“")
    header.append("")

    yield "\n".join(header) + "\n"

    # --- 5. Plan ---
    plan: List[str] = []
    plan.append("## Plan")
    plan.append("")
    plan.append(f"- **Total Files:** {len(files)} (Text: {len(text_files)})")
    plan.append(f"- **Total Size:** {human_size(total_size)}")
    plan.append(f"- **Included Content:** {included_count} files (full)")
    if text_files:
        plan.append(
            f"- **Coverage:** {included_count}/{len(text_files)} Textdateien mit Inhalt (`full`/`truncated`)"
        )
    plan.append("")

    # Mini-Summary pro Repo – damit KIs schnell die Lastverteilung sehen
    # files_by_root was calculated earlier for Health Check

    if files_by_root:
        plan.append("### Repo Snapshots")
        plan.append("")
        for root in sorted(files_by_root.keys()):
            root_files = files_by_root[root]
            root_total = len(root_files)
            # „relevante Textdateien“: Code, Docs, Config, Tests, CI, Contracts
            root_text = sum(
                1
                for f in root_files
                if f.is_text
                and f.category in {"source", "doc", "config", "test", "ci", "contract"}
            )
            root_bytes = sum(f.size for f in root_files)
            root_included = included_by_root.get(root, 0)
            plan.append(
                f"- `{root}` → {root_total} files "
                f"({root_text} relevant text, {human_size(root_bytes)}, {root_included} with content)"
            )
        plan.append("")
    plan.append("**Folder Highlights:**")
    if code_folders: plan.append(f"- Code: `{', '.join(sorted(code_folders))}`")
    if doc_folders: plan.append(f"- Docs: `{', '.join(sorted(doc_folders))}`")
    if infra_folders: plan.append(f"- Infra: `{', '.join(sorted(infra_folders))}`")
    plan.append("")

    # Organismus-Overview (im Plan, ohne Spec-Reihenfolge zu brechen)
    plan.append("### Organism Overview")
    plan.append("")
    plan.append(
        f"- AI-Kontext-Organe: {len(organism_ai_ctx)} Datei(en) (`ai-context`)"
    )
    plan.append(
        f"- Contracts: {len(organism_contracts)} Datei(en) (category = `contract`)"
    )
    plan.append(
        f"- Pipelines (CI/CD): {len(organism_pipelines)} Datei(en) (Tag `ci`)"
    )
    plan.append(
        f"- Fleet-/WGX-Profile: {len(organism_wgx_profiles)} Datei(en) (Tag `wgx-profile`)"
    )
    plan.append("")

    yield "\n".join(plan) + "\n"

    # --- Health Report (Stage 1: Repo Doctor) ---
    # Note: health_collector was already populated before header generation
    if extras.health and health_collector:
        health_report = health_collector.render_markdown()
        if health_report:
            yield health_report

    # --- Organism Index (Stage 2: Single Repo) ---
    if extras.organism_index and len(roots) == 1:
        organism_index = []
        organism_index.append("<!-- @organism-index:start -->")
        organism_index.append("## 🧬 Organism Index")
        organism_index.append("")
        
        if organism_ai_ctx:
            organism_index.append("**AI-Context:**")
            for fi in organism_ai_ctx:
                organism_index.append(f"- `{fi.rel_path}`")
            organism_index.append("")
        
        if organism_contracts:
            organism_index.append("**Contracts:**")
            for fi in organism_contracts:
                organism_index.append(f"- `{fi.rel_path}`")
            organism_index.append("")
        
        if organism_pipelines:
            organism_index.append("**CI & Pipelines:**")
            for fi in organism_pipelines:
                organism_index.append(f"- `{fi.rel_path}`")
            organism_index.append("")
        
        if organism_wgx_profiles:
            organism_index.append("**WGX-Profile:**")
            for fi in organism_wgx_profiles:
                organism_index.append(f"- `{fi.rel_path}`")
            organism_index.append("")
        
        organism_index.append("<!-- @organism-index:end -->")
        organism_index.append("")
        yield "\n".join(organism_index)

    # --- Fleet Panorama (Stage 2: Multi-Repo) ---
    if extras.fleet_panorama and len(roots) > 1:
        fleet_panorama = []
        fleet_panorama.append("<!-- @fleet-panorama:start -->")
        fleet_panorama.append("## 🛰 Fleet Panorama")
        fleet_panorama.append("")
        fleet_panorama.append(f"**Summary:** {len(roots)} repos, {human_size(total_size)}, {len(files)} files")
        fleet_panorama.append("")
        
        for root in sorted(files_by_root.keys()):
            root_files = files_by_root[root]
            root_total = len(root_files)
            root_bytes = sum(f.size for f in root_files)
            
            # Count categories for this repo
            root_cat_counts: Dict[str, int] = {}
            for fi in root_files:
                cat = fi.category or "other"
                root_cat_counts[cat] = root_cat_counts.get(cat, 0) + 1
            
            cat_parts = [f"{cat}={count}" for cat, count in sorted(root_cat_counts.items())]
            
            # Check for key indicators
            has_wgx = any(".wgx" in f.rel_path.parts for f in root_files)
            has_ci = any("ci" in (f.tags or []) for f in root_files)
            
            fleet_panorama.append(f"**`{root}`:**")
            fleet_panorama.append(f"- Files: {root_total}")
            fleet_panorama.append(f"- Size: {human_size(root_bytes)}")
            fleet_panorama.append(f"- Categories: {', '.join(cat_parts)}")
            
            # Role determination
            role = "utility"
            if "metarepo" in root.lower():
                role = "governance"
            elif "contract" in root.lower():
                role = "schema authority"
            elif "tool" in root.lower():
                role = "tooling"
            
            fleet_panorama.append(f"- Role: {role}")
            
            indicators = []
            if has_wgx:
                indicators.append("WGX")
            if has_ci:
                indicators.append("CI")
            if indicators:
                fleet_panorama.append(f"- Indicators: {', '.join(indicators)}")
            
            fleet_panorama.append("")
        
        fleet_panorama.append("<!-- @fleet-panorama:end -->")
        fleet_panorama.append("")
        yield "\n".join(fleet_panorama)

    # --- Augment Intelligence (Stage 4: Sidecar) ---
    if extras.augment_sidecar:
        augment_block = _render_augment_block(sources)
        if augment_block:
            yield augment_block
    
    # --- Delta Report (Stage 3: Content) ---
    if extras.delta_reports and delta_meta:
        delta_block = _render_delta_block(delta_meta)
        if delta_block:
            yield delta_block

    if plan_only:
        return

    # --- 6. Structure ---
    structure = []
    structure.append("## 📁 Structure")
    structure.append("")
    structure.append(build_tree(files))
    structure.append("")
    yield "\n".join(structure) + "\n"

    # --- Index (Patch B) ---
    # Generated Categories Index
    index_blocks = []
    index_blocks.append("## Index")

    # List of categories to index
    # CI ist ein Tag, keine eigene Kategorie – wird separat indiziert.
    cats_to_idx = ["source", "doc", "config", "contract", "test"]
    for c in cats_to_idx:
        index_blocks.append(f"- [{c.capitalize()}](#cat-{c})")

    # Tags can be indexed too if needed, e.g. wgx-profile
    index_blocks.append("- [CI Pipelines](#tag-ci)")
    index_blocks.append("- [WGX Profiles](#tag-wgx-profile)")
    index_blocks.append("")

    # Category Lists
    for c in cats_to_idx:
        cat_files = [f for f in files if f.category == c]
        if cat_files:
            index_blocks.append(f"## Category: {c} {{#cat-{c}}}")
            for f in cat_files:
                index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
            index_blocks.append("")

    # Tag Lists – CI-Pipelines
    ci_files = [f for f in files if "ci" in (f.tags or [])]
    if ci_files:
        index_blocks.append("## Tag: ci {#tag-ci}")
        for f in ci_files:
            index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
        index_blocks.append("")

    # Tag Lists (example)
    wgx_files = [f for f in files if "wgx-profile" in f.tags]
    if wgx_files:
        index_blocks.append("## Tag: wgx-profile {#tag-wgx-profile}")
        for f in wgx_files:
             index_blocks.append(f"- [`{f.rel_path}`](#{f.anchor})")
        index_blocks.append("")

    yield "\n".join(index_blocks) + "\n"

    # --- 7. Manifest (Patch A) ---
    manifest: List[str] = []
    manifest.append("## 🧾 Manifest {#manifest}")
    manifest.append("")
    manifest.append("| Root | Path | Category | Tags | Roles | Size | Included | MD5 |")
    manifest.append("| --- | --- | --- | --- | --- | ---: | --- | --- |")
    for fi, status in processed_files:
        tags_str = ", ".join(fi.tags) if fi.tags else "-"
        roles_str = ", ".join(fi.roles) if fi.roles else "-"
        # Noise kennzeichnen, ohne das Schema zu ändern
        included_label = status
        if is_noise_file(fi):
            included_label = f"{status} (noise)"

        # Link in Manifest
        path_str = f"[`{fi.rel_path}`](#{fi.anchor})"
        manifest.append(
            f"| `{fi.root_label}` | {path_str} | `{fi.category}` | {tags_str} | {roles_str} | "
            f"{human_size(fi.size)} | `{included_label}` | `{fi.md5}` |"
        )
    manifest.append("")
    yield "\n".join(manifest) + "\n"

    # --- Optional: Fleet Consistency ---
    consistency_warnings = check_fleet_consistency(files)
    if consistency_warnings:
        cons = []
        cons.append("## Fleet Consistency")
        cons.append("")
        for w in consistency_warnings:
            cons.append(w)
        cons.append("")
        yield "\n".join(cons) + "\n"

    # --- 8. Content ---
    # Per Spec v2.3 / Validator requirements
    yield "## 📄 Content\n\n"

    current_root = None

    for fi, status in processed_files:
        if status in ("omitted", "meta-only"):
            continue

        if fi.root_label != current_root:
            yield f"## 📦 {fi.root_label} {{#repo-{fi.root_label}}}\n\n"
            current_root = fi.root_label

        block = []
        block.append(f'<a id="{fi.anchor}"></a>')
        block.append(f"### `{fi.rel_path}`")
        block.append(f"- Category: {fi.category}")
        if fi.tags:
            block.append(f"- Tags: {', '.join(fi.tags)}")
        else:
            block.append(f"- Tags: -")
        block.append(f"- Size: {human_size(fi.size)}")
        block.append(f"- Included: {status}")
        block.append(f"- MD5: {fi.md5}")

        content, truncated, trunc_msg = read_smart_content(fi, max_file_bytes)

        lang = lang_for(fi.ext)
        block.append("")
        block.append(f"```{lang}")
        block.append(content)
        block.append("```")
        block.append("")
        block.append("[↑ Zurück zum Manifest](#manifest)")
        yield "\n".join(block) + "\n\n"

def generate_report_content(
    files: List[FileInfo],
    level: str,
    max_file_bytes: int,
    sources: List[Path],
    plan_only: bool,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
    delta_meta: Optional[Dict[str, Any]] = None,
) -> str:
    report = "".join(iter_report_blocks(files, level, max_file_bytes, sources, plan_only, debug, path_filter, ext_filter, extras, delta_meta))
    if plan_only:
        return report
    try:
        validate_report_structure(report)
    except ValueError as e:
        if debug:
            print(f"DEBUG: Validation Error: {e}")
        # In strict mode, we might want to raise, but for now let's just warn or allow passing if debug
        # User said "Fehler -> kein Merge wird geschrieben." in Spec.
        # So we should probably re-raise.
        raise
    return report

def write_reports_v2(
    merges_dir: Path,
    hub: Path,
    repo_summaries: List[Dict],
    detail: str,
    mode: str,
    max_bytes: int,
    plan_only: bool,
    split_size: int = 0,
    debug: bool = False,
    path_filter: Optional[str] = None,
    ext_filter: Optional[List[str]] = None,
    extras: Optional[ExtrasConfig] = None,
    delta_meta: Optional[Dict[str, Any]] = None,
) -> List[Path]:
    out_paths = []

    # Helper for writing logic
    def process_and_write(target_files, target_sources, output_filename_base_func):
        if split_size > 0:
            local_out_paths = []
            part_num = 1
            current_size = 0
            current_lines = []

            # Helper to flush
            def flush_part(is_last=False):
                nonlocal part_num, current_size, current_lines
                if not current_lines:
                    return

                out_path = output_filename_base_func(part=part_num)
                out_path.write_text("".join(current_lines), encoding="utf-8")
                local_out_paths.append(out_path)

                part_num += 1
                current_lines = []
                # Add continuation header for next part
                if not is_last:
                    header = f"# WC-Merge Report (Part {part_num})\n\n"
                    current_lines.append(header)
                    current_size = len(header.encode('utf-8'))
                else:
                    current_size = 0

            iterator = iter_report_blocks(target_files, detail, max_bytes, target_sources, plan_only, debug, path_filter, ext_filter, extras, delta_meta)

            for block in iterator:
                block_len = len(block.encode('utf-8'))

                if current_size + block_len > split_size and len(current_lines) > 1:
                    flush_part()

                current_lines.append(block)
                current_size += block_len

            flush_part(is_last=True)

            # Nachlauf: Header aller Teile auf "Part N/M" normalisieren.
            # Hintergrund:
            # - Während des Schreibens kennen wir die Gesamtzahl der Teile noch nicht.
            # - Jetzt (nach allen flushes) können wir die Header 1/1, 1/3, 2/3, … sauber setzen.
            total_parts = len(local_out_paths)
            if total_parts >= 1:
                prefix_part = "# WC-Merge Report (Part "
                prefix_main = "# WC-Merge Report"

                for idx, path in enumerate(local_out_paths, start=1):
                    try:
                        text = path.read_text(encoding="utf-8")
                    except Exception:
                        # Wenn das Lesen fehlschlägt, diesen Part überspringen.
                        continue

                    lines = text.splitlines(True)
                    if not lines:
                        continue

                    # Robuste Header-Erkennung: BOM und Whitespace tolerieren
                    header_idx = None
                    for i, line in enumerate(lines):
                        stripped = line.lstrip("\ufeff")  # Remove BOM if present
                        if stripped.startswith(prefix_part) or stripped.startswith(prefix_main):
                            header_idx = i
                            break

                    if header_idx is None:
                        continue

                    # Nur die Header-Zeile ersetzen, Rest unverändert lassen.
                    lines[header_idx] = f"# WC-Merge Report (Part {idx}/{total_parts})\n"
                    try:
                        path.write_text("".join(lines), encoding="utf-8")
                    except Exception:
                        # Schreibfehler nicht fatal machen.
                        pass

            out_paths.extend(local_out_paths)

        else:
            # Standard single file
            content = generate_report_content(target_files, detail, max_bytes, target_sources, plan_only, debug, path_filter, ext_filter, extras, delta_meta)
            out_path = output_filename_base_func(part=None)
            out_path.write_text(content, encoding="utf-8")
            out_paths.append(out_path)

    if mode == "gesamt":
        all_files = []
        repo_names = []
        sources = []
        for s in repo_summaries:
            all_files.extend(s["files"])
            repo_names.append(s["name"])
            sources.append(s["root"])

        # kosmetisches Label im Dateinamen:
        # nur ein Repo → "single", mehrere → "multi"
        mode_label = "single" if len(repo_names) == 1 else "multi"
        process_and_write(
            all_files,
            sources,
            lambda part=None: make_output_filename(merges_dir, repo_names, mode_label, detail, part),
        )

    else:
        for s in repo_summaries:
            s_name = s["name"]
            s_files = s["files"]
            s_root = s["root"]

            process_and_write(s_files, [s_root], lambda part=None: make_output_filename(merges_dir, [s_name], "repo", detail, part))

    return out_paths

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-wc-merger-README-md"></a>
### `merger/wc-merger/README.md`
- Category: doc
- Tags: ai-context
- Size: 6.72 KB
- Included: full
- MD5: 63c94fde1efcff1050e511a744f9e742

```markdown
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
    *   `Spec-Version: 2.3` Header immer setzen.

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
     scope: "single repo `tools`"
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

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-wc-merger-tools_augment-yml"></a>
### `merger/wc-merger/tools_augment.yml`
- Category: config
- Tags: -
- Size: 400.00 B
- Included: full
- MD5: 68576b277d2584c7c5a6196a9324a4ea

```yaml
augment:
  version: 1

  hotspots:
    - path: merger/wc-merger/merge_core.py
      reason: "Complex branching logic"
      severity: "medium"

  suggestions:
    - "Extract profile logic into strategy pattern"
    - "Add comprehensive unit tests"

  risks:
    - "Large merges may exhaust memory"

  priorities:
    - priority: 1
      task: "Complete super-merger roadmap"
      status: "complete"

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-wc-merger-validate_merge_meta-py"></a>
### `merger/wc-merger/validate_merge_meta.py`
- Category: source
- Tags: -
- Size: 3.24 KB
- Included: full
- MD5: 7627015fff49c8e17a82febe8f4b4cb8

```python
#!/usr/bin/env python3
"""
Validiert den @meta-Block eines WC-Merger-Reports gegen die JSON-Schemas.

Nutzung:

    python3 validate_merge_meta.py path/to/report.md

Voraussetzungen:
    pip install pyyaml jsonschema
"""

import argparse
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def extract_meta_block(markdown: str) -> dict:
    """
    Sucht den ersten @meta-Block im Markdown und parst den YAML-Inhalt.
    """
    meta_pattern = re.compile(
        r"<!-- @meta:start -->\s*```yaml\s*(?P<yaml>.*?)```",
        re.DOTALL,
    )
    match = meta_pattern.search(markdown)
    if not match:
        raise ValueError("Kein @meta-Block mit ```yaml ... ``` gefunden.")
    return yaml.safe_load(match.group("yaml"))


def load_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_report_meta(report_path: Path) -> None:
    # Schemas liegen neben dem Skript, nicht zwingend neben dem Report
    script_dir = Path(__file__).resolve().parent

    text = report_path.read_text(encoding="utf-8")
    meta = extract_meta_block(text)

    merge_meta = meta.get("merge")
    if not isinstance(merge_meta, dict):
        raise ValueError("Im @meta-Block fehlt der Schlüssel 'merge' oder er ist kein Objekt.")

    # Hauptschema laden
    report_schema_path = (script_dir / "wc-merge-report.schema.json").resolve()
    if not report_schema_path.exists():
        raise FileNotFoundError(f"Schema nicht gefunden: {report_schema_path}")

    report_schema = load_schema(report_schema_path)
    merge_schema = report_schema["properties"]["merge"]

    validator = Draft202012Validator(merge_schema)
    errors = sorted(validator.iter_errors(merge_meta), key=lambda e: e.path)
    if errors:
        print(f"❌ Merge-Meta-Block in {report_path} verletzt das Schema:")
        for err in errors:
            path = ".".join(str(p) for p in err.path)
            print(f"  - [{path}] {err.message}")
        raise SystemExit(1)

    print(f"✅ Merge-Meta-Block in {report_path} ist schema-konform.")

    # Optional: Delta-Contract validieren, falls vorhanden
    delta = merge_meta.get("delta")
    if isinstance(delta, dict) and delta.get("type") == "wc-merge-delta":
        delta_schema_path = (script_dir / "wc-merge-delta.schema.json").resolve()
        if not delta_schema_path.exists():
            print("⚠️  Delta-Schema nicht gefunden, überspringe Delta-Validierung.")
            return
        delta_schema = load_schema(delta_schema_path)
        delta_validator = Draft202012Validator(delta_schema)
        delta_errors = sorted(delta_validator.iter_errors(delta), key=lambda e: e.path)
        if delta_errors:
            print("❌ Delta-Metadaten verletzen das Delta-Schema:")
            for err in delta_errors:
                path = ".".join(str(p) for p in err.path)
                print(f"  - [{path}] {err.message}")
            raise SystemExit(1)
        print("✅ Delta-Metadaten sind schema-konform.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path, help="Pfad zur Merge-Report-Markdown-Datei")
    args = parser.parse_args()

    validate_report_meta(args.report)


if __name__ == "__main__":
    main()

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-wc-merger-wc-extractor-py"></a>
### `merger/wc-merger/wc-extractor.py`
- Category: source
- Tags: -
- Size: 19.71 KB
- Included: full
- MD5: e4c6e2660f5280b4f2ea6afd0d2a683b

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc_extractor – ZIPs im wc-hub entpacken und Repos aktualisieren.
Verwendet merge_core.

Funktion:
- Suche alle *.zip im Hub (wc-hub).
- Für jede ZIP:
  - Entpacke in temporären Ordner.
  - Wenn es bereits einen Zielordner mit gleichem Namen gibt:
    - Erzeuge einfachen Diff-Bericht (Markdown) alt vs. neu.
    - Lösche den alten Ordner.
  - Benenne Temp-Ordner in Zielordner um.
  - Lösche die ZIP-Datei.

Diff-Berichte:
- Liegen direkt im merges-Verzeichnis des Hubs.
"""

import sys
import shutil
import zipfile
import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any

try:
    import console  # type: ignore
except ImportError:
    console = None  # type: ignore

# Import from core
try:
    from merge_core import (
        detect_hub_dir,
        get_merges_dir,
        get_repo_snapshot,
    )
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from merge_core import (
        detect_hub_dir,
        get_merges_dir,
        get_repo_snapshot,
    )


def detect_hub() -> Path:
    script_path = Path(__file__).resolve()
    return detect_hub_dir(script_path)


def build_delta_meta_from_diff(
    only_old: List[str],
    only_new: List[str],
    changed: List[Tuple[str, int, int, str, str, str, str]],
    base_timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Builds a delta metadata dict conforming to wc-merge-delta.schema.json.
    
    Args:
        only_old: List of files removed
        only_new: List of files added
        changed: List of changed file tuples (path, size_old, size_new, ...)
        base_timestamp: Optional timestamp of base import
    
    Returns:
        Delta metadata dict conforming to schema
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    
    delta_meta = {
        "type": "wc-merge-delta",
        "base_import": base_timestamp or now.isoformat(),
        "current_timestamp": now.isoformat(),
        "summary": {
            "files_added": len(only_new),
            "files_removed": len(only_old),
            "files_changed": len(changed),
        },
        # Optional: detailed lists (extension to schema)
        "files_added": list(only_new),
        "files_removed": list(only_old),
        "files_changed": [
            {
                "path": item[0],
                "size_delta": item[2] - item[1],  # size_new - size_old
            }
            for item in changed
        ],
    }
    
    return delta_meta


def diff_trees(
    old: Path,
    new: Path,
    repo_name: str,
    merges_dir: Path,
) -> Path:
    """
    Vergleicht zwei Repo-Verzeichnisse und schreibt einen Markdown-Diff-Bericht.

    Neu: „Manifest-Anklang“
      - kleine Tabelle mit Pfad, Status, Kategorie, Größen und MD5-Änderung
      - Kategorien stammen aus merge_core.classify_file_v2 via get_repo_snapshot

    Rückgabe:
      Pfad zur Diff-Datei.
    """
    # Snapshot-Maps:
    #   rel_path -> (size, md5, category)
    old_map = get_repo_snapshot(old)
    new_map = get_repo_snapshot(new)

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    only_old = sorted(old_keys - new_keys)
    only_new = sorted(new_keys - old_keys)
    common = sorted(old_keys & new_keys)

    # Für gemeinsame Dateien merken wir uns auch MD5 und Kategorien
    changed = []
    for rel in common:
        size_old, md5_old, cat_old = old_map[rel]
        size_new, md5_new, cat_new = new_map[rel]
        if size_old != size_new or md5_old != md5_new:
            changed.append((rel, size_old, size_new, md5_old, md5_new, cat_old, cat_new))

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    fname = "{}-import-diff-{}.md".format(repo_name, ts)
    out_path = merges_dir / fname

    lines: List[str] = []
    lines.append("# Import-Diff `{}`".format(repo_name))
    lines.append("")
    lines.append("- Zeitpunkt: `{}`".format(now))
    lines.append("- Alter Pfad: `{}`".format(old))
    lines.append("- Neuer Pfad (Temp): `{}`".format(new))
    lines.append("")
    lines.append("- Dateien nur im alten Repo: **{}**".format(len(only_old)))
    lines.append("- Dateien nur im neuen Repo: **{}**".format(len(only_new)))
    lines.append("- Dateien mit geändertem Inhalt: **{}**".format(len(changed)))
    lines.append("")

    # Manifest-artige Tabelle: ein Eintrag pro betroffener Datei
    any_rows = bool(only_old or only_new or changed)
    if any_rows:
        lines.append("## Dateiliste (Manifest-Stil)")
        lines.append("")
        lines.append(
            "| Pfad | Status | Kategorie | Größe alt | Größe neu | Δ Größe | MD5 geändert |"
        )
        lines.append("| --- | --- | --- | ---: | ---: | ---: | --- |")

        # Entfernte Dateien
        for rel in only_old:
            size_old, md5_old, cat_old = old_map[rel]
            lines.append(
                "| `{path}` | removed | `{cat}` | {s_old} | - | -{delta} | n/a |".format(
                    path=rel,
                    cat=cat_old,
                    s_old=size_old,
                    delta=size_old,
                )
            )

        # Neue Dateien
        for rel in only_new:
            size_new, md5_new, cat_new = new_map[rel]
            lines.append(
                "| `{path}` | added | `{cat}` | - | {s_new} | +{delta} | n/a |".format(
                    path=rel,
                    cat=cat_new,
                    s_new=size_new,
                    delta=size_new,
                )
            )

        # Geänderte Dateien
        for (
            rel,
            s_old,
            s_new,
            md5_old,
            md5_new,
            cat_old,
            cat_new,
        ) in changed:
            delta = s_new - s_old
            md5_changed = "ja" if md5_old != md5_new else "nein"
            # Falls sich die Kategorie ändert (selten), neue Kategorie anzeigen
            cat_display = cat_new or cat_old
            lines.append(
                "| `{path}` | changed | `{cat}` | {s_old} | {s_new} | {delta:+d} | {md5_flag} |".format(
                    path=rel,
                    cat=cat_display,
                    s_old=s_old,
                    s_new=s_new,
                    delta=delta,
                    md5_flag=md5_changed,
                )
            )

        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def import_zip(zip_path: Path, hub: Path, merges_dir: Path) -> Optional[Path]:
    """
    Entpackt eine einzelne ZIP-Datei in den Hub, behandelt Konflikte,
    schreibt ggf. Diff und ersetzt das alte Repo.

    Rückgabe:
      Pfad zum Diff-Bericht oder None.
    """
    repo_name = zip_path.stem
    target_dir = hub / repo_name
    tmp_dir = hub / ("__extract_tmp_" + repo_name)

    print("Verarbeite ZIP:", zip_path.name, "-> Repo", repo_name)

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    tmp_dir.mkdir(parents=True, exist_ok=True)

    # ZIP entpacken
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp_dir)

    diff_path = None  # type: Optional[Path]

    # Wenn es schon ein Repo mit diesem Namen gibt -> Diff + löschen
    if target_dir.exists():
        print("  Zielordner existiert bereits:", target_dir)
        try:
            diff_path = diff_trees(target_dir, tmp_dir, repo_name, merges_dir)
            print("  Diff-Bericht:", diff_path)
        except Exception as e:
            print(f"  Warnung: Fehler beim Diff-Erstellen ({e}). Fahre fort.")

        shutil.rmtree(target_dir)
        print("  Alter Ordner gelöscht:", target_dir)
    else:
        print("  Kein vorhandenes Repo – frischer Import.")

    # Temp-Ordner ins Ziel verschieben
    tmp_dir.rename(target_dir)
    print("  Neuer Repo-Ordner:", target_dir)

    # ZIP nach erfolgreichem Import löschen
    try:
        zip_path.unlink()
        print("  ZIP gelöscht:", zip_path.name)
    except OSError as e:
        print(f"  Warnung: Konnte ZIP nicht löschen ({e})")
    print("")

    return diff_path


def import_zip_wrapper(zip_path: Path, hub: Path, merges_dir: Path) -> Optional[Path]:
    """Wraps import_zip, erzeugt optional Delta-Merge und sorgt für Cleanup."""
    diff_path: Optional[Path] = None
    try:
        # Normalen Import + Diff laufen lassen
        diff_path = import_zip(zip_path, hub, merges_dir)

        # Automatisch Delta-Merge erzeugen, wenn ein Diff existiert
        if diff_path is not None:
            repo_name = zip_path.stem
            repo_root = hub / repo_name
            if repo_root.exists():
                try:
                    delta_path = create_delta_merge_from_diff(
                        diff_path, repo_root, merges_dir, profile="delta-full"
                    )
                    print(f"  Delta-Merge: {delta_path}")
                except Exception as e:
                    print(f"  Warnung: Konnte Delta-Merge nicht erzeugen ({e}).")

        return diff_path
    except Exception:
        raise
    finally:
        if zip_path.exists():
            try:
                zip_path.unlink()
                print(f"  Cleanup: ZIP gelöscht ({zip_path.name})")
            except OSError:
                pass


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="wc-extractor-v2: Import ZIPs to hub.")
    parser.add_argument("--hub", help="Hub directory override.")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    hub = detect_hub_dir(script_path, args.hub)

    if not hub.exists():
         print(f"Hub directory not found: {hub}")
         return 1

    merges_dir = get_merges_dir(hub)

    print("wc_extractor-v2 – Hub:", hub)
    zips = sorted(hub.glob("*.zip"))

    if not zips:
        msg = "Keine ZIP-Dateien im Hub gefunden."
        print(msg)
        if console:
            console.alert("wc_extractor-v2", msg, "OK", hide_cancel_button=True)
        return 0

    diff_paths = []

    for zp in zips:
        try:
            diff = import_zip_wrapper(zp, hub, merges_dir)
            if diff is not None:
                diff_paths.append(diff)
        except Exception as e:
            print("Fehler bei {}: {}".format(zp, e), file=sys.stderr)

    summary_lines = []
    summary_lines.append("Import fertig.")
    summary_lines.append("Hub: {}".format(hub))
    if diff_paths:
        summary_lines.append(
            "Diff-Berichte ({}):".format(len(diff_paths))
        )
        for p in diff_paths:
            summary_lines.append("  - {}".format(p))
    else:
        summary_lines.append("Keine Diff-Berichte erzeugt.")

    summary = "\n".join(summary_lines)
    print(summary)

    if console:
        console.alert("wc_extractor-v2", summary, "OK", hide_cancel_button=True)

    return 0



# ---------------------------------------------------------------------------
# Diff-Parser (Prototyp)
# ---------------------------------------------------------------------------

def parse_import_diff_table(text: str) -> List[Dict[str, Any]]:
    """
    Parst die „Dateiliste (Manifest-Stil)“-Tabelle aus einem Import-Diff.

    Rückgabe:
      Liste von Dicts mit Schlüsseln:
        - path: str
        - status: "added" | "removed" | "changed"
        - category: str
        - size_old: Optional[int]
        - size_new: Optional[int]
        - delta: Optional[int]
        - md5_changed: Optional[bool]  # True/False/nicht verfügbar

    Wenn die Tabelle nicht gefunden wird, wird eine leere Liste zurückgegeben.
    """
    lines = text.splitlines()

    # Header-Zeile der Tabelle finden
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| Pfad | Status | Kategorie |"):
            header_idx = i
            break

    if header_idx is None or header_idx + 2 >= len(lines):
        return []

    # Nach der Headerzeile kommt die Separatorzeile, danach die Datenzeilen
    rows = []
    i = header_idx + 2
    while i < len(lines):
        line = lines[i]
        if not line.strip().startswith("|"):
            break
        # Spalten extrahieren: | col1 | col2 | ... |
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 7:
            i += 1
            continue

        path_raw, status, category_raw, s_old_raw, s_new_raw, delta_raw, md5_flag_raw = parts[:7]

        def _strip_ticks(s):
            s = s.strip()
            if s.startswith("`") and s.endswith("`") and len(s) >= 2:
                return s[1:-1]
            return s

        path = _strip_ticks(path_raw)
        category = _strip_ticks(category_raw)

        def _parse_int_or_none(s):
            s = s.strip()
            if s == "-" or not s:
                return None
            try:
                return int(s.replace("+", ""))
            except ValueError:
                return None

        size_old = _parse_int_or_none(s_old_raw)
        size_new = _parse_int_or_none(s_new_raw)
        delta = _parse_int_or_none(delta_raw)

        md5_flag = md5_flag_raw.strip().lower()
        if md5_flag in ("ja", "yes", "true"):
            md5_changed = True
        elif md5_flag in ("nein", "no", "false"):
            md5_changed = False
        else:
            md5_changed = None

        rows.append(
            {
                "path": path,
                "status": status.strip(),
                "category": category,
                "size_old": size_old,
                "size_new": size_new,
                "delta": delta,
                "md5_changed": md5_changed,
            }
        )
        i += 1

    return rows


# ---------------------------------------------------------------------------
# Delta-Merge auf Basis des Import-Diffs
# ---------------------------------------------------------------------------

def build_delta_merge_report(
    repo_root: Path,
    repo_name: str,
    diff_rows: List[Dict[str, Any]],
    merges_dir: Path,
    profile: str = "delta-full",
) -> Path:
    """
    Erzeugt einen WC-Merger-kompatiblen Delta-Report auf Basis eines
    Import-Diffs (parse_import_diff_table).

    Standardverhalten:
      - Status "changed" und "added" → mit Inhalt
      - Status "removed"             → nur im Manifest / Summary
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    ts = now.strftime("%y%m%d-%H%M")
    fname = f"{repo_name}_{profile}_delta_{ts}_merge.md"
    out_path = merges_dir / fname

    rows = list(diff_rows or [])
    changed = [r for r in rows if r.get("status") == "changed"]
    added = [r for r in rows if r.get("status") == "added"]
    removed = [r for r in rows if r.get("status") == "removed"]

    lines = []
    lines.append("# WC-Merger Delta Report (v2.x)")
    lines.append("")
    lines.append("## Source & Profile")
    lines.append(f"- **Source:** {repo_name}")
    lines.append(f"- **Profile:** `{profile}`")
    lines.append(f"- **Generated At:** {now.isoformat()} (UTC)")
    lines.append("- **Spec-Version:** 2.3")
    lines.append(
        f"- **Declared Purpose:** Delta-Merge – changed+added files for `{repo_name}`"
    )
    lines.append(f"- **Scope:** single repo `{repo_name}`")
    lines.append("")

    lines.append("## Change Summary")
    lines.append("")
    lines.append(f"- Changed files: **{len(changed)}**")
    lines.append(f"- Added files: **{len(added)}**")
    lines.append(f"- Removed files: **{len(removed)}**")
    lines.append("")

    if rows:
        lines.append("## File Manifest (Delta)")
        lines.append("")
        lines.append(
            "| Pfad | Status | Kategorie | Größe alt | Größe neu | Δ Größe | MD5 geändert |"
        )
        lines.append("| --- | --- | --- | ---: | ---: | ---: | --- |")

        def _fmt_int(v):
            if v is None:
                return "-"
            return str(v)

        for row in rows:
            path = row.get("path", "")
            status = row.get("status", "")
            category = row.get("category") or "-"
            size_old = row.get("size_old")
            size_new = row.get("size_new")
            delta = row.get("delta")
            md5_flag = row.get("md5_changed")
            if md5_flag is True:
                md5_text = "ja"
            elif md5_flag is False:
                md5_text = "nein"
            else:
                md5_text = "n/a"

            lines.append(
                f"| `{path}` | {status} | `{category}` | "
                f"{_fmt_int(size_old)} | {_fmt_int(size_new)} | {_fmt_int(delta)} | {md5_text} |"
            )

        lines.append("")

    def _anchor_for(rel_path: str) -> str:
        return "delta-" + rel_path.replace("/", "-").replace(".", "-")

    lines.append("## Content – changed & added")
    lines.append("")

    if not (changed or added):
        lines.append("_Keine geänderten oder neuen Dateien im Snapshot._")
    else:
        interesting = sorted(changed + added, key=lambda r: r.get("path", ""))
        for row in interesting:
            rel = row.get("path", "")
            status = row.get("status", "")
            category = row.get("category") or "-"
            size_old = row.get("size_old")
            size_new = row.get("size_new")
            delta = row.get("delta")
            md5_flag = row.get("md5_changed")
            if md5_flag is True:
                md5_text = "ja"
            elif md5_flag is False:
                md5_text = "nein"
            else:
                md5_text = "n/a"

            lines.append(f"<a id=\"file-{_anchor_for(rel)}\"></a>")
            lines.append(f"### `{rel}`")
            lines.append(f"- Status: `{status}`")
            lines.append(f"- Kategorie: `{category}`")
            if size_old is not None:
                lines.append(f"- Größe alt: {size_old}")
            if size_new is not None:
                lines.append(f"- Größe neu: {size_new}")
            if delta is not None:
                try:
                    lines.append(f"- Δ Größe: {int(delta):+d}")
                except Exception:
                    lines.append(f"- Δ Größe: {delta}")
            lines.append(f"- MD5 geändert: {md5_text}")
            lines.append("")

            target = (repo_root / rel)
            if status in ("changed", "added") and target.is_file():
                ext = target.suffix.lower()
                lang_map = {
                    ".py": "python",
                    ".rs": "rust",
                    ".ts": "ts",
                    ".tsx": "tsx",
                    ".js": "js",
                    ".json": "json",
                    ".toml": "toml",
                    ".yml": "yaml",
                    ".yaml": "yaml",
                }
                lang = lang_map.get(ext, "")
                fence = f"```{lang}".rstrip()
                lines.append(fence)
                try:
                    content = target.read_text(encoding="utf-8")
                except Exception:
                    try:
                        content = target.read_text(errors="replace")
                    except Exception:
                        content = "[Fehler beim Lesen der Datei]"
                lines.append(content)
                lines.append("```")
            else:
                lines.append("_Inhalt nicht verfügbar (Datei fehlt im Repo)._")

            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def create_delta_merge_from_diff(
    diff_path: Path,
    repo_root: Path,
    merges_dir: Path,
    profile: str = "delta-full",
) -> Path:
    """
    Komfort-Helfer:
      - liest einen vorhandenen Import-Diff
      - parst die Manifest-Tabelle
      - erzeugt einen Delta-Merge-Report

    Rückgabe:
      Pfad zur erzeugten Delta-Merge-Datei.
    """
    text = diff_path.read_text(encoding="utf-8")
    rows = parse_import_diff_table(text)
    return build_delta_merge_report(repo_root, repo_root.name, rows, merges_dir, profile=profile)


if __name__ == "__main__":
    sys.exit(main())

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-wc-merger-wc-merge-delta-schema-json"></a>
### `merger/wc-merger/wc-merge-delta.schema.json`
- Category: config
- Tags: -
- Size: 1.22 KB
- Included: full
- MD5: 155b7dbfd8cf6185fa8472ee279c7ebf

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://heimgewebe.tools/contracts/wc-merge-delta.schema.json",
  "title": "WC Merge Delta",
  "description": "Delta-Contract für WC-Merger: beschreibt Änderungen zwischen zwei Import-Snapshots.",
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "const": "wc-merge-delta"
    },
    "base_import": {
      "type": "string",
      "format": "date-time",
      "description": "Zeitstempel des Basis-Snapshots."
    },
    "current_timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Zeitstempel des aktuellen Snapshots."
    },
    "summary": {
      "type": "object",
      "description": "Aggregierte Delta-Zusammenfassung.",
      "properties": {
        "files_added": {
          "type": "integer",
          "minimum": 0
        },
        "files_removed": {
          "type": "integer",
          "minimum": 0
        },
        "files_changed": {
          "type": "integer",
          "minimum": 0
        }
      },
      "required": ["files_added", "files_removed", "files_changed"]
    }
  },
  "required": ["type", "base_import", "current_timestamp", "summary"],
  "additionalProperties": true
}

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-wc-merger-wc-merge-report-schema-json"></a>
### `merger/wc-merger/wc-merge-report.schema.json`
- Category: config
- Tags: -
- Size: 4.02 KB
- Included: full
- MD5: fd7fd4981baccb5dd65057c18eb749c8

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://heimgewebe.local/schema/wc-merge-report.schema.json",
  "title": "wc-merger Report Contract (wc-merge-report v2.3)",
  "description": "JSON Schema für den maschinenlesbaren Meta-Block (`merge:`) in WC-Merger-Reports (Spec 2.3, Contract `wc-merge-report`).",
  "type": "object",
  "additionalProperties": false,
  "required": ["merge"],
  "properties": {
    "merge": {
      "type": "object",
      "description": "Meta-Informationen zu diesem Merge-Report (Contract `wc-merge-report`).",
      "additionalProperties": true,
      "required": [
        "spec_version",
        "profile",
        "contract",
        "contract_version",
        "plan_only",
        "max_file_bytes",
        "scope",
        "source_repos",
        "path_filter",
        "ext_filter"
      ],
      "properties": {
        "spec_version": {
          "type": "string",
          "description": "Version der WC-Merger-Spezifikation.",
          "const": "2.3"
        },
        "profile": {
          "type": "string",
          "description": "Profil / Detailgrad des Merges.",
          "enum": ["overview", "summary", "dev", "max"]
        },
        "contract": {
          "type": "string",
          "description": "Fester Contract-Name dieses Merge-Typs.",
          "const": "wc-merge-report"
        },
        "contract_version": {
          "type": "string",
          "description": "Version des Merge-Contracts. Entspricht der Spec-Version für v2.3.",
          "const": "2.3"
        },
        "plan_only": {
          "type": "boolean",
          "description": "true = nur Kopf/Plan/Struktur, kein Content-Block."
        },
        "max_file_bytes": {
          "type": "integer",
          "description": "Per-File-Limit in Bytes (0 = kein Limit / „unlimited“).",
          "minimum": 0
        },
        "scope": {
          "type": "string",
          "description": "Menschlich lesbare Beschreibung des Scopes (z. B. `single repo `tools`` oder `3 repos: `wgx`, `metarepo`, …`).",
          "minLength": 1
        },
        "source_repos": {
          "type": "array",
          "description": "Liste der beteiligten Repos (Root-Label), in der Reihenfolge des Merges.",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "path_filter": {
          "description": "Optionaler Pfad-Filter (z. B. `docs/`), ansonsten null.",
          "type": ["string", "null"]
        },
        "ext_filter": {
          "description": "Optionaler Extension-Filter (z. B. [\".md\", \".yml\"]) oder null.",
          "type": ["array", "null"],
          "items": {
            "type": "string",
            "pattern": "^\\.[A-Za-z0-9._-]+$"
          }
        },
        "extras": {
          "type": "object",
          "description": "Aktivierte Zusatzschichten des Super-Mergers.",
          "properties": {
            "health": { "type": "boolean" },
            "organism_index": { "type": "boolean" },
            "fleet_panorama": { "type": "boolean" },
            "augment_sidecar": { "type": "boolean" },
            "delta_reports": { "type": "boolean" }
          },
          "additionalProperties": false
        },
        "health": {
          "type": "object",
          "description": "Health-Report des Repositories.",
          "properties": {
            "status": { "type": "string" },
            "missing": {
              "type": "array",
              "items": { "type": "string" }
            }
          }
        },
        "delta": {
          "type": "object",
          "description": "Delta-Metadaten, wenn Delta-Reports aktiv sind.",
          "additionalProperties": true
        },
        "augment": {
          "type": "object",
          "description": "Augment-Sidecar-Verknüpfung.",
          "properties": {
            "sidecar": {
              "type": ["string", "null"],
              "description": "Pfad zur Augment-Sidecar-Datei (YAML)."
            }
          },
          "additionalProperties": true
        }
      }
    }
  }
}

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-merger-wc-merger-wc-merger-py"></a>
### `merger/wc-merger/wc-merger.py`
- Category: source
- Tags: -
- Size: 43.55 KB
- Included: full
- MD5: 33fb8321cd2a8b3883fc5e816b541bd2

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wc-merger – Working-Copy Merger.
Enhanced AI-optimized reports with strict Pflichtenheft structure.
"""

import sys
import os
import json
import traceback
from pathlib import Path
from typing import List
from importlib.machinery import SourceFileLoader

try:
    import appex  # type: ignore
except Exception:
    appex = None  # type: ignore

# Try importing Pythonista modules
# In Shortcuts-App-Extension werfen diese Importe NotImplementedError.
# Deshalb JEGLICHEN Import-Fehler abfangen, nicht nur ImportError.
try:
    import ui        # type: ignore
except Exception:
    ui = None        # type: ignore

try:
    TF_BORDER_NONE = ui.TEXT_FIELD_BORDER_NONE  # neuere Pythonista-Versionen
except Exception:
    TF_BORDER_NONE = 0  # Fallback: Standardwert, entspricht "kein Rahmen"

try:
    import console   # type: ignore
except Exception:
    console = None   # type: ignore

try:
    import editor    # type: ignore
except Exception:
    editor = None    # type: ignore


def force_close_files(paths: List[Path]) -> None:
    """
    Ensures generated files are not left open in the editor.
    """
    if editor is None:
        return

    try:
        open_files = editor.get_open_files()
    except Exception:
        return

    target_names = {p.name for p in paths}

    for fpath in open_files:
        if os.path.basename(fpath) in target_names:
            try:
                editor.close_file(fpath)
            except Exception:
                pass


# Merger-UI merkt sich die letzte Auswahl in dieser JSON-Datei im Hub:
LAST_STATE_FILENAME = ".wc-merger-state.json"

# Import core logic
try:
    from merge_core import (
        MERGES_DIR_NAME,
        DEFAULT_MAX_BYTES,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
    )
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from merge_core import (
        MERGES_DIR_NAME,
        DEFAULT_MAX_BYTES,
        SKIP_ROOTS,
        detect_hub_dir,
        get_merges_dir,
        scan_repo,
        write_reports_v2,
        _normalize_ext_list,
        ExtrasConfig,
    )

PROFILE_DESCRIPTIONS = {
    # Kurzbeschreibung der Profile für den UI-Hint
    "overview": (
        "Index-Profil: Struktur + Manifest. "
        "Nur README / Runbooks / ai-context mit Inhalt."
    ),
    "summary": (
        "Doku-/Kontext-Profil: Docs, zentrale Config, CI, Contracts voll. "
        "Code größtenteils nur im Manifest."
    ),
    "dev": (
        "Arbeits-Profil: Code, Tests, Config, CI voll. "
        "Doku nur für README/Runbooks/ai-context voll."
    ),
    "max": (
        "Vollsnapshot: alle Textdateien mit Inhalt (bis zum Max-Bytes-Limit pro Datei)."
    ),
}

# Voreinstellungen pro Profil:
# - Split-Größe (Part-Größe): standardmäßig 10 MB, d. h. große Merges
#   werden in mehrere Dateien aufgeteilt – es gibt aber kein Gesamtlimit.
# - Max Bytes/File: 0 = unbegrenzt (volle Dateien), Limit nur,
#   wenn explizit gesetzt.
PROFILE_PRESETS = {
    "overview": {
        # 0 → „kein per-File-Limit“
        "max_bytes": 0,
        "split_mb": 10,
    },
    "summary": {
        "max_bytes": 0,
        "split_mb": 10,
    },
    "dev": {
        "max_bytes": 0,
        "split_mb": 10,
    },
    "max": {
        "max_bytes": 0,
        "split_mb": 10,
    },
}


# --- Helper ---

def find_repos_in_hub(hub: Path) -> List[str]:
    repos: List[str] = []
    if not hub.exists():
        return []
    for child in sorted(hub.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name in SKIP_ROOTS:
            continue
        if child.name == MERGES_DIR_NAME:
            continue
        if child.name.startswith("."):
            continue
        repos.append(child.name)
    return repos

def parse_human_size(text: str) -> int:
    text = text.upper().strip()
    if not text: return 0
    if text.isdigit(): return int(text)

    units = {"K": 1024, "M": 1024**2, "G": 1024**3}
    for u, m in units.items():
        if text.endswith(u) or text.endswith(u+"B"):
            val = text.rstrip(u+"B").rstrip(u)
            try:
                return int(float(val) * m)
            except ValueError:
                return 0
    return 0


def _load_wc_extractor_module():
    """Dynamically load wc-extractor.py from the same directory.

    In Pythonista ist ``__file__`` nicht immer gesetzt (z. B. bei Ausführung
    aus bestimmten UI-/Shortcut-Kontexten). In dem Fall fallen wir auf
    ``sys.argv[0]`` bzw. das aktuelle Arbeitsverzeichnis zurück, statt mit
    einem ``NameError`` abzustürzen.
    """
    from importlib.machinery import SourceFileLoader
    import types
    import sys

    try:
        # Normalfall: __file__ ist definiert.
        script_path = Path(__file__).resolve()
    except NameError:
        # Eingebetteter / Pythonista-Sonderfall.
        candidate = None
        if getattr(sys, "argv", None):
            candidate = sys.argv[0] or None
        if candidate:
            script_path = Path(candidate).resolve()
        else:
            # Fallback – besser ein „best guess“ als ein Crash.
            script_path = Path.cwd() / "wc-merger.py"

    extractor_path = script_path.with_name("wc-extractor.py")
    if not extractor_path.exists():
        return None
    try:
        loader = SourceFileLoader("wc_extractor", str(extractor_path))
        mod = types.ModuleType(loader.name)
        loader.exec_module(mod)
        return mod
    except Exception as exc:
        print(f"[wc-merger] could not load wc-extractor: {exc}")
        return None


# --- UI Class (Pythonista) ---

def run_ui(hub: Path) -> int:
    """Starte den Merger im Vollbild-UI-Modus ohne Pythonista-Titlebar."""
    ui_obj = MergerUI(hub)
    v = ui_obj.view
    # Volle Fläche, eigene „Titlebar“ im View, keine weiße System-Leiste
    v.present('fullscreen', hide_title_bar=True)
    return 0

class MergerUI(object):
    def __init__(self, hub: Path) -> None:
        self.hub = hub
        self.repos = find_repos_in_hub(hub)

        # Pfad zur State-Datei
        self._state_path = (self.hub / LAST_STATE_FILENAME).resolve()

        # Basic argv parsing for UI defaults
        # Expected format: wc-merger.py --level max --mode gesamt ...
        import argparse
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--level", default="dev")
        parser.add_argument("--mode", default="gesamt")
        # 0 = unbegrenzt
        parser.add_argument("--max-bytes", type=int, default=0)
        # Default: ab 10 MB wird gesplittet
        parser.add_argument("--split-size", default="10")
        parser.add_argument("--extras", default="none")
        # Ignore unknown args
        args, _ = parser.parse_known_args()

        # Initiale Extras aus CLI args
        self.extras_config = ExtrasConfig()
        if args.extras and args.extras.lower() != "none":
            for part in args.extras.split(","):
                part = part.strip().lower()
                if hasattr(self.extras_config, part):
                    setattr(self.extras_config, part, True)

        v = ui.View()
        v.name = "WC-Merger"
        v.background_color = "#111111"

        # Vollbild nutzen – die Größe übernimmt dann das fullscreen-Present.
        try:
            screen_w, screen_h = ui.get_screen_size()
            v.frame = (0, 0, screen_w, screen_h)
        except Exception:
            # Fallback, falls get_screen_size nicht verfügbar ist
            v.frame = (0, 0, 1024, 768)
        v.flex = "WH"

        self.view = v

        def _wrap_textfield_in_dark_bg(parent_view, tf):
            """
            Wrapper für Eingabefelder.

            Wichtiger als „perfekt dunkel“ ist hier:
            - Text immer gut lesbar
            - keine weiße Schrift auf weißem Feld

            Darum nutzen wir den systemhellen TextField-Hintergrund
            und erzwingen nur gut sichtbare Schrift / Cursor.
            """

            # System-Hintergrund (hell) beibehalten
            tf.background_color = None
            tf.text_color = "black"        # gut lesbar auf hell
            tf.tint_color = "#007aff"      # Standard-iOS-Blau für Cursor/Markierung

            if hasattr(tf, "border_style"):
                try:
                    tf.border_style = TF_BORDER_NONE
                except Exception:
                    pass

            # Kein extra Hintergrund-View mehr – direkt hinzufügen
            parent_view.add_subview(tf)

        # kleine Helper-Funktion für Dark-Theme-Textfelder
        def _style_textfield(tf: ui.TextField) -> None:
            """Basis-Styling, Wrapper übernimmt das Dunkel-Thema."""
            tf.autocorrection_type = False
            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE

        margin = 10
        y = 10

        # --- TOP HEADER ---
        base_label = ui.Label()
        # etwas Platz rechts für den Close-Button lassen
        base_label.frame = (10, y, v.width - 80, 34)
        base_label.flex = "W"
        base_label.number_of_lines = 2
        base_label.text = f"Base-Dir: {hub}"
        base_label.text_color = "white"
        base_label.background_color = "#111111"
        base_label.font = ("<System>", 11)
        v.add_subview(base_label)
        self.base_label = base_label

        # Close-Button rechts oben – leicht nach innen versetzt,
        # damit er nicht mit iOS-Ecken kollidiert.
        close_btn = ui.Button()
        close_btn.title = "Close"
        # etwas mehr Rand nach rechts: ca. 20pt Abstand
        close_btn.frame = (v.width - 80, y + 3, 60, 28)
        close_btn.flex = "L"
        close_btn.background_color = "#333333"
        close_btn.tint_color = "white"
        close_btn.corner_radius = 4.0
        close_btn.action = self.close_view
        v.add_subview(close_btn)
        self.close_button = close_btn

        y += 40

        repo_label = ui.Label()
        # Platz lassen für „Alle auswählen“-Button rechts
        repo_label.frame = (10, y, v.width - 110, 20)
        repo_label.flex = "W"
        repo_label.text = "Repos (Tap to select – None = All):"
        repo_label.text_color = "white"
        repo_label.background_color = "#111111"
        repo_label.font = ("<System>", 13)
        v.add_subview(repo_label)

        select_all_btn = ui.Button()
        select_all_btn.title = "All"
        select_all_btn.frame = (v.width - 90, y - 2, 80, 24)
        select_all_btn.flex = "L"
        select_all_btn.background_color = "#333333"
        select_all_btn.tint_color = "white"
        select_all_btn.corner_radius = 4.0
        select_all_btn.action = self.select_all_repos
        v.add_subview(select_all_btn)
        self.select_all_button = select_all_btn
        # interner Toggle-Status für den All-Button
        self._all_toggle_selected = False

        y += 22
        top_header_height = y

        # --- BOTTOM SETTINGS & ACTIONS ---
        # Container view for all controls that should stick to the bottom
        # Layout calculation inside the container (starts at y=0)
        cy = 10
        cw = v.width
        # We'll set the container height at the end

        # We need a temporary container to add subviews to, but we'll attach it to v later
        bottom_container = ui.View()
        # Set initial width so subview flex calculations (right margin) work correctly
        bottom_container.frame = (0, 0, cw, 100)
        bottom_container.background_color = "#111111" # Same as v

        ext_field = ui.TextField()
        ext_field.frame = (10, cy, cw - 20, 28)
        ext_field.flex = "W"
        ext_field.placeholder = ".md,.yml,.rs (empty = all)"
        ext_field.text = ""
        _style_textfield(ext_field)
        _wrap_textfield_in_dark_bg(bottom_container, ext_field)
        self.ext_field = ext_field

        cy += 34

        path_field = ui.TextField()
        path_field.frame = (10, cy, cw - 20, 28)
        path_field.flex = "W"
        path_field.placeholder = "Path contains (e.g. docs/ or .github/)"
        _style_textfield(path_field)
        path_field.autocorrection_type = False
        path_field.spellchecking_type = False
        _wrap_textfield_in_dark_bg(bottom_container, path_field)
        self.path_field = path_field

        cy += 36

        # --- Detail: eigene Zeile ---
        detail_label = ui.Label()
        detail_label.text = "Detail:"
        detail_label.text_color = "white"
        detail_label.background_color = "#111111"
        detail_label.frame = (10, cy, 60, 22)
        bottom_container.add_subview(detail_label)

        seg_detail = ui.SegmentedControl()
        seg_detail.segments = ["overview", "summary", "dev", "max"]
        try:
            seg_detail.selected_index = seg_detail.segments.index(args.level)
        except ValueError:
            seg_detail.selected_index = 2  # Default dev
        seg_detail.frame = (70, cy - 2, cw - 80, 28)
        seg_detail.flex = "W"
        # Use standard iOS blue instead of white for better contrast
        seg_detail.tint_color = "#007aff"
        seg_detail.background_color = "#dddddd"
        seg_detail.action = self.on_profile_changed
        bottom_container.add_subview(seg_detail)
        self.seg_detail = seg_detail

        # Kurzer Text unterhalb der Detail-Presets
        self.profile_hint = ui.Label(
            frame=(margin, cy + 28, cw - 2 * margin, 20),
            flex="W",
            text="",
            text_color="white",
            font=("<system>", 12),
        )
        bottom_container.add_subview(self.profile_hint)
        cy += 24 # Platz für Hint

        cy += 36  # neue Zeile für Mode

        # --- Mode: darunter, eigene Zeile ---
        mode_label = ui.Label()
        mode_label.text = "Mode:"
        mode_label.text_color = "white"
        mode_label.background_color = "#111111"
        mode_label.frame = (10, cy, 60, 22)
        bottom_container.add_subview(mode_label)

        seg_mode = ui.SegmentedControl()
        seg_mode.segments = ["combined", "per repo"]
        if args.mode == "pro-repo":
            seg_mode.selected_index = 1
        else:
            seg_mode.selected_index = 0
        seg_mode.frame = (70, cy - 2, cw - 80, 28)
        seg_mode.flex = "W"
        # Same accent color as detail segmented control
        seg_mode.tint_color = "#007aff"
        seg_mode.background_color = "#dddddd"
        bottom_container.add_subview(seg_mode)
        self.seg_mode = seg_mode

        cy += 36

        max_label = ui.Label()
        max_label.text = "Max Bytes/File:"
        max_label.text_color = "white"
        max_label.background_color = "#111111"
        max_label.frame = (10, cy, 120, 22)
        bottom_container.add_subview(max_label)

        max_field = ui.TextField()
        # 0 oder kleiner = „unbegrenzt“ → Feld leer lassen
        if args.max_bytes and args.max_bytes > 0:
            max_field.text = str(args.max_bytes)
        else:
            max_field.text = ""
        max_field.frame = (130, cy - 2, 140, 28)
        max_field.flex = "W"
        max_field.placeholder = "0 / empty = unlimited"
        _style_textfield(max_field)
        max_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        _wrap_textfield_in_dark_bg(bottom_container, max_field)
        self.max_field = max_field

        cy += 36

        split_label = ui.Label()
        # Globale Split-Größe:
        # steuert optional, ob der Merge in mehrere Dateien aufgeteilt wird,
        # ist aber **kein** harter Global-Limit-Cut.
        split_label.text = "Split Size (MB):"
        split_label.text_color = "white"
        split_label.background_color = "#111111"
        split_label.frame = (10, cy, 120, 22)
        bottom_container.add_subview(split_label)

        split_field = ui.TextField()
        # Leer oder 0 = kein Split → ein Merge ohne globales Größenlimit.
        split_field.placeholder = "leer/0 = kein Split"
        split_field.text = args.split_size if args.split_size != "0" else ""
        split_field.frame = (130, cy - 2, 140, 28)
        split_field.flex = "W"
        _style_textfield(split_field)
        split_field.keyboard_type = ui.KEYBOARD_NUMBER_PAD
        _wrap_textfield_in_dark_bg(bottom_container, split_field)
        self.split_field = split_field

        cy += 36

        # --- Plan Only Switch ---
        plan_label = ui.Label()
        plan_label.text = "Plan only:"
        plan_label.text_color = "white"
        plan_label.background_color = "#111111"
        plan_label.frame = (10, cy, 120, 22)
        bottom_container.add_subview(plan_label)

        plan_switch = ui.Switch()
        plan_switch.frame = (130, cy - 2, 60, 32)
        plan_switch.flex = "W"
        plan_switch.value = False
        bottom_container.add_subview(plan_switch)
        self.plan_only_switch = plan_switch

        cy += 36

        info_label = ui.Label()
        info_label.text_color = "white"
        info_label.background_color = "#111111"
        info_label.font = ("<System>", 11)
        info_label.number_of_lines = 1
        info_label.frame = (10, cy, cw - 20, 18)
        info_label.flex = "W"
        bottom_container.add_subview(info_label)
        self.info_label = info_label
        self._update_repo_info()

        # Initiale Anzeige des Hints
        self.on_profile_changed(None)

        cy += 26

        # --- Buttons am unteren Rand (innerhalb des Containers) ---

        cy += 10 # Gap

        small_btn_height = 32

        # --- Extras Button ---
        extras_btn = ui.Button()
        extras_btn.title = "Extras..."
        extras_btn.font = ("<System>", 14)
        extras_btn.frame = (10, cy, cw - 20, small_btn_height)
        extras_btn.flex = "W"
        extras_btn.background_color = "#333333"
        extras_btn.tint_color = "white"
        extras_btn.corner_radius = 6.0
        extras_btn.action = self.show_extras_sheet
        bottom_container.add_subview(extras_btn)

        cy += small_btn_height + 10 # Gap

        # --- Load State Button ---
        load_btn = ui.Button()
        load_btn.title = "Load Last Config"
        load_btn.font = ("<System>", 14)
        load_btn.frame = (10, cy, cw - 20, small_btn_height)
        load_btn.flex = "W"
        load_btn.background_color = "#333333"
        load_btn.tint_color = "white"
        load_btn.corner_radius = 6.0
        load_btn.action = self.restore_last_state
        bottom_container.add_subview(load_btn)

        cy += small_btn_height + 10 # Gap

        # --- Delta Button ---
        delta_btn = ui.Button()
        delta_btn.title = "Delta from Last Import"
        delta_btn.font = ("<System>", 14)
        delta_btn.frame = (10, cy, cw - 20, small_btn_height)
        delta_btn.flex = "W"
        delta_btn.background_color = "#444444"
        delta_btn.tint_color = "white"
        delta_btn.corner_radius = 6.0
        delta_btn.action = self.run_delta_from_last_import
        bottom_container.add_subview(delta_btn)
        self.delta_button = delta_btn

        cy += small_btn_height + 10 # Gap

        # --- Run Button ---
        run_height = 40
        btn = ui.Button()
        btn.title = "Run Merge"
        btn.frame = (10, cy, cw - 20, run_height)
        btn.flex = "W"
        btn.background_color = "#007aff"
        btn.tint_color = "white"
        btn.corner_radius = 6.0
        btn.action = self.run_merge
        bottom_container.add_subview(btn)
        self.run_button = btn

        cy += run_height + 24 # Bottom margin inside container

        container_height = cy

        # Now place the container at the bottom of the main view
        bottom_container.frame = (0, v.height - container_height, v.width, container_height)
        bottom_container.flex = "WT" # Width flex, Top margin flex (stays at bottom)
        v.add_subview(bottom_container)

        # --- REPO LIST ---
        # The list fills the space between header and bottom container
        tv = ui.TableView()

        # Calculate height: available space between top header and bottom container
        list_height = v.height - top_header_height - container_height

        tv.frame = (10, top_header_height, v.width - 20, list_height)
        tv.flex = "WH" # Width flex, Height flex (fills space)
        tv.background_color = "#111111"
        tv.separator_color = "#333333"
        tv.row_height = 32
        tv.allows_multiple_selection = True
        # Improve readability on dark background
        tv.tint_color = "#007aff"

        ds = ui.ListDataSource(self.repos)
        ds.text_color = "white"
        # Bei Auswahl/Deselektion die Statuszeile aktualisieren
        ds.action = self._on_repo_selection_changed
        # deutliche Selektion: kräftiges Blau statt „grau auf schwarz“
        ds.highlight_color = "#0050ff"
        ds.tableview_cell_for_row = self._tableview_cell
        tv.data_source = ds
        tv.delegate = ds
        v.add_subview(tv)
        self.tv = tv
        self.ds = ds

    def _on_repo_selection_changed(self, sender) -> None:
        """Callback des ListDataSource – hält die Info-Zeile in Sync."""
        self._update_repo_info()

    def _update_repo_info(self) -> None:
        """Zeigt unten an, wie viele Repos es gibt und wie viele ausgewählt sind."""
        if not self.repos:
            self.info_label.text = "No repos found in Hub."
            return

        total = len(self.repos)
        tv = getattr(self, "tv", None)
        if tv is None:
            self.info_label.text = f"{total} Repos found."
            return

        rows = tv.selected_rows or []
        if not rows:
            # Semantik „none = all“ steht bereits in der Überschrift über der Liste.
            self.info_label.text = f"{total} Repos found."
        else:
            self.info_label.text = f"{total} Repos found ({len(rows)} selected)."

    def select_all_repos(self, sender) -> None:
        """
        Toggle: nichts → alle ausgewählt, alles ausgewählt → Auswahl löschen.
        Semantik bleibt: „keine Auswahl = alle Repos“, nur die Optik ändert sich.
        """
        if not self.repos:
            return

        tv = self.tv
        rows = tv.selected_rows or []

        if rows and len(rows) == len(self.repos):
            # alles war ausgewählt → Auswahl löschen (zurück zu „none = all“)
            tv.selected_rows = []
        else:
            # explizit alle Zeilen selektieren
            tv.selected_rows = [(0, i) for i in range(len(self.repos))]

        # Info-Zeile aktualisieren
        self._update_repo_info()

    def close_view(self, sender=None) -> None:
        """Schließt den Merger-Screen in Pythonista."""
        try:
            self.view.close()
        except Exception:
            # im Zweifel lieber still scheitern, statt iOS-Alert zu nerven
            pass

    def show_extras_sheet(self, sender):
        """Zeigt ein Sheet zur Konfiguration der Extras."""
        s = ui.View()
        s.name = "Extras"
        s.background_color = "#222222"
        s.frame = (0, 0, 300, 340)

        y = 20
        margin = 20
        w = 300 - 2 * margin

        lbl = ui.Label(frame=(margin, y, w, 40))
        lbl.text = "Optionale Zusatzanalysen\n(Health, Organism, etc.)"
        lbl.number_of_lines = 2
        lbl.text_color = "white"
        lbl.alignment = ui.ALIGN_CENTER
        s.add_subview(lbl)
        y += 50

        # Helper for switches
        def add_switch(key, title):
            nonlocal y
            sw = ui.Switch()
            sw.value = getattr(self.extras_config, key)
            sw.name = key
            # Action: direkt in self.extras_config schreiben
            def action(sender):
                setattr(self.extras_config, key, sender.value)
            sw.action = action
            sw.frame = (w - 60, y, 60, 32)

            l = ui.Label(frame=(margin, y, w - 70, 32))
            l.text = title
            l.text_color = "white"

            s.add_subview(l)
            s.add_subview(sw)
            y += 40

        add_switch("health", "Repo Health Checks")
        add_switch("organism_index", "Organism Index")
        add_switch("fleet_panorama", "Fleet Panorama (Multi-Repo)")
        add_switch("delta_reports", "Delta Reports (wenn Diff verfügbar)")
        add_switch("augment_sidecar", "Augment Sidecar (Playbooks)")

        # Close button
        y += 20
        btn = ui.Button(frame=(margin, y, w, 40))
        btn.title = "Done"
        btn.background_color = "#007aff"
        btn.tint_color = "white"
        btn.corner_radius = 6
        def close_action(sender):
            s.close()
        btn.action = close_action
        s.add_subview(btn)

        s.present("sheet")

    def on_profile_changed(self, sender):
        """
        Aktualisiert den Hint-Text und setzt sinnvolle Defaults
        für max_bytes / split_size basierend auf dem gewählten Profil.

        Wichtig: Pfad- und Extension-Filter bleiben unverändert, damit
        man sie frei kombinieren kann (Profil + eigener Filter).
        """
        idx = self.seg_detail.selected_index
        if not (0 <= idx < len(self.seg_detail.segments)):
            return

        seg_name = self.seg_detail.segments[idx]

        # Hint-Text aktualisieren
        desc = PROFILE_DESCRIPTIONS.get(seg_name, "")
        self.profile_hint.text = desc

        # Presets anwenden (nur max_bytes + split_mb)
        preset = PROFILE_PRESETS.get(seg_name)
        if preset:
            # Max Bytes/File:
            # 0 oder None = unbegrenzt → Feld leer lassen
            max_bytes = preset.get("max_bytes", 0)
            if max_bytes is None or max_bytes <= 0:
                self.max_field.text = ""
            else:
                try:
                    self.max_field.text = str(int(max_bytes))
                except Exception:
                    # Fallback: lieber „unlimited“ als ein falscher Wert
                    self.max_field.text = ""

            # Gesamtlimit (Total Limit / Split = Part-Größe):
            split_mb = preset.get("split_mb")
            # None oder <=0 = kein Split → Feld leer lassen
            if split_mb is None or (
                isinstance(split_mb, (int, float)) and split_mb <= 0
            ):
                self.split_field.text = ""
            else:
                try:
                    self.split_field.text = str(int(split_mb))
                except Exception:
                    self.split_field.text = ""

    # --- State-Persistenz -------------------------------------------------

    def _collect_selected_repo_names(self) -> List[str]:
        """Liest die aktuell in der Liste selektierten Repos aus."""
        # abhängig davon, wie deine TableView/DataSource arbeitet:
        ds = self.ds
        selected: List[str] = []
        if hasattr(ds, "items"):
            # Standard ui.ListDataSource
            rows = getattr(self.tv, "selected_rows", None) or []
            for idx, name in enumerate(ds.items):
                # selected_rows ist eine Liste von Tupeln (section, row)
                if any(r == idx for sec, r in rows):
                    selected.append(name)
        return selected

    def _apply_selected_repo_names(self, names: List[str]) -> None:
        """Setzt die Repo-Auswahl anhand gespeicherter Namen."""
        ds = self.ds
        if not hasattr(ds, "items"):
            return

        name_to_index = {name: i for i, name in enumerate(ds.items)}

        rows = []
        for name in names:
            idx = name_to_index.get(name)
            if idx is not None:
                rows.append((0, idx))

        if not rows:
            return

        tv = self.tv
        try:
            tv.selected_rows = rows
        except Exception:
            # Fallback: nur die erste gefundene Zeile selektieren
            try:
                tv.selected_row = rows[0]
            except Exception:
                pass

    def save_last_state(self) -> None:
        """
        Persistiert den aktuellen UI-Zustand in einer JSON-Datei.

        Speichert die ausgewählten Repositories, Filtereinstellungen, das gewählte Profil,
        sowie weitere relevante UI-Parameter in einer Datei unter `self._state_path`.
        Dies ermöglicht das Wiederherstellen des letzten Zustands beim nächsten Start.
        """
        if not self.repos:
            return

        detail_idx = self.seg_detail.selected_index
        if 0 <= detail_idx < len(self.seg_detail.segments):
            detail = self.seg_detail.segments[detail_idx]
        elif self.seg_detail.segments:
            detail = self.seg_detail.segments[0]
        else:
            detail = ""

        data = {
            "selected_repos": self._collect_selected_repo_names(),
            "ext_filter": self.ext_field.text or "",
            "path_filter": self.path_field.text or "",
            "detail_profile": detail,
            "max_bytes": self.max_field.text or "",
            "split_mb": self.split_field.text or "",
            "plan_only": bool(self.plan_only_switch.value),
            "extras": {
                "health": self.extras_config.health,
                "organism_index": self.extras_config.organism_index,
                "fleet_panorama": self.extras_config.fleet_panorama,
                "delta_reports": self.extras_config.delta_reports,
                "augment_sidecar": self.extras_config.augment_sidecar,
            }
        }
        try:
            self._state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[wc-merger] could not persist state: {exc}")

    def restore_last_state(self, sender=None) -> None:
        try:
            raw = self._state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            if sender: # Nur bei Klick Feedback geben
                if console:
                    console.alert("wc-merger", "No saved state found.", "OK", hide_cancel_button=True)
            return
        except Exception as exc:
            print(f"[wc-merger] could not read state: {exc!r}")
            return

        try:
            data = json.loads(raw)
        except Exception as exc:
            print(f"[wc-merger] invalid state JSON: {exc!r}")
            return

        # Felder setzen
        profile = data.get("detail_profile")
        if profile and profile in self.seg_detail.segments:
            try:
                self.seg_detail.selected_index = self.seg_detail.segments.index(profile)
            except ValueError:
                # If the profile is not found in segments, just skip setting selected_index.
                pass

        self.ext_field.text = data.get("ext_filter", "")
        self.path_field.text = data.get("path_filter", "")
        self.max_field.text = data.get("max_bytes", "")
        self.split_field.text = data.get("split_mb", "")
        self.plan_only_switch.value = bool(data.get("plan_only", False))

        # Restore Extras
        extras_data = data.get("extras", {})
        if extras_data:
            self.extras_config.health = extras_data.get("health", False)
            self.extras_config.organism_index = extras_data.get("organism_index", False)
            self.extras_config.fleet_panorama = extras_data.get("fleet_panorama", False)
            self.extras_config.delta_reports = extras_data.get("delta_reports", False)
            self.extras_config.augment_sidecar = extras_data.get("augment_sidecar", False)

        # Update hint text to match restored profile
        self.on_profile_changed(None)

        selected = data.get("selected_repos") or []
        if selected:
            # Direkt anwenden – ohne ui.delay, das auf manchen Wegen nicht verfügbar ist
            self._apply_selected_repo_names(selected)

        if sender and console:
            # Kurzes Feedback, aber niemals hart failen
            try:
                console.hud_alert("Config loaded")
            except Exception:
                pass

        # Info-Zeile nach dem Wiederherstellen aktualisieren
        self._update_repo_info()


    def _tableview_cell(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.background_color = "#111111"
        if 0 <= row < len(self.repos):
            cell.text_label.text = self.repos[row]
        cell.text_label.text_color = "white"
        cell.text_label.background_color = "#111111"

        selected_bg = ui.View()
        # gut sichtbarer Selected-Hintergrund
        selected_bg.background_color = "#0050ff"
        cell.selected_background_view = selected_bg
        return cell

    def _get_selected_repos(self) -> List[str]:
        tv = self.tv
        rows = tv.selected_rows or []
        if not rows:
            return list(self.repos)
        names: List[str] = []
        for section, row in rows:
            if 0 <= row < len(self.repos):
                names.append(self.repos[row])
        return names

    def _parse_max_bytes(self) -> int:
        txt = (self.max_field.text or "").strip()
        # Leeres Feld → Standard: unbegrenzt (0 = „no limit“)
        if not txt:
            return 0

        # Optional: Eingaben wie "10M", "512K", "1G" akzeptieren
        try:
            val = parse_human_size(txt)
        except Exception:
            val = 0

        # <=0 interpretieren wir bewusst als „kein Limit“
        if val <= 0:
            return 0
        return val

    def _parse_split_size(self) -> int:
        txt = (self.split_field.text or "").strip()
        if not txt:
            return 0
        try:
            # Assume MB if plain number in UI, or allow "1GB"
            if txt.isdigit():
                return int(txt) * 1024 * 1024
            return parse_human_size(txt)
        except Exception:
            return 0

    def run_delta_from_last_import(self, sender) -> None:
        """
        Erzeugt einen Delta-Merge aus dem neuesten Import-Diff im merges-Ordner.
        Nutzt die Delta-Helfer aus wc-extractor.py (falls verfügbar).
        """
        merges_dir = get_merges_dir(self.hub)
        try:
            candidates = list(merges_dir.glob("*-import-diff-*.md"))
        except Exception as exc:
            print(f"[wc-merger] could not scan merges dir: {exc}")
            candidates = []

        if not candidates:
            if console:
                console.alert(
                    "wc-merger",
                    "No import diff found.",
                    "OK",
                    hide_cancel_button=True,
                )
            else:
                print("[wc-merger] No import diff found.")
            return

        # jüngstes Diff wählen
        try:
            diff_path = max(candidates, key=lambda p: p.stat().st_mtime)
        except Exception as exc:
            if console:
                console.alert(
                    "wc-merger",
                    f"Failed to select latest diff: {exc}",
                    "OK",
                    hide_cancel_button=True,
                )
            else:
                print(f"[wc-merger] Failed to select latest diff: {exc}")
            return

        name = diff_path.name
        prefix = "-import-diff-"
        if prefix in name:
            repo_name = name.split(prefix, 1)[0]
        else:
            repo_name = name

        repo_root = self.hub / repo_name
        if not repo_root.exists():
            msg = f"Repo root not found for diff {diff_path.name}"
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[wc-merger] {msg}")
            return

        mod = _load_wc_extractor_module()
        if mod is None or not hasattr(mod, "create_delta_merge_from_diff"):
            msg = "Delta helper (wc-extractor) not available."
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[wc-merger] {msg}")
            return

        try:
            delta_path = mod.create_delta_merge_from_diff(
                diff_path, repo_root, merges_dir, profile="delta-full"
            )
        except Exception as exc:
            msg = f"Delta merge failed: {exc}"
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(f"[wc-merger] {msg}")
            return

        # Eventuell im Editor automatisch geöffnete Dateien wieder schließen
        force_close_files([delta_path])

        msg = f"Delta report: {delta_path.name}"
        if console:
            try:
                console.hud_alert(msg)
            except Exception:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
        else:
            print(f"[wc-merger] {msg}")

    def run_merge(self, sender) -> None:
        try:
            # Aktuellen Zustand merken
            self.save_last_state()
            self._run_merge_inner()
        except Exception as e:
            traceback.print_exc()
            msg = f"Error: {e}"
            if console:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
            else:
                print(msg, file=sys.stderr)

    def _run_merge_inner(self) -> None:
        selected = self._get_selected_repos()
        if not selected:
            if console:
                console.alert("wc-merger", "No repos selected.", "OK", hide_cancel_button=True)
            return

        ext_text = (self.ext_field.text or "").strip()
        extensions = _normalize_ext_list(ext_text)

        path_contains = (self.path_field.text or "").strip() or None

        detail_idx = self.seg_detail.selected_index
        detail = ["overview", "summary", "dev", "max"][detail_idx]

        mode_idx = self.seg_mode.selected_index
        mode = ["gesamt", "pro-repo"][mode_idx]

        max_bytes = self._parse_max_bytes()
        split_size = self._parse_split_size()

        # Plan-only wird aus dem Switch gelesen; falls Switch nicht existiert,
        # bleibt der Modus aus.
        plan_switch = getattr(self, "plan_only_switch", None)
        plan_only = bool(plan_switch and plan_switch.value)

        summaries = []
        for name in selected:
            root = self.hub / name
            if not root.is_dir():
                continue
            summary = scan_repo(root, extensions or None, path_contains, max_bytes)
            summaries.append(summary)

        if not summaries:
            if console:
                console.alert("wc-merger", "No valid repos found.", "OK", hide_cancel_button=True)
            return

        merges_dir = get_merges_dir(self.hub)
        out_paths = write_reports_v2(
            merges_dir,
            self.hub,
            summaries,
            detail,
            mode,
            max_bytes,
            plan_only,
            split_size,
            debug=False,
            path_filter=path_contains,
            ext_filter=extensions or None,
            extras=self.extras_config,
        )

        if not out_paths:
            if console:
                console.alert("wc-merger", "No report generated.", "OK", hide_cancel_button=True)
            else:
                print("No report generated.")
            return

        # Force close any tabs that might have opened
        force_close_files(out_paths)

        msg = f"Generated {len(out_paths)} report(s)."
        if console:
            try:
                console.hud_alert(msg)
            except Exception:
                console.alert("wc-merger", msg, "OK", hide_cancel_button=True)
        else:
            print(f"wc-merger: OK ({msg})")
            for p in out_paths:
                print(f"  - {p.name}")


# --- CLI Mode ---

def _is_headless_requested() -> bool:
    # Headless wenn:
    # 1) --headless Flag, oder
    # 2) WC_HEADLESS=1 in der Umgebung, oder
    # 3) ui-Framework nicht verfügbar
    return ("--headless" in sys.argv) or (os.environ.get("WC_HEADLESS") == "1") or (ui is None)

def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="wc-merger CLI")
    parser.add_argument("paths", nargs="*", help="Repositories to merge")
    parser.add_argument("--hub", help="Base directory (wc-hub)")
    parser.add_argument("--level", choices=["overview", "summary", "dev", "max"], default="dev")
    parser.add_argument("--mode", choices=["gesamt", "pro-repo"], default="gesamt")
    # 0 = unbegrenzt pro Datei
    parser.add_argument("--max-bytes", type=int, default=0)
    parser.add_argument("--split-size", help="Split output into chunks (e.g. 50MB, 1GB)", default="10MB")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--headless", action="store_true", help="Force headless (no Pythonista UI/editor)")
    parser.add_argument("--extras", help="Comma-separated list of extras (health,organism_index,fleet_panorama,delta_reports,augment_sidecar) or 'none'", default="none")

    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    hub = detect_hub_dir(script_path, args.hub)

    sources = []
    if args.paths:
        for p in args.paths:
            path = Path(p)
            if not path.exists():
                path = hub / p
            if path.exists() and path.is_dir():
                sources.append(path)
            else:
                print(f"Warning: {path} not found.")
    else:
        repos = find_repos_in_hub(hub)
        for r in repos:
            sources.append(hub / r)

    if not sources:
        cwd = Path.cwd()
        print(f"No sources in hub ({hub}). Scanning current directory: {cwd}")
        sources.append(cwd)

    print(f"Hub: {hub}")
    print(f"Sources: {[s.name for s in sources]}")

    summaries = []
    for src in sources:
        print(f"Scanning {src.name}...")
        summary = scan_repo(src, None, None, args.max_bytes)
        summaries.append(summary)

    # Default: ab 10 MB wird gesplittet, aber kein Gesamtlimit – es werden
    # beliebig viele Parts erzeugt.
    split_size = 0
    if args.split_size:
        split_size = parse_human_size(args.split_size)
        print(f"Splitting at {split_size} bytes")

    extras_config = ExtrasConfig()
    if args.extras and args.extras.lower() != "none":
        for part in args.extras.split(","):
            part = part.strip().lower()
            if hasattr(extras_config, part):
                setattr(extras_config, part, True)
            else:
                print(f"Warning: Unknown extra '{part}' ignored.")

    merges_dir = get_merges_dir(hub)
    out_paths = write_reports_v2(
        merges_dir,
        hub,
        summaries,
        args.level,
        args.mode,
        args.max_bytes,
        args.plan_only,
        split_size,
        debug=args.debug,
        path_filter=None,
        ext_filter=None,
        extras=extras_config,
    )

    print(f"Generated {len(out_paths)} report(s):")
    for p in out_paths:
        print(f"  - {p}")


def main():
    # UI nur verwenden, wenn wir NICHT als App-Extension laufen und NICHT headless requested ist
    use_ui = (
        ui is not None
        and not _is_headless_requested()
        and (appex is None or not appex.is_running_extension())
    )

    if use_ui:
        try:
            script_path = Path(__file__).resolve()
            hub = detect_hub_dir(script_path)
            return run_ui(hub)
        except Exception as e:
            # Fallback auf CLI (headless), falls UI trotz ui-Import nicht verfügbar ist
            if console:
                try:
                    console.alert(
                        "wc-merger",
                        f"UI not available, falling back to CLI. ({e})",
                        "OK",
                        hide_cancel_button=True,
                    )
                except Exception:
                    pass
            else:
                print(
                    f"wc-merger: UI not available, falling back to CLI. ({e})",
                    file=sys.stderr,
                )
            main_cli()
    else:
        main_cli()

if __name__ == "__main__":
    main()

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-README-md"></a>
### `README.md`
- Category: doc
- Tags: ai-context
- Size: 1.16 KB
- Included: full
- MD5: 95c1304a1cf70a8aa6305bd21bc6a96e

```markdown
# Tools – Index

Kurzüberblick über Ordner:
- `scripts/` – wiederverwendbare Helfer
- `repomerger/` – Repo-Zusammenführungen
- `ordnermerger/` – Ordner-Zusammenführungen

## Nutzung (Beispiele)

Minimale Befehle, um die verfügbaren Werkzeuge aufzurufen:

```bash
bash scripts/jsonl-validate.sh --help
bash scripts/jsonl-tail.sh --help
```

Weitere Details zu den einzelnen Werkzeugen findest du in den jeweiligen README-Dateien oder mittels der `--help`-Optionen.

## JSONL Tools
- `scripts/jsonl-validate.sh` – prüft NDJSON (eine JSON-Entität pro Zeile) gegen ein JSON-Schema (AJV v5).
- `scripts/jsonl-tail.sh`
- `scripts/jsonl-compact.sh`

## Organismus-Kontext

Dieses Repository ist Teil des **Heimgewebe-Organismus**.

Die übergeordnete Architektur, Achsen, Rollen und Contracts sind zentral beschrieben im  
👉 [`metarepo/docs/heimgewebe-organismus.md`](https://github.com/heimgewebe/metarepo/blob/main/docs/heimgewebe-organismus.md)  
👉 [`metarepo/docs/heimgewebe-zielbild.md`](https://github.com/heimgewebe/metarepo/blob/main/docs/heimgewebe-zielbild.md).

Alle Rollen-Definitionen, Datenflüsse und Contract-Zuordnungen dieses Repos
sind dort verankert.

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-scripts-jsonl-compact-sh"></a>
### `scripts/jsonl-compact.sh`
- Category: source
- Tags: script
- Size: 375.00 B
- Included: full
- MD5: 282492c366277ca1a983eac375b7e22a

```bash
#!/usr/bin/env bash
set -euo pipefail
in="${1:-}"; out="${2:-/dev/stdout}"
[[ -n "$in" && -f "$in" ]] || { echo "usage: jsonl-compact.sh <input-file> [output-file]" >&2; exit 2; }
while IFS= read -r ln || [[ -n "$ln" ]]; do
 [[ -n "${ln//[[:space:]]/}" ]] || continue
 printf '%s\n' "$ln" | tr -d '\r' | jq -c . || { echo "bad json line" >&2; exit 1; }
done < "$in" > "$out"

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-scripts-jsonl-tail-sh"></a>
### `scripts/jsonl-tail.sh`
- Category: source
- Tags: script
- Size: 199.00 B
- Included: full
- MD5: 2c26222e41af7e908c1f7a837e5953ba

```bash
#!/usr/bin/env bash
set -euo pipefail
file="${1:-}"
limit="${2:-50}"
[[ -n "$file" && -f "$file" ]] || { echo "usage: jsonl-tail.sh <file> [limit]" >&2; exit 2; }
awk 'NF' "$file" | tail -n "$limit"

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-scripts-jsonl-validate-sh"></a>
### `scripts/jsonl-validate.sh`
- Category: source
- Tags: script
- Size: 3.20 KB
- Included: full
- MD5: adf4b1b63385ab361e3684c270948d2e

```bash
#!/usr/bin/env bash
set -euo pipefail
usage() {
 cat <<USAGE
jsonl-validate.sh

Validates every non-empty line as standalone JSON object against a JSON Schema (draft 2020-12).
Requires: node + npm
USAGE
}
[[ $# -ge 2 ]] || { usage >&2; exit 2; }
PATTERN="$1"; SCHEMA="$2"; shift 2 || true
STRICT=false; FORMATS=true
while [[ $# -gt 0 ]]; do
 case "$1" in
 --strict) STRICT=true ;;
 --no-formats) FORMATS=false ;;
 -h|--help) usage; exit 0 ;;
 *) echo "Unknown flag: $1" >&2; usage >&2; exit 2 ;;
 esac
 shift
done

command -v node >/dev/null || { echo "node required" >&2; exit 127; }
command -v npm >/dev/null || { echo "npm required" >&2; exit 127; }

shopt -s nullglob
mapfile -t FILES < <(compgen -G "$PATTERN" || true)
(( ${#FILES[@]} )) || { echo "no files match: $PATTERN" >&2; exit 1; }

# Setup temporary environment for validation script
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

# Copy schema to work dir to avoid path issues
cp "$SCHEMA" "$WORK_DIR/schema.json"
SCHEMA_PATH="$WORK_DIR/schema.json"

# Create the JS validator script
cat <<'JS' > "$WORK_DIR/validate.js"
const fs = require('fs');
const Ajv2020 = require('ajv/dist/2020');
const addFormats = require('ajv-formats');

const schemaPath = process.argv[2];
const strictMode = process.argv[3] === 'true';
const validateFormats = process.argv[4] === 'true';
const files = process.argv.slice(5);

try {
    const schemaContent = fs.readFileSync(schemaPath, 'utf8');
    const schema = JSON.parse(schemaContent);

    const ajv = new Ajv2020({ allErrors: true, strict: strictMode });
    if (validateFormats) {
        addFormats(ajv);
    }
    const validate = ajv.compile(schema);

    let fails = 0;

    files.forEach(file => {
        console.log("==> " + file);
        try {
            const content = fs.readFileSync(file, 'utf8');
            const lines = content.split('\n');
            lines.forEach((line, index) => {
                if (!line.trim()) return;
                try {
                    const data = JSON.parse(line);
                    const valid = validate(data);
                    if (!valid) {
                        console.error(`::error file=${file},line=${index + 1}::validation failed`);
                        validate.errors.forEach(err => {
                             console.error(`  ${err.instancePath} ${err.message}`);
                        });
                        fails = 1;
                    }
                } catch (e) {
                    console.error(`::error file=${file},line=${index + 1}::invalid json: ${e.message}`);
                    fails = 1;
                }
            });
        } catch (e) {
             console.error(`::error file=${file}::could not read file: ${e.message}`);
             fails = 1;
        }
    });

    process.exit(fails);
} catch (e) {
    console.error("Fatal error:", e);
    process.exit(1);
}
JS

# Install dependencies quietly
pushd "$WORK_DIR" >/dev/null
# Initialize package.json to avoid warnings
echo '{}' > package.json
# Install ajv and ajv-formats
npm install --silent --no-audit --no-fund ajv ajv-formats >/dev/null 2>&1
popd >/dev/null

# Run the validation
NODE_PATH="$WORK_DIR/node_modules" node "$WORK_DIR/validate.js" "$SCHEMA_PATH" "$STRICT" "$FORMATS" "${FILES[@]}"

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-scripts-README-md"></a>
### `scripts/README.md`
- Category: doc
- Tags: ai-context
- Size: 705.00 B
- Included: full
- MD5: 8b5fd3bbea862544e86d1553b30fec6d

```markdown
# JSONL helper scripts

## `jsonl-validate.sh`

Validate a JSON Lines file against a JSON Schema using [`ajv-cli`](https://github.com/ajv-validator/ajv-cli).

```bash
scripts/jsonl-validate.sh schema.json data.jsonl
```

This command will run `npx ajv-cli@5 validate -s schema.json -d data.jsonl` under the hood. Ensure `npx` is available (provided by Node.js) so that the Ajv CLI can be downloaded on demand.

## `jsonl-tail.sh`

Pretty-print the last entries of a JSON Lines file.

```bash
scripts/jsonl-tail.sh [-n <lines>] data.jsonl
```

The default is to display the last 10 entries. Increase or decrease the number of lines with `-n`. Each line is parsed and rendered through `jq` for readability.

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-scripts-wgx-metrics-snapshot-sh"></a>
### `scripts/wgx-metrics-snapshot.sh`
- Category: source
- Tags: script
- Size: 1.74 KB
- Included: full
- MD5: 31a8b111ad533c6d71f66e3b2f564c4b

```bash
#!/usr/bin/env bash
set -euo pipefail
print_json=0
output_path=${WGX_METRICS_OUTPUT:-metrics.json}

usage() {
  cat <<'EOF'
wgx-metrics-snapshot.sh [--json] [--output PATH]
Erzeugt metrics.json (ts, host, updates, backup, drift).
  --json           zusätzlich JSON auf STDOUT
  --output PATH    Ziel-Datei (Default: metrics.json)
EOF
}

while (($#)); do
  case "$1" in
    --json) print_json=1;;
    --output)
      shift; [[ $# -gt 0 ]] || { echo "--output braucht einen Pfad" >&2; exit 1; }
      output_path="$1"
      ;;
    -h|--help) usage; exit 0;;
    *) echo "Unbekannte Option: $1" >&2; usage; exit 1;;
  esac
  shift || true
done

[[ -n "$output_path" ]] || { echo "Der Ausgabe-Pfad darf nicht leer sein" >&2; exit 1; }
outdir="$(dirname "$output_path")"; [[ -d "$outdir" ]] || mkdir -p "$outdir"

ts=$(date +%s)
host=$(hostname)
updates_os=${UPDATES_OS:-0}
updates_pkg=${UPDATES_PKG:-0}
updates_flatpak=${UPDATES_FLATPAK:-0}
age_days=${BACKUP_AGE_DAYS:-1}
# Determine if we have GNU date (supports -d) or BSD/macOS date (supports -v)
if date -d "yesterday" +%F >/dev/null 2>&1; then
  # GNU date
  last_ok=$(date -d "${age_days} day ago" +%F)
else
  # BSD/macOS date
  last_ok=$(date -v-"${age_days}"d +%F)
fi
drift_templates=${DRIFT_TEMPLATES:-0}

json=$(jq -n \
  --arg host "$host" \
  --arg last_ok "$last_ok" \
  --argjson ts "$ts" \
  --argjson uos "$updates_os" \
  --argjson upkg "$updates_pkg" \
  --argjson ufp "$updates_flatpak" \
  --argjson age "$age_days" \
  --argjson drift "$drift_templates" \
  '{
    ts: $ts,
    host: $host,
    updates: { os: $uos, pkg: $upkg, flatpak: $ufp },
    backup: { last_ok: $last_ok, age_days: $age },
    drift: { templates: $drift }
  }')

printf '%s\n' "$json" >"$output_path"
(( print_json )) && printf '%s\n' "$json"

```

[↑ Zurück zum Manifest](#manifest)

<a id="file-tools-tools_augment-yml"></a>
### `tools_augment.yml`
- Category: config
- Tags: -
- Size: 1.96 KB
- Included: full
- MD5: 1d91951e03ce43db6407bb43a757719a

```yaml
# Augment Sidecar for tools repository
# Version: 1.0
# Purpose: Provide additional context and recommendations for AI agents

augment:
  version: 1
  
  # Hotspots: Areas requiring special attention
  hotspots:
    - path: merger/wc-merger/merge_core.py
      reason: "Complex branching logic with multiple profile modes"
      severity: "medium"
      lines: [1000, 1100]
    
    - path: merger/wc-merger/wc-merger.py
      reason: "UI state management and Pythonista-specific code"
      severity: "low"
      lines: [200, 400]
  
  # Suggestions: Architectural recommendations
  suggestions:
    - "Consider extracting profile logic into strategy pattern classes"
    - "Add comprehensive unit tests for health and organism layers"
    - "Document the relationship between merge_core and wc-extractor"
    - "Consider splitting merge_core.py into smaller modules"
  
  # Risks: Known issues or concerns
  risks:
    - "Large merges may exhaust Pythonista memory on iOS"
    - "Multi-part merges need proper header normalization"
    - "Delta reports depend on wc-extractor being available"
  
  # Dependencies: Key external dependencies
  dependencies:
    - name: "Pythonista"
      required: false
      purpose: "iOS UI support"
    
    - name: "wc-extractor"
      required: false
      purpose: "ZIP import and delta generation"
  
  # Priorities: Focus areas for development
  priorities:
    - priority: 1
      task: "Complete all 5 stages of super-merger roadmap"
      status: "in-progress"
    
    - priority: 2
      task: "Add contract validation for all extras"
      status: "pending"
    
    - priority: 3
      task: "Improve test coverage"
      status: "pending"
  
  # Context: Additional information for AI understanding
  context:
    coding_style: "Python 3.7+, type hints, dataclasses"
    architecture: "Generator-based report building for memory efficiency"
    testing: "Manual testing via Pythonista and CLI"
    deployment: "Runs on iOS (Pythonista) and Linux/macOS (CLI)"

```

[↑ Zurück zum Manifest](#manifest)

