from typing import NamedTuple, List, Optional, Callable, Dict
import sys
from merger_config import DebugConfig
from merger_model import FileInfo

class DebugItem(NamedTuple):
    level: str  # 'info', 'warning', 'error'
    code: str   # e.g., 'category-unknown'
    context: str  # e.g., filename
    message: str

class DebugCollector:
    """Collects debug information during the merge process."""

    def __init__(self) -> None:
        self.items: List[DebugItem] = []

    def log(self, level: str, code: str, context: str, message: str) -> None:
        self.items.append(DebugItem(level, code, context, message))

    def info(self, code: str, context: str, message: str) -> None:
        self.log("info", code, context, message)

    def warning(self, code: str, context: str, message: str) -> None:
        self.log("warning", code, context, message)

    def error(self, code: str, context: str, message: str) -> None:
        self.log("error", code, context, message)

    def print_summary(self) -> None:
        if not self.items:
            return
        print("\n--- Debug Report ---", file=sys.stderr)
        for item in self.items:
            print(f"[{item.level.upper()}] {item.code} @ {item.context}: {item.message}", file=sys.stderr)
        print("--------------------\n", file=sys.stderr)

# Helper for run_debug_checks
def _debug_log_func(collector: DebugCollector, level: str) -> Callable[[str, str, str], None]:
    if level == "warning":
        return collector.warning
    elif level == "error":
        return collector.error
    elif level == "info":
        return collector.info
    else:
        # 'ignore' or unknown
        return lambda code, ctx, msg: None

DEBUG_CONFIG = DebugConfig() # Default instance

def run_debug_checks(file_infos: List[FileInfo], debug: DebugCollector) -> None:
    """
    Leichte, rein lesende Debug-Checks auf Basis der FileInfos.
    Verändert keine Merge-Logik, liefert nur Hinweise.
    """
    # 1. Unbekannte Kategorien / Tags
    for fi in file_infos:
        ctx = f"{fi.root_label}/{fi.rel_path.as_posix()}"
        cat = fi.category or "other"

        if cat not in DEBUG_CONFIG.allowed_categories:
            # Use configured severity
            log_func = _debug_log_func(debug, DEBUG_CONFIG.unknown_category_level)
            log_func(
                "category-unknown",
                ctx,
                f"Unbekannte Kategorie '{cat}' – erwartet sind {sorted(DEBUG_CONFIG.allowed_categories)}.",
            )

        for tag in getattr(fi, "tags", []) or []:
            if tag not in DEBUG_CONFIG.allowed_tags:
                log_func = _debug_log_func(debug, DEBUG_CONFIG.unknown_tag_level)
                log_func(
                    "tag-unknown",
                    ctx,
                    f"Tag '{tag}' ist nicht im v2.4-Schema registriert.",
                )

    # 2. Fleet-/Heimgewebe-Checks pro Repo
    per_root: Dict[str, List[FileInfo]] = {}
    for fi in file_infos:
        per_root.setdefault(fi.root_label, []).append(fi)

    for root, fis in per_root.items():
        # README-Check
        if not any(f.rel_path.name.lower() == "readme.md" for f in fis):
            debug.info(
                "repo-no-readme",
                root,
                "README.md fehlt – Repo ist für KIs schwerer einzuordnen.",
            )
        # WGX-Profil-Check
        if not any(
            ".wgx" in f.rel_path.parts and str(f.rel_path).endswith("profile.yml")
            for f in fis
        ):
            debug.info(
                "repo-no-wgx-profile",
                root,
                "`.wgx/profile.yml` nicht gefunden – Repo ist nicht vollständig Fleet-konform.",
            )
