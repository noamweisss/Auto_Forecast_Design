"""Explicit application-boundary logging configuration contracts."""

from datetime import datetime

from src.clock import ISRAEL_TIMEZONE
from src.utils.logger import configure_logging


def test_configure_logging_creates_the_dated_file_only_when_called(tmp_path):
    now = datetime(2026, 7, 20, 9, 30, tzinfo=ISRAEL_TIMEZONE)

    logger = configure_logging(tmp_path, now, log_to_file=True)
    logger.info("Hebrew-safe log message")
    for handler in logger.handlers:
        handler.flush()

    log_file = tmp_path / "forecast_2026-07-20.log"
    assert log_file.is_file()
    assert "Hebrew-safe log message" in log_file.read_text(encoding="utf-8")


def test_configure_logging_does_not_create_directory_when_file_logging_is_disabled(tmp_path):
    log_dir = tmp_path / "logs"
    now = datetime(2026, 7, 20, 9, 30, tzinfo=ISRAEL_TIMEZONE)

    configure_logging(log_dir, now, log_to_file=False)

    assert not log_dir.exists()
