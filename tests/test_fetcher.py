"""
Tests for XML Fetcher Module

Tests the HTTP fetching functionality including:
- Successful fetches
- Retry logic
- UTF-8 encoding for Hebrew text
"""

import pytest
from unittest.mock import patch, Mock
import requests

from src.data.fetcher import (
    fetch_country_forecast,
    fetch_cities_forecast,
    fetch_with_retry,
    fetch_xml,
    COUNTRY_FORECAST_URL,
    CITIES_FORECAST_URL
)


class TestFetchWithRetry:
    """Tests for the retry logic."""
    
    @patch('src.data.fetcher.requests.get')
    def test_fetch_success_first_attempt(self, mock_get):
        """Test successful fetch on first attempt."""
        mock_response = Mock()
        mock_response.content = b'<?xml version="1.0"?><test>Success</test>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = fetch_with_retry("http://example.com/test.xml", retries=3)
        
        assert result is not None
        assert "<test>Success</test>" in result
        assert mock_get.call_count == 1
    
    @patch('src.data.fetcher.time.sleep')  # Skip actual delays
    @patch('src.data.fetcher.requests.get')
    def test_fetch_eventual_success(self, mock_get, mock_sleep):
        """Test success after initial failures."""
        # First two attempts fail with timeout, third succeeds
        mock_success = Mock()
        mock_success.content = b'<test>Success</test>'
        mock_success.raise_for_status = Mock()
        
        # Use Timeout exception which doesn't need response attribute
        mock_get.side_effect = [
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.Timeout("Timeout"),
            mock_success
        ]
        
        result = fetch_with_retry("http://example.com/test.xml", retries=3)
        
        assert result is not None
        assert "<test>Success</test>" in result
        assert mock_get.call_count == 3
    
    @patch('src.data.fetcher.time.sleep')
    @patch('src.data.fetcher.requests.get')
    def test_fetch_all_retries_fail(self, mock_get, mock_sleep):
        """Test that None is returned when all retries fail."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        result = fetch_with_retry("http://example.com/test.xml", retries=3)
        
        assert result is None
        assert mock_get.call_count == 3
    
    @patch('src.data.fetcher.requests.get')
    def test_fetch_timeout(self, mock_get):
        """Test timeout handling."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        result = fetch_with_retry("http://example.com/test.xml", retries=1)
        
        assert result is None


class TestHebrewEncoding:
    """Tests for proper Hebrew text handling."""
    
    @patch('src.data.fetcher.requests.get')
    def test_hebrew_preserved(self, mock_get):
        """Test that Hebrew characters are properly preserved."""
        hebrew_xml = '<?xml version="1.0"?><city>ירושלים</city>'
        mock_response = Mock()
        mock_response.content = hebrew_xml.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = fetch_with_retry("http://example.com/test.xml")
        
        assert result is not None
        assert "ירושלים" in result


class TestFetchFunctions:
    """Tests for the main fetch functions."""
    
    @patch('src.data.fetcher.fetch_with_retry')
    def test_fetch_country_uses_correct_url(self, mock_fetch):
        """Test that country fetch uses correct URL."""
        mock_fetch.return_value = "<xml>test</xml>"
        
        fetch_country_forecast()
        
        mock_fetch.assert_called_once_with(COUNTRY_FORECAST_URL)
    
    @patch('src.data.fetcher.fetch_with_retry')
    def test_fetch_cities_uses_correct_url(self, mock_fetch):
        """Test that cities fetch uses correct URL."""
        mock_fetch.return_value = "<xml>test</xml>"
        
        fetch_cities_forecast()
        
        mock_fetch.assert_called_once_with(CITIES_FORECAST_URL)
