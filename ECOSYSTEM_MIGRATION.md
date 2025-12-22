# Migration Guide: repoLens -> lenskit

The `merger/repoLens` folder has been renamed to `merger/lenskit` to reflect the new architecture.
This change affects the `heimgewebe` ecosystem. Since `tools` is a fleet repository, other repositories might rely on its structure.

## Changes

*   **Old Path:** `merger/repoLens`
*   **New Path:** `merger/lenskit`
*   **CLI Entry Point:** `merger/lenskit/cli/rlens.py` (formerly `repolens.py` or `service/rlens.py`)
*   **Core Logic:** `merger/lenskit/core/merge.py` (formerly `merge_core.py`)
*   **Security:** `merger/lenskit/adapters/security.py` (formerly `service/security.py`)

## Check List for Ecosystem Repositories

Please check the following locations in `metarepo`, `wgx`, `hausKI`, etc.:

### 1. CI Workflows (`.github/workflows/`)

Grep for `merger/repoLens` in your workflows. Common patterns:

```yaml
# OLD
- name: Run repoLens
  run: python3 merger/repoLens/repolens.py ...

# NEW
- name: Run repoLens (LensKit)
  run: python3 merger/lenskit/cli/rlens.py ...
```

### 2. Scripts and Makefiles

Check `scripts/` or `Makefile` / `Justfile` for hardcoded paths.

```bash
# OLD
RLENS_DIR="$HOME/repos/tools/merger/repoLens"

# NEW
RLENS_DIR="$HOME/repos/tools/merger/lenskit"
```

### 3. Documentation

Update links in `README.md` or `docs/`.

*   Link to spec: `merger/lenskit/repoLens-spec.md`
*   Link to schemas: `merger/lenskit/contracts/*.json`

### 4. Metarepo Configuration

If `metarepo` defines sync rules for `repoLens`, update the source paths in `metarepo/sync/tools.yml` (or similar).

### 5. AI Context Files (`.ai-context.yml`)

If `.ai-context.yml` mentions `repoLens` as a tool path, update it.

## Verification

After updating, run the `guard` task in the respective repo to ensure no broken links or script errors.
