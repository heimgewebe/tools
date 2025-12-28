
import re
import pytest
import shutil
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path to allow importing lenskit
# Matches existing test pattern: merger/lenskit/tests -> ../.. -> merger/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    import yaml
except ImportError:
    yaml = None

from lenskit.core import merge
from lenskit.core.merge import FileInfo, ExtrasConfig

class ReportParser:
    """
    A minimal parser to verify machine-readability of repoLens reports.
    """
    def __init__(self, content: str):
        self.content = content
        self.zones = []
        self.artifacts = []
        self.file_markers = []
        self.meta = {}
        self._parse()

    def _parse(self):
        # 1. Parse Zones
        # Regex for <!-- zone:begin type=... attrs... -->
        # We find all begin markers and match with end markers (nested zones not supported in this simple parser)
        zone_pattern = re.compile(r'<!-- zone:begin type=(\w+)(.*?) -->', re.DOTALL)
        # End pattern should match type if present
        end_pattern = re.compile(r'<!-- zone:end(?:\s+type=(\w+))? -->')

        pos = 0
        while True:
            match = zone_pattern.search(self.content, pos)
            if not match:
                break

            z_type = match.group(1)
            z_attrs_str = match.group(2)
            start_content = match.end()

            # Find matching end tag
            end_match = end_pattern.search(self.content, start_content)
            if not end_match:
                break # Broken zone

            # If the end marker declares a type, it must match the begin type.
            end_type = end_match.group(1)
            if end_type and end_type != z_type:
                raise AssertionError(f"Zone end type mismatch: begin={z_type} end={end_type}")

            end_content = end_match.start()

            attrs = self._parse_attrs(z_attrs_str)
            self.zones.append({
                "type": z_type,
                "attrs": attrs,
                "content": self.content[start_content:end_content],
                "start": match.start(),
                "end": end_match.end()
            })
            pos = end_match.end()

    def _parse_attrs(self, attr_str: str) -> Dict[str, str]:
        # Robust attribute parser: key=value or key="value with spaces"
        attrs = {}
        # Regex matches key="value" or key=value
        # Allow alphanumeric, underscore, and hyphens in keys (future-proofing)
        pattern = re.compile(r'([a-zA-Z0-9_-]+)=(?:"([^"]*)"|(\S+))')
        for match in pattern.finditer(attr_str):
            key = match.group(1)
            val = match.group(2) if match.group(2) is not None else match.group(3)
            attrs[key] = val
        return attrs

    def extract_artifacts(self):
        # <!-- artifact:type basename="name" -->
        pattern = re.compile(r'<!-- artifact:(\w+)\s+basename="(.*?)" -->')
        for match in pattern.finditer(self.content):
            self.artifacts.append({
                "type": match.group(1),
                "basename": match.group(2)
            })
        return self.artifacts

    def extract_file_markers(self):
        # <!-- file:id=... path=... -->
        pattern = re.compile(r'<!-- file:id=(.*?)\s+path=(.*?) -->')
        for match in pattern.finditer(self.content):
            self.file_markers.append({
                "id": match.group(1),
                "path": match.group(2)
            })
        return self.file_markers

    def parse_meta(self):
        # Find meta zone
        for z in self.zones:
            if z['type'] == 'meta':
                # Extract yaml block
                match = re.search(r'```yaml\n(.*?)\n```', z['content'], re.DOTALL)
                if match and yaml:
                    self.meta = yaml.safe_load(match.group(1))
                elif not yaml:
                    self.meta = {"error": "PyYAML missing"}
                break
        return self.meta

    def get_manifest_header(self):
        for z in self.zones:
            if z['type'] == 'manifest':
                # Look for table header
                lines = z['content'].strip().splitlines()
                for line in lines:
                    if line.startswith("|") and "Path" in line and "Category" in line:
                        return line
        return None

def test_generated_report_is_parsable(tmp_path):
    # Setup
    root = tmp_path / "repo"
    root.mkdir()
    (root / "src").mkdir()
    f1 = root / "src/main.py"
    f1.write_text("print('hello')", encoding="utf-8")

    fi = FileInfo(
        root_label="repo",
        abs_path=f1,
        rel_path=Path("src/main.py"),
        size=100,
        is_text=True,
        md5="abc",
        category="source",
        tags=[],
        ext=".py",
        content=None,
        inclusion_reason="normal"
    )
    # Explicitly set roles to trigger role_semantics deterministically
    fi.roles = ["explicit_role"]

    files = [fi]

    merges_dir = tmp_path / "merges"
    merges_dir.mkdir()

    extras = ExtrasConfig(json_sidecar=True, augment_sidecar=True) # augment won't be found but logic runs

    # Generate
    artifacts = merge.write_reports_v2(
        merges_dir=merges_dir,
        hub=tmp_path,
        repo_summaries=[{"name": "repo", "files": files, "root": root}],
        detail="dev",
        mode="single",
        max_bytes=1000,
        plan_only=False,
        extras=extras
    )

    md_content = artifacts.canonical_md.read_text(encoding="utf-8")

    # Parse
    parser = ReportParser(md_content)

    # 1. Verify Zones
    zone_types = [z['type'] for z in parser.zones]
    assert "meta" in zone_types
    assert "manifest" in zone_types
    assert "code" in zone_types

    # Verify code zone has id attribute
    for z in parser.zones:
        if z['type'] == 'code':
            assert 'id' in z['attrs']
            assert z['attrs']['id'].startswith('FILE:')
            break

    # Verify meta/manifest/structure have ids (same as type)
    for ztype in ['meta', 'manifest', 'structure']:
        # Structure is optional (skipped for machine-lean), but we use dev profile in test
        # Structure is present in dev profile unless machine-lean
        found = False
        for z in parser.zones:
            if z['type'] == ztype:
                found = True
                assert 'id' in z['attrs'], f"Zone {ztype} missing id"
                assert z['attrs']['id'] == ztype
                break
        # manifest is mandatory unless code_only? dev has manifest.
        # structure has id=structure
        if ztype == 'structure' and 'structure' not in zone_types:
             pass # might be skipped if logic changes, but dev has it
        elif ztype == 'manifest':
             assert found, "Manifest zone not found"

    # 2. Verify Meta
    meta = parser.parse_meta()
    if yaml:
        assert meta["merge"]["role_semantics"] == "heuristic"
        assert meta["merge"]["depends_semantics"] == "placeholder"

    # 3. Verify Artifacts
    parser.extract_artifacts()
    art_types = [a['type'] for a in parser.artifacts]
    assert "index_json" in art_types
    # augment_sidecar won't be here because file didn't exist

    # 4. Verify File Markers
    parser.extract_file_markers()
    assert len(parser.file_markers) == 1
    assert parser.file_markers[0]['id'].startswith("FILE:")
    assert str(parser.file_markers[0]['path']) == "src/main.py"

    # 5. Verify Manifest Header
    header = parser.get_manifest_header()
    assert header is not None
    assert "Role?" in header
    assert "Depends?" in header

def test_no_roles_semantics(tmp_path):
    # Setup file without roles
    root = tmp_path / "repo"
    root.mkdir()
    f1 = root / "util.py"
    f1.write_text("pass", encoding="utf-8")

    fi = FileInfo(
        root_label="repo",
        abs_path=f1,
        rel_path=Path("util.py"),
        size=10,
        is_text=True,
        md5="def",
        category="source",
        tags=[],
        ext=".py",
        content=None,
        inclusion_reason="normal"
    )

    merges_dir = tmp_path / "merges"
    merges_dir.mkdir()
    extras = ExtrasConfig.none()

    artifacts = merge.write_reports_v2(
        merges_dir=merges_dir,
        hub=tmp_path,
        repo_summaries=[{"name": "repo", "files": [fi], "root": root}],
        detail="dev",
        mode="single",
        max_bytes=1000,
        plan_only=False,
        extras=extras
    )

    md_content = artifacts.canonical_md.read_text(encoding="utf-8")
    parser = ReportParser(md_content)
    meta = parser.parse_meta()

    if yaml:
        assert "role_semantics" not in meta["merge"]
        assert meta["merge"]["depends_semantics"] == "placeholder"
