"""Guard script to prevent accidental stdlib/dependency shadowing.

Fail if well-known dependency names are added to the repository root (e.g.
`fastapi/`, `pydantic/`, `starlette/`). This script can be used in CI to catch
regressions early.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(os.getenv("RLENS_ROOT") or Path(__file__).resolve().parents[1]).resolve()
FORBIDDEN = {"fastapi", "pydantic", "starlette"}


def main() -> int:
    offenders = [name for name in FORBIDDEN if (ROOT / name).exists()]
    if offenders:
        sys.stderr.write(
            "Forbidden shadowing directories present at repo root: "
            + ", ".join(sorted(offenders))
            + "\n"
        )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

