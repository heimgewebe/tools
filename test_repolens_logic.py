import sys
from pathlib import Path

# Mock UI modules
sys.modules['ui'] = type('MockUI', (), {'View': object, 'Button': object, 'Label': object, 'TableView': object, 'TableViewCell': object, 'ListDataSource': object, 'SegmentedControl': object, 'TextField': object, 'Switch': object})
sys.modules['console'] = type('MockConsole', (), {'alert': print, 'hud_alert': print})
sys.modules['dialogs'] = type('MockDialogs', (), {})

# Mock Core
sys.modules['lenskit.core.merge'] = type('MockCore', (), {
    'MERGES_DIR_NAME': 'merges',
    'PR_SCHAU_DIR': 'pr-schau',
    'SKIP_ROOTS': [],
    'detect_hub_dir': lambda x, y: Path('/tmp/hub'),
    'get_merges_dir': lambda x: Path('/tmp/hub/merges'),
    'scan_repo': lambda *args, **kwargs: {'name': 'repo1', 'files': []},
    'write_reports_v2': lambda *args, **kwargs: type('Artifacts', (), {'get_all_paths': lambda: []})(),
    '_normalize_ext_list': lambda x: x,
    'ExtrasConfig': type('ExtrasConfig', (), {}),
    'parse_human_size': lambda x: 0
})

# Import repolens
# We need to add the path to sys.path
sys.path.append('merger/lenskit/frontends/pythonista')
import repolens
from repolens import normalize_path

# Subclass MergerUI to test logic without UI
class TestUI(repolens.MergerUI):
    def __init__(self):
        self.hub = Path('/tmp/hub')
        self.repos = ['repo1']
        self.ignored_repos = set()
        self._state_path = Path('/tmp/hub/.repoLens-state.json')
        self.extras_config = repolens.ExtrasConfig()

        # Initialize saved selections with structured format
        self.saved_prescan_selections = {}

        # Initialize UI elements mocks
        self.ext_field = type('Obj', (), {'text': ''})()
        self.path_field = type('Obj', (), {'text': ''})()
        self.max_field = type('Obj', (), {'text': ''})()
        self.split_field = type('Obj', (), {'text': ''})()
        self.plan_only_switch = type('Obj', (), {'value': False})()
        self.code_only_switch = type('Obj', (), {'value': False})()
        self.seg_detail = type('Obj', (), {'selected_index': 0, 'segments': ['overview']})()
        self.seg_mode = type('Obj', (), {'selected_index': 0, 'segments': ['combined']})()
        self.tv = type('Obj', (), {'selected_rows': []})()
        self.info_label = type('Obj', (), {'text': ''})()


def test_normalize_path():
    """Test path normalization"""
    assert normalize_path("./src/main.py") == "src/main.py", "Should remove leading ./"
    assert normalize_path("src/dir/") == "src/dir", "Should remove trailing /"
    assert normalize_path("") == ".", "Empty should become ."
    assert normalize_path("/") == "/", "Root should stay /"
    assert normalize_path("  src/main.py  ") == "src/main.py", "Should trim whitespace"
    
    print("✓ test_normalize_path passed")


def test_pool_structured_format():
    """Test structured format with raw and compressed"""
    ui = TestUI()
    repo = "repo1"
    
    # Set structured format
    ui.saved_prescan_selections[repo] = {
        "raw": ["src/main.py", "src/utils.py"],
        "compressed": ["src"]
    }
    
    entry = ui.saved_prescan_selections[repo]
    assert isinstance(entry, dict), "Should be structured dict"
    assert entry["raw"] == ["src/main.py", "src/utils.py"], "Raw should match"
    assert entry["compressed"] == ["src"], "Compressed should match"
    
    print("✓ test_pool_structured_format passed")


def test_pool_all_state():
    """Test ALL state representation"""
    ui = TestUI()
    repo = "repo1"
    
    # ALL state
    ui.saved_prescan_selections[repo] = {"raw": None, "compressed": None}
    
    entry = ui.saved_prescan_selections[repo]
    assert entry["raw"] is None, "Raw should be None for ALL"
    assert entry["compressed"] is None, "Compressed should be None for ALL"
    
    print("✓ test_pool_all_state passed")


def test_serialization_structured():
    """Test serialization preserves structure"""
    ui = TestUI()
    
    # Set up structured pools
    ui.saved_prescan_selections['repo1'] = {"raw": None, "compressed": None}  # ALL
    ui.saved_prescan_selections['repo2'] = {
        "raw": ["src/main.py", "src/utils.py"],
        "compressed": ["src"]
    }
    
    # Serialize
    serialized = ui._serialize_prescan_pool()
    
    assert serialized['repo1'] == {"raw": None, "compressed": None}, "ALL state preserved"
    assert serialized['repo2']['raw'] == ["src/main.py", "src/utils.py"], "Raw preserved"
    assert serialized['repo2']['compressed'] == ["src"], "Compressed preserved"
    
    print("✓ test_serialization_structured passed")


def test_deserialization_legacy():
    """Test deserialization handles legacy formats"""
    ui = TestUI()
    
    # Legacy formats
    legacy_pool = {
        'repo1': None,  # ALL in legacy
        'repo2': ['src/main.py', 'src/utils.py']  # List in legacy
    }
    
    deserialized = ui._deserialize_prescan_pool(legacy_pool)
    
    # Should convert to structured
    assert deserialized['repo1'] == {"raw": None, "compressed": None}, "Legacy None -> structured ALL"
    assert deserialized['repo2']['raw'] == deserialized['repo2']['compressed'], "Legacy list -> both fields"
    
    print("✓ test_deserialization_legacy passed")


def test_deserialization_preserves_both_fields():
    """Test deserialization preserves both raw and compressed"""
    ui = TestUI()
    
    structured_pool = {
        'repo1': {
            "raw": ["src/main.py", "src/utils.py", "docs/README.md"],
            "compressed": ["src", "docs/README.md"]
        }
    }
    
    deserialized = ui._deserialize_prescan_pool(structured_pool)
    
    # Should preserve both fields
    assert len(deserialized['repo1']['raw']) == 3, "Raw should have 3 paths"
    assert len(deserialized['repo1']['compressed']) == 2, "Compressed should have 2 paths"
    
    print("✓ test_deserialization_preserves_both_fields passed")


def test_deserialization_handles_empty_lists():
    """Test deserialization keeps empty lists and filters non-strings"""
    ui = TestUI()

    structured_pool = {
        'repo1': {
            "raw": [],
            "compressed": []
        },
        'repo2': {
            "raw": ["src/main.py", None, 123],
            "compressed": ["docs", {}, "src/utils.py"]
        }
    }

    deserialized = ui._deserialize_prescan_pool(structured_pool)

    assert deserialized['repo1']['raw'] == [], "Empty raw list should stay empty"
    assert deserialized['repo1']['compressed'] == [], "Empty compressed list should stay empty"
    assert deserialized['repo2']['raw'] == ["src/main.py"], "Non-strings should be filtered from raw"
    assert deserialized['repo2']['compressed'] == ["docs", "src/utils.py"], "Non-strings should be filtered from compressed"

    legacy_pool = {
        'repo3': []
    }

    deserialized_legacy = ui._deserialize_prescan_pool(legacy_pool)
    assert deserialized_legacy['repo3']['raw'] == [], "Legacy empty list should stay empty"
    assert deserialized_legacy['repo3']['compressed'] == [], "Legacy empty list should stay empty"

    print("✓ test_deserialization_handles_empty_lists passed")


def test_append_union_both_fields():
    """Test append unions both raw and compressed fields"""
    ui = TestUI()
    repo = "repo1"
    
    # Existing selection
    ui.saved_prescan_selections[repo] = {
        "raw": ["src/main.py"],
        "compressed": ["src/main.py"]
    }
    
    # Simulate append operation
    existing = ui.saved_prescan_selections.get(repo)
    new_raw = ["src/utils.py", "docs/README.md"]
    new_compressed = ["src/utils.py", "docs/README.md"]
    
    if existing and isinstance(existing, dict):
        existing_raw = existing.get("raw") or []
        existing_compressed = existing.get("compressed") or []
        
        merged_raw = set(existing_raw)
        merged_raw.update(new_raw)
        
        merged_compressed = set(existing_compressed)
        merged_compressed.update(new_compressed)
        
        ui.saved_prescan_selections[repo] = {
            "raw": sorted(list(merged_raw)),
            "compressed": sorted(list(merged_compressed))
        }
    
    entry = ui.saved_prescan_selections[repo]
    assert len(entry["raw"]) == 3, "Raw should have 3 paths after union"
    assert len(entry["compressed"]) == 3, "Compressed should have 3 paths after union"
    assert "src/main.py" in entry["raw"], "Should keep original raw"
    assert "src/utils.py" in entry["raw"], "Should add new raw"
    
    print("✓ test_append_union_both_fields passed")


def test_all_plus_partial_equals_all():
    """Test ALL + partial = ALL in append"""
    ui = TestUI()
    repo = "repo1"
    
    # Existing is ALL
    ui.saved_prescan_selections[repo] = {"raw": None, "compressed": None}
    
    # Try to append partial
    existing = ui.saved_prescan_selections.get(repo)
    if existing and isinstance(existing, dict):
        if existing.get("raw") is None and existing.get("compressed") is None:
            # Existing is ALL - keep ALL
            ui.saved_prescan_selections[repo] = {"raw": None, "compressed": None}
    
    entry = ui.saved_prescan_selections[repo]
    assert entry["raw"] is None, "Should remain ALL"
    assert entry["compressed"] is None, "Should remain ALL"
    
    print("✓ test_all_plus_partial_equals_all passed")


def test_fallback_to_raw_when_compressed_empty():
    """Test that deserialization repairs compressed when it becomes empty after filtering"""
    ui = TestUI()
    
    # Test Case 1: compressed filtered to empty, raw has content
    # After deserialization, compressed should be repaired to match raw
    structured_pool = {
        'repo1': {
            "raw": ["src/main.py", "docs/README.md"],
            "compressed": [None, 123, {}]  # All non-strings, will be filtered
        }
    }
    
    deserialized = ui._deserialize_prescan_pool(structured_pool)
    
    # Deserialization should repair: when compressed becomes [] but raw has content,
    # set compressed = raw to preserve user intent
    assert deserialized['repo1']['raw'] == ["src/main.py", "docs/README.md"], "Raw should preserve valid strings"
    assert deserialized['repo1']['compressed'] == ["src/main.py", "docs/README.md"], "Compressed should fallback to raw when filtered to empty"
    
    # Test Case 2: Both empty after filtering - should stay empty (intentional block)
    structured_pool2 = {
        'repo2': {
            "raw": [None, 123],
            "compressed": [{}]
        }
    }
    
    deserialized2 = ui._deserialize_prescan_pool(structured_pool2)
    assert deserialized2['repo2']['raw'] == [], "Raw should be empty after filtering"
    assert deserialized2['repo2']['compressed'] == [], "Compressed should stay empty (intentional block)"
    
    # Test Case 3: Compressed has valid content - should preserve as-is
    structured_pool3 = {
        'repo3': {
            "raw": ["src/main.py", "src/utils.py"],
            "compressed": ["src"]
        }
    }
    
    deserialized3 = ui._deserialize_prescan_pool(structured_pool3)
    assert deserialized3['repo3']['raw'] == ["src/main.py", "src/utils.py"], "Raw should preserve content"
    assert deserialized3['repo3']['compressed'] == ["src"], "Compressed should preserve valid content"
    
    # Test Case 4: Explicitly empty lists (not filtered) - should stay empty
    structured_pool4 = {
        'repo4': {
            "raw": [],
            "compressed": []
        }
    }
    
    deserialized4 = ui._deserialize_prescan_pool(structured_pool4)
    assert deserialized4['repo4']['raw'] == [], "Empty raw should stay empty"
    assert deserialized4['repo4']['compressed'] == [], "Empty compressed should stay empty"
    
    print("✓ test_fallback_to_raw_when_compressed_empty passed")


def run_all_tests():
    """Run all tests"""
    print("Running prescan pool tests with structured format...")
    print()
    
    test_normalize_path()
    test_pool_structured_format()
    test_pool_all_state()
    test_serialization_structured()
    test_deserialization_legacy()
    test_deserialization_preserves_both_fields()
    test_deserialization_handles_empty_lists()
    test_append_union_both_fields()
    test_all_plus_partial_equals_all()
    test_fallback_to_raw_when_compressed_empty()
    
    print()
    print("All tests passed! ✓")


if __name__ == '__main__':
    run_all_tests()
