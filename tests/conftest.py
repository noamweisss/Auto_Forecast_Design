"""Shared helpers for committed, offline IMS XML fixtures."""

from pathlib import Path

import pytest

from src.app_paths import PATHS
from src.settings import load_settings


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ims"


def load_ims_fixture(name: str) -> str:
    """Return a committed IMS fixture decoded as UTF-8."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def app_settings():
    """Load the committed application settings once for parser tests."""
    return load_settings(PATHS)
