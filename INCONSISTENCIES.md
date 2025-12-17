# Code Inconsistencies Report (Ungereimtheiten)

## Executive Summary

This document identifies code inconsistencies found in the tools repository and provides recommendations for improvements.

## ✅ Resolved Issues

### 1. Massive Code Duplication in Merger Scripts (Resolved)

**Status**: Resolved. The duplicate scripts (`hauski-merger.py`, `wgx-merger.py`, `weltgewebe-merger.py`) have been removed. The current architecture relies on `repolens.py` and `merge_core.py` (v2.4 Standard).

### 2. Silent Exception Handling (Resolved)

**Status**: Resolved. Critical silent `except Exception: pass` blocks in `repolens.py`, `merge_core.py`, and `repolens-extractor.py` have been patched to log warnings to `sys.stderr`.

## ℹ️ Minor Issues

### 3. Unused Shared Library

**Problem**: `merger/ordnermerger/merger_lib.py` and `ordnermerger.py` exist but seem to be legacy artifacts superseded by `merge_core.py`.

**Recommendation**: Consider removing them if no legacy scripts rely on them.

## 📊 Statistics

- **Total duplicate lines**: 0 (Resolved)
- **Silent exception handlers**: Patched critical ones.

## 🎯 Recommended Priorities

### Priority 1: Cleanup Legacy Libraries
- Remove `merger/ordnermerger/` if confirmed unused.
