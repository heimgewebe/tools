#!/usr/bin/env python3
"""
Compatibility shim.

repolens_service.py was renamed to repolensd.py.
Keep this file to avoid breaking existing scripts and docs.
"""
from __future__ import annotations

import sys

from repolensd import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
