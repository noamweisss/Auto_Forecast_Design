"""Repository paths used by the application.

Keeping these paths in one small module means commands work no matter which
folder they are launched from.  They describe *where* project files live; code
that needs a different location in a test can still pass or monkeypatch that
location explicitly.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    """Locations owned by this repository."""

    root: Path

    @classmethod
    def from_repository(cls) -> "AppPaths":
        """Build paths from this installed source file, not the shell cwd."""
        return cls(root=Path(__file__).resolve().parent.parent)

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def assets(self) -> Path:
        return self.root / "assets"

    @property
    def archive(self) -> Path:
        return self.root / "archive"

    @property
    def output(self) -> Path:
        return self.root / "output"

    @property
    def ims_fixtures(self) -> Path:
        """Committed sanitized IMS XML used by the offline fixture workflow."""
        return self.root / "tests" / "fixtures" / "ims"

    @property
    def logs(self) -> Path:
        return self.root / "logs"


PATHS = AppPaths.from_repository()
