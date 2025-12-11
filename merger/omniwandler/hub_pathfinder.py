#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hub_pathfinder – schreibt den echten wandler-hub Pfad in die OmniWandler-Konfiguration.

Nutzung (Pythonista):
1. Kopiere dieses Script in den gewünschten Hub-Ordner (z. B. wandler-hub).
2. Öffne es in Pythonista und führe es aus.
3. Danach liest omniwandler.py beim Start den exakt gleichen Pfad.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import console  # type: ignore
except ImportError:
    console = None


def safe_script_dir() -> Path:
    """Ermittelt robust das Verzeichnis, in dem dieses Script liegt."""
    try:
        return Path(__file__).resolve().parent
    except NameError:
        argv0 = sys.argv[0] if sys.argv else None
        if argv0:
            return Path(argv0).resolve().parent
        return Path.cwd()


def main() -> None:
    script_dir = safe_script_dir()

    # Konfig-Pfad exakt wie in omniwandler.py
    home = Path.home()
    cfg_dir = home / ".config" / "omniwandler"
    cfg_path = cfg_dir / "hub-path.txt"

    cfg_dir.mkdir(parents=True, exist_ok=True)

    # Wir schreiben den absoluten Pfad des aktuellen Verzeichnisses
    hub_path = script_dir.resolve()
    cfg_path.write_text(str(hub_path), encoding="utf-8")

    msg_lines = [
        "=== OmniWandler Hub-Pathfinder ===",
        "",
        "Dieses Script liegt bei:",
        f"  {script_dir}",
        "",
        "Geschriebene Konfiguration:",
        f"  {cfg_path}",
        "",
        "Inhalt von hub-path.txt:",
        f"  {hub_path}",
        "",
        "Beim nächsten Start wird omniwandler.py diesen Pfad",
        "als wandler-hub verwenden (falls OMNIWANDLER_HUB nicht gesetzt ist).",
        "",
        "=== Ende ===",
    ]

    text = "\n".join(msg_lines)

    # Ausgabe in Pythonista-Konsole und optional als HUD
    print(text)
    if console is not None:
        try:
            console.clear()
        except Exception:
            pass
        console.set_color(1, 1, 1)
        print(text)
        try:
            console.hud_alert("Hub-Pfad gespeichert", "success", 1.2)
        except Exception:
            pass


if __name__ == "__main__":
    main()
