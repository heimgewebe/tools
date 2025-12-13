from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

@dataclass
class FileInfo:
    """Represents a file's metadata and content state."""
    rel_path: Path
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_text: bool = False
    size_bytes: int = 0
    content: Optional[str] = None
    truncated: bool = False
    md5_hash: str = ""
    root_label: str = ""  # The repository/root name this file belongs to

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

@dataclass
class MergeArtifacts:
    """Holds the result of a merge operation."""
    main_report_path: Path
    part_files: List[Path] = field(default_factory=list)
    delta_reports: List[Path] = field(default_factory=list)
    json_sidecar: Optional[Path] = None

    def get_all_paths(self) -> List[Path]:
        """Return all paths in deterministic order."""
        paths = []
        if self.json_sidecar:
            paths.append(self.json_sidecar)
        if self.main_report_path and self.main_report_path not in paths:
            paths.append(self.main_report_path)
        for p in self.part_files:
            if p not in paths:
                paths.append(p)
        for p in self.delta_reports:
            if p not in paths:
                paths.append(p)
        return paths
