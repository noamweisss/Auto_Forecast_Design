"""
Test Date Utilities - Verify Date Formatting Works Correctly

These tests ensure that Hebrew and Georgian date formatting works.
Date display is critical for the header design.
"""

import pytest
from datetime import date

from src.utils.date_utils import (
    get_georgian_date_hebrew,
    get_day_of_week_hebrew,
    format_date_for_filename
)


class TestGeorgianDateHebrew:
    """Tests for Georgian date display in Hebrew."""
    
    def test_december_date_format(self):
        """
        Test that December dates format correctly.
        
        2024-12-18 should become "18 בדצמבר 2024"
        """
        test_date = date(2024, 12, 18)
        result = get_georgian_date_hebrew(test_date)
        assert result == "18 בדצמבר 2024"
    
    def test_january_date_format(self):
        """
        Test that January dates format correctly.
        
        2025-01-05 should become "5 בינואר 2025"
        """
        test_date = date(2025, 1, 5)
        result = get_georgian_date_hebrew(test_date)
        assert result == "5 בינואר 2025"


class TestDayOfWeekHebrew:
    """Tests for Hebrew day of week names."""
    
    def test_wednesday_is_yom_revii(self):
        """
        Test that Wednesday returns "יום רביעי".
        
        December 18, 2024 is a Wednesday.
        """
        test_date = date(2024, 12, 18)
        result = get_day_of_week_hebrew(test_date)
        assert result == "יום רביעי"
    
    def test_saturday_is_yom_shabbat(self):
        """
        Test that Saturday returns "יום שבת".
        
        December 21, 2024 is a Saturday.
        """
        test_date = date(2024, 12, 21)
        result = get_day_of_week_hebrew(test_date)
        assert result == "יום שבת"


class TestFilenameFormatting:
    """Tests for filename-safe date formatting."""
    
    def test_date_iso_format(self):
        """
        Test that dates format as ISO 8601 for filenames.
        
        2024-12-18 should become "2024-12-18"
        """
        test_date = date(2024, 12, 18)
        result = format_date_for_filename(test_date)
        assert result == "2024-12-18"
