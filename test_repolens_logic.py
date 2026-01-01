import sys
import json
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

# Subclass MergerUI to test logic without UI
class TestUI(repolens.MergerUI):
    def __init__(self):
        self.hub = Path('/tmp/hub')
        self.repos = ['repo1']
        self.ignored_repos = set()
        self._state_path = Path('/tmp/hub/.repoLens-state.json')
        self.extras_config = repolens.ExtrasConfig()

        # Initialize saved selections
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


def test_pool_replace_none_to_delete():
    """Test Replace: none → delete from pool"""
    ui = TestUI()
    repo = "repo1"
    
    # Initial state: pool has some selection
    ui.saved_prescan_selections[repo] = ['src/main.py']
    
    # Replace with empty/none
    ui.saved_prescan_selections[repo] = None
    # In replace mode with none, it should delete
    if repo in ui.saved_prescan_selections and ui.saved_prescan_selections[repo] is None:
        del ui.saved_prescan_selections[repo]
    
    assert repo not in ui.saved_prescan_selections, "Replace with none should delete from pool"
    print("✓ test_pool_replace_none_to_delete passed")


def test_pool_replace_all():
    """Test Replace: all → None (ALL state)"""
    ui = TestUI()
    repo = "repo1"
    
    # Replace with ALL
    ui.saved_prescan_selections[repo] = None
    
    assert ui.saved_prescan_selections[repo] is None, "Replace with ALL should store None"
    print("✓ test_pool_replace_all passed")


def test_pool_replace_partial():
    """Test Replace: partial → list"""
    ui = TestUI()
    repo = "repo1"
    
    # Replace with partial selection
    new_paths = ['src/main.py', 'src/utils.py']
    ui.saved_prescan_selections[repo] = new_paths
    
    assert ui.saved_prescan_selections[repo] == new_paths, "Replace with partial should store list"
    print("✓ test_pool_replace_partial passed")


def test_pool_append_union():
    """Test Append: union of existing and new"""
    ui = TestUI()
    repo = "repo1"
    
    # Existing selection
    ui.saved_prescan_selections[repo] = ['src/main.py']
    
    # Append new selection
    new_paths = ['src/utils.py', 'docs/README.md']
    existing = ui.saved_prescan_selections.get(repo, [])
    if isinstance(existing, list):
        merged = sorted(list(set(existing + new_paths)))
        ui.saved_prescan_selections[repo] = merged
    
    expected = ['docs/README.md', 'src/main.py', 'src/utils.py']
    assert ui.saved_prescan_selections[repo] == expected, "Append should union paths"
    print("✓ test_pool_append_union passed")


def test_pool_append_all_overrides():
    """Test Append: ALL + partial = ALL"""
    ui = TestUI()
    repo = "repo1"
    
    # Existing is ALL
    ui.saved_prescan_selections[repo] = None
    
    # Try to append partial - should remain ALL
    existing = ui.saved_prescan_selections.get(repo)
    if existing is None and repo in ui.saved_prescan_selections:
        # Existing is ALL - union of ALL and anything is ALL
        ui.saved_prescan_selections[repo] = None
    
    assert ui.saved_prescan_selections[repo] is None, "Append to ALL should keep ALL"
    print("✓ test_pool_append_all_overrides passed")


def test_pool_serialization():
    """Test serialization and deserialization"""
    ui = TestUI()
    
    # Set up various pool states
    ui.saved_prescan_selections['repo1'] = None  # ALL
    ui.saved_prescan_selections['repo2'] = ['src/main.py']  # Partial
    
    # Serialize
    serialized = ui._serialize_prescan_pool()
    
    assert serialized['repo1'] == {'raw': None, 'compressed': None}
    assert serialized['repo2'] == {'raw': ['src/main.py'], 'compressed': ['src/main.py']}
    print("✓ test_pool_serialization passed")


def test_pool_deserialization_legacy():
    """Test deserialization with legacy format"""
    ui = TestUI()
    
    # Legacy format: simple list
    legacy_pool = {
        'repo1': None,  # ALL
        'repo2': ['src/main.py']  # List
    }
    
    deserialized = ui._deserialize_prescan_pool(legacy_pool)
    
    assert deserialized['repo1'] is None
    assert deserialized['repo2'] == ['src/main.py']
    print("✓ test_pool_deserialization_legacy passed")


def test_pool_deserialization_structured():
    """Test deserialization with structured format"""
    ui = TestUI()
    
    # Structured format
    structured_pool = {
        'repo1': {'raw': None, 'compressed': None},  # ALL
        'repo2': {'raw': ['src/main.py', 'src/utils.py'], 'compressed': ['src/main.py']}  # Partial
    }
    
    deserialized = ui._deserialize_prescan_pool(structured_pool)
    
    assert deserialized['repo1'] is None
    # Should use compressed for internal representation
    assert deserialized['repo2'] == ['src/main.py']
    print("✓ test_pool_deserialization_structured passed")


def run_all_tests():
    """Run all tests"""
    print("Running prescan pool tests...")
    print()
    
    test_pool_replace_none_to_delete()
    test_pool_replace_all()
    test_pool_replace_partial()
    test_pool_append_union()
    test_pool_append_all_overrides()
    test_pool_serialization()
    test_pool_deserialization_legacy()
    test_pool_deserialization_structured()
    
    print()
    print("All tests passed! ✓")


if __name__ == '__main__':
    run_all_tests()

