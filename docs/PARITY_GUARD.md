# Frontend Feature Parity Guard

The **Parity Guard** (`tools/parity_guard.py`) is a CI tool designed to prevent feature divergence between the backend capabilities and the frontend interfaces.

## Purpose

The `repoLens` system exposes a rich configuration model via `JobRequest` in the backend. It supports two primary frontends:
1.  **WebUI (`rLens`)**: Browser-based interface (`app.js`).
2.  **Pythonista UI (`repoLens`)**: iOS-native script with CLI and UI modes (`repolens.py`).

Historically, new features added to the backend (e.g., `meta_density`, `json_sidecar`) were sometimes forgotten in one of the frontends. This guard ensures that every field in the backend model is explicitly exposed or handled in both frontends.

## How it Works

The script runs as a static analysis tool:

1.  **Source of Truth**: It parses `merger/lenskit/service/models.py` (using Python AST) to extract all fields from the `JobRequest` Pydantic model.
2.  **WebUI Check**: It scans `app.js` using Regex to ensure every field is present as a key in the payload construction (e.g., `json_sidecar: ...`). It heuristically ignores comments to reduce false positives.
3.  **Pythonista Check**: It scans `repolens.py` to ensure:
    *   **CLI Exposure**: `add_argument(...)` exists for the field (checking for robust argument definition variations).
    *   **Logic Usage**: The field variable is actively referenced in the code body (e.g., `args.field` or passing it to core functions), ensuring the flag is not just defined but implemented.

## Rules & Policies

*   **Zero Drift**: The build fails if a backend field is missing in a frontend.
*   **Explicit Mapping**: If a field has a different name or mechanism in a frontend (e.g., `repos` vs `paths` arg), it must be explicitly configured in the `MAPPINGS` dictionary within the script.
*   **Payload vs Derived**:
    *   **WebUI**: Checks for the existence of the *Payload Key* (what is sent to the server). Logic for value derivation is assumed if the key exists.
    *   **Pythonista**: Checks for *CLI Argument* (user input) AND *Code Usage* (implementation).
    *   **json_sidecar**: Treated as a direct payload field in WebUI ("js_key": "json_sidecar") and a CLI flag/usage in Pythonista.

## Usage

Run the guard locally:

```bash
python3 tools/parity_guard.py
```

## Troubleshooting Failures

If the guard fails:

1.  **Missing Field**: Did you add a field to `JobRequest`? Add the corresponding control to `index.html` / `app.js` and `repolens.py` (CLI + Logic).
2.  **False Positive**: Does the feature use a different name in the frontend? Update `MAPPINGS` in `tools/parity_guard.py`.
3.  **Internal Field**: Is the field purely backend-internal (not user-configurable)? Add it to `IGNORE_FIELDS`.
4.  **CLI Argument Not Found**: Ensure you are using `add_argument` and the regex in `tools/parity_guard.py` matches your definition (it handles standard quotes and whitespace).
5.  **Usage Logic Not Found**: Ensure the variable is used in `repolens.py` outside of the argument definition.
