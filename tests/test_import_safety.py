"""Subprocess coverage for cwd independence and side-effect-free imports."""

import os
import subprocess
import sys

from src.app_paths import PATHS


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PATHS.root)
    return env


def test_imports_create_no_files_and_do_not_load_cwd_dotenv(tmp_path):
    marker = "SLICE1_IMPORT_MARKER"
    (tmp_path / ".env").write_text(f"{marker}=loaded\n", encoding="utf-8")
    script = f"""
import os
from pathlib import Path
os.environ.pop({marker!r}, None)
before = {{path.name for path in Path.cwd().iterdir()}}
import src.data.archive
import src.data.fetcher
import src.data.parser
import src.application
import src.delivery.email_sender
import src.delivery.file_saver
import src.main
after = {{path.name for path in Path.cwd().iterdir()}}
assert os.getenv({marker!r}) is None
assert after == before, (before, after)
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=_subprocess_env(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_settings_and_fixture_parsing_work_outside_repository(tmp_path):
    fixture = PATHS.root / "tests" / "fixtures" / "ims" / "cities_forecast.xml"
    script = f"""
from datetime import date, datetime, timezone
from pathlib import Path
from src.app_paths import AppPaths
from src.data.parser import parse_cities_forecast
from src.data.snapshots import FeedType, SnapshotSource, build_snapshot
from src.settings import load_settings
paths = AppPaths.from_repository()
settings = load_settings(paths)
xml = Path({str(fixture)!r}).read_text(encoding='utf-8')
snapshot = build_snapshot(
    xml,
    FeedType.CITIES,
    source=SnapshotSource.FIXTURE,
    fetched_at=datetime(2025, 12, 17, 3, 0, tzinfo=timezone.utc),
)
cities = parse_cities_forecast([snapshot], date(2025, 12, 17), settings=settings)
assert len(cities) == 15
assert next(city for city in cities if city.city_id == '510').internal_key == 'jerusalem'
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=_subprocess_env(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
