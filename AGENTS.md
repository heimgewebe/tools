# Instructions for Agents

## Frontend Feature Parity

This repository maintains two frontends:
1.  **repoLens** (Pythonista UI/CLI) - `merger/lenskit/frontends/pythonista/repolens.py`
2.  **rLens** (Web UI) - `merger/lenskit/frontends/webui/`

**Rule:** Any new feature added to the backend `JobRequest` model (`merger/lenskit/service/models.py`) MUST be implemented in BOTH frontends.

**Verification:**
Always run the parity guard script after modifying the `JobRequest` model or UI components:

```bash
python3 tools/parity_guard.py
```

This script checks for:
*   Backend model definition.
*   CLI arguments in `repolens.py`.
*   HTML IDs in `index.html`.
*   JS payload keys in `app.js`.

See `docs/PARITY_GUARD.md` for details.
