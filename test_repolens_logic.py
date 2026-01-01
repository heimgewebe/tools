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

        # Initialize saved selections (mimicking what we want to implement)
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

    # Override save/restore to use memory or temp file
    # ... uses self._state_path which is mocked.

# Test Append Logic
def test_append():
    ui = TestUI()

    # Simulating "Append" logic which is currently MISSING in repolens.py
    # We want to add it.

    repo = "repo1"

    # 1. First Selection: ['src/main.py']
    selection1 = ['src/main.py']

    # We need a method to "Apply" selection to the pool.
    # Currently repolens.py only has `_temp_include_paths`.

    # Proposed change: ui.apply_prescan_selection(repo, new_paths, append=True)

    pass
