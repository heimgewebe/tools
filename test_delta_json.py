import sys
import os
from pathlib import Path
import json
import types

# Add module path
sys.path.append("merger")

# Import extractor from lenskit
try:
    from lenskit.core import extractor as repolens_extractor
except ImportError as e:
    print(f"ERROR: Could not import lenskit.core.extractor: {e}")
    sys.exit(1)

# Verify function existence
if not hasattr(repolens_extractor, "build_delta_meta_from_diff"):
    print("ERROR: build_delta_meta_from_diff not found!")
    sys.exit(1)

print("SUCCESS: Function is defined.")
