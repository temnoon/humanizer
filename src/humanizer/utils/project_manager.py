# src/humanizer/utils/project_manager.py
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Set
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    CONFIG = "config"
    DATABASE = "database"
    SECURITY = "security"
    API = "api"

@dataclass
class ProjectFile:
    path: Path
    dependencies: Set[str]
    change_types: Set[ChangeType]
    priority: int  # Lower numbers = higher priority

class ProjectManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.files: Dict[str, ProjectFile] = self._map_project_files()

    def _map_project_files(self) -> Dict[str, ProjectFile]:
        """Create dependency map of project files"""
        base_files = {
            # Configuration Files (Priority 1)
            "config/__init__.py": ProjectFile(
                path=self.project_root / "src/humanizer/config/__init__.py",
                dependencies=set(),
                change_types={ChangeType.CONFIG, ChangeType.SECURITY},
                priority=1
            ),

            # Database Files (Priority 2)
            "db/session.py": ProjectFile(
                path=self.project_root / "src/humanizer/db/session.py",
                dependencies={"config/__init__.py"},
                change_types={ChangeType.DATABASE, ChangeType.SECURITY},
                priority=2
            ),
            "scripts/setup_permissions.py": ProjectFile(
                path=self.project_root / "src/humanizer/scripts/setup_permissions.py",
                dependencies={"config/__init__.py", "db/session.py"},
                change_types={ChangeType.DATABASE, ChangeType.SECURITY},
                priority=2
            ),

            # Core Implementation Files (Priority 3)
            "core/content/importer.py": ProjectFile(
                path=self.project_root / "src/humanizer/core/content/importer.py",
                dependencies={"db/session.py", "config/__init__.py"},
                change_types={ChangeType.DATABASE},
                priority=3
            ),
            "core/content/processor.py": ProjectFile(
                path=self.project_root / "src/humanizer/core/content/processor.py",
                dependencies={"core/embedding/service.py", "db/session.py"},
                change_types={ChangeType.DATABASE},
                priority=3,
            ),
            "core/embedding/service.py": ProjectFile(
                path=self.project_root / "src/humanizer/core/embedding/service.py",
                dependencies={"config/__init__.py"},
                change_types={ChangeType.SECURITY, ChangeType.CONFIG},
                priority=3,
            ),

            # CLI and Scripts (Priority 4)
            "cli/import_cmd.py": ProjectFile(
                path=self.project_root / "src/humanizer/cli/import_cmd.py",
                dependencies={"core/content/importer.py", "config/__init__.py"},
                change_types={ChangeType.CONFIG},
                priority=4
            ),
            "cli/embedding_cmd.py": ProjectFile(
                path=self.project_root / "src/humanizer/cli/embedding_cmd.py",
                dependencies={"core/content/processor.py"},
                change_types={ChangeType.CONFIG},
                priority=4
            ),
        }

        files_affected_by_dimensions = {
            "db/models/content.py": ProjectFile(
                path=self.project_root / "src/humanizer/db/models/content.py",
                dependencies={"config/__init__.py"},
                change_types={ChangeType.CONFIG, ChangeType.DATABASE},
                priority=2
            ),
            "core/embedding/service.py": ProjectFile(
                path=self.project_root / "src/humanizer/core/embedding/service.py",
                dependencies={"config/__init__.py"},
                change_types={ChangeType.CONFIG},
                priority=2
            ),
        }

        return {**base_files, **files_affected_by_dimensions}

    def get_affected_files(self, change_type: ChangeType) -> List[ProjectFile]:
        """Get files affected by a specific type of change"""
        affected = []
        for file in self.files.values():
            if change_type in file.change_types:
                affected.append(file)
        return sorted(affected, key=lambda x: x.priority)

    def generate_update_plan(self, change_type: ChangeType) -> List[str]:
        """Generate ordered list of files that need updating"""
        affected = self.get_affected_files(change_type)
        return [str(f.path.relative_to(self.project_root)) for f in affected]

    def verify_dependencies(self) -> List[str]:
        """Verify all file dependencies exist"""
        missing = []
        for name, file in self.files.items():
            for dep in file.dependencies:
                if dep not in self.files:
                    missing.append(f"{name} depends on missing file {dep}")
        return missing
