"""Validate and atomically publish one canonical forecast Story PNG."""

from datetime import date
from io import BytesIO
import logging
import os
from pathlib import Path
import tempfile

from PIL import Image, UnidentifiedImageError


logger = logging.getLogger(__name__)


class OutputSaveError(RuntimeError):
    """A finished PNG could not be validated or safely published."""


def save_forecast_png(
    png_bytes: bytes,
    target_date: date,
    output_directory: Path,
) -> Path:
    """Publish one checked 1080x1920 PNG, replacing a same-date file atomically."""
    _validate_png(png_bytes)

    directory = Path(output_directory).resolve()
    final_path = directory / f"forecast_{target_date.isoformat()}.png"
    temporary_path: Path | None = None
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=directory,
            prefix=f".{final_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(png_bytes)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, final_path)
    except OSError as error:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not remove temporary PNG %s", temporary_path)
        raise OutputSaveError(f"Could not save forecast PNG: {error}") from error

    logger.info("Saved PNG: %s", final_path)
    return final_path


def _validate_png(png_bytes: bytes) -> None:
    if not isinstance(png_bytes, bytes) or not png_bytes:
        raise OutputSaveError("Output must be a nonempty 1080x1920 PNG")
    try:
        with Image.open(BytesIO(png_bytes)) as image:
            image.load()
            image_format = image.format
            image_size = image.size
    except (OSError, UnidentifiedImageError, ValueError) as error:
        raise OutputSaveError(f"Output must be a hydrated 1080x1920 PNG: {error}") from error
    if image_format != "PNG" or image_size != (1080, 1920):
        raise OutputSaveError(
            f"Output must be a hydrated 1080x1920 PNG; got {image_format} {image_size}"
        )
