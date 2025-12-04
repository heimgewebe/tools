# Code Inconsistencies Report (Ungereimtheiten)

## Executive Summary

This document identifies code inconsistencies found in the tools repository and provides recommendations for improvements.

## 🔴 Critical Issues

### 1. Massive Code Duplication in Merger Scripts

**Problem**: Three nearly identical merger scripts contain 30+ duplicate functions:
- `repomerger/hauski-merger.py` (708 lines)
- `repomerger/weltgewebe-merger.py` (662 lines)  
- `repomerger/wgx-merger.py` (710 lines)

**Duplicated Functions**:
- Utility functions: `human()`, `_deurl()`, `ensure_dir()`, `safe_is_dir()`
- File operations: `is_text_file()`, `lang_for()`, `file_md5()`
- Config handling: `load_config()`, `cfg_get_int()`, `cfg_get_str()`
- Analysis: `classify_category()`, `summarize_ext()`, `summarize_cat()`
- Merge operations: `write_tree()`, `parse_manifest()`, `build_diff()`, `keep_last_n()`
- Main logic: `do_merge()`, `extract_source_path()`, `main()`, `_safe_main()`

**Impact**:
- **~2100 lines** of duplicated code across 3 files
- Bug fixes must be applied to 3 different locations
- High risk of divergence and maintenance issues
- Identical functions have minor formatting differences (e.g., `weltgewebe-merger.py` uses compressed syntax)

**Existing Solution**:
The repository already has shared libraries:
- `ordnermerger/merger_lib.py` - contains utility functions
- `ordnermerger/repomerger_lib.py` - contains `RepoMerger` class with shared logic

**Recommendation**:
Refactor the three scripts to use the `RepoMerger` class and shared utilities, keeping only configuration-specific code.

### 2. Silent Exception Handling

**Problem**: Multiple locations use `except: pass` or `except Exception: pass`, silently swallowing errors.

**Locations**:

`hauski-merger.py`:
- Line 184-185: `find_dir_by_basename()` - silently ignores search errors
- Line 278-279: `find_dir_by_basename()` - silently ignores rglob errors  
- Line 378-379: `parse_manifest()` - silently ignores file parsing errors
- Line 417-418: `keep_last_n()` - silently ignores file deletion errors

`wgx-merger.py`:
- Line 184-185: `find_dir_by_basename()` - silently ignores search errors
- Line 278-279: `find_dir_by_basename()` - silently ignores rglob errors
- Line 378-379: `parse_manifest()` - silently ignores file parsing errors
- Line 417-418: `keep_last_n()` - silently ignores file deletion errors

`weltgewebe-merger.py`:
- Line 171-172: `load_config()` - silently ignores config read errors
- Line 261-262: `find_dir_by_basename()` - silently ignores rglob errors
- Line 332-333: `parse_manifest()` - silently ignores file parsing errors

`repomerger.py`:
- Line 679-680: `safe_delete_source()` - silently ignores resolution errors

**Impact**:
- Debugging is extremely difficult when errors are hidden
- Users don't know when operations fail
- Silent failures can lead to data loss or corruption

**Recommendation**:
Replace with proper error handling:
```python
# Instead of:
except Exception:
    pass

# Use:
except OSError as e:
    print(f"Warning: Failed to read config: {e}", file=sys.stderr)
except Exception as e:
    print(f"Unexpected error: {e}", file=sys.stderr)
```

### 3. Inconsistent Code Style in Duplicates

**Problem**: The same function has different formatting across files.

**Example - `human()` function**:

`merger_lib.py` (well-formatted):
```python
def human(n: int) -> str:
    """Konvertiert Bytes in ein menschenlesbares Format (KB, MB, ...)."""
    u = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(u) - 1:
        f /= 1024
        i += 1
    return f"{f:.2f} {u[i]}"
```

`weltgewebe-merger.py` (compressed):
```python
def human(n: int) -> str:
    u=["B","KB","MB","GB","TB"]; f=float(n); i=0
    while f>=1024 and i<len(u)-1: f/=1024; i+=1
    return f"{f:.2f} {u[i]}"
```

**Impact**: Inconsistent code style makes the codebase harder to read and maintain.

## ⚠️ Medium Issues

### 4. Unused Shared Library

**Problem**: `ordnermerger/repomerger_lib.py` contains a `RepoMerger` class designed for code reuse, but the three merger scripts don't use it.

**Impact**: The architecture is confusing - shared code exists but isn't used.

### 5. Inconsistent Import Patterns

**Problem**: Some files use relative imports, others use absolute imports.

`ordnermerger/repomerger_lib.py` (line 14):
```python
from . import merger_lib as ml
```

vs. standalone scripts that duplicate everything.

**Recommendation**: Establish consistent import guidelines.

## ℹ️ Minor Issues

### 6. Missing Variable Protection in Bash Scripts

**Problem**: Some bash scripts don't use `set -u` to catch undefined variables.

**Files**:
- ✓ `scripts/jsonl-validate.sh` - has `set -euo pipefail` (good!)
- ✗ `scripts/jsonl-tail.sh` - has `set -euo pipefail` but uses `${2:-50}` (actually safe)
- ✗ `scripts/jsonl-compact.sh` - has `set -euo pipefail` (good!)
- ✗ `scripts/wgx-metrics-snapshot.sh` - has `set -euo pipefail` (good!)

**Update**: After closer inspection, all scripts actually have proper error handling with `set -euo pipefail`. The earlier analysis was incorrect.

### 7. Documentation Inconsistencies

**Problem**: The three merger scripts have detailed docstrings, but they're nearly identical with minor variations in examples.

## 📊 Statistics

- **Total duplicate lines**: ~2100 lines across 3 files
- **Number of duplicate functions**: 30+
- **Silent exception handlers**: 11 locations
- **Files affected**: 7 Python files, 4 bash scripts

## 🎯 Recommended Priorities

### Priority 1: Fix Silent Exception Handling (Quick Win)
- **Effort**: Low (1-2 hours)
- **Impact**: High (improves debuggability immediately)
- Replace all `except: pass` with proper logging

### Priority 2: Document Current State (Quick Win)  
- **Effort**: Low (30 minutes)
- **Impact**: Medium (helps future maintainers)
- Add this findings document to the repository

### Priority 3: Refactor to Use Shared Library (Long-term)
- **Effort**: High (1-2 days)
- **Impact**: Very High (eliminates ~2000 lines of duplication)
- Refactor merger scripts to use `RepoMerger` class
- This is a larger architectural change requiring careful testing

### Priority 4: Add Tests (Long-term)
- **Effort**: High (ongoing)
- **Impact**: High (prevents regressions)
- Add unit tests for shared library functions
- Add integration tests for merger scripts

## 🔧 Immediate Action Items

1. **Add better error handling** to all `except: pass` blocks
2. **Document this analysis** in the repository
3. **Create follow-up issues** for the refactoring work
4. **Add code review guidelines** to prevent future duplication

## Conclusion

The codebase is functional but suffers from significant code duplication. The good news is that shared libraries already exist (`merger_lib.py`, `repomerger_lib.py`) - they just need to be utilized. The most urgent issue is the silent exception handling, which should be fixed immediately to improve debuggability.
