### 📄 repomergers/hauski-merger.py

**Größe:** 1 KB | **md5:** `3befd8217bebc614134f8b73e2ad1f02`

```python
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
```

### 📄 repomergers/weltgewebe-merger.py

**Größe:** 929 B | **md5:** `677c14353209d8aab6a244dbe5cca274`

```python
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
```

### 📄 repomergers/wgx-merger.py

**Größe:** 889 B | **md5:** `ebe1ef4cef0d3f4246e208070b531373`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wgx-merger – Ruft die zentrale RepoMerger-Logik mit WGX-spezifischen Konfigurationen auf.
"""

import sys
from pathlib import Path

# Füge das übergeordnete Verzeichnis zum Suchpfad hinzu, um ordnermergers zu finden
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ordnermergers.repomerger_lib import RepoMerger

def main():
    """Konfiguriert und startet den Merge-Prozess für WGX."""

    # Spezifische Konfiguration für dieses Repo
    merger = RepoMerger(
        config_name  = "wgx-merger",
        title        = "WGX-Merge",
        env_var      = "WGX_SOURCE",
        merge_prefix = "WGX_MERGE_",
        def_basename = "wgx"
    )

    # Führe den Merge-Prozess mit den übergebenen Kommandozeilenargumenten aus
    return merger.run(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())
```

