#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import os
import sys

try:
    import console  # type: ignore
except Exception:
    console = None  # type: ignore


def safe_script_path() -> Path:
    try:
        return Path(__file__).resolve()
    except Exception:
        # letzte Rettung: aktuelles Verzeichnis
        return Path.cwd().resolve() / "repolens-hub-pathfinder.py"


def find_repolens_dirs(home: Path) -> list[Path]:
    """
    Heuristik: typische Install-Orte in Pythonista.
    Wir schreiben den Pfad in jedes gefundene repoLens-Verzeichnis.
    """
    candidates = [
        home / "merger" / "repoLens",
        home / "repoLens",
        home / "wc-merger",
        home / "merger" / "wc-merger",
    ]

    found: list[Path] = []
    for d in candidates:
        try:
            if d.is_dir():
                # repoLens lässt sich meist über repolens.py erkennen
                if (d / "repolens.py").exists() or (d / "repolens_app.py").exists():
                    found.append(d)
                else:
                    # notfalls trotzdem aufnehmen, wenn es "repoLens" heißt
                    if d.name.lower() == "repolens":
                        found.append(d)
        except Exception:
            pass

    # Duplikate entfernen, Reihenfolge behalten
    uniq: list[Path] = []
    for d in found:
        if d not in uniq:
            uniq.append(d)
    return uniq


def write_pathfile(target_dir: Path, hub_dir: Path) -> tuple[bool, str]:
    out_file = target_dir / ".repolens-hub-path.txt"
    try:
        out_file.write_text(str(hub_dir), encoding="utf-8")
        return True, str(out_file)
    except Exception as e:
        return False, f"{out_file} -> {e}"


def main() -> int:
    script_path = safe_script_path()
    hub_dir = script_path.parent.resolve()  # <- das ist der ganze Trick

    if not hub_dir.is_dir():
        msg = f"Not a directory (script parent): {hub_dir}"
        print(msg)
        if console:
            console.alert("repoLens hub pathfinder", msg, "OK", hide_cancel_button=True)
        return 2

    home = Path(os.path.expanduser("~")).resolve()

    # 1) immer in den Hub selbst schreiben
    ok_hub, info_hub = write_pathfile(hub_dir, hub_dir)

    # 2) zusätzlich in repoLens-Verzeichnisse schreiben (falls gefunden)
    repolens_dirs = find_repolens_dirs(home)
    results = []
    for d in repolens_dirs:
        ok, info = write_pathfile(d, hub_dir)
        results.append((ok, info))

    lines = []
    lines.append(f"Hub detected as script folder:\n{hub_dir}\n")
    lines.append("Written files:")

    lines.append(f"- HUB: {'OK' if ok_hub else 'FAIL'}  {info_hub}")

    if repolens_dirs:
        for (d, (ok, info)) in zip(repolens_dirs, results):
            lines.append(f"- repoLens @ {d}: {'OK' if ok else 'FAIL'}  {info}")
    else:
        lines.append("- repoLens: (not found automatically)")

    msg = "\n".join(lines)
    print(msg)

    if console:
        console.alert("repoLens hub pathfinder", msg, "OK", hide_cancel_button=True)

    # Wenn der Hub-Eintrag schon nicht geht, ist es wirklich kaputt.
    return 0 if ok_hub else 3


if __name__ == "__main__":
    raise SystemExit(main())
