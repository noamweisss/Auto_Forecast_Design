"""
Tests for File Saver Module

Tests the image saving functionality including:
- Dual format output (JPEG + PNG)
- Directory creation
- Cleanup of old files
"""

import pytest
from datetime import date, timedelta
from pathlib import Path
from PIL import Image

from src.delivery.file_saver import (
    save_forecast_image,
    cleanup_old_outputs,
    get_latest_output,
    get_output_path,
    list_outputs,
    OUTPUT_DIR
)


def create_test_image(width=100, height=100):
    """Create a simple test image."""
    return Image.new('RGBA', (width, height), color=(255, 0, 0, 255))


class TestSaveForecastImage:
    """Tests for image saving."""
    
    def test_creates_output_directory(self, tmp_path, monkeypatch):
        """Test that output directory is created if missing."""
        test_output_dir = tmp_path / "output"
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        assert not test_output_dir.exists()
        
        image = create_test_image()
        save_forecast_image(image, "2024-12-18")
        
        assert test_output_dir.exists()
    
    def test_saves_jpeg(self, tmp_path, monkeypatch):
        """Test that JPEG is saved."""
        test_output_dir = tmp_path / "output"
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        image = create_test_image()
        paths = save_forecast_image(image, "2024-12-18")
        
        jpeg_path = Path(paths["jpeg"])
        assert jpeg_path.exists()
        assert jpeg_path.suffix == ".jpg"
    
    def test_saves_png(self, tmp_path, monkeypatch):
        """Test that PNG is saved."""
        test_output_dir = tmp_path / "output"
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        image = create_test_image()
        paths = save_forecast_image(image, "2024-12-18")
        
        png_path = Path(paths["png"])
        assert png_path.exists()
        assert png_path.suffix == ".png"
    
    def test_returns_both_paths(self, tmp_path, monkeypatch):
        """Test that both paths are returned."""
        test_output_dir = tmp_path / "output"
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        image = create_test_image()
        paths = save_forecast_image(image, "2024-12-18")
        
        assert "jpeg" in paths
        assert "png" in paths
    
    def test_filename_includes_date(self, tmp_path, monkeypatch):
        """Test that filename includes the date."""
        test_output_dir = tmp_path / "output"
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        image = create_test_image()
        paths = save_forecast_image(image, "2024-12-18")
        
        assert "2024-12-18" in paths["jpeg"]
        assert "2024-12-18" in paths["png"]
    
    def test_jpeg_is_rgb(self, tmp_path, monkeypatch):
        """Test that JPEG is converted to RGB (no transparency)."""
        test_output_dir = tmp_path / "output"
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        # Create RGBA image
        image = create_test_image()
        paths = save_forecast_image(image, "2024-12-18")
        
        # Load saved JPEG
        saved_jpeg = Image.open(paths["jpeg"])
        assert saved_jpeg.mode == "RGB"


class TestCleanupOldOutputs:
    """Tests for output cleanup."""
    
    def test_deletes_old_files(self, tmp_path, monkeypatch):
        """Test that old files are deleted."""
        test_output_dir = tmp_path / "output"
        test_output_dir.mkdir()
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        # Create old file
        old_date = date.today() - timedelta(days=35)
        old_file = test_output_dir / f"forecast_{old_date.isoformat()}.jpg"
        old_file.write_text("old")
        
        deleted = cleanup_old_outputs(max_age_days=30)
        
        assert deleted == 1
        assert not old_file.exists()
    
    def test_preserves_recent_files(self, tmp_path, monkeypatch):
        """Test that recent files are kept."""
        test_output_dir = tmp_path / "output"
        test_output_dir.mkdir()
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        # Create recent file
        recent_date = date.today() - timedelta(days=5)
        recent_file = test_output_dir / f"forecast_{recent_date.isoformat()}.jpg"
        recent_file.write_text("recent")
        
        deleted = cleanup_old_outputs(max_age_days=30)
        
        assert deleted == 0
        assert recent_file.exists()


class TestGetOutputPath:
    """Tests for output path generation."""
    
    def test_jpeg_extension(self):
        """Test JPEG path has .jpg extension."""
        path = get_output_path("2024-12-18", "jpeg")
        
        assert path.suffix == ".jpg"
        assert "2024-12-18" in str(path)
    
    def test_png_extension(self):
        """Test PNG path has .png extension."""
        path = get_output_path("2024-12-18", "png")
        
        assert path.suffix == ".png"


class TestGetLatestOutput:
    """Tests for finding latest output."""
    
    def test_returns_empty_when_no_outputs(self, tmp_path, monkeypatch):
        """Test empty dict when no outputs exist."""
        test_output_dir = tmp_path / "output"
        test_output_dir.mkdir()
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        result = get_latest_output()
        
        assert result == {}
    
    def test_returns_latest_files(self, tmp_path, monkeypatch):
        """Test that latest files are returned."""
        test_output_dir = tmp_path / "output"
        test_output_dir.mkdir()
        monkeypatch.setattr("src.delivery.file_saver.OUTPUT_DIR", test_output_dir)
        
        # Create some files
        (test_output_dir / "forecast_2024-12-17.jpg").write_text("old")
        (test_output_dir / "forecast_2024-12-18.jpg").write_text("new")
        
        result = get_latest_output()
        
        assert "jpeg" in result
        assert "2024-12-18" in str(result["jpeg"])
