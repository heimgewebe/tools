# Frontend Feature Parity Guard

## Issue
To prevent feature divergence between the WebUI (`rLens`) and Pythonista UI (`repoLens`), we need a mechanized way to ensure that all controls available in the backend `JobRequest` model are exposed in the frontends.

## Current State
A normative section "Frontend Feature Parity" has been added to `repoLens-spec.md`. However, this is a text-based contract and does not enforce compliance automatically.

## Proposed Solution (CI Guard)
Implement a CI step (e.g., Python script) that:
1.  Introspects the `JobRequest` Pydantic model in `merger/lenskit/service/models.py`.
2.  Parses the WebUI HTML/JS (`index.html`, `app.js`) to find corresponding input fields/payload keys.
3.  Fails the build if a field in `JobRequest` is missing from the frontend implementation.

## Example Checks
*   **Backend:** `JobRequest.meta_density` exists.
*   **Frontend:** `document.getElementById('metaDensity')` must exist in `index.html`.
*   **Frontend:** Payload construction in `app.js` must include `meta_density`.

## Priority
High - to be implemented in the next maintenance cycle.
