#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
hauski-merger – Ruft die zentrale RepoMerger-Logik mit Hauski-spezifischen Konfigurationen auf.
"""

import sys
from pathlib import Path

# Füge das übergeordnete Verzeichnis zum Suchpfad hinzu, um ordnermergers zu finden
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ordnermergers.repomerger_lib import RepoMerger

def main():
    """Konfiguriert und startet den Merge-Prozess für Hauski."""

    # Spezifische Konfiguration für dieses Repo
    merger = RepoMerger(
        config_name  = "hauski-merger",
        title        = "Hauski-Merge",
        env_var      = "HAUSKI_SOURCE",
        merge_prefix = "HAUSKI_MERGE_",
        def_basename = "hauski"
    )

    # Führe den Merge-Prozess mit den übergebenen Kommandozeilenargumenten aus
    # sys.exit wird innerhalb von run() nicht aufgerufen, daher fangen wir den Rückgabewert ab
    return merger.run(sys.argv[1:])

if __name__ == "__main__":
    # Beende das Skript mit dem entsprechenden Exit-Code
    sys.exit(main())
