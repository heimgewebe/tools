# 2. LensKit Architecture & Semantic Refactoring

Date: 2025-05-15

## Status

Accepted

## Context

The folder name `repoLens` became semantically too narrow as the system evolved from a pure repository merger to a project, context, and topology instrument (Atlas, FS-Resolver, Metarepo-Sync). The name pulled mental models back to "single repo" thinking.

Functionally, the code was already modular but lacked a semantic boundary to prevent logic duplication between the local Pythonista path and the Service Web-UI path.

## Decision

We renamed the project structure to `lenskit` to serve as a semantic umbrella.

1.  **lenskit** is the system core.
2.  **repoLens** and **rLens** are perspectives (frontends) on it.

### Structural Changes

The directory `merger/repoLens` is refactored into `merger/lenskit` with the following structure:

```
merger/
└── lenskit/              # Semantic Root
    ├── core/             # Core logic (scanning, merging, evaluating)
    ├── adapters/         # Adapters (FS, Metarepo, Atlas, Security)
    ├── contracts/        # Schemas
    ├── cli/              # rLens CLI wrapper
    ├── service/          # Service Application (Web/API)
    └── frontends/
        ├── pythonista/   # Local UI & Tools (repolens.py)
        └── webui/        # Browser UI Assets
```

### Core Principles

1.  **Core-First Rule**: Any logic that scans, merges, syncs, or evaluates MUST live in `core/` or `adapters/`. Frontends (Pythonista, Web-UI) only orchestrate.
2.  **Two Frontends, One Core**:
    *   **Pythonista**: Provides path selection, local config, trigger. Uses `core/*` directly.
    *   **Web-UI**: Uses the same `core` but via HTTP transport and Job/State management.
3.  **No Logic Duplication**: Business logic is strictly forbidden in frontend layers.

## Consequences

*   **Imports**: All imports must now reference `lenskit.*`.
*   **Mental Model**: Developers (and AI agents) now distinguish between the Kit (functionality) and the Lens (View/Tool).
*   **Maintenance**: Reduces risk of feature drift between local and service versions.
