import sys
import os
import types

# Add module path
sys.path.append(os.path.abspath("."))

from merger.lenskit.core import extractor

# Verify function existence
if not hasattr(extractor, "build_delta_meta_from_diff"):
    print("ERROR: build_delta_meta_from_diff not found!")
    sys.exit(1)

print("SUCCESS: Function is defined.")
