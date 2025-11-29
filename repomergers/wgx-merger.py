#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wgx-merger – Ruft die zentrale RepoMerger-Logik mit WGX-spezifischen Konfigurationen auf.
"""

import sys
from pathlib import Path

# Füge das übergeordnete Verzeichnis zum Suchpfad hinzu, um ordnermergers zu finden
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ordnermergers.repomerger_lib import RepoMerger  # noqa: E402


def main():
    """Konfiguriert und startet den Merge-Prozess für WGX."""

    # Spezifische Konfiguration für dieses Repo
    merger = RepoMerger(
        config_name="wgx-merger",
        title="WGX-Merge",
        env_var="WGX_SOURCE",
        merge_prefix="WGX_MERGE_",
        def_basename="wgx"
    )

    # Führe den Merge-Prozess mit den übergebenen Kommandozeilenargumenten aus
    return merger.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
