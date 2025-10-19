#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
weltgewebe-merger – Ruft die zentrale RepoMerger-Logik mit Gewebe-spezifischen Konfigurationen auf.
"""

import sys
from pathlib import Path

# Füge das übergeordnete Verzeichnis zum Suchpfad hinzu, um ordnermergers zu finden
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ordnermergers.repomerger_lib import RepoMerger

def main():
    """Konfiguriert und startet den Merge-Prozess für Weltgewebe."""

    # Spezifische Konfiguration für dieses Repo
    merger = RepoMerger(
        config_name  = "weltgewebe-merger",
        title        = "Gewebe-Merge",
        env_var      = "GEWEBE_SOURCE",
        merge_prefix = "GEWEBE_MERGE_",
        def_basename = "weltgewebe"
    )

    # Führe den Merge-Prozess mit den übergebenen Kommandozeilenargumenten aus
    return merger.run(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())
