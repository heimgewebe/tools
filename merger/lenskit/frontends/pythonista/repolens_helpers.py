from typing import Dict, Any, Optional, List
from .repolens import normalize_repo_id, normalize_path

def resolve_pool_include_paths(pool_norm: Dict[str, Any], repo_name: str) -> Optional[List[str]]:
    """
    Resolve include paths for a repository from the normalized pool.

    Logic:
    1. Lookup entry by normalized repo name.
    2. If no entry -> None (Global filters apply).
    3. If entry is dict (structured):
       - If compressed has items -> return compressed.
       - If compressed is empty AND raw has items AND _sanitized_dropped flag is True ->
         Fallback to raw (filtered to strings), assuming corruption/sanitization issue.
       - Else -> return None (ALL / Blocked depending on context, but here strictly what's in pool).
         Wait, if compressed is empty list `[]`, we usually want to return `[]` to block.
         If None, we return None (ALL).

    Returns:
        List[str] or None.
    """
    if not pool_norm:
        return None

    entry = pool_norm.get(normalize_repo_id(repo_name))
    if not entry:
        return None

    if isinstance(entry, dict):
        compressed = entry.get("compressed")
        raw = entry.get("raw")
        sanitized_dropped = entry.get("_sanitized_dropped", False)

        # 1. Normal case: compressed has content
        if compressed and len(compressed) > 0:
            return compressed

        # 2. Fallback case: compressed is empty (potentially blocked), BUT raw has content AND we dropped something during sanitization.
        # This heuristics assumes that if we dropped something, the empty compressed might be a result of that data loss
        # rather than user intent to block everything.
        # We also verify raw has valid strings.
        if (compressed is not None and len(compressed) == 0) and (raw and len(raw) > 0) and sanitized_dropped:
            # Filter raw to ensure safety (only strings)
            safe_raw = [p for p in raw if isinstance(p, str)]
            if safe_raw:
                return [normalize_path(p) for p in safe_raw]

        # 3. Explicit Empty/Block or ALL
        # If compressed is [], return []. If None, return None.
        return compressed

    # Legacy fallback (should be handled by deserialize, but safe to keep)
    return entry if isinstance(entry, list) else None
