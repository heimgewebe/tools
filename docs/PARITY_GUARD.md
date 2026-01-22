# Frontend Feature Parity Guard

## Overview
To prevent feature divergence between the WebUI (`rLens`) and Pythonista UI (`repoLens`), we have implemented a mechanized guard. This script ensures that control fields defined in the backend `JobRequest` model are exposed in both frontends.

## The Guard Script
The script is located at `tools/parity_guard.py`.

It checks:
1.  **Backend Model**: Ensures features exist in `JobRequest` (sanity check).
2.  **Pythonista CLI**: Checks `repolens.py` for `argparse` definitions matching the feature.
3.  **Web UI HTML**: Checks `index.html` for input elements with specific IDs.
4.  **Web UI JS**: Checks `app.js` for payload construction including the feature key.

## Usage
Run the script from the repository root:

```bash
python3 tools/parity_guard.py
```

## Adding New Features
When adding a new feature (control) to `JobRequest`:
1.  Add the field to `JobRequest` in `merger/lenskit/service/models.py`.
2.  Add the feature to the `FEATURES` dictionary in `tools/parity_guard.py`.
3.  Run the script. It will fail.
4.  Implement the feature in `repolens.py` (CLI argument + UI logic).
5.  Implement the feature in `index.html` (Input element) and `app.js` (Payload logic).
6.  Run the script again. It should pass.

## CI Integration
This script should be part of the pre-commit checks or CI pipeline to enforce parity.
