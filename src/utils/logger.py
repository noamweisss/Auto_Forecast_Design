"""Explicit logging setup for the application boundary.

Library modules use ``logging.getLogger(__name__)``. Importing them therefore
does not create directories or files; ``main()`` opts into file logging here.
"""

from datetime import datetime
import logging
from pathlib import Path
import sys


LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_HANDLER_MARKER = "_ims_forecast_handler"


def configure_logging(
    log_dir: Path,
    now: datetime,
    log_to_file: bool = True,
) -> logging.Logger:
    """Configure console and optional file logging for one application run."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in list(root_logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            root_logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    setattr(console_handler, _HANDLER_MARKER, True)
    root_logger.addHandler(console_handler)

    if log_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"forecast_{now:%Y-%m-%d}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        setattr(file_handler, _HANDLER_MARKER, True)
        root_logger.addHandler(file_handler)

    return root_logger
