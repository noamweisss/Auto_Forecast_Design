"""Contracts for the ignored Story visual-diagnostic utility."""

from io import BytesIO
import json

from PIL import Image
import pytest


def _png_bytes(color: tuple[int, int, int], size: tuple[int, int] = (4, 3)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_visual_helper_writes_only_named_artifacts_and_metrics(tmp_path):
    from tests.story_visual import create_visual_diagnostics

    reference_path = tmp_path / "reference.png"
    reference_path.write_bytes(_png_bytes((0, 0, 0)))
    rendered = _png_bytes((10, 20, 30))

    metrics = create_visual_diagnostics(reference_path, rendered, tmp_path)

    assert {path.name for path in tmp_path.iterdir()} == {
        "reference.png",
        "rendered.png",
        "overlay.png",
        "difference-amplified.png",
        "metrics.json",
    }
    assert metrics["dimensions"] == [4, 3]
    assert metrics["changed_pixel_bbox"] == [0, 0, 4, 3]
    assert metrics["mean_absolute_channel_difference"] == [10.0, 20.0, 30.0]
    assert metrics["mean_absolute_color_difference"] == 20.0
    assert json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8")) == metrics


def test_visual_helper_rejects_different_dimensions_without_output(tmp_path):
    from tests.story_visual import create_visual_diagnostics

    reference_path = tmp_path / "reference.png"
    reference_path.write_bytes(_png_bytes((0, 0, 0)))

    with pytest.raises(ValueError, match="equal dimensions"):
        create_visual_diagnostics(
            reference_path,
            _png_bytes((0, 0, 0), size=(3, 3)),
            tmp_path / "diagnostics",
        )

    assert not (tmp_path / "diagnostics").exists()
