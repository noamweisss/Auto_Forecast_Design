"""
Tests for XML Archive Module

Tests the archive system including:
- Saving XML to archive
- Retrieving fallback data
- Cleanup of old files
"""

import pytest
from datetime import date, timedelta
from pathlib import Path

from src.data.archive import (
    save_to_archive,
    get_fallback_xml,
    get_fallback_for_date,
    cleanup_old_archives,
    get_archive_path,
    list_archives,
    ARCHIVE_DIR,
    MAX_ARCHIVE_DAYS
)


class TestGetArchivePath:
    """Tests for archive path generation."""
    
    def test_correct_filename_format(self):
        """Test that archive path has correct format."""
        test_date = date(2024, 12, 18)
        path = get_archive_path("cities", test_date)
        
        assert path.name == "2024-12-18_cities.xml"
        assert path.parent == ARCHIVE_DIR
    
    def test_country_type(self):
        """Test country type path."""
        test_date = date(2024, 12, 18)
        path = get_archive_path("country", test_date)
        
        assert path.name == "2024-12-18_country.xml"


class TestSaveToArchive:
    """Tests for saving XML to archive."""
    
    def test_creates_archive_directory(self, tmp_path, monkeypatch):
        """Test that archive directory is created if missing."""
        # Use temp directory as archive
        test_archive_dir = tmp_path / "archive"
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        assert not test_archive_dir.exists()
        
        save_to_archive("<test>content</test>", "test", date.today())
        
        assert test_archive_dir.exists()
    
    def test_saves_with_correct_encoding(self, tmp_path, monkeypatch):
        """Test that Hebrew text is saved correctly."""
        test_archive_dir = tmp_path / "archive"
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        hebrew_content = "<city>ירושלים</city>"
        path = save_to_archive(hebrew_content, "test", date.today())
        
        # Read back and verify
        saved_content = path.read_text(encoding='utf-8')
        assert "ירושלים" in saved_content
    
    def test_returns_correct_path(self, tmp_path, monkeypatch):
        """Test that returned path is correct."""
        test_archive_dir = tmp_path / "archive"
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        test_date = date(2024, 12, 18)
        path = save_to_archive("<test/>", "cities", test_date)
        
        assert path.name == "2024-12-18_cities.xml"


class TestGetFallbackXml:
    """Tests for fallback retrieval."""
    
    def test_returns_none_when_no_archive(self, tmp_path, monkeypatch):
        """Test None returned when no archive exists."""
        test_archive_dir = tmp_path / "archive"
        test_archive_dir.mkdir()
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        result = get_fallback_xml("cities")
        
        assert result is None
    
    def test_returns_yesterday_if_available(self, tmp_path, monkeypatch):
        """Test that yesterday's archive is returned first."""
        test_archive_dir = tmp_path / "archive"
        test_archive_dir.mkdir()
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        # Create yesterday's archive
        yesterday = date.today() - timedelta(days=1)
        yesterday_file = test_archive_dir / f"{yesterday.isoformat()}_cities.xml"
        yesterday_file.write_text("<yesterday/>", encoding='utf-8')
        
        result = get_fallback_xml("cities")
        
        assert result is not None
        content, archive_date = result
        assert archive_date == yesterday
        assert "<yesterday/>" in content
    
    def test_skips_to_older_if_yesterday_missing(self, tmp_path, monkeypatch):
        """Test fallback to older archive if yesterday is missing."""
        test_archive_dir = tmp_path / "archive"
        test_archive_dir.mkdir()
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        # Create archive from 3 days ago
        three_days_ago = date.today() - timedelta(days=3)
        old_file = test_archive_dir / f"{three_days_ago.isoformat()}_cities.xml"
        old_file.write_text("<old/>", encoding='utf-8')
        
        result = get_fallback_xml("cities")
        
        assert result is not None
        content, archive_date = result
        assert archive_date == three_days_ago
    
    def test_returns_none_after_max_days(self, tmp_path, monkeypatch):
        """Test None returned if all archives are too old."""
        test_archive_dir = tmp_path / "archive"
        test_archive_dir.mkdir()
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        # Create archive older than MAX_ARCHIVE_DAYS
        very_old = date.today() - timedelta(days=MAX_ARCHIVE_DAYS + 5)
        old_file = test_archive_dir / f"{very_old.isoformat()}_cities.xml"
        old_file.write_text("<too_old/>", encoding='utf-8')
        
        result = get_fallback_xml("cities")
        
        assert result is None


class TestCleanupOldArchives:
    """Tests for archive cleanup."""
    
    def test_deletes_old_files(self, tmp_path, monkeypatch):
        """Test that old files are deleted."""
        test_archive_dir = tmp_path / "archive"
        test_archive_dir.mkdir()
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        # Create old file
        old_date = date.today() - timedelta(days=MAX_ARCHIVE_DAYS + 5)
        old_file = test_archive_dir / f"{old_date.isoformat()}_cities.xml"
        old_file.write_text("<old/>")
        
        deleted = cleanup_old_archives()
        
        assert deleted == 1
        assert not old_file.exists()
    
    def test_preserves_recent_files(self, tmp_path, monkeypatch):
        """Test that recent files are kept."""
        test_archive_dir = tmp_path / "archive"
        test_archive_dir.mkdir()
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        # Create recent file
        recent_date = date.today() - timedelta(days=2)
        recent_file = test_archive_dir / f"{recent_date.isoformat()}_cities.xml"
        recent_file.write_text("<recent/>")
        
        deleted = cleanup_old_archives()
        
        assert deleted == 0
        assert recent_file.exists()
    
    def test_returns_correct_count(self, tmp_path, monkeypatch):
        """Test that correct deletion count is returned."""
        test_archive_dir = tmp_path / "archive"
        test_archive_dir.mkdir()
        monkeypatch.setattr("src.data.archive.ARCHIVE_DIR", test_archive_dir)
        
        # Create multiple old files
        for i in range(3):
            old_date = date.today() - timedelta(days=MAX_ARCHIVE_DAYS + 1 + i)
            (test_archive_dir / f"{old_date.isoformat()}_cities.xml").write_text("<old/>")
        
        deleted = cleanup_old_archives()
        
        assert deleted == 3
