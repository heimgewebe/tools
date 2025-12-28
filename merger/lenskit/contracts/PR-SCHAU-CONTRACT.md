# PR-Schau Contract (v1.0)

**Thesis:** PR-Schau must never silently truncate content. It must split or explicitly mark truncation in a machine-readable way.

PR-Schau is a two-layer artifact:
1.  **Index Layer (Small, Fast, Robust):** A JSON sidecar (`bundle.json` conforming to `pr-schau.v1.schema.json`) that acts as the canonical entry point.
2.  **Content Layer (Full, Canonical):** One or more Markdown files (`review.md`, `review_part2.md`, etc.) that contain the actual review content.

## 1. Completeness Policy ("No-Truncate")

To prevent epistemic errors ("hallucination on partial data"), the generator must adhere to the following rules:

*   **No Silent Truncation:** If the content exceeds a single-file limit (e.g., 40KB or 200KB), the generator **MUST NOT** simply cut it off with a text note.
*   **Splitting:** The preferred strategy is to split the content into multiple parts (`review.md`, `review_part2.md`, ...).
*   **Machine-Readable Truth:** The `completeness` block in the JSON Index determines the reliability of the content.

### JSON Completeness Block
```json
"completeness": {
  "is_complete": true,
  "policy": "split",
  "parts": ["review.md", "review_part2.md"],
  "expected_bytes": 150000,
  "emitted_bytes": 150000
}
```

If `is_complete` is `false`, the consumer must treat the review as a **Preview** or **Index**, not as the canonical source of truth.

## 2. Artifacts & Linking

The JSON Index acts as the portable manifest. It links to artifacts using relative `basename` references, allowing the bundle to be moved (e.g., zipped, attached to tickets) without breaking links.

```json
"artifacts": [
  {
    "role": "index_json",
    "basename": "bundle.json",
    "mime": "application/json"
  },
  {
    "role": "canonical_md",
    "basename": "review.md",
    "sha256": "...",
    "mime": "text/markdown"
  },
  {
    "role": "part_md",
    "basename": "review_part2.md",
    "sha256": "...",
    "mime": "text/markdown"
  }
]
```

## 3. Semantic Zones (Markdown)

To facilitate robust parsing of the human-readable Markdown by AI agents, the content should be wrapped in Semantic Zone Markers. These markers are HTML comments that do not affect rendering but provide clear boundaries.

**Syntax:** `<!-- zone:begin type=<type> [attrs...] -->` ... `<!-- zone:end -->`

**Standard Zones:**

*   `summary`: High-level stats (added, removed, changed).
*   `files_manifest`: The list/table of changed files.
*   `diff`: The actual file content diffs or full content.
*   `hotspots`: (Optional) List of critical files.

**Example:**
```markdown
# PR-Review: my-repo

<!-- zone:begin type=summary -->
- **Date:** 2023-10-27T10:00:00Z
- **Stats:** +5 / ~2 / -1
<!-- zone:end -->

<!-- zone:begin type=files_manifest -->
| Path | Status | ...
| ... | ... | ...
<!-- zone:end -->

<!-- zone:begin type=diff -->
### 📝 `src/main.py`
...
<!-- zone:end -->
```

## 4. Versioning

This is **Version 1.0** of the PR-Schau Contract.
Schema URI: `https://heimgewebe.local/schema/pr-schau.v1.schema.json`
