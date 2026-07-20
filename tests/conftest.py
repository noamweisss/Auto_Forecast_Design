"""Shared helpers for committed, offline IMS XML fixtures."""

from pathlib import Path


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ims"


def load_ims_fixture(name: str) -> str:
    """Return a committed IMS fixture decoded as UTF-8."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")
