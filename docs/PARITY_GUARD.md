# Frontend Feature Parity Guard

## Overview
To prevent feature divergence between the WebUI (`rLens`) and Pythonista UI (`repoLens`), we have implemented a mechanized guard. This script ensures that control fields defined in the backend `JobRequest` model are exposed in both frontends.

## The Guard Script
The script is located at `tools/parity_guard.py`.

It checks:
1.  **Backend Model**: Ensures features exist in `JobRequest` (sanity check).
2.  **Pythonista CLI (`repolens.py`)**:
    *   Verifies that `argparse` definitions exist for the feature (using robust regex).
    *   Verifies that the argument is actually accessed in the script logic (e.g., `args.my_feature`).
3.  **Web UI HTML (`index.html`)**: Checks for input elements with specific IDs matching the feature.
4.  **Web UI JS (`app.js`)**: Checks for payload construction logic (key assignment) while ignoring comments.

## Feature Definitions
The guard uses a `FEATURES` dictionary to map backend fields to frontend implementation details.
*   **`cli_arg`**: The expected CLI flag (e.g., `--my-feature`).
*   **`repolens_usage`**: The expected variable access (e.g., `args.my_feature`).
*   **`html_id`**: The ID of the input element in HTML.
*   **`js_key`**: The key used in the JSON payload object in `app.js`.

### Special Case: `json_sidecar`
While `json_sidecar` is technically derived from the "extras" string in some contexts, the Parity Guard enforces that it is present as an explicit key in the `app.js` payload object to match the `JobRequest` boolean field. This ensures explicit control.

## Usage
Run the script from the repository root:

```bash
python3 tools/parity_guard.py
```

## Adding New Features
When adding a new feature (control) to `JobRequest`:
1.  Add the field to `JobRequest` in `merger/lenskit/service/models.py`.
2.  Add the feature to the `FEATURES` dictionary in `tools/parity_guard.py` with all required mappings.
3.  Run the script. It will fail.
4.  Implement the feature in `repolens.py` (CLI argument + Usage logic).
5.  Implement the feature in `index.html` (Input element) and `app.js` (Payload logic).
6.  Run the script again. It should pass.

## CI Integration
This script should be part of the pre-commit checks or CI pipeline to enforce parity.
