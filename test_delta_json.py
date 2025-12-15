import sys
import os
from pathlib import Path
import json
from importlib.machinery import SourceFileLoader
import types

# Add module path
sys.path.append("merger/wc-merger")

# Mock merge_core to avoid dependencies
mock_core = types.ModuleType("merge_core")
mock_core.detect_hub_dir = lambda x, y=None: Path(".")
mock_core.get_merges_dir = lambda x: Path("merges")
mock_core.get_repo_snapshot = lambda x: {}
sys.modules["merge_core"] = mock_core

# Load wc-extractor.py
loader = SourceFileLoader("wc_extractor", "merger/wc-merger/wc-extractor.py")
wc_extractor = types.ModuleType(loader.name)
loader.exec_module(wc_extractor)

# Verify function existence
if not hasattr(wc_extractor, "build_delta_meta_from_diff"):
    print("ERROR: build_delta_meta_from_diff not found!")
    sys.exit(1)

print("SUCCESS: Function is defined.")
