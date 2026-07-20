"""Contracts for publishing one canonical Story PNG atomically."""

from datetime import date
from io import BytesIO
import importlib
from pathlib import Path

from PIL import Image
import pytest


TARGET_DATE = date(2025, 12, 18)


def _file_saver_module():
    return importlib.import_module("src.delivery.file_saver")


def _png_bytes(
    size: tuple[int, int] = (1080, 1920),
    color: tuple[int, int, int] = (18, 52, 86),
) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, color).save(output, format="PNG")
    return output.getvalue()


def test_saves_exact_png_to_nested_directory_with_canonical_absolute_path(tmp_path):
    file_saver = _file_saver_module()
    output_directory = tmp_path / "nested" / "forecast"
    png_bytes = _png_bytes()

    output_path = file_saver.save_forecast_png(
        png_bytes,
        TARGET_DATE,
        output_directory,
    )

    assert output_path == (output_directory / "forecast_2025-12-18.png").resolve()
    assert output_path.read_bytes() == png_bytes
    with Image.open(output_path) as image:
        image.load()
        assert image.format == "PNG"
        assert image.size == (1080, 1920)


@pytest.mark.parametrize(
    "invalid_bytes",
    [
        b"",
        b"not an image",
        _png_bytes(size=(1079, 1920)),
        b"\x89PNG\r\n\x1a\ntruncated",
    ],
    ids=["empty", "not-png", "wrong-size", "truncated-png"],
)
def test_invalid_png_fails_before_any_file_is_published(tmp_path, invalid_bytes):
    file_saver = _file_saver_module()
    output_directory = tmp_path / "not-created"

    with pytest.raises(file_saver.OutputSaveError, match="1080x1920 PNG|PNG"):
        file_saver.save_forecast_png(invalid_bytes, TARGET_DATE, output_directory)

    assert not output_directory.exists()


def test_non_png_image_fails_before_publication(tmp_path):
    file_saver = _file_saver_module()
    output = BytesIO()
    Image.new("RGB", (1080, 1920), "red").save(output, format="JPEG")

    with pytest.raises(file_saver.OutputSaveError, match="PNG"):
        file_saver.save_forecast_png(output.getvalue(), TARGET_DATE, tmp_path)

    assert not (tmp_path / "forecast_2025-12-18.png").exists()


def test_same_date_rerun_atomically_replaces_the_complete_file(tmp_path):
    file_saver = _file_saver_module()
    first = _png_bytes(color=(200, 20, 20))
    second = _png_bytes(color=(20, 200, 20))

    output_path = file_saver.save_forecast_png(first, TARGET_DATE, tmp_path)
    replaced_path = file_saver.save_forecast_png(second, TARGET_DATE, tmp_path)

    assert replaced_path == output_path
    assert output_path.read_bytes() == second
    assert not list(tmp_path.glob(".*.tmp"))


def test_failed_atomic_replace_preserves_old_file_and_removes_temporary_file(
    tmp_path,
    monkeypatch,
):
    file_saver = _file_saver_module()
    original = _png_bytes(color=(200, 20, 20))
    replacement = _png_bytes(color=(20, 200, 20))
    output_path = file_saver.save_forecast_png(original, TARGET_DATE, tmp_path)

    def fail_replace(source, destination):
        assert Path(source).parent == tmp_path
        assert Path(destination) == output_path
        raise OSError("replace blocked")

    monkeypatch.setattr(file_saver.os, "replace", fail_replace)

    with pytest.raises(file_saver.OutputSaveError, match="replace blocked"):
        file_saver.save_forecast_png(replacement, TARGET_DATE, tmp_path)

    assert output_path.read_bytes() == original
    assert not list(tmp_path.glob(".*.tmp"))


def test_explicit_output_directory_has_no_cwd_or_global_output_dependency(
    tmp_path,
    monkeypatch,
):
    file_saver = _file_saver_module()
    launch_directory = tmp_path / "launch"
    launch_directory.mkdir()
    explicit_output = tmp_path / "chosen" / "nested"
    monkeypatch.chdir(launch_directory)

    output_path = file_saver.save_forecast_png(
        _png_bytes(),
        TARGET_DATE,
        explicit_output,
    )

    assert output_path.parent == explicit_output.resolve()
    assert not (launch_directory / "output").exists()
    assert not hasattr(file_saver, "OUTPUT_DIR")
